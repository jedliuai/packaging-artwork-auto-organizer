@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

set "SCRIPT=包装稿自动分类工具.py"

if not exist "%SCRIPT%" (
    echo 未找到启动文件：%SCRIPT%
    echo.
    pause
    exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
    py "%SCRIPT%"
    goto end
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "%SCRIPT%"
    goto end
)

echo 未检测到 Python。
echo 请先安装 Python，并勾选“Add Python to PATH”。
echo.
pause
exit /b 1

:end
if not %errorlevel%==0 (
    echo.
    echo 程序运行失败，错误码：%errorlevel%
    pause
    exit /b %errorlevel%
)
