# -*- coding: utf-8 -*-
"""
右侧上半区：SQL 语句 DIY 存储（槽位数量可增减，默认 10）。
每个 slot 从左到右：名称（仅显示，超长省略）→ 编辑（弹窗编辑名称 + SQL）→ 采用（把 SQL 送入 SQL 编辑器）。
数据持久化在 settings["sql_snippets"]：[{"name": str, "sql": str}, ...]；槽位数量存 settings["sql_snippet_slots"]。
"""

import os

import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, SubtleButton, HLine
import i18n

DEFAULT_SLOTS = 10
MIN_SLOTS = 1
MAX_SLOTS = 50          # 硬上限，避免误加过多
MAX_NAME_DISPLAY = 22   # 名称显示最大字符数，超出以 … 省略（防止挤压按钮）


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
        self._len = DEFAULT_SLOTS
        self._slots = self._load_slots()

        # ---------- 头部 ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 4))

        # 标题行：标题（左）+ 槽位增减控件（右，先占位确保可见）
        top = ctk.CTkFrame(header, fg_color="transparent")
        top.pack(fill="x")

        ctrl = ctk.CTkFrame(top, fg_color="transparent")
        ctrl.pack(side="right")
        # 从右往左依次：+ | 数量 | −  →  视觉为 − 10 +
        SubtleButton(ctrl, text="+", command=self._inc_slots,
                     width=28, height=24).pack(side="right")
        self._count_lbl = ctk.CTkLabel(
            ctrl, text=str(self._len), font=self._fonts.small,
            text_color=T.TEXT_2, width=26, anchor="center")
        self._count_lbl.pack(side="right", padx=4)
        SubtleButton(ctrl, text="−", command=self._dec_slots,
                     width=28, height=24).pack(side="right")

        ctk.CTkLabel(top, text=i18n.t("snippets.title"), font=self._fonts.section,
                     text_color=T.TEXT, anchor="w").pack(side="left")

        ctk.CTkLabel(header, text=i18n.t("snippets.hint"), font=self._fonts.tiny,
                     text_color=T.TEXT_3, anchor="w").pack(fill="x", pady=(2, 0))

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
        """从 settings 读取槽位数据与数量。

        - 已存数据不截断：减少槽位只是“隐藏”，不丢数据，加回后原文还在。
        - 数量 clamp 到 [MIN_SLOTS, MAX_SLOTS]，默认 DEFAULT_SLOTS。
        """
        raw = self._settings.get("sql_snippets")
        slots = []
        if isinstance(raw, list):
            for item in raw[:MAX_SLOTS]:
                if isinstance(item, dict):
                    slots.append({
                        "name": str(item.get("name", "")),
                        "sql": str(item.get("sql", "")),
                    })
        try:
            n = int(self._settings.get("sql_snippet_slots", DEFAULT_SLOTS))
        except (TypeError, ValueError):
            n = DEFAULT_SLOTS
        n = max(MIN_SLOTS, min(MAX_SLOTS, n))
        self._len = n
        while len(slots) < n:
            slots.append({"name": "", "sql": ""})
        return slots

    def _save_slots(self):
        self._settings.set("sql_snippets", self._slots)
        self._settings.set("sql_snippet_slots", self._len)
        self._settings.save()

    # ==================== 视图 ====================
    def _display_name(self, name, idx):
        """名称显示文本：空 → '槽位 N'；超长 → 截断加省略号（仅显示，不改真实数据）。"""
        name = (name or "").strip()
        if not name:
            return f"{i18n.t('snippets.slot_prefix')} {idx + 1}"
        if len(name) > MAX_NAME_DISPLAY:
            return name[:MAX_NAME_DISPLAY - 1] + "…"
        return name

    def _build_rows(self):
        self._rows = []
        for idx in range(self._len):
            self._add_row(idx)

    def _rebuild_rows(self):
        for r in self._rows:
            try:
                r["frame"].destroy()
            except Exception:
                pass
        self._rows = []
        for idx in range(self._len):
            self._add_row(idx)
        try:
            self._count_lbl.configure(text=str(self._len))
        except Exception:
            pass

    def _add_row(self, idx):
        slot = self._slots[idx]
        row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))

        # 先让右侧两个按钮占位（pack side=right 先入先占），名称再填剩余空间，
        # 这样名称再长也只会被裁剪，绝不会把按钮挤出可视区。
        adopt_btn = SubtleButton(row, text=i18n.t("snippets.adopt"),
                                command=lambda i=idx: self._adopt(i),
                                width=52, height=26)
        adopt_btn.pack(side="right")                       # 最右
        SubtleButton(row, text=i18n.t("snippets.edit"),
                     command=lambda i=idx: self._open_editor(i),
                     width=52, height=26).pack(side="right", padx=(0, 6))  # 采用左侧

        name = slot.get("name", "").strip()
        name_color = T.TEXT if name else T.TEXT_3
        name_lbl = ctk.CTkLabel(row, text=self._display_name(name, idx),
                               font=self._fonts.body, text_color=name_color, anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True, padx=(4, 8))

        if not slot.get("sql", "").strip():
            adopt_btn.configure(state="disabled")

        self._rows.append({"frame": row, "name_lbl": name_lbl, "adopt_btn": adopt_btn})

    def _refresh_row(self, idx):
        slot = self._slots[idx]
        r = self._rows[idx]
        name = slot.get("name", "").strip()
        r["name_lbl"].configure(
            text=self._display_name(name, idx),
            text_color=T.TEXT if name else T.TEXT_3)
        r["adopt_btn"].configure(
            state="normal" if slot.get("sql", "").strip() else "disabled")

    # ==================== 槽位增减 ====================
    def _inc_slots(self):
        if self._len >= MAX_SLOTS:
            return
        self._len += 1
        while len(self._slots) < self._len:
            self._slots.append({"name": "", "sql": ""})
        self._rebuild_rows()
        self._save_slots()

    def _dec_slots(self):
        if self._len <= MIN_SLOTS:
            return
        self._len -= 1          # 仅隐藏最后一项，数据保留在 self._slots 中
        self._rebuild_rows()
        self._save_slots()

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
