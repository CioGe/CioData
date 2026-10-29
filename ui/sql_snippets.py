# -*- coding: utf-8 -*-
"""
右侧上半区：SQL 语句 DIY 存储（10 个 slot）。
每个 slot 从左到右：名称（仅显示）→ 编辑（弹窗编辑名称 + SQL）→ 采用（把 SQL 送入 SQL 编辑器）。
数据持久化在 settings["sql_snippets"]：长度为 10 的 [{"name": str, "sql": str}, ...] 列表。
"""

import os

import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, SubtleButton, HLine
import i18n

MAX_SLOTS = 10


class SqlSnippetsPanel(ctk.CTkFrame):
    def __init__(self, master, settings, on_adopt=None, on_status=None, **kw):
        super().__init__(
            master, fg_color=T.SURFACE, border_width=1,
            border_color=T.BORDER, corner_radius=T.RADIUS, **kw,
        )
        self._fonts = FontsHolder.get()
        self._settings = settings
        self._on_adopt = on_adopt
        self._on_status = on_status
        self._slots = self._load_slots()

        # ---------- 头部 ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(header, text=i18n.t("snippets.title"), font=self._fonts.section,
                     text_color=T.TEXT, anchor="w").pack(side="left")
        ctk.CTkLabel(header, text=i18n.t("snippets.hint"), font=self._fonts.tiny,
                     text_color=T.TEXT_3, anchor="w").pack(side="left", padx=(10, 0))

        HLine(self).pack(fill="x", padx=14)

        # ---------- 槽位列表（可滚动） ----------
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=T.BORDER_STRONG,
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(6, 10))

        self._rows = []
        self._build_rows()

    # ==================== 数据 ====================
    def _load_slots(self):
        """从 settings 读取并归一化为恰好 MAX_SLOTS 个 {name, sql} 字典。"""
        raw = self._settings.get("sql_snippets")
        slots = []
        if isinstance(raw, list):
            for item in raw[:MAX_SLOTS]:
                if isinstance(item, dict):
                    slots.append({
                        "name": str(item.get("name", "")),
                        "sql": str(item.get("sql", "")),
                    })
        while len(slots) < MAX_SLOTS:
            slots.append({"name": "", "sql": ""})
        return slots[:MAX_SLOTS]

    def _save_slots(self):
        self._settings.set("sql_snippets", self._slots)
        self._settings.save()

    # ==================== 视图 ====================
    def _build_rows(self):
        self._rows = []
        for idx in range(MAX_SLOTS):
            self._add_row(idx)

    def _add_row(self, idx):
        slot = self._slots[idx]
        row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))

        # 名称（仅显示，左对齐占满剩余宽度）
        name = slot.get("name", "").strip()
        if name:
            name_text, name_color = name, T.TEXT
        else:
            name_text = f"{i18n.t('snippets.slot_prefix')} {idx + 1}"
            name_color = T.TEXT_3
        name_lbl = ctk.CTkLabel(row, text=name_text, font=self._fonts.body,
                               text_color=name_color, anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True, padx=(4, 8))

        # 编辑（中间）
        SubtleButton(row, text=i18n.t("snippets.edit"),
                     command=lambda i=idx: self._open_editor(i),
                     width=52, height=26).pack(side="left", padx=(0, 6))

        # 采用（右侧）；空槽位禁用
        adopt_btn = SubtleButton(row, text=i18n.t("snippets.adopt"),
                                command=lambda i=idx: self._adopt(i),
                                width=52, height=26)
        adopt_btn.pack(side="left")
        if not slot.get("sql", "").strip():
            adopt_btn.configure(state="disabled")

        self._rows.append({"name_lbl": name_lbl, "adopt_btn": adopt_btn})

    def _refresh_row(self, idx):
        slot = self._slots[idx]
        r = self._rows[idx]
        name = slot.get("name", "").strip()
        if name:
            r["name_lbl"].configure(text=name, text_color=T.TEXT)
        else:
            r["name_lbl"].configure(
                text=f"{i18n.t('snippets.slot_prefix')} {idx + 1}", text_color=T.TEXT_3)
        r["adopt_btn"].configure(
            state="normal" if slot.get("sql", "").strip() else "disabled")

    # ==================== 行为 ====================
    def _adopt(self, idx):
        sql = self._slots[idx].get("sql", "").strip()
        if not sql:
            return
        if self._on_adopt:
            self._on_adopt(sql)

    def _open_editor(self, idx):
        slot = self._slots[idx]
        win = ctk.CTkToplevel(self)
        win.title(i18n.t("snippets.dialog_title"))
        win.resizable(True, True)
        win.attributes("-topmost", True)
        # 弹窗同样会被 CTk 200ms 后用默认蓝图标覆盖，必须走 iconbitmap
        try:
            _ico = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "assets", "icon.ico")
            if os.path.exists(_ico):
                win.after(10, lambda: win.iconbitmap(_ico))
        except Exception:
            pass

        ctk.CTkLabel(win, text=i18n.t("snippets.dialog_name"), font=self._fonts.small,
                     text_color=T.TEXT_2, anchor="w").pack(anchor="w", padx=16, pady=(16, 4))
        name_entry = ctk.CTkEntry(
            win, font=self._fonts.body,
            placeholder_text=i18n.t("snippets.dialog_name_ph"))
        name_entry.pack(fill="x", padx=16, pady=(0, 8))
        name_entry.insert(0, slot.get("name", ""))

        ctk.CTkLabel(win, text=i18n.t("snippets.dialog_sql"), font=self._fonts.small,
                     text_color=T.TEXT_2, anchor="w").pack(anchor="w", padx=16, pady=(4, 4))
        sql_box = ctk.CTkTextbox(
            win, height=200, wrap="word", font=self._fonts.mono,
            fg_color=T.SURFACE_2, border_width=1, border_color=T.BORDER,
            corner_radius=T.RADIUS_SM, text_color=T.TEXT)
        sql_box.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        sql_box.insert("1.0", slot.get("sql", ""))

        def _save():
            self._slots[idx] = {
                "name": name_entry.get().strip(),
                "sql": sql_box.get("1.0", "end-1c"),
            }
            self._save_slots()
            self._refresh_row(idx)
            win.destroy()
            self._toast(i18n.t("snippets.toast_saved"))

        def _clear():
            self._slots[idx] = {"name": "", "sql": ""}
            self._save_slots()
            self._refresh_row(idx)
            win.destroy()

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 14))
        SubtleButton(btns, text=i18n.t("snippets.dialog_clear"),
                     command=_clear, width=64, height=30).pack(side="left")
        right_grp = ctk.CTkFrame(btns, fg_color="transparent")
        right_grp.pack(side="right")
        SubtleButton(right_grp, text=i18n.t("snippets.dialog_cancel"),
                     command=win.destroy, width=72, height=30).pack(side="right", padx=(8, 0))
        ctk.CTkButton(right_grp, text=i18n.t("snippets.dialog_save"),
                      command=_save, height=30, width=80,
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                      text_color=T.ON_ACCENT, corner_radius=T.RADIUS_SM,
                      font=self._fonts.body).pack(side="right")

        win.geometry("460x380")
        try:
            self.update_idletasks()
            root = self.winfo_toplevel()
            x = root.winfo_x() + (root.winfo_width() - 460) // 2
            y = root.winfo_y() + (root.winfo_height() - 380) // 2
            win.geometry(f"460x380+{x}+{y}")
        except Exception:
            pass

    def _toast(self, text):
        if self._on_status:
            self._on_status(text)

    # ==================== 主题 ====================
    def apply_theme(self):
        pass  # 颜色均为主题令牌，随 appearance mode 自动切换
