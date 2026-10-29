# -*- coding: utf-8 -*-
"""
AI 对话面板：聊天气泡 + SQL 代码块 + 「采用」按钮 + 输入框。
消息流同时记入 log 列表（App 持有），界面重建（如语言切换）后按 log 重放。
  user 气泡（右侧，主色浅底）
  assistant 文本气泡（左侧）
  assistant SQL 气泡（左侧，等宽代码块 + 采用并执行/仅采用 按钮）
  错误提示（左侧，红色浅底）
"""

import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, PrimaryButton, SubtleButton, HLine
import i18n


class ChatPanel(ctk.CTkFrame):
    def __init__(self, master, on_send=None, on_adopt_run=None, on_adopt_only=None,
                 on_clear=None, log=None, **kw):
        super().__init__(master, fg_color=T.SURFACE, border_width=1,
                         border_color=T.BORDER, corner_radius=T.RADIUS, **kw)
        self._fonts = FontsHolder.get()
        self._on_send = on_send
        self._on_adopt_run = on_adopt_run
        self._on_adopt_only = on_adopt_only
        self._on_clear = on_clear
        self._thinking = False
        self._log = log if log is not None else []

        # ---------- 头部 ----------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(header, text=i18n.t("chat.title"), font=self._fonts.section,
                     text_color=T.TEXT, anchor="w").pack(side="left")
        self.status_label = ctk.CTkLabel(header, text="", font=self._fonts.tiny,
                                         text_color=T.TEXT_3)
        self.status_label.pack(side="left", padx=(8, 0))
        SubtleButton(header, text=i18n.t("chat.clear"), command=self._clear, width=44,
                     height=24).pack(side="right")

        # ---------- 消息流 ----------
        self.messages = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=T.BORDER_STRONG,
        )
        self.messages.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self.render_log()

        # ---------- 输入区 ----------
        HLine(self).pack(fill="x", padx=14)
        input_bar = ctk.CTkFrame(self, fg_color="transparent")
        input_bar.pack(fill="x", padx=14, pady=10)
        self.input = ctk.CTkTextbox(
            input_bar, height=64, wrap="word", font=self._fonts.body,
            fg_color=T.SURFACE_2, border_width=1, border_color=T.BORDER,
            corner_radius=T.RADIUS_SM, text_color=T.TEXT,
        )
        self.input.pack(fill="x")
        self.input.bind("<Return>", self._on_enter)
        self.input.bind("<Shift-Return>", lambda e: None)
        btn_row = ctk.CTkFrame(input_bar, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(btn_row, text=i18n.t("chat.input_hint"),
                     font=self._fonts.tiny, text_color=T.TEXT_3).pack(side="left")
        self.send_btn = PrimaryButton(btn_row, text=i18n.t("chat.send"),
                                      command=self._send, width=72, height=28)
        self.send_btn.pack(side="right")

    # ---------- 内部 ----------
    def render_log(self):
        """按日志重放全部消息（界面重建后调用）。"""
        self.clear()
        if not self._log:
            self._placeholder()
            return
        for kind, payload in self._log:
            if kind == "user":
                self._draw_user(payload)
            elif kind == "text":
                self._draw_text(payload)
            elif kind == "error":
                self._draw_error(payload)
            elif kind == "sql":
                self._draw_sql(payload)

    def _placeholder(self):
        lbl = ctk.CTkLabel(
            self.messages,
            text=i18n.t("chat.placeholder"),
            font=self._fonts.small, text_color=T.TEXT_3, justify="left",
        )
        lbl.pack(anchor="w", padx=8, pady=8)

    def _scroll_bottom(self):
        def _do():
            try:
                if self.messages.winfo_exists():
                    self.messages._parent_canvas.yview_moveto(1.0)
            except Exception:
                pass  # 面板已被销毁（如语言切换重建），忽略
        try:
            self.after(60, _do)
        except Exception:
            pass

    def _on_enter(self, event=None):
        self._send()
        return "break"

    def _send(self):
        if self._thinking:
            return
        text = self.input.get("1.0", "end-1c").strip()
        if not text:
            return
        self.input.delete("1.0", "end")
        if self._on_send:
            self._on_send(text)

    def _clear(self):
        if self._on_clear:
            self._on_clear()

    # ---------- 绘制原语 ----------
    def _draw_user(self, text):
        self._clear_placeholder_if_needed()
        bubble = ctk.CTkFrame(self.messages, fg_color=T.ACCENT_SOFT,
                              corner_radius=T.RADIUS_SM)
        ctk.CTkLabel(bubble, text=text, font=self._fonts.body,
                     text_color=T.TEXT, justify="left", wraplength=200).pack(
            padx=10, pady=8)
        bubble.pack(anchor="e", padx=8, pady=4)
        self._scroll_bottom()

    def _draw_text(self, text):
        self._clear_placeholder_if_needed()
        bubble = ctk.CTkFrame(self.messages, fg_color=T.SURFACE_2,
                              corner_radius=T.RADIUS_SM)
        ctk.CTkLabel(bubble, text=text, font=self._fonts.body,
                     text_color=T.TEXT, justify="left", wraplength=200).pack(
            padx=10, pady=8)
        bubble.pack(anchor="w", padx=8, pady=4)
        self._scroll_bottom()

    def _draw_error(self, text):
        self._clear_placeholder_if_needed()
        bubble = ctk.CTkFrame(self.messages, fg_color=T.ERROR_SOFT,
                              corner_radius=T.RADIUS_SM)
        ctk.CTkLabel(bubble, text=text, font=self._fonts.small,
                     text_color=T.ERROR, justify="left", wraplength=200).pack(
            padx=10, pady=8)
        bubble.pack(anchor="w", padx=8, pady=4)
        self._scroll_bottom()

    def _draw_sql(self, sql):
        self._clear_placeholder_if_needed()
        wrap = ctk.CTkFrame(self.messages, fg_color="transparent")
        wrap.pack(anchor="w", padx=4, pady=4, fill="x")
        code = ctk.CTkTextbox(
            wrap, height=90, wrap="word", font=self._fonts.mono_sm,
            fg_color=T.CODE_BG, text_color=T.CODE_TEXT,
            border_width=1, border_color=T.BORDER, corner_radius=T.RADIUS_SM,
        )
        code.insert("1.0", sql)
        code.configure(state="disabled")
        code.pack(fill="x", padx=4, pady=(0, 4))
        btns = ctk.CTkFrame(wrap, fg_color="transparent")
        btns.pack(fill="x", padx=4)
        PrimaryButton(btns, text=i18n.t("chat.adopt_run"), height=26,
                      command=lambda: self._adopt(sql, run=True)).pack(side="left")
        SubtleButton(btns, text=i18n.t("chat.adopt_only"), height=26, width=88,
                     command=lambda: self._adopt(sql, run=False)).pack(side="left", padx=(6, 0))
        self._scroll_bottom()

    def _adopt(self, sql, run):
        if run and self._on_adopt_run:
            self._on_adopt_run(sql)
        elif not run and self._on_adopt_only:
            self._on_adopt_only(sql)

    def _clear_placeholder_if_needed(self):
        children = self.messages.winfo_children()
        if len(children) == 1 and isinstance(children[0], ctk.CTkLabel):
            children[0].destroy()

    # ---------- 对外 API ----------
    def clear(self):
        for w in self.messages.winfo_children():
            w.destroy()

    def reset(self):
        """清空并恢复占位提示。"""
        self._log.clear()
        self.clear()
        self._placeholder()

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def set_thinking(self, thinking: bool):
        self._thinking = thinking
        if thinking:
            self.send_btn.configure(state="disabled", text=i18n.t("chat.sending"))
            self.input.configure(state="disabled")
        else:
            self.send_btn.configure(state="normal", text=i18n.t("chat.send"))
            self.input.configure(state="normal")
            self.input.focus()

    def add_user(self, text: str):
        self._log.append(("user", text))
        self._draw_user(text)

    def add_text(self, text: str):
        self._log.append(("text", text))
        self._draw_text(text)

    def add_error(self, text: str):
        self._log.append(("error", text))
        self._draw_error(text)

    def add_sql(self, sql: str):
        self._log.append(("sql", sql))
        self._draw_sql(sql)

    def apply_theme(self):
        pass  # 颜色均为主题令牌，随 appearance mode 自动切换
