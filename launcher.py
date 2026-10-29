#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CioData 源码版启动器（需本机 Python 3.9 ~ 3.12，推荐 3.12）
=============================================================
本启动器使用【本机 Python】，不依赖内置 runtime/：
  1. 自动创建虚拟环境 .venv（首次）；
  2. 用清华/阿里/官方镜像自动安装 requirements.txt 里的依赖；
  3. 启动 main.py。

适合开发调试，或直接用本机 Python 跑源码。
若要"免安装、双击即用"，请用便携版：CioData_portable_win64/CioData/启动 CioData.bat

用法：
  双击 run.bat  （Windows，等价于 python launcher.py）
  python launcher.py            # 装依赖 + 启动
  python launcher.py --check   # 仅做依赖自检，不启动 GUI
"""

import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(HERE, ".venv")
VENV_PY = (os.path.join(VENV, "Scripts", "python.exe")
           if os.name == "nt" else os.path.join(VENV, "bin", "python"))
APP = os.path.join(HERE, "main.py")
REQ = os.path.join(HERE, "requirements.txt")

# 源码版依赖（与 requirements.txt 保持一致）
REQUIRED = ["numpy", "pandas", "openpyxl", "requests", "customtkinter", "tkinter"]

MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.org/simple",
]


def _log(msg=""):
    print(msg)


def ensure_venv():
    """创建 .venv（若不存在）。返回 venv 里的 python 路径。"""
    if os.path.exists(VENV_PY):
        return VENV_PY
    _log("[1/3] 创建虚拟环境 .venv ...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV])
    except subprocess.CalledProcessError as e:
        _log("\n[错误] 无法创建虚拟环境：%s" % e)
        _log("       请确认本机 Python 3.9~3.12 安装完整（含 venv 模块）。")
        _log("       也可手动：python -m venv .venv")
        input("按回车退出...")
        sys.exit(1)
    return VENV_PY


def pip_install(venv_py):
    """用多镜像重试安装 requirements.txt。成功返回 True。"""
    last_err = None
    for mirror in MIRRORS:
        _log("  · 使用镜像 %s" % mirror)
        try:
            subprocess.check_call([
                venv_py, "-m", "pip", "install", "--prefer-binary",
                "-i", mirror, "-r", REQ,
            ])
            return True
        except subprocess.CalledProcessError as e:
            last_err = e
            _log("    失败，尝试下一个镜像...")
    if last_err:
        _log("\n[错误] 依赖安装失败：%s" % last_err)
    return False


def probe_deps(venv_py):
    """检查 REQUIRED 模块是否可导入。返回 {模块: 'ok'|'fail:...'}。"""
    code = (
        "import importlib, json\n"
        "out = {}\n"
        "for m in %r:\n"
        "    try:\n"
        "        importlib.import_module(m)\n"
        "        out[m] = 'ok'\n"
        "    except Exception as e:\n"
        "        out[m] = 'fail:%%s' %% e\n"
        "print('<<<P>>>' + json.dumps(out, ensure_ascii=False))"
    ) % (REQUIRED,)
    try:
        out = subprocess.check_output(
            [venv_py, "-c", code], stderr=subprocess.DEVNULL, text=True
        )
        for line in out.splitlines():
            if line.startswith("<<<P>>>"):
                return json.loads(line[len("<<<P>>>"):])
    except Exception:
        pass
    return {}


def main():
    _log("=" * 60)
    _log("  CioData 源码版启动器（本机 Python %s）" % sys.version.split()[0])
    _log("  位置：%s" % HERE)
    _log("=" * 60)

    if not os.path.exists(APP):
        _log("\n[错误] 找不到 main.py，目录不完整。")
        input("按回车退出...")
        return 1

    venv_py = ensure_venv()

    _log("\n[2/3] 检查依赖...")
    status = probe_deps(venv_py)
    missing = [m for m, s in status.items() if not str(s).startswith("ok")]
    if missing or not status:
        _log("  需要安装依赖：%s" % (", ".join(missing) if missing else "全部"))
        if not pip_install(venv_py):
            _log("       请检查网络后重试，或手动在 .venv 中执行：")
            _log("       %s -m pip install -r requirements.txt" % venv_py)
            input("按回车退出...")
            return 1
        status = probe_deps(venv_py)
        missing = [m for m, s in status.items() if not str(s).startswith("ok")]
        if missing:
            _log("\n[错误] 以下依赖仍缺失：%s" % ", ".join(missing))
            _log("       常见原因：当前 Python 版本与 customtkinter 不兼容"
                 "（建议用 Python 3.12），或网络不通。")
            _log("       也可直接用便携版（自带 Python 3.12 + 全部依赖）。")
            input("按回车退出...")
            return 1
    else:
        _log("  依赖齐全，跳过安装。")

    if "--check" in sys.argv:
        _log("\n[--check] 自检通过，不启动应用。")
        return 0

    _log("\n[3/3] 启动应用...")
    _log("-" * 60)
    try:
        rc = subprocess.call([venv_py, APP], cwd=HERE)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        _log("\n[错误] 启动失败：%s" % e)
        input("按回车退出...")
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
