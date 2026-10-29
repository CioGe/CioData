# -*- coding: utf-8 -*-
"""
CioNote 风格设计令牌 —— 浅色为主，暗色自适应。
所有颜色用 (浅色, 暗色) 二元组，交给 CustomTkinter 的 set_appearance_mode 切换。
"""

# ---------- 颜色（浅色, 暗色） ----------
BG          = ("#F5F5F7", "#16161B")   # 应用底色
SURFACE     = ("#FFFFFF", "#1E1E24")   # 卡片
SURFACE_2   = ("#FAFAFB", "#24242C")   # 卡片内嵌区 / 代码块
HOVER       = ("#F0F0F3", "#2A2A33")   # 悬停
BORDER      = ("#E5E5EA", "#2E2E38")   # 细边框
BORDER_STRONG = ("#D4D4DB", "#3A3A46")

TEXT        = ("#23232B", "#EFEFF3")   # 主文字
TEXT_2      = ("#6E6E78", "#A6A6B0")   # 次文字
TEXT_3      = ("#A8A8B2", "#63636E")   # 占位/弱提示

ACCENT      = ("#5254E8", "#7C7FF5")   # 主色（克制靛蓝）
ACCENT_HOVER= ("#4143D6", "#8B8DF8")
ACCENT_SOFT = ("#EEEEFC", "#26263C")   # 主色浅底（user气泡/选中态）
ON_ACCENT   = ("#FFFFFF", "#FFFFFF")

SUCCESS     = ("#15803D", "#4ADE80")
SUCCESS_SOFT= ("#EBF7EE", "#1B2E1F")
ERROR       = ("#DC2626", "#F87171")
ERROR_SOFT  = ("#FDECEC", "#331c1C")
WARNING     = ("#B45309", "#FBBF24")
WARNING_SOFT= ("#FDF3E3", "#33260F")

CODE_BG     = ("#F7F7F9", "#141419")
CODE_TEXT   = ("#3B3B46", "#D6D6DE")

# SQL 高亮色
SQL_KEYWORD = ("#7C3AED", "#C4B5FD")
SQL_STRING  = ("#15803D", "#86EFAC")
SQL_NUMBER  = ("#B45309", "#FCD34D")
SQL_COMMENT = ("#9CA3AF", "#6B7280")
SQL_FUNC    = ("#0369A1", "#7DD3FC")

SELECTED_ROW = ("#E8E8FD", "#2E2E45")

# ---------- 字体 ----------
UI_FONT_FAMILY = "Microsoft YaHei UI"
UI_FONT_FALLBACKS = ("Microsoft YaHei", "Segoe UI", "PingFang SC", "Noto Sans CJK SC",
                    "Source Han Sans SC", "WenQuanYi Micro Hei", "DejaVu Sans", "sans-serif")
MONO_FAMILY = ("Consolas", "Cascadia Mono", "JetBrains Mono", "Menlo", "monospace")

# ---------- 尺寸 ----------
RADIUS = 10          # 卡片圆角
RADIUS_SM = 7        # 按钮/输入框圆角
SIDEBAR_W = 248      # 左侧栏宽
CHAT_W = 320         # 右侧对话栏宽
TITLEBAR_H = 46
STATUSBAR_H = 30

# ---------- 主题元数据 ----------
THEME_LIGHT = "light"
THEME_DARK = "dark"


def resolve(color):
    """把 (浅色, 暗色) 二元组按当前外观模式解析为单个颜色值。
    原生 tk 控件（tag_config / Text.configure 等）不认二元组，必须先解析。"""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        import customtkinter as ctk
        try:
            return color[0] if ctk.get_appearance_mode() == "Light" else color[1]
        except Exception:
            return color[0]
    return color


def _pick_family(candidates):
    """返回第一个匹配当前环境的字体族（由调用方在 Tk 初始化后探测）。"""
    return candidates


def mono_family():
    return MONO_FAMILY[0]


def ui_family():
    return UI_FONT_FAMILY
