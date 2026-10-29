# -*- coding: utf-8 -*-
"""
中间工作区：SQL 编辑器卡片 + 数据结果表格。
"""

import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, Card, PrimaryButton, SubtleButton, HLine
from .sql_editor import SqlEditor
from .data_table import DataTable
import config
import i18n


class Workspace(ctk.CTkFrame):
    def __init__(self, master, callbacks: dict, **kw):
        """
        callbacks:
          on_run(sql)          执行SQL
          on_export(df)        导出CSV
          on_reset_sql()       重置SQL
          on_page_size(n)      每页行数变更
        """
        super().__init__(master, fg_color=T.BG, corner_radius=0, **kw)
        self._fonts = FontsHolder.get()
        self._cb = callbacks

        # ---------- SQL 编辑器卡片 ----------
        card = Card(self, title=i18n.t("ws.sql_title"))
        card.pack(fill="x", padx=10, pady=(10, 8))
        head = ctk.CTkFrame(card.body, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text=i18n.t("ws.sql_hint"),
                     font=self._fonts.tiny, text_color=T.TEXT_3).pack(side="left")
        SubtleButton(head, text=i18n.t("ws.reset_sql"), command=self._reset, height=26,
                     width=76).pack(side="right")
        self.run_btn = PrimaryButton(head, text=i18n.t("ws.run"), command=self._run,
                                     height=28, width=88)
        self.run_btn.pack(side="right", padx=(0, 6))

        self.editor = SqlEditor(card.body)
        self.editor.pack(fill="x", pady=(6, 0))
        self.editor.code.bind("<Control-Return>", self._run)
        self.editor.code.bind("<Control-Key-Return>", self._run)

        self.msg_label = ctk.CTkLabel(card.body, text="", font=self._fonts.small,
                                      text_color=T.ERROR, anchor="w", wraplength=700,
                                      justify="left")
        self.msg_label.pack(fill="x", pady=(6, 0))
        self.msg_label.pack_forget()

        # ---------- 结果表格 ----------
        self.table = DataTable(
            self,
            on_export=self._export,
            on_page_size_change=lambda n: self._cb.get("on_page_size", lambda _n: None)(n),
        )
        self.table.pack(fill="both", expand=True, padx=10, pady=(8, 10))

    # ---------- API ----------
    def get_sql(self) -> str:
        return self.editor.get_text()

    def set_sql(self, sql: str):
        self.editor.set_text(sql)
        self.hide_msg()
        self.editor.code.focus()

    def show_msg(self, text, level="error"):
        self.msg_label.configure(text=text,
                                 text_color={"error": T.ERROR, "ok": T.SUCCESS,
                                             "warn": T.WARNING}[level])
        self.msg_label.pack(fill="x", pady=(6, 0))

    def hide_msg(self):
        self.msg_label.pack_forget()

    def set_data(self, df, page_size=None, keep_page=False):
        self.table.set_data(df, page_size=page_size, keep_page=keep_page)

    def refresh_table(self):
        self.table.refresh()

    def apply_theme(self):
        self.editor.apply_theme()
        self.table.apply_theme()

    # ---------- 内部 ----------
    def _run(self, event=None):
        sql = self.editor.get_text().strip()
        if not sql:
            self.show_msg(i18n.t("ws.sql_empty"), "warn")
            return
        if self._cb.get("on_run"):
            self._cb["on_run"](sql)

    def _reset(self):
        self.set_sql(config.DEFAULT_SQL)
        if self._cb.get("on_reset_sql"):
            self._cb["on_reset_sql"]()

    def _export(self, df):
        if self._cb.get("on_export"):
            self._cb["on_export"](df)
