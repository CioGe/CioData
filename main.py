#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CioData 入口文件。
直接运行: python main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _install_excepthook():
    """未捕获异常时打印堆栈 + 非模态错误窗，而不是静默消失或模态卡死。"""
    import traceback
    import i18n

    def hook(exc_type, exc, tb):
        traceback.print_exc()
        try:
            import tkinter
            win = tkinter.Toplevel()
            win.title(i18n.t("common.error_title"))
            win.attributes("-topmost", True)
            win.geometry("460x200")
            tkinter.Label(win, text=i18n.t("common.error_body", err=exc),
                          justify="left", wraplength=420).pack(padx=20, pady=20)
            tkinter.Button(win, text=i18n.t("common.ok"), width=10,
                           command=win.destroy).pack(pady=(0, 16))
        except Exception:
            pass

    sys.excepthook = hook


def main():
    _install_excepthook()
    import customtkinter as ctk  # noqa: F401
    from ui.app import App

    app = App()
    app.mainloop()
    # Windows + Tk8.6 下 mainloop 返回后解释器收尾可能死锁（关窗后黑窗口不退），
    # 此时所有状态已在 _on_close 中持久化，直接强制退出。
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(0)


if __name__ == "__main__":
    main()
