import os
import shutil
import tkinter as tk
from tkinter import filedialog

# ==================== 配置区 (Config) ====================
# 关键词与新文件名的映射关系
# 格式: {"文件名中包含的关键词": "重命名后的文件名(不含扩展名)"}
KEYWORD_MAPPING = {
    "烤字": "ceramic baked lettering",
    "瓶签": "Label",
    "盒子": "box",
    "中盒": "box",
    "小盒": "small box",
    "说明书": "insert",
    "外箱": "carton",
}

# 提取产品名时需要去掉的首尾分隔符
TRIM_SEPARATORS = " -_—–"
# =======================================================


def choose_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    initial_dir = os.getcwd()
    selected_dir = filedialog.askdirectory(
        title="请选择需要处理的文件夹",
        initialdir=initial_dir,
    )

    root.destroy()
    return selected_dir


def find_file_type(file_name):
    for keyword, new_name in KEYWORD_MAPPING.items():
        if keyword in file_name:
            return keyword, new_name
    return "", ""


def extract_product_spec(file_stem, type_keyword):
    keyword_index = file_stem.find(type_keyword)
    if keyword_index == -1:
        return ""

    product_spec = file_stem[:keyword_index].strip(TRIM_SEPARATORS)
    return product_spec


def organize_files(directory_path):
    if not directory_path:
        print("未选择文件夹，程序已取消。")
        return

    if not os.path.exists(directory_path):
        print(f"指定的文件夹不存在: {directory_path}")
        return

    files = []
    for current_root, _, file_names in os.walk(directory_path):
        for file_name in file_names:
            files.append((current_root, file_name))

    success_count = 0

    print(f"开始处理文件夹及其所有子文件夹: {directory_path}\n")

    for current_root, file_name in files:
        old_file_path = os.path.join(current_root, file_name)

        if not os.path.isfile(old_file_path):
            continue

        type_keyword, file_type = find_file_type(file_name)
        if not type_keyword:
            print(f"跳过: 无法在 '{file_name}' 中找到可识别关键词。")
            continue

        file_stem, extension = os.path.splitext(file_name)
        product_spec = extract_product_spec(file_stem, type_keyword)
        if not product_spec:
            print(f"跳过: 无法从 '{file_name}' 中提取产品名。")
            continue

        folder_path = os.path.join(current_root, product_spec)
        os.makedirs(folder_path, exist_ok=True)

        new_file_name = f"{file_type}{extension}"
        new_file_path = os.path.join(folder_path, new_file_name)

        if os.path.exists(new_file_path):
            print(f"警告: 目标文件 {new_file_path} 已存在，跳过移动。")
            continue

        print(f"成功: '{file_name}'\n  -> 移动至 '{os.path.join(product_spec, new_file_name)}'\n")
        shutil.move(old_file_path, new_file_path)
        success_count += 1

    print(f"执行完毕！共成功处理了 {success_count} 个文件。")


if __name__ == "__main__":
    selected_directory = choose_directory()
    organize_files(selected_directory)
