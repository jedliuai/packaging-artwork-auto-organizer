import csv
import os
import re
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog


SCRIPT_DIR = Path(__file__).resolve().parent
MAPPING_FILE = SCRIPT_DIR / "映射表.csv"

SOURCE_COLUMN = "原包装名中包含文字"
TARGET_COLUMN = "转换为名字"

FILE_TYPE_MAPPING = {
    "烤字": "ceramic baked lettering",
    "瓶签": "Label",
    "铝箔": "Label",
    "胶囊壳": "capsule shell",
    "盒子": "box",
    "中盒": "box",
    "小盒": "small box",
    "说明书": "insert",
    "外箱": "carton",
}

SPEC_PATTERN = re.compile(
    r"(?P<spec>\d+(?:\.\d+)?\s*(?:mg|g|kg|ml|l|iu|万iu|万单位|单位|%))",
    re.IGNORECASE,
)

INVALID_FILENAME_CHARS = r'<>:"/\|?*'


def choose_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    selected_dir = filedialog.askdirectory(
        title="请选择需要处理的文件夹",
        initialdir=os.getcwd(),
    )

    root.destroy()
    return selected_dir


def load_mapping(mapping_path):
    if not mapping_path.exists():
        raise FileNotFoundError(f"未找到映射表：{mapping_path}")

    mapping = []
    with mapping_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):
            source = (row.get(SOURCE_COLUMN) or "").strip()
            target = (row.get(TARGET_COLUMN) or "").strip()

            if not source or not target:
                print(f"跳过映射表第 {row_number} 行：原文字或转换名为空。")
                continue

            mapping.append((source, target))

    if not mapping:
        raise ValueError("映射表没有可用规则。")

    return sorted(mapping, key=lambda item: len(item[0]), reverse=True)


def sanitize_name(name):
    cleaned = name
    for char in INVALID_FILENAME_CHARS:
        cleaned = cleaned.replace(char, " ")

    return re.sub(r"\s+", " ", cleaned).strip().rstrip(".")


def extract_spec(text, matched_text):
    start_index = text.find(matched_text)
    if start_index == -1:
        return ""

    text_after_match = text[start_index + len(matched_text) :]
    match = SPEC_PATTERN.search(text_after_match)
    if not match:
        return ""

    return re.sub(r"\s+", "", match.group("spec"))


def find_product_rule(text, mapping):
    for source, target in mapping:
        if source in text:
            return source, target

    return "", ""


def build_product_folder_name(text, mapping):
    source, target = find_product_rule(text, mapping)
    if not source:
        return ""

    spec = extract_spec(text, source)
    if spec:
        return sanitize_name(f"{target} {spec}")

    return sanitize_name(target)


def build_standard_file_name(file_name):
    file_path = Path(file_name)
    for keyword, target_name in FILE_TYPE_MAPPING.items():
        if keyword in file_path.stem:
            return f"{sanitize_name(target_name)}{file_path.suffix}"

    return ""


def collect_files(root_path):
    files = []
    for current_root, _, file_names in os.walk(root_path):
        for file_name in file_names:
            file_path = Path(current_root) / file_name
            if file_path.is_file():
                files.append(file_path)

    return files


def collect_directories(root_path):
    directories = [root_path]
    for current_root, dir_names, _ in os.walk(root_path):
        current_path = Path(current_root)
        for dir_name in dir_names:
            directories.append(current_path / dir_name)

    return sorted(directories, key=lambda path: len(path.parts), reverse=True)


def is_already_target_folder(folder_path, target_folder_name, mapping):
    current_name = folder_path.name
    if current_name == target_folder_name:
        return True

    renamed_current_folder = build_product_folder_name(current_name, mapping)
    return renamed_current_folder == target_folder_name


def move_and_rename_files(root_path, mapping):
    success_count = 0
    files = collect_files(root_path)

    for file_path in files:
        if not file_path.exists():
            continue

        product_folder_name = build_product_folder_name(file_path.stem, mapping)
        if not product_folder_name:
            print(f"跳过文件：'{file_path.name}' 未匹配映射表中的产品规则。")
            continue

        new_file_name = build_standard_file_name(file_path.name)
        if not new_file_name:
            print(f"跳过文件：'{file_path.name}' 未匹配包装稿类型规则。")
            continue

        if is_already_target_folder(file_path.parent, product_folder_name, mapping):
            target_folder = file_path.parent
        else:
            target_folder = file_path.parent / product_folder_name

        target_folder.mkdir(exist_ok=True)
        target_path = target_folder / new_file_name

        if target_path.exists():
            print(f"跳过文件：目标文件已存在：{target_path}")
            continue

        print(f"文件成功：'{file_path.name}' -> '{target_folder.name}\\{new_file_name}'")
        shutil.move(str(file_path), str(target_path))
        success_count += 1

    return success_count


def rename_product_folders(root_path, mapping):
    success_count = 0
    directories = collect_directories(root_path)

    for folder_path in directories:
        if not folder_path.exists() or not folder_path.is_dir():
            continue

        new_folder_name = build_product_folder_name(folder_path.name, mapping)
        if not new_folder_name:
            continue

        if folder_path.name == new_folder_name:
            continue

        new_path = folder_path.with_name(new_folder_name)
        if new_path.exists():
            print(f"跳过文件夹：目标文件夹已存在：{new_path}")
            continue

        print(f"文件夹成功：'{folder_path.name}' -> '{new_folder_name}'")
        folder_path.rename(new_path)
        success_count += 1

    return success_count


def remove_empty_folders(root_path):
    removed_count = 0
    directories = collect_directories(root_path)

    for folder_path in directories:
        if folder_path == root_path:
            continue

        if not folder_path.exists() or not folder_path.is_dir():
            continue

        try:
            next(folder_path.iterdir())
        except StopIteration:
            folder_path.rmdir()
            removed_count += 1

    return removed_count


def process_directory(directory_path):
    if not directory_path:
        print("未选择文件夹，程序已取消。")
        return

    root_path = Path(directory_path)
    if not root_path.exists():
        print(f"指定的文件夹不存在：{root_path}")
        return

    mapping = load_mapping(MAPPING_FILE)

    print(f"开始处理包装稿：{root_path}\n")

    file_success_count = move_and_rename_files(root_path, mapping)
    folder_success_count = rename_product_folders(root_path, mapping)
    removed_empty_count = remove_empty_folders(root_path)

    print(
        "\n执行完毕！"
        f"共成功整理 {file_success_count} 个文件，"
        f"重命名 {folder_success_count} 个文件夹，"
        f"清理 {removed_empty_count} 个空文件夹。"
    )


if __name__ == "__main__":
    selected_directory = choose_directory()
    process_directory(selected_directory)
