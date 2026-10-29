#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CioData 便携版（免安装）启动器
=====================================
本目录自带完整的 Python 3.12 + pandas/numpy/openpyxl/customtkinter/Tkinter。
不读系统 Python、不写注册表、不改 PATH、不联网装任何东西。
整个文件夹拷到 U 盘或任意目录都能直接跑（路径含中文/空格也没问题）。

用法：
  双击「启动 CioData.bat」
  命令行：runtime\\python.exe portable_launcher.py --check
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

HERE = Path(__file__).parent.resolve()
RUNTIME = HERE / "runtime"
PYEXE = RUNTIME / "python.exe"
APP = HERE / "main.py"
LOG = HERE / "debug_launcher.log"

REQUIRED = [
    "numpy", "pandas", "openpyxl", "requests", "customtkinter", "tkinter", "PIL",
    "dateutil", "pytz", "tzdata", "urllib3", "certifi", "charset_normalizer",
    "sqlite3", "tkinter.filedialog", "tkinter.font", "tkinter.ttk",
]

_PROBE = r'''
import sys, json, os
out = {}
for m in sys.argv[1].split(","):
    try:
        mod = __import__(m)
        v = getattr(mod, "__version__", "")
        out[m] = ["ok", str(v or "ok"), str(getattr(mod, "__file__", ""))]
    except BaseException as e:
        out[m] = ["fail", "%s: %s" % (type(e).__name__, e), ""]
# tkinter 真正可用性：连上 Tcl 解释器并真正画一个窗口才算行
try:
    import tkinter
    t = tkinter.Tcl()
    patch = t.eval("info patchlevel")
    r = tkinter.Tk()
    r.withdraw()
    r.update_idletasks()
    r.destroy()
    out["__tcl__"] = ["ok", "Tcl/Tk " + patch, ""]
except BaseException as e:
    out["__tcl__"] = ["fail", "%s: %s" % (type(e).__name__, e), ""]
# pandas 读写 Excel 的实际链路（引擎 + lib 是否齐全）
try:
    import io, pandas as pd
    buf = io.BytesIO()
    pd.DataFrame({"a": [1, 2]}).to_excel(buf, index=False)
    buf.seek(0)
    pd.read_excel(buf)
    out["__excel__"] = ["ok", "pandas + openpyxl", ""]
except BaseException as e:
    out["__excel__"] = ["fail", "%s: %s" % (type(e).__name__, e), ""]
# Databricks 连接器：本版已内置，失败要报错（不是可选了）
try:
    import logging as _lg
    _lg.getLogger("databricks.sql.client").setLevel(_lg.ERROR)
    import databricks.sql as _dbx
    ver = getattr(_dbx, "__version__", "?")
    # 顺带确认几个关键依赖在位
    import lz4, thrift, oauthlib  # noqa: F401
    out["__dbx__"] = ["ok", "connector %s" % ver, ""]
except BaseException as e:
    out["__dbx__"] = ["fail", "%s: %s" % (type(e).__name__, e), ""]
print("<<<P>>>" + json.dumps(out, ensure_ascii=False))
# 结果同时落盘：个别安全软件会注入子进程并持有 stdout 管道句柄不放，
# 父进程等管道 EOF 就会卡死（实测本机出现过）；文件通道不受影响。
# 另外探针建过 Tk 窗口，Windows + Tk8.6 解释器收尾也可能死锁，
# 与 main.py 同理直接 os._exit，不等 finalize。
_probe_out = os.environ.get("CIODATA_PROBE_OUT")
if _probe_out:
    with open(_probe_out, "w", encoding="utf-8") as _f:
        _f.write(json.dumps(out, ensure_ascii=False))
sys.stdout.flush()
os._exit(0)
'''


def build_env():
    """构造干净运行环境：屏蔽系统 Python 与用户级包，钉死 Tcl/Tk 路径。"""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONNOUSERSITE"] = "1"
    env.pop("PYTHONPATH", None)
    env["PYTHONHOME"] = str(RUNTIME)
    env["TCL_LIBRARY"] = str(RUNTIME / "tcl" / "tcl8.6")
    env["TK_LIBRARY"] = str(RUNTIME / "tcl" / "tk8.6")
    env["PATH"] = os.pathsep.join([
        str(RUNTIME), str(RUNTIME / "DLLs"), env.get("PATH", "")
    ])
    return env


def main():
    print("=" * 60)
    print("  CioData 便携版（免安装 · 自带 Python 3.12）")
    print("  位置：%s" % HERE)
    print("=" * 60)

    if not APP.exists():
        print("\n[错误] 找不到 main.py，文件夹不完整，请重新解压。")
        input("按回车退出...")
        return 1
    if not PYEXE.exists():
        print("\n[错误] 找不到 runtime\\python.exe，文件夹不完整。")
        print("       请把压缩包**整个**重新解压（不要只拖几个文件出来）。")
        input("按回车退出...")
        return 1

    env = build_env()

    print("\n[1/2] 检查内置依赖（不联网、不读系统环境）...")
    payload = None
    out_file = HERE / "_probe_result.json"
    err_file = HERE / "_probe_error.log"
    for f in (out_file, err_file):
        if f.exists():
            try:
                f.unlink()
            except Exception:
                pass
    env["CIODATA_PROBE_OUT"] = str(out_file)
    try:
        # 走文件通道拿结果，stdout/stderr 不用管道：
        # 子进程即使被安全软件注入拖住句柄，也不会把父进程卡死。
        with open(err_file, "w", encoding="utf-8") as errf:
            p = subprocess.Popen([str(PYEXE), "-c", _PROBE, ",".join(REQUIRED)],
                                 cwd=str(HERE), env=env,
                                 stdout=subprocess.DEVNULL, stderr=errf)
            # 轮询结果文件而不是 p.wait() 阻塞等待：
            # 个别环境下（安全软件注入/作业对象信号延迟）子进程已退出并写出
            # 结果文件，p.wait() 却长时间不返回；文件一到就继续，最稳。
            deadline = time.time() + 180
            finished = False
            while time.time() < deadline:
                if out_file.exists() and out_file.stat().st_size > 0:
                    finished = True
                    break
                if p.poll() is not None:
                    finished = True
                    break
                time.sleep(0.4)
            if not finished:
                p.kill()
                p.wait()
                print("\n[错误] 自检超时（180 秒）。")
                print("       常见原因：文件放在网络盘/移动硬盘且传输极慢，或被杀软实时扫描卡住。")
                print("       建议把整个文件夹复制到本地磁盘再试。")
                input("按回车退出...")
                return 1
        if out_file.exists():
            try:
                payload = json.loads(out_file.read_text(encoding="utf-8"))
            except ValueError:
                payload = None
    except Exception as e:
        print("\n[错误] 自检子进程失败：%s" % e)
        input("按回车退出...")
        return 1

    if not payload:
        print("\n[错误] 内置 Python 启动异常，错误输出：")
        try:
            print(err_file.read_text(encoding="utf-8", errors="replace")[-1500:] or "(无输出)")
        except Exception:
            print("(无输出)")
        print("\n常见原因：")
        print("  · 解压不完整（被杀毒软件拦截）—— 关掉杀软重新解压")
        print("  · 文件夹放在只读网络盘 —— 换到本地磁盘或 U 盘")
        input("按回车退出...")
        return 1

    bad = []
    labels = {
        "__tcl__": "Tcl/Tk 运行时",
        "__excel__": "Excel 读写链路",
        "__dbx__": "Databricks 连接",
    }
    order = ["numpy", "pandas", "openpyxl", "PIL", "customtkinter", "tkinter",
             "tkinter.filedialog", "tkinter.font", "tkinter.ttk", "sqlite3",
             "requests", "urllib3", "certifi", "charset_normalizer", "dateutil",
             "pytz", "tzdata", "__tcl__", "__excel__", "__dbx__"]

    for m in order:
        info = payload.get(m)
        if not info:
            continue
        label = labels.get(m, m)
        state, detail = info[0], info[1]
        if state == "ok":
            print("   OK    %-20s %s" % (label, detail))
        elif state == "opt":
            print("   --    %-20s %s" % (label, detail))
        else:
            print("   FAIL  %-20s %s" % (label, detail))
            bad.append(m)

    if bad:
        print("\n[错误] 内置依赖不完整：%s" % ", ".join(bad))
        print("       本压缩包可能被安全软件删改过，请重新解压一份完整的。")
        print("       若反复失败，把压缩包换到别的目录解压再试。")
        input("按回车退出...")
        return 1

    # 清理探针临时文件
    for f in (out_file, err_file):
        try:
            if f.exists():
                f.unlink()
        except Exception:
            pass

    if "--check" in sys.argv:
        print("\n[--check] 体检通过，不启动应用。")
        return 0

    print("\n[2/2] 启动应用...")
    print("-" * 60)
    try:
        rc = subprocess.run([str(PYEXE), str(APP)], cwd=str(HERE), env=env).returncode
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print("\n[错误] 启动失败：%s" % e)
        input("按回车退出...")
        return 1

    if rc != 0:
        print("\n[错误] 应用异常退出，返回码 %s" % rc)
        print("       日志：%s" % LOG)
        input("按回车退出...")
    return rc


if __name__ == "__main__":
    sys.exit(main())
