# -*- coding: utf-8 -*-
"""
分页数据表格：ttk.Treeview 深度定制（扁平无边框、表头排序、主题适配）。
只渲染当前页数据，10万行也不卡。
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, SubtleButton, GhostButton, HLine
import i18n

_PAGE_SIZES = [100, 200, 500, 1000]


def _fmt_cell(v) -> str:
    """单元格显示格式化：NaN→空，整值float→整数串。"""
    if v is None:
        return ""
    try:
        if v != v:  # NaN
            return ""
    except Exception:
        return str(v)
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return repr(v)
    return str(v)


class DataTable(ctk.CTkFrame):
    def __init__(self, master, on_export=None, on_page_size_change=None, **kw):
        super().__init__(master, fg_color=T.SURFACE, border_width=1,
                         border_color=T.BORDER, corner_radius=T.RADIUS, **kw)
        self._fonts = FontsHolder.get()
        self._on_export = on_export
        self._on_page_size_change = on_page_size_change

        self.df = None
        self.page = 1
        self.page_size = 100
        self._sort_col = None
        self._sort_desc = False

        # ---------- 工具栏 ----------
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(12, 6))
        self.info_label = ctk.CTkLabel(bar, text=i18n.t("ws.no_data"), font=self._fonts.small,
                                       text_color=T.TEXT_2, anchor="w")
        self.info_label.pack(side="left")
        self.export_btn = GhostButton(bar, text=i18n.t("ws.export"), command=self._export, height=28)
        self.export_btn.pack(side="right")
        self.export_btn.configure(state="disabled")

        # ---------- 表格 ----------
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.tree = ttk.Treeview(table_frame, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self._on_double_click)

        # ---------- 分页栏 ----------
        self._build_pagination()
        self._style_tree()
        self.apply_theme()

    # ---------- 分页栏 ----------
    def _build_pagination(self):
        HLine(self).pack(fill="x", padx=14, pady=(4, 6))
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=14, pady=(0, 12))
        self.prev_btn = SubtleButton(nav, text=i18n.t("ws.prev"), command=self.prev_page, width=80)
        self.prev_btn.pack(side="left")
        self.page_label = ctk.CTkLabel(nav, text=i18n.t("ws.page", page=1, pages=1),
                                       font=self._fonts.small, text_color=T.TEXT_2)
        self.page_label.pack(side="left", padx=12)
        self.next_btn = SubtleButton(nav, text=i18n.t("ws.next"), command=self.next_page, width=80)
        self.next_btn.pack(side="left")
        self.goto_entry = ctk.CTkEntry(nav, width=52, height=26, border_width=1,
                                       border_color=T.BORDER, fg_color=T.SURFACE_2,
                                       font=self._fonts.small, placeholder_text=i18n.t("ws.page_box"))
        self.goto_entry.pack(side="left", padx=(12, 0))
        self.goto_entry.bind("<Return>", self._on_goto)
        ctk.CTkLabel(nav, text=i18n.t("ws.per_page"), font=self._fonts.small,
                     text_color=T.TEXT_2).pack(side="right", padx=(0, 4))
        self.size_var = ctk.StringVar(value="100")
        size_menu = ctk.CTkOptionMenu(nav, values=[str(s) for s in _PAGE_SIZES],
                                      variable=self.size_var, width=76, height=26,
                                      command=self._on_size_change,
                                      fg_color=T.SURFACE_2, button_color=T.SURFACE_2,
                                      button_hover_color=T.HOVER, text_color=T.TEXT,
                                      dropdown_font=self._fonts.small, font=self._fonts.small)
        size_menu.pack(side="right")
        self._size_menu = size_menu

    # ---------- 样式 ----------
    def _style_tree(self):
        style = ttk.Style()
        style.layout("Treeview", [
            ("Treeview.treearea", {"sticky": "nsew"}),
        ])
        style.configure("Treeview", rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", T.SELECTED_ROW[0])])

    def apply_theme(self):
        light = ctk.get_appearance_mode() == "Light"
        style = ttk.Style()
        style.configure("Treeview",
                        background=T.SURFACE[0 if light else 1],
                        fieldbackground=T.SURFACE[0 if light else 1],
                        foreground=T.TEXT[0 if light else 1],
                        font=(self._fonts.mono_family, 11))
        style.configure("Treeview.Heading",
                        background=T.SURFACE_2[0 if light else 1],
                        foreground=T.TEXT_2[0 if light else 1],
                        font=(self._fonts.ui_family, 11, "bold"))
        style.map("Treeview", background=[("selected", T.SELECTED_ROW[0 if light else 1])])

    # ---------- 数据 ----------
    def set_data(self, df, page_size=None, keep_page=False):
        self.df = df
        if page_size:
            self.page_size = page_size
            self.size_var.set(str(page_size))
        if not keep_page:
            self.page = 1
        self._sort_col = None
        self._sort_desc = False
        self._rebuild_columns()
        self.refresh()

    def _rebuild_columns(self):
        cols = [str(c) for c in self.df.columns]
        self.tree["columns"] = cols
        for i, c in enumerate(cols):
            self.tree.heading(c, text=c, command=lambda _c=c: self.sort_by(_c))
            # 估算列宽：表头 + 前200行内容，封顶240px
            sample = self.df.iloc[:200, i].map(_fmt_cell)
            longest = max([len(str(c))] + [len(s) for s in sample], default=8)
            width = min(max(longest * 8 + 24, 90), 240)
            self.tree.column(c, width=width, minwidth=70, stretch=False, anchor="w")

    def _sort_key(self, col):
        """
        为排序构造一个「不破坏原值」的临时键列。

        原实现直接 astype(float) → to_datetime(errors="coerce") → astype(str)，
        问题在于 errors="coerce" 会把转不了的值变成 NaT（空）。
        对城市名/备注这类纯文本列，to_datetime 一个都转不了 → 整列变空 → 表格一片空白。
        对「2024-01-15 + 暂无」这种混合列，还会悄悄清掉一半数据。

        改为：先判断能不能整体转换，只有「能转的占绝大多数、且没有新增空值」才使用，
        否则一律退回按字符串排序 —— 排序可以不准，但绝不能丢内容。
        """
        s = self.df[col]
        n = len(s)
        if n == 0:
            return s

        # 原始非空值个数，用于校验转换后有没有凭空产生空值
        orig_na = int(s.isna().sum())

        # 1) 数值列：能转就用数值键（让 10 排在 9 后面，而不是按字符串排）
        if not pd.api.types.is_numeric_dtype(s):
            try:
                num = pd.to_numeric(s, errors="coerce")
                # 全部原始非空值都转成功，且没多出空值，才认可
                if int(num.isna().sum()) == orig_na:
                    return num
            except Exception:
                pass
        else:
            return s

        # 2) 日期列：先不带 coerce 试一次整体解析，成功率高才采用
        if not pd.api.types.is_datetime64_any_dtype(s):
            try:
                import warnings
                with warnings.catch_warnings():
                    # 屏蔽 "Could not infer format" 之类的 UserWarning
                    warnings.simplefilter("ignore")
                    dt = pd.to_datetime(s, errors="coerce")
                # 关键：转换后空值数必须和原始一致，说明没有值被吞掉
                if int(dt.isna().sum()) == orig_na:
                    return dt
            except Exception:
                pass

        # 3) 兜底：按字符串排序（NaN 保持 NaN，不丢内容）
        return s.astype(str).where(s.notna(), None)

    def _visible_df(self):
        df = self.df
        if self._sort_col is not None and self._sort_col in df.columns:
            try:
                key = self._sort_key(self._sort_col)
                df = df.assign(**{"__sort_key__": key}).sort_values(
                    by="__sort_key__", ascending=not self._sort_desc,
                    kind="stable", na_position="last").drop(columns="__sort_key__")
            except Exception:
                # 排序失败不应影响数据展示，退回原顺序
                pass
        return df

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.df is None or len(self.df) == 0:
            self.info_label.configure(text=i18n.t("ws.empty_result"))
            self.page_label.configure(text=i18n.t("ws.page_zero"))
            self.export_btn.configure(state="disabled")
            return
        total = len(self.df)
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page = min(max(1, self.page), pages)
        start = (self.page - 1) * self.page_size
        end = min(start + self.page_size, total)
        page_df = self._visible_df().iloc[start:end]
        rows = [[_fmt_cell(v) for v in row] for row in page_df.itertuples(index=False, name=None)]
        for r in rows:
            self.tree.insert("", "end", values=r)
        self.info_label.configure(text=i18n.t(
            "ws.rows_info", total=f"{total:,}", cols=len(self.df.columns),
            start=f"{start + 1:,}", end=f"{end:,}"))
        self.page_label.configure(text=i18n.t("ws.page", page=self.page, pages=pages))
        self.prev_btn.configure(state="normal" if self.page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.page < pages else "disabled")
        self.export_btn.configure(state="normal")

    # ---------- 交互 ----------
    def sort_by(self, col):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        self._refresh_headings()
        self.refresh()

    def _refresh_headings(self):
        for c in self.tree["columns"]:
            label = str(c)
            if c == self._sort_col:
                label += " ▼" if self._sort_desc else " ▲"
            self.tree.heading(c, text=label, command=lambda _c=c: self.sort_by(_c))

    def _on_double_click(self, event):
        # 双击复制单元格内容
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col:
            return
        try:
            idx = int(col.replace("#", "")) - 1
            values = self.tree.item(item, "values")
            text = values[idx]
            self.clipboard_clear()
            self.clipboard_append(text)
            self.info_label.configure(text=i18n.t("ws.copied", text=text[:60]))
        except Exception:
            pass

    def prev_page(self):
        self.page -= 1
        self.refresh()

    def next_page(self):
        self.page += 1
        self.refresh()

    def _on_goto(self, event=None):
        try:
            p = int(self.goto_entry.get().strip())
            self.page = p
            self.goto_entry.delete(0, "end")
            self.refresh()
        except Exception:
            pass

    def _on_size_change(self, value):
        try:
            self.page_size = int(value)
        except Exception:
            return
        self.page = 1
        self.refresh()
        if self._on_page_size_change:
            self._on_page_size_change(self.page_size)

    def _export(self):
        if self._on_export and self.df is not None:
            self._on_export(self.df)
