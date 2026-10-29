# -*- coding: utf-8 -*-
"""
SQL编辑器组件：等宽字体 + 行号槽 + 关键字高亮（防抖刷新）。
只负责编辑体验，不负责执行。
"""

import re
import tkinter as tk
import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder

_SQL_KEYWORDS = [
    "SELECT", "FROM", "WHERE", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "FULL", "CROSS", "ON", "USING",
    "AS", "AND", "OR", "NOT", "IN", "IS", "NULL", "LIKE", "BETWEEN", "EXISTS",
    "CASE", "WHEN", "THEN", "ELSE", "END", "DISTINCT", "UNION", "ALL",
    "WITH", "INSERT", "UPDATE", "DELETE", "INTO", "VALUES", "SET",
    "ASC", "DESC", "OVER", "PARTITION", "ROWS", "RANGE", "UNBOUNDED", "PRECEDING",
    "CURRENT", "ROW", "CAST", "COALESCE", "NULLIF", "IFNULL",
    "COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "ABS", "LENGTH", "SUBSTR",
    "UPPER", "LOWER", "TRIM", "REPLACE", "STRFTIME", "DATE", "DATETIME", "JULIANDAY",
    "IF", "IIF", "GROUP_CONCAT", "TOTAL", "RANDOM", "PRINTF",
]
_KEYWORD_RE = re.compile(
    r"(?P<comment>--[^\n]*|/\*.*?\*/)"
    r"|(?P<string>'(?:[^']|'')*')"
    r'|(?P<qident>"(?:[^"]|"")*")'
    r"|(?P<number>\b\d+\.?\d*\b)"
    r"|(?P<func>\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\())"
    r"|(?P<word>[A-Za-z_][A-Za-z0-9_]*)",
    re.DOTALL,
)


class SqlEditor(ctk.CTkFrame):
    """带行号和语法高亮的 SQL 编辑区。"""

    def __init__(self, master, on_change=None, **kw):
        super().__init__(master, fg_color=T.CODE_BG, border_width=1,
                         border_color=T.BORDER, corner_radius=T.RADIUS_SM, **kw)
        self._fonts = FontsHolder.get()
        self._on_change = on_change
        self._highlight_job = None
        self._suppress = False

        # 行号槽（原生 tk.Text，避免 CTkTextbox 的自动滚动条干扰）
        self.gutter = tk.Text(
            self, width=4, padx=8, pady=10, wrap="none",
            bd=0, highlightthickness=0, relief="flat",
            state="disabled", takefocus=0, cursor="arrow",
            font=self._fonts.mono_sm,
        )
        self.gutter.pack(side="left", fill="y")

        # 代码编辑区
        self.code = ctk.CTkTextbox(
            self, fg_color=T.CODE_BG, text_color=T.CODE_TEXT,
            font=self._fonts.mono, wrap="none", height=120,
            corner_radius=0, border_width=0, padx=10, pady=8,
            activate_scrollbars=True,
        )
        self.code.pack(side="left", fill="both", expand=True)

        # 高亮标签（原生 tag_config 不认主题二元组，先解析）
        self.code.tag_config("kw", foreground=T.resolve(T.SQL_KEYWORD))
        self.code.tag_config("str", foreground=T.resolve(T.SQL_STRING))
        self.code.tag_config("num", foreground=T.resolve(T.SQL_NUMBER))
        self.code.tag_config("cmt", foreground=T.resolve(T.SQL_COMMENT))
        self.code.tag_config("fn", foreground=T.resolve(T.SQL_FUNC))

        # 事件
        self.code.bind("<KeyRelease>", self._on_key)
        self.code.bind("<MouseWheel>", self._sync_scroll)
        self.gutter.bind("<MouseWheel>", self._gutter_wheel)
        self.gutter.bind("<Button-4>", self._gutter_wheel)
        self.gutter.bind("<Button-5>", self._gutter_wheel)

        self.apply_theme()

    # ---------- 主题 ----------
    def apply_theme(self):
        self.gutter.configure(bg=T.resolve(T.CODE_BG), fg=T.resolve(T.TEXT_3))
        # 高亮标签颜色随主题重建
        for tag, color in (("kw", T.SQL_KEYWORD), ("str", T.SQL_STRING),
                           ("num", T.SQL_NUMBER), ("cmt", T.SQL_COMMENT),
                           ("fn", T.SQL_FUNC)):
            self.code.tag_config(tag, foreground=T.resolve(color))
        self._highlight_now()

    # ---------- 内容 ----------
    def get_text(self) -> str:
        return self.code.get("1.0", "end-1c")

    def set_text(self, sql: str):
        self._suppress = True
        self.code.delete("1.0", "end")
        self.code.insert("1.0", sql)
        self._suppress = False
        self._refresh_gutter()
        self._highlight_now()
        self.code.see("1.0")

    # ---------- 事件 ----------
    def _on_key(self, event=None):
        if self._suppress:
            return
        self._schedule_highlight()
        self._sync_scroll()
        if self._on_change:
            self._on_change(self.get_text())

    def _schedule_highlight(self):
        if self._highlight_job is not None:
            try:
                self.after_cancel(self._highlight_job)
            except Exception:
                pass
        try:
            self._highlight_job = self.after(220, self._highlight_now)
        except Exception:
            self._highlight_job = None

    def _highlight_now(self):
        self._highlight_job = None
        try:
            if not self.code.winfo_exists():
                return
        except Exception:
            return
        text = self.get_text()
        try:
            for tag in ("kw", "str", "num", "cmt", "fn"):
                self.code.tag_remove(tag, "1.0", "end")
            for m in _KEYWORD_RE.finditer(text):
                if m.lastgroup == "comment":
                    tag = "cmt"
                elif m.lastgroup in ("string", "qident"):
                    tag = "str"
                elif m.lastgroup == "number":
                    tag = "num"
                elif m.lastgroup == "func":
                    tag = "fn"
                elif m.group("word") and m.group("word").upper() in _SQL_KEYWORDS:
                    tag = "kw"
                else:
                    continue
                start = f"1.0 + {m.start()} chars"
                end = f"1.0 + {m.end()} chars"
                self.code.tag_add(tag, start, end)
        except Exception:
            pass  # 高亮失败不影响编辑
        self._refresh_gutter()

    # ---------- 行号槽 ----------
    def _refresh_gutter(self):
        try:
            n_lines = int(self.code.index("end-1c").split(".")[0])
        except Exception:
            n_lines = 1
        nums = "\n".join(str(i) for i in range(1, n_lines + 1))
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", nums)
        self.gutter.configure(state="disabled")
        self._sync_scroll()

    def _sync_scroll(self, event=None):
        try:
            top = self.code.yview()[0]
            self.gutter.yview_moveto(top)
        except Exception:
            pass

    def _gutter_wheel(self, event=None):
        # 行号槽上的滚轮转给代码区
        try:
            delta = -1 if getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4 else 1
            self.code.yview_scroll(delta * 3, "units")
            self._sync_scroll()
        except Exception:
            pass
        return "break"
