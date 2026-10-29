# -*- coding: utf-8 -*-
"""
左侧栏：数据源 / 显示字段 / AI 模型 / 提示词 四个配置区。
所有配置变更实时写入 settings.json；所有文案走 i18n。
"""

import os
import tkinter.filedialog as filedialog
import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, Card, PrimaryButton, GhostButton, SubtleButton
import config
import i18n


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, settings, callbacks: dict, **kw):
        """
        callbacks:
          on_load_file(path, sheet, row_limit)
          on_load_databricks(db_cfg)
          on_load_sample()
          on_file_picked(path)
          on_columns_changed(visible_cols)
          on_test_llm(llm_cfg)
          on_backend_changed(backend)      后端切换（切到 ollama 自动触发本地模型扫描）
        """
        super().__init__(master, fg_color=T.BG, width=T.SIDEBAR_W, corner_radius=0, **kw)
        self._fonts = FontsHolder.get()
        self._settings = settings
        self._cb = callbacks
        self._selected_file = ""
        self._sheets = []
        self._col_vars = {}

        self.pack_propagate(False)
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=T.BORDER_STRONG,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        self._build_data_source(scroll)
        self._build_columns(scroll)
        self._build_llm(scroll)
        self._build_prompt(scroll)

    # ==================== 数据源 ====================
    def _build_data_source(self, parent):
        card = Card(parent, title=i18n.t("sidebar.data_source"))
        card.pack(fill="x", padx=10, pady=(10, 8))

        self.src_tabs = ctk.CTkSegmentedButton(
            card.body, values=[i18n.t("src.tab_file"), i18n.t("src.tab_db")],
            command=self._on_src_tab, height=28,
            fg_color=T.SURFACE_2, selected_color=T.ACCENT,
            selected_hover_color=T.ACCENT_HOVER, text_color=T.TEXT_2,
            font=self._fonts.small,
        )
        self.src_tabs.set(i18n.t("src.tab_file"))
        self.src_tabs.pack(fill="x", pady=(0, 8))

        # ---- 文件面板 ----
        self.file_panel = ctk.CTkFrame(card.body, fg_color="transparent")
        self.file_panel.pack(fill="x")
        self.file_btn = GhostButton(self.file_panel, text=i18n.t("src.pick_file"),
                                    command=self._pick_file, height=30)
        self.file_btn.pack(fill="x")
        self.file_label = ctk.CTkLabel(self.file_panel, text=i18n.t("src.no_file"),
                                       font=self._fonts.tiny, text_color=T.TEXT_3, anchor="w")
        self.file_label.pack(fill="x", pady=(4, 6))

        row = ctk.CTkFrame(self.file_panel, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text=i18n.t("src.sheet"), font=self._fonts.small,
                     text_color=T.TEXT_2).pack(side="left")
        self.sheet_var = ctk.StringVar(value="")
        self.sheet_menu = ctk.CTkComboBox(
            row, variable=self.sheet_var, values=[i18n.t("src.sheet_placeholder")],
            width=140, height=28,
            font=self._fonts.small, dropdown_font=self._fonts.small,
            fg_color=T.SURFACE_2, border_color=T.BORDER, button_color=T.SURFACE_2,
            button_hover_color=T.HOVER, text_color=T.TEXT,
        )
        self.sheet_menu.pack(side="right")

        row2 = ctk.CTkFrame(self.file_panel, fg_color="transparent")
        row2.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(row2, text=i18n.t("src.load_limit"), font=self._fonts.small,
                     text_color=T.TEXT_2).pack(side="left")
        self._limit_keys = {v: k for v, k in config.ROW_LIMIT_OPTIONS}   # 值 -> i18n键
        cur_limit = self._settings.get("row_limit", config.DEFAULT_ROW_LIMIT)
        self.limit_var = ctk.StringVar(value=i18n.t(self._limit_keys.get(cur_limit, "src.limit.100000")))
        self.limit_menu = ctk.CTkComboBox(
            row2, variable=self.limit_var,
            values=[i18n.t(k) for _, k in config.ROW_LIMIT_OPTIONS],
            width=140, height=28, font=self._fonts.small, dropdown_font=self._fonts.small,
            fg_color=T.SURFACE_2, border_color=T.BORDER, button_color=T.SURFACE_2,
            button_hover_color=T.HOVER, text_color=T.TEXT,
            command=lambda _v: self._save_row_limit(),
        )
        self.limit_menu.pack(side="right")

        self.load_file_btn = PrimaryButton(self.file_panel, text=i18n.t("src.load_file"),
                                           command=self._load_file, height=30)
        self.load_file_btn.pack(fill="x", pady=(8, 0))
        SubtleButton(self.file_panel, text=i18n.t("src.load_sample"),
                     command=self._load_sample, height=24).pack(fill="x", pady=(2, 0))

        # ---- Databricks 面板 ----
        self.db_panel = ctk.CTkFrame(card.body, fg_color="transparent")
        self._db_entries = {}
        db_fields = [
            ("db.host", "db_host", "xxx.cloud.databricks.com", False),
            ("db.http_path", "db_http_path", "/sql/1.0/warehouses/xxx", False),
            ("db.token", "db_token", "", True),
            ("db.catalog", "db_catalog", "hive_metastore", False),
            ("db.schema", "db_schema", "default", False),
        ]
        for label_key, key, ph, secret in db_fields:
            ctk.CTkLabel(self.db_panel, text=i18n.t(label_key), font=self._fonts.small,
                         text_color=T.TEXT_2, anchor="w").pack(fill="x", pady=(4, 0))
            e = ctk.CTkEntry(self.db_panel, height=28, placeholder_text=ph,
                             show="•" if secret else "",
                             fg_color=T.SURFACE_2, border_color=T.BORDER,
                             font=self._fonts.small, text_color=T.TEXT)
            e.insert(0, self._settings.get(key, "") or "")
            e.pack(fill="x")
            self._db_entries[key] = e
        ctk.CTkLabel(self.db_panel, text=i18n.t("db.query"), font=self._fonts.small,
                     text_color=T.TEXT_2, anchor="w").pack(fill="x", pady=(6, 0))
        self.db_query = ctk.CTkTextbox(self.db_panel, height=60, wrap="word",
                                       font=self._fonts.mono_sm, fg_color=T.SURFACE_2,
                                       border_width=1, border_color=T.BORDER,
                                       corner_radius=T.RADIUS_SM, text_color=T.TEXT)
        self.db_query.insert("1.0", self._settings.get("db_query", "") or "")
        self.db_query.pack(fill="x")
        PrimaryButton(self.db_panel, text=i18n.t("db.connect"),
                      command=self._load_databricks, height=30).pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(self.db_panel, text=i18n.t("db.install_hint"),
                     font=self._fonts.tiny, text_color=T.TEXT_3, anchor="w",
                     wraplength=200, justify="left").pack(fill="x", pady=(4, 0))

        # ---- 当前数据源状态 ----
        self.src_status = ctk.CTkLabel(card.body, text="", font=self._fonts.small,
                                       text_color=T.SUCCESS, anchor="w", wraplength=210,
                                       justify="left")
        self.src_status.pack(fill="x", pady=(8, 0))

    # ==================== 显示字段 ====================
    def _build_columns(self, parent):
        card = Card(parent, title=i18n.t("sidebar.fields"))
        card.pack(fill="x", padx=10, pady=8)
        self.cols_hint = ctk.CTkLabel(card.body, text=i18n.t("fields.hint_empty"),
                                      font=self._fonts.tiny, text_color=T.TEXT_3, anchor="w")
        self.cols_hint.pack(fill="x", pady=(0, 6))
        btn_row = ctk.CTkFrame(card.body, fg_color="transparent")
        btn_row.pack(fill="x")
        SubtleButton(btn_row, text=i18n.t("fields.select_all"),
                     command=lambda: self._set_all_cols(True), width=44, height=24).pack(side="left")
        SubtleButton(btn_row, text=i18n.t("fields.invert"),
                     command=lambda: self._set_all_cols(None), width=44, height=24).pack(side="left", padx=4)
        self.cols_box = ctk.CTkScrollableFrame(card.body, fg_color=T.SURFACE_2,
                                               corner_radius=T.RADIUS_SM, height=160,
                                               scrollbar_button_color=T.BORDER_STRONG)
        self.cols_box.pack(fill="x", pady=(6, 0))

    # ==================== AI 模型 ====================
    def _build_llm(self, parent):
        card = Card(parent, title=i18n.t("sidebar.ai_model"))
        card.pack(fill="x", padx=10, pady=8)
        card.body.grid_columnconfigure(0, weight=1)
        backend = self._settings.get("llm_backend", "openai")
        self.backend_var = ctk.StringVar(value=self._backend_label(backend))
        # 显示标签 -> 后端键（如 "Ollama 本地大模型" -> "ollama"）
        self._backend_keys = {i18n.t(i18n_key): backend_key
                              for backend_key, i18n_key in config.LLM_BACKENDS.items()}
        self.backend_menu = ctk.CTkComboBox(
            card.body, variable=self.backend_var,
            values=list(self._backend_keys.keys()),
            width=200, height=28, font=self._fonts.small, dropdown_font=self._fonts.small,
            fg_color=T.SURFACE_2, border_color=T.BORDER, button_color=T.SURFACE_2,
            button_hover_color=T.HOVER, text_color=T.TEXT,
            # 注意：CTkComboBox 的 command 不同步 variable，必须用传入的 value
            command=self._on_backend_change,
        )
        self.backend_menu.grid(row=0, column=0, sticky="ew")

        # 字段容器：切换后端时清空重建。
        # 不用容器显隐（pack_forget/pack 或 grid_remove/grid）——customtkinter 的
        # CTkFrame 是 canvas+window 结构，容器重新显示时部分子控件不会重绘。
        self.llm_fields = ctk.CTkFrame(card.body, fg_color="transparent")
        self.llm_fields.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.llm_entries = {"openai": {}, "ollama": {}, "dify": {}}
        # 显式跟踪当前显示的后端（CTkComboBox 的 variable 同步时机不确定，
        # 绝不能依赖 backend_var 推断当前后端）
        self._active_backend = backend

        self.dify_note = ctk.CTkLabel(card.body, text="", font=self._fonts.tiny,
                                      text_color=T.TEXT_3, anchor="w", wraplength=210,
                                      justify="left")
        self.dify_note.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.dify_note.grid_remove()   # 默认隐藏（grid_remove 记住位置）

        test_row = ctk.CTkFrame(card.body, fg_color="transparent")
        test_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        SubtleButton(test_row, text=i18n.t("llm.test"), command=self._test_llm,
                     height=26).pack(side="left")
        self.test_status = ctk.CTkLabel(test_row, text="", font=self._fonts.tiny,
                                        text_color=T.TEXT_2, anchor="w")
        self.test_status.pack(side="left", padx=(8, 0))
        # 字段区不在此处构建：构造期间 Sidebar 尚未 pack 进主窗口（未映射），
        # 此时创建的 CTkLabel/CTkButton 不会绘制。由 build_fields() 在 pack 后调用。

    def build_fields(self):
        """pack 进主窗口后构建字段区（App._build_body 中调用）。"""
        self._llm_fields_rebuild(self._active_backend)

    def _backend_label(self, backend):
        return i18n.t(config.LLM_BACKENDS.get(backend, "llm.backend.openai"))

    def _llm_fields_rebuild(self, backend):
        """按后端重建字段区。值从 settings 恢复（切换前已保存，不丢数据）。
        三个后端配置彻底分家；ollama 精简为：模型下拉 + 刷新 + 扫描状态。"""
        for w in self.llm_fields.winfo_children():
            w.destroy()
        # 清空所有后端的控件引用（旧控件已销毁，留着会炸）
        self.llm_entries = {"openai": {}, "ollama": {}, "dify": {}}
        self._active_backend = backend
        parent = self.llm_fields

        def _add_label(text_key):
            ctk.CTkLabel(parent, text=i18n.t(text_key), font=self._fonts.small,
                         text_color=T.TEXT_2, anchor="w").pack(fill="x", pady=(4, 0))

        def _add_entry(key, placeholder="", secret=False):
            e = ctk.CTkEntry(parent, height=28, show="•" if secret else "",
                             placeholder_text=placeholder,
                             fg_color=T.SURFACE_2, border_color=T.BORDER,
                             font=self._fonts.small, text_color=T.TEXT)
            e.insert(0, self._settings.get(key, "") or "")
            e.bind("<FocusOut>", lambda _e: self._save_llm())
            e.bind("<Return>", lambda _e: self._save_llm())
            e.pack(fill="x")
            self.llm_entries[backend][key] = e
            return e

        if backend == "dify":
            _add_label("llm.dify_url")
            _add_entry("dify_api_url", "https://api.dify.ai/v1")
            _add_label("llm.api_key")
            _add_entry("dify_api_key", secret=True)
        elif backend == "ollama":
            # ---- Ollama：只选模型（切到该后端即自动扫描，无需按钮）----
            # 扫描结果走底部状态栏；Base URL 走 settings.json
            self.ollama_model_var = ctk.StringVar(
                value=self._settings.get("ollama_model", "") or "")
            self.ollama_model_menu = ctk.CTkComboBox(
                parent, variable=self.ollama_model_var,
                values=[], width=200, height=28,
                font=self._fonts.small, dropdown_font=self._fonts.small,
                fg_color=T.SURFACE_2, border_color=T.BORDER, button_color=T.SURFACE_2,
                button_hover_color=T.HOVER, text_color=T.TEXT,
                command=self._on_ollama_model_change,
            )
            self.ollama_model_menu.pack(side="left", pady=(4, 0))
        else:
            _add_label("llm.base_url")
            _add_entry("openai_base_url")
            _add_label("llm.api_key")
            _add_entry("openai_api_key", secret=True)
            _add_label("llm.model")
            _add_entry("openai_model")

    def set_ollama_models(self, models):
        """扫描完成后更新模型下拉（主线程调用）。"""
        self.ollama_model_menu.configure(values=models)
        cur = (self.ollama_model_var.get() or "").strip()
        if models and (not cur or cur not in models):
            self.ollama_model_var.set(models[0])
            self._settings.set("ollama_model", models[0])
            self._settings.save()

    # ==================== 提示词 ====================
    def _build_prompt(self, parent):
        card = Card(parent, title=i18n.t("sidebar.prompts"))
        card.pack(fill="x", padx=10, pady=(8, 16))
        cur = self._settings.get("prompt_template", config.DEFAULT_TEMPLATE)
        if cur not in config.PROMPT_TEMPLATES:
            cur = config.DEFAULT_TEMPLATE
        self.tpl_var = ctk.StringVar(value=cur)
        self.tpl_menu = ctk.CTkComboBox(
            card.body, variable=self.tpl_var, values=list(config.PROMPT_TEMPLATES.keys()),
            width=200, height=28, font=self._fonts.small, dropdown_font=self._fonts.small,
            fg_color=T.SURFACE_2, border_color=T.BORDER, button_color=T.SURFACE_2,
            button_hover_color=T.HOVER, text_color=T.TEXT,
            command=lambda _v: self._save_prompt(),
        )
        self.tpl_menu.pack(fill="x")
        self.tpl_desc = ctk.CTkLabel(card.body, text=self._tpl_desc(cur),
                                     font=self._fonts.tiny, text_color=T.TEXT_3, anchor="w",
                                     wraplength=210, justify="left")
        self.tpl_desc.pack(fill="x", pady=(4, 6))

        ctk.CTkLabel(card.body, text=i18n.t("prompt.rules"), font=self._fonts.small,
                     text_color=T.TEXT_2, anchor="w").pack(fill="x", pady=(2, 0))
        self.rules_box = ctk.CTkTextbox(card.body, height=90, wrap="word",
                                        font=self._fonts.small, fg_color=T.SURFACE_2,
                                        border_width=1, border_color=T.BORDER,
                                        corner_radius=T.RADIUS_SM, text_color=T.TEXT)
        saved_rules = self._settings.get("custom_rules", "") or ""
        self.rules_box.insert("1.0", saved_rules if saved_rules else i18n.t("prompt.custom_rules_placeholder"))
        self.rules_box.pack(fill="x")
        self.rules_box.bind("<FocusOut>", lambda _e: self._save_prompt())

        self.adv_btn = SubtleButton(card.body, text=i18n.t("prompt.adv_show"),
                                    command=self._toggle_advanced, height=24)
        self.adv_btn.pack(fill="x", pady=(6, 0))
        self.adv_frame = ctk.CTkFrame(card.body, fg_color="transparent")
        self.sys_prompt_box = ctk.CTkTextbox(self.adv_frame, height=140, wrap="word",
                                             font=self._fonts.mono_sm, fg_color=T.SURFACE_2,
                                             border_width=1, border_color=T.BORDER,
                                             corner_radius=T.RADIUS_SM, text_color=T.TEXT)
        self.sys_prompt_box.pack(fill="x")
        self.sys_prompt_box.bind("<FocusOut>", lambda _e: self._save_prompt())
        adv_btns = ctk.CTkFrame(self.adv_frame, fg_color="transparent")
        adv_btns.pack(fill="x", pady=(4, 0))
        SubtleButton(adv_btns, text=i18n.t("prompt.adv_reset"),
                     command=self._reset_sys_prompt, height=24).pack(side="left")
        self._advanced_visible = False

    def _tpl_desc(self, tpl_name):
        key = config.PROMPT_TEMPLATES.get(tpl_name, {}).get("desc_key", "")
        return i18n.t(key) if key else ""

    # ==================== 数据源交互 ====================
    def _on_src_tab(self, value):
        if value == i18n.t("src.tab_file"):
            self.db_panel.pack_forget()
            self.file_panel.pack(fill="x")
        else:
            self.file_panel.pack_forget()
            self.db_panel.pack(fill="x")

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title=i18n.t("dialog.pick_title"),
            filetypes=[(i18n.t("dialog.file_data"), "*.xlsx *.xls *.csv"),
                       (i18n.t("dialog.file_excel"), "*.xlsx *.xls"),
                       (i18n.t("dialog.file_csv"), "*.csv")],
        )
        if not path:
            return
        self._selected_file = path
        self.file_label.configure(text=os.path.basename(path))
        if self._cb.get("on_file_picked"):
            self._cb["on_file_picked"](path)

    def _load_file(self):
        if not self._selected_file:
            self.file_label.configure(text=i18n.t("src.no_file"))
            return
        limit = self._current_row_limit()
        sheet = self.sheet_var.get()
        if not sheet or sheet == i18n.t("src.sheet_placeholder"):
            sheet = None
        self._cb["on_load_file"](self._selected_file, sheet, limit)

    def _current_row_limit(self):
        label = self.limit_var.get()
        for v, k in config.ROW_LIMIT_OPTIONS:
            if i18n.t(k) == label:
                return v
        return config.DEFAULT_ROW_LIMIT

    def _load_sample(self):
        if self._cb.get("on_load_sample"):
            self._cb["on_load_sample"]()

    def _load_databricks(self):
        cfg = {k: e.get().strip() for k, e in self._db_entries.items()}
        cfg["query"] = self.db_query.get("1.0", "end-1c").strip()
        self._settings.set_many({**cfg, "db_query": cfg["query"]})
        self._settings.save()
        if self._cb.get("on_load_databricks"):
            self._cb["on_load_databricks"](cfg)

    def set_sheets(self, sheets, source_name=""):
        self._sheets = list(sheets)
        if self._sheets:
            self.sheet_menu.configure(values=self._sheets)
            self.sheet_var.set(self._sheets[0])
        else:
            self.sheet_menu.configure(values=[i18n.t("src.sheet_placeholder")])
            self.sheet_var.set(i18n.t("src.sheet_placeholder"))

    def set_source_status(self, text, ok=True):
        self.src_status.configure(text=text, text_color=T.SUCCESS if ok else T.ERROR)

    def _save_row_limit(self):
        self._settings.set("row_limit", self._current_row_limit())
        self._settings.save()

    # ==================== 显示字段 ====================
    def set_columns(self, columns, checked=None):
        for w in self.cols_box.winfo_children():
            w.destroy()
        self._col_vars = {}
        checked_set = set(checked) if checked is not None else None
        for c in columns:
            var = ctk.BooleanVar(value=True if checked_set is None else (c in checked_set))
            cb = ctk.CTkCheckBox(
                self.cols_box, text=str(c), variable=var, height=22,
                font=self._fonts.small, text_color=T.TEXT,
                checkbox_width=16, checkbox_height=16,
                fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                border_color=T.BORDER_STRONG, border_width=1,
                command=self._emit_columns,
            )
            cb.pack(anchor="w", pady=1)
            self._col_vars[c] = var
        self.cols_hint.configure(text=i18n.t("fields.hint", n=len(columns)))
        self._emit_columns()

    def _set_all_cols(self, value):
        for c, var in self._col_vars.items():
            var.set(True if value is True else (not var.get()))
        self._emit_columns()

    def _emit_columns(self):
        cols = [c for c, var in self._col_vars.items() if var.get()]
        if self._cb.get("on_columns_changed"):
            self._cb["on_columns_changed"](cols)

    def get_visible_columns(self):
        return [c for c, var in self._col_vars.items() if var.get()]

    # ==================== AI 模型 ====================
    def _on_backend_change(self, value=None):
        """后端切换。value 为 CTkComboBox command 传入的新标签——
        注意 CTkComboBox 的 command 不同步绑定的 variable，绝不能直接读 var。
        字段区用「清空重建」实现切换（Tk 容器显隐会丢子控件绘制）。"""
        label = value if value else self.backend_var.get()
        backend = self._backend_keys.get(label, "openai")
        if backend != self._active_backend:
            self._save_llm(self._active_backend)   # 保存当前实际显示的后端
        if self.backend_var.get() != label:
            self.backend_var.set(label)
        self._llm_fields_rebuild(backend)
        self._save_llm(backend)   # 保存新后端（rebuild 后控件已就绪）
        if backend == "dify":
            self.dify_note.grid()
            self.dify_note.configure(text=i18n.t("llm.dify_note"))
        else:
            self.dify_note.grid_remove()
        if self._cb.get("on_backend_changed"):
            self._cb["on_backend_changed"](backend)

    def _current_backend(self):
        return self._active_backend

    def get_llm_config(self):
        backend = self._current_backend()
        cfg = {"backend": backend}
        if backend == "dify":
            cfg["dify_api_url"] = self._entry_value("dify_api_url")
            cfg["api_key"] = self._entry_value("dify_api_key")
        elif backend == "ollama":
            cfg["base_url"] = self.get_ollama_base_url()
            cfg["model"] = self.get_ollama_model()
        else:
            cfg["base_url"] = self._entry_value("openai_base_url")
            cfg["api_key"] = self._entry_value("openai_api_key")
            cfg["model"] = self._entry_value("openai_model")
        return cfg

    def get_ollama_base_url(self):
        """Ollama 专用 Base URL（settings.json 独立存储，不与 other 后端混用）。"""
        return (self._settings.get("ollama_base_url", "")
                or "http://localhost:11434/v1")

    def get_ollama_model(self):
        if getattr(self, "ollama_model_var", None) is not None:
            return (self.ollama_model_var.get() or "").strip()
        return self._settings.get("ollama_model", "") or ""

    def _entry_value(self, key):
        widget = self.llm_entries.get(self._active_backend, {}).get(key)
        if widget is not None:
            try:
                if widget.winfo_exists():
                    return widget.get().strip()
            except Exception:
                pass
        return self._settings.get(key, "") or ""

    def _save_llm(self, backend=None):
        """只写指定后端自己那份配置，三个后端互不污染。"""
        backend = backend or self._active_backend
        if backend == "dify":
            self._settings.set_many({
                "llm_backend": backend,
                "dify_api_url": self._entry_value("dify_api_url"),
                "dify_api_key": self._entry_value("dify_api_key"),
            })
        elif backend == "ollama":
            self._settings.set_many({
                "llm_backend": backend,
                "ollama_base_url": self.get_ollama_base_url(),
                "ollama_model": self.get_ollama_model(),
            })
        else:
            self._settings.set_many({
                "llm_backend": backend,
                "openai_base_url": self._entry_value("openai_base_url"),
                "openai_api_key": self._entry_value("openai_api_key"),
                "openai_model": self._entry_value("openai_model"),
            })
        self._settings.save()

    def _test_llm(self):
        cfg = self.get_llm_config()
        self.test_status.configure(text=i18n.t("llm.testing"), text_color=T.TEXT_2)
        if self._cb.get("on_test_llm"):
            self._cb["on_test_llm"](cfg)

    def _on_ollama_model_change(self, value=None):
        """模型下拉选择（同样用 command 传入值，不信任 variable 时序）。"""
        model = (value if value else self.ollama_model_var.get() or "").strip()
        if value:
            self.ollama_model_var.set(value)
        self._settings.set("ollama_model", model)
        self._settings.save()

    def set_test_status(self, text, ok=True):
        self.test_status.configure(text=text, text_color=T.SUCCESS if ok else T.ERROR)

    # ==================== 提示词 ====================
    def _save_prompt(self):
        tpl = self.tpl_var.get()
        self.tpl_desc.configure(text=self._tpl_desc(tpl))
        self._settings.set("prompt_template", tpl)
        raw_rules = self.rules_box.get("1.0", "end-1c").rstrip("\n")
        self._settings.set("custom_rules", self._strip_placeholder(raw_rules))
        if self._advanced_visible:
            self._settings.set("system_prompt", self.sys_prompt_box.get("1.0", "end-1c").rstrip("\n"))
        self._settings.save()

    def _strip_placeholder(self, text: str) -> str:
        text = (text or "").strip()
        ph_zh = i18n.get_in("prompt.custom_rules_placeholder", "zh")
        ph_en = i18n.get_in("prompt.custom_rules_placeholder", "en")
        if text == ph_zh or text == ph_en or text.startswith("（在此添加"):
            return ""
        return text

    def get_prompt_config(self):
        custom = self._strip_placeholder(self.rules_box.get("1.0", "end-1c"))
        sys_prompt = ""
        if self._advanced_visible:
            sys_prompt = self.sys_prompt_box.get("1.0", "end-1c").strip()
        return {
            "template": self.tpl_var.get(),
            "custom_rules": custom,
            "system_prompt": sys_prompt,
        }

    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            tpl = self.tpl_var.get()
            default = config.PROMPT_TEMPLATES[tpl].get("system_prompt_en") if i18n.current() == "en" else config.PROMPT_TEMPLATES[tpl]["system_prompt"]
            self.sys_prompt_box.delete("1.0", "end")
            self.sys_prompt_box.insert("1.0", self._settings.get("system_prompt", "") or default)
            self.adv_frame.pack(fill="x", pady=(4, 0))
            self.adv_btn.configure(text=i18n.t("prompt.adv_hide"))
        else:
            self.adv_frame.pack_forget()
            self.adv_btn.configure(text=i18n.t("prompt.adv_show"))

    def _reset_sys_prompt(self):
        tpl = self.tpl_var.get()
        default = config.PROMPT_TEMPLATES[tpl]["system_prompt"]
        self.sys_prompt_box.delete("1.0", "end")
        self.sys_prompt_box.insert("1.0", default)
        self._save_prompt()
