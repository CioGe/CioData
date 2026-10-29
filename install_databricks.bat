@echo off
chcp 65001 >nul
cd /d %~dp0
title CioData - Databricks 依赖安装

echo ============================================================
echo   CioData · Databricks 连接依赖安装
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境 .venv\
    echo 请先双击「run.bat」完成首次初始化（创建虚拟环境+安装核心依赖），
    echo 然后再运行本脚本。
    echo.
    pause
    exit /b 1
)

echo [1/2] 正在安装 databricks-sql-connector（清华镜像，优先二进制）...
.venv\Scripts\python.exe -m pip install --prefer-binary --no-cache-dir databricks-sql-connector -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo [提示] 清华源失败，尝试阿里云镜像...
    .venv\Scripts\python.exe -m pip install --prefer-binary --no-cache-dir databricks-sql-connector -i https://mirrors.aliyun.com/pypi/simple
)
if errorlevel 1 (
    echo.
    echo [提示] 阿里源失败，尝试官方源...
    .venv\Scripts\python.exe -m pip install --prefer-binary --no-cache-dir databricks-sql-connector
)

echo.
echo [2/2] 验证安装...
.venv\Scripts\python.exe -c "from databricks import sql; print('[OK] databricks-sql-connector 安装成功')"
if errorlevel 1 (
    echo.
    echo [失败] 安装未成功。可能原因：
    echo   - 网络不通（可尝试手机热点后重跑本脚本）
    echo   - 系统缺少 C++ 编译工具（thrift/lz4 需要编译时）
    echo     建议改用 Excel/CSV 方式加载数据，功能不受影响。
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   安装完成！重启 CioData 后，左侧数据源切换到
echo   「Databricks」标签即可连接。
echo ============================================================
echo.
pause
