@echo off
chcp 65001 >nul
cd /d %~dp0
title CioData 启动器

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [错误] 未检测到 Python。
    echo 请先从 https://www.python.org/downloads/ 安装 Python 3.9 ~ 3.12（推荐 3.12），
    echo 安装界面底部务必勾选 "Add Python to PATH"，装完重启电脑再试。
    echo 若只想免安装双击即用，请用便携版：CioData_portable_win64\CioData\启动 CioData.bat
    echo.
    pause
    exit /b 1
)

python launcher.py
if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请查看 debug_launcher.log 或上方输出。
    pause
)
