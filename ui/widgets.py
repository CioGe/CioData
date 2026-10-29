# -*- coding: utf-8 -*-
"""
通用 UI 组件：字体管理、卡片、分区标题、按钮、分隔线。
所有颜色来自 ui.theme 的 (浅色, 暗色) 二元组令牌。
"""

import tkinter.font as tkfont
import customtkinter as ctk

from . import theme as T


def pick_family(candidates):
    """从候选字体族中选当前系统真实存在的第一个。"""
    try:
        available = set(tkfont.families())
    except Exception:
        return candidates[0]
    for c in candidates:
        if c in available:
            return c
    return candidates[-1]


class Fonts:
    """全局字体（需在 CTk 根窗口创建后实例化）。"""

    def __init__(self):
        self.ui_family = pick_family([T.UI_FONT_FAMILY, *T.UI_FONT_FALLBACKS])
        self.mono_family = pick_family(list(T.MONO_FAMILY))
        ui, mono = self.ui_family, self.mono_family
        self.title = ctk.CTkFont(family=ui, size=14, weight="bold")
        self.section = ctk.CTkFont(family=ui, size=12, weight="bold")
        self.body = ctk.CTkFont(family=ui, size=12)
        self.small = ctk.CTkFont(family=ui, size=11)
        self.tiny = ctk.CTkFont(family=ui, size=10)
        self.mono = ctk.CTkFont(family=mono, size=12)
        self.mono_sm = ctk.CTkFont(family=mono, size=11)
        self.mono_lg = ctk.CTkFont(family=mono, size=13)


class Card(ctk.CTkFrame):
    """白色圆角卡片 + 细边框。"""

    def __init__(self, master, title: str = None, **kw):
        super().__init__(
            master,
            fg_color=T.SURFACE,
            border_width=1,
            border_color=T.BORDER,
            corner_radius=T.RADIUS,
            **kw,
        )
        self._body = None
        if title:
            hdr = ctk.CTkLabel(self, text=title, font=FontsHolder.get().section, text_color=T.TEXT, anchor="w")
            hdr.pack(fill="x", padx=14, pady=(12, 2))
            self._body = ctk.CTkFrame(self, fg_color="transparent")
            self._body.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    @property
    def body(self):
        return self._body if self._body is not None else self


class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        super().__init__(
            master, text=text, font=FontsHolder.get().small,
            text_color=T.TEXT_2, anchor="w", **kw,
        )


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, height=32, **kw):
        super().__init__(
            master, text=text, command=command, height=height,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color=T.ON_ACCENT, corner_radius=T.RADIUS_SM,
            font=FontsHolder.get().body, border_width=0, **kw,
        )


class GhostButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, height=32, **kw):
        super().__init__(
            master, text=text, command=command, height=height,
            fg_color="transparent", hover_color=T.HOVER,
            text_color=T.TEXT, border_width=1, border_color=T.BORDER_STRONG,
            corner_radius=T.RADIUS_SM, font=FontsHolder.get().body, **kw,
        )


class SubtleButton(ctk.CTkButton):
    """无边框弱化按钮，用于工具栏小操作。"""

    def __init__(self, master, text, command=None, height=28, **kw):
        super().__init__(
            master, text=text, command=command, height=height,
            fg_color="transparent", hover_color=T.HOVER,
            text_color=T.TEXT_2, corner_radius=T.RADIUS_SM,
            font=FontsHolder.get().small, border_width=0, **kw,
        )


class HLine(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, height=1, fg_color=T.BORDER, **kw)


class _FontsHolder:
    _fonts = None

    @classmethod
    def set(cls, fonts):
        cls._fonts = fonts

    @classmethod
    def get(cls):
        if cls._fonts is None:
            cls._fonts = Fonts()
        return cls._fonts


FontsHolder = _FontsHolder
