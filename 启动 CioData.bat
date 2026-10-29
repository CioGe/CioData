@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
title CioData 便携版

rem ============================================================
rem  CioData 便携版 / 免安装
rem  使用本目录内自带的 Python 3.12，不读系统 Python、
rem  不写注册表、不改 PATH、不联网安装任何东西。
rem ============================================================

set "PY=%~dp0runtime\python.exe"

if not exist "%PY%" (
    echo.
    echo  [错误] 找不到内置的 runtime\python.exe
    echo.
    echo  这说明文件夹解压不完整，常见原因：
    echo    1. 只从压缩包里拖出来了一部分文件
    echo    2. 杀毒软件把 python.exe 当病毒删了
    echo.
    echo  处理办法：关掉杀毒软件实时防护，把压缩包整个重新解压一遍。
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0portable_launcher.py" (
    echo.
    echo  [错误] 找不到 portable_launcher.py，文件夹不完整。
    echo         请把压缩包整个重新解压。
    echo.
    pause
    exit /b 1
)

rem 清掉可能干扰内置 Python 的环境变量
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONSTARTUP="

"%PY%" "%~dp0portable_launcher.py" %*
set "RC=!ERRORLEVEL!"

rem 正常退出（RC=0）就直接关窗口；出错才停住让人看信息。
if not "!RC!"=="0" (
    echo.
    echo  [程序异常退出，返回码 !RC!]
    echo  日志位置：%~dp0debug_launcher.log
    echo.
    pause
)

endlocal
exit /b %RC%
