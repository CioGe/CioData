# -*- coding: utf-8 -*-
"""
CioData 主窗口：标题栏 + 三区布局 + 状态栏。
编排所有业务流程：数据加载 / SQL执行 / AI对话 / 导出 / 主题 / 语言切换。
所有耗时操作走 TaskRunner 后台线程，UI 不卡；Tk 控件只在主线程访问。
"""

import os
from datetime import datetime
import tkinter.filedialog as filedialog
import customtkinter as ctk

from . import theme as T
from .widgets import FontsHolder, Fonts, GhostButton
from .tasks import TaskRunner, TaskFailed
from .sidebar import Sidebar
from .workspace import Workspace
from .chat_panel import ChatPanel
from .sql_snippets import SqlSnippetsPanel

import config
import i18n
from settings import Settings
from data_loader import load_excel, load_csv, load_from_databricks, list_excel_sheets
from sql_engine import execute_sql, get_schema_hint, apply_column_visibility
from llm_client import LLMClient, list_ollama_models

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_FILE = os.path.join(_PROJECT_DIR, "示例销售数据.xlsx")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        i18n.set_language(self.settings.get("language", "zh"))
        FontsHolder.set(Fonts())
        self._fonts = FontsHolder.get()

        ctk.set_appearance_mode(self.settings.get("theme", "light"))

        # ---------- 窗口 ----------
        self.title(f"{i18n.t('app.title')} · {i18n.t('app.subtitle')}")
        geo = self.settings.get("window_geometry", "1280x800")
        try:
            self.geometry(geo)
        except Exception:
            self.geometry("1280x800")
        self.minsize(1100, 680)

        # ---------- 窗口图标（assets/，缺失时静默跳过） ----------
        # 注意：必须用 iconbitmap（而非 iconphoto）。CTk 会在启动 200ms 后检查
        # _iconbitmap_method_called，若为 False 会用 CustomTkinter 默认蓝图标覆盖 iconphoto。
        try:
            _ico = os.path.join(_PROJECT_DIR, "assets", "icon.ico")
            _png = os.path.join(_PROJECT_DIR, "assets", "icon.png")
            if os.path.exists(_ico):
                self.iconbitmap(_ico)          # CTk 记录已调用，200ms 后不再覆盖
            elif os.path.exists(_png):
                from PIL import Image, ImageTk
                self._icon_img = ImageTk.PhotoImage(Image.open(_png))
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # ---------- 状态 ----------
        self.loaded_df = None      # 原始加载数据（只读副本）
        self.result_df = None      # 最近一次SQL执行结果（含全部列）
        self.source_name = ""
        self.chat_history = []     # LLM 对话上下文 [{"role","content"}]
        self.chat_log = []         # 聊天面板渲染日志（语言切换后重放）
        self._last_checked = None  # 最近一次字段勾选状态
        self._last_status = ""     # 状态栏最近文案

        # ---------- 任务器 ----------
        self.tasks = TaskRunner(self)

        # ---------- Tk 回调异常不再静默：弹窗提示并保持运行 ----------
        self.report_callback_exception = self._on_tk_error

        self._build_titlebar()
        self._build_body()
        self._build_statusbar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_status(i18n.t("status.ready"))

        # Ollama 后端：延迟自动扫描本地模型（等界面就绪）
        if self.sidebar._current_backend() == "ollama":
            self.after(600, self._scan_ollama)
    # ==================== 布局 ====================
    def _build_titlebar(self):
        # 工具条：OS 标题栏已有应用名，这里只放数据源 chip / 语言 / 主题等功能件
        bar = ctk.CTkFrame(self, fg_color=T.SURFACE, height=T.TITLEBAR_H, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.source_chip = ctk.CTkLabel(bar, text="", font=self._fonts.small,
                                        text_color=T.TEXT_2, fg_color=T.SURFACE_2,
                                        corner_radius=12, padx=10, pady=2)
        # 空文字不 pack：空 chip 带底色会像一块浅色残影
        self.lang_btn = GhostButton(bar, text=i18n.t("titlebar.lang_btn"),
                                    command=self._switch_language, width=52, height=28)
        self.lang_btn.pack(side="right", padx=(0, 8))
        self.theme_btn = GhostButton(bar, text="", command=self._toggle_theme,
                                     width=84, height=28)
        self.theme_btn.pack(side="right", padx=16)
        self._refresh_theme_btn()
        self._titlebar = bar

    def _show_source_chip(self, text):
        """数据源 chip：有文字才显示，空则隐藏（避免空底色残影）。"""
        if not text:
            self.source_chip.pack_forget()
            return
        self.source_chip.configure(text=text)
        if not self.source_chip.winfo_ismapped() and not self.source_chip.winfo_manager():
            self.source_chip.pack(side="left", padx=(16, 0))

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        # 用 grid 而不是 pack：pack 的 expand=True 会让 workspace 抢占
        # 后声明的 chat 面板，加载数据后表格变宽就把 AI 对话框盖掉。
        # grid 按列权分配空间，chat 列是固定宽度，永远不会被挤没。
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=0, minsize=T.SIDEBAR_W)  # 左：字段区
        body.grid_columnconfigure(1, weight=1, minsize=420)          # 中：工作区（吸收多余宽度）
        body.grid_columnconfigure(2, weight=0, minsize=T.CHAT_W)     # 右：AI 对话（固定宽）

        self.sidebar = Sidebar(body, self.settings, callbacks={
            "on_load_file": self._load_file,
            "on_load_databricks": self._load_databricks,
            "on_load_sample": self._load_sample,
            "on_file_picked": self._file_picked,
            "on_columns_changed": self._on_columns_changed,
            "on_test_llm": self._test_llm,
            "on_backend_changed": self._on_backend_changed,
        })
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        # 字段区推迟到窗口完成映射后再构建（pack 后同步创建时 Tk 尚未映射，
        # 该批 CTkLabel/CTkButton 不会被绘制）
        self.after(50, self.sidebar.build_fields)

        self.workspace = Workspace(body, callbacks={
            "on_run": self._run_sql,
            "on_export": self._export_csv,
            "on_reset_sql": self._reset_view,
            "on_page_size": self._on_page_size,
        })
        self.workspace.grid(row=0, column=1, sticky="nsew")

        # 右侧：上下一分二 —— 上半=SQL 片段存储，下半=AI 对话（固定宽）
        right = ctk.CTkFrame(body, fg_color=T.BG, corner_radius=0)
        right.grid(row=0, column=2, sticky="nsew")
        right.grid_rowconfigure(0, weight=0, minsize=220)   # 上：片段存储（固定高，内部滚动）
        right.grid_rowconfigure(1, weight=1, minsize=280)   # 下：AI 对话（吸收剩余高）
        right.grid_columnconfigure(0, weight=1)

        self.snippets = SqlSnippetsPanel(
            right, self.settings,
            on_adopt=self._adopt_sql_only,
            on_status=self._set_status,
        )
        self.snippets.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        self.chat = ChatPanel(
            right, width=T.CHAT_W, log=self.chat_log,
            on_send=self._on_chat_send,
            on_adopt_run=self._adopt_sql_run,
            on_adopt_only=self._adopt_sql_only,
            on_clear=self._on_chat_clear,
        )
        self.chat.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self.chat.grid_propagate(False)
        self._body = body

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=T.SURFACE, height=T.STATUSBAR_H, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_label = ctk.CTkLabel(bar, text="", font=self._fonts.tiny,
                                         text_color=T.TEXT_2, anchor="w")
        self.status_label.pack(side="left", padx=16)
        self.task_label = ctk.CTkLabel(bar, text="", font=self._fonts.tiny,
                                       text_color=T.ACCENT, anchor="e")
        self.task_label.pack(side="right", padx=16)
        self._statusbar = bar

    # ==================== 语言切换（重建界面并恢复状态） ====================
    def _switch_language(self):
        if self.tasks.busy:
            self._set_status(i18n.t("msg.wait_task"))
            return
        lang = "en" if i18n.current() == "zh" else "zh"
        i18n.set_language(lang)
        self.settings.set("language", lang)
        self.settings.save()
        self._rebuild_ui()

    def _rebuild_ui(self):
        """销毁并重建三区布局，从 App 状态完整恢复（数据/SQL/聊天/来源信息）。"""
        # 1. 快照
        sql_text = self.workspace.get_sql() if hasattr(self, "workspace") else config.DEFAULT_SQL
        # 2. 销毁
        for attr in ("_titlebar", "_body", "_statusbar"):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass
        # 3. 重建
        self.title(f"{i18n.t('app.title')} · {i18n.t('app.subtitle')}")
        self._build_titlebar()
        self._build_body()
        self._build_statusbar()
        # 4. 恢复数据视图
        if self.loaded_df is not None:
            checked = self._last_checked or list(self.result_df.columns)
            self.sidebar.set_columns(list(self.result_df.columns), checked=checked)
            self.workspace.set_data(apply_column_visibility(self.result_df, checked),
                                    page_size=self.settings.get("page_size", config.DEFAULT_PAGE_SIZE))
            self.sidebar.set_source_status(i18n.t(
                "src.loaded", name=self.source_name,
                rows=f"{len(self.loaded_df):,}", cols=len(self.loaded_df.columns)))
            self._show_source_chip(i18n.t("titlebar.source", name=self.source_name))
        # 5. 恢复 SQL 与状态栏
        self.workspace.set_sql(sql_text)
        if self._last_status:
            self._set_status(self._last_status)

    # ==================== 状态栏 ====================
    def _set_status(self, text):
        self._last_status = text
        if hasattr(self, "status_label"):
            self.status_label.configure(text=text)

    def _set_task(self, text):
        if hasattr(self, "task_label"):
            self.task_label.configure(text=text)

    # ==================== 数据加载 ====================
    def _file_picked(self, path):
        """选中文件后自动读取 sheet 列表。"""
        self.sidebar.set_source_status(i18n.t("src.reading", name=os.path.basename(path)), ok=True)

        def work():
            if path.lower().endswith((".xlsx", ".xls")):
                sheets, err = list_excel_sheets(path)
                if err:
                    raise TaskFailed(err)
                return sheets
            return ["(CSV)"]

        self.tasks.run(
            "读取结构", work,
            on_success=lambda sheets: (
                self.sidebar.set_sheets(sheets),
                self.sidebar.set_source_status(i18n.t("src.picked", name=os.path.basename(path))),
            ),
            on_error=lambda err: self.sidebar.set_source_status(err, ok=False),
        )

    def _load_file(self, path, sheet, limit):
        if not os.path.exists(path):
            self.workspace.show_msg(i18n.t("err.file_missing", path=path), "error")
            return
        nrows = limit if limit and limit > 0 else None

        def work():
            if path.lower().endswith((".xlsx", ".xls")):
                sheets, err = load_excel(path, sheet_name=sheet, nrows=nrows)
                if err:
                    raise TaskFailed(err)
                df = sheets[sheet] if sheet in sheets else next(iter(sheets.values()))
            elif path.lower().endswith(".csv"):
                df, err = load_csv(path, nrows=nrows)
                if err:
                    raise TaskFailed(err)
            else:
                raise TaskFailed(i18n.t("err.only_xlsx"))
            return df

        self._run_load_task(work, f"{os.path.basename(path)}" + (f" / {sheet}" if sheet else ""))

    def _load_sample(self):
        if not os.path.exists(SAMPLE_FILE):
            self.workspace.show_msg(i18n.t("err.sample_missing"), "error")
            return
        self._run_load_task(self._load_sample_df, "示例销售数据.xlsx")

    def _load_sample_df(self):
        sheets, err = load_excel(SAMPLE_FILE, sheet_name=0)
        if err:
            raise TaskFailed(err)
        return next(iter(sheets.values()))

    def _load_databricks(self, cfg):
        def work():
            df, err = load_from_databricks(
                cfg.get("db_host", ""), cfg.get("db_http_path", ""), cfg.get("db_token", ""),
                cfg.get("db_catalog", ""), cfg.get("db_schema", ""), cfg.get("query", ""),
            )
            if err:
                raise TaskFailed(err)
            return df

        self._run_load_task(work, f"Databricks: {cfg.get('db_catalog', '')}.{cfg.get('db_schema', '')}")

    def _run_load_task(self, work, source_name):
        self._set_task(i18n.t("task.loading"))

        def on_start():
            self.sidebar.set_source_status(i18n.t("src.loading"), ok=True)

        def on_success(df):
            self._on_data_loaded(df, source_name)

        def on_error(err):
            self.sidebar.set_source_status(err, ok=False)
            self.workspace.show_msg(err, "error")
            self._set_task("")

        def on_finish():
            self._set_task("")

        self.tasks.run(i18n.t("task.loading"), work, on_success=on_success,
                       on_error=on_error, on_start=on_start, on_finish=on_finish)

    def _on_data_loaded(self, df, source_name):
        if df is None or len(df) == 0:
            self.workspace.show_msg(i18n.t("ws.empty_result"), "warn")
            return
        self.loaded_df = df.copy()
        self.result_df = df.copy()
        self.source_name = source_name
        self.sidebar.set_columns(list(df.columns))
        self.sidebar.set_source_status(i18n.t("src.loaded", name=source_name,
                                              rows=f"{len(df):,}", cols=len(df.columns)))
        self._show_source_chip(i18n.t("titlebar.source", name=source_name))
        self.workspace.set_data(apply_column_visibility(self.result_df, self.sidebar.get_visible_columns()),
                                page_size=self.settings.get("page_size", config.DEFAULT_PAGE_SIZE))
        self.workspace.set_sql(config.DEFAULT_SQL)
        self.workspace.show_msg(i18n.t("msg.loaded_ok", rows=f"{len(df):,}", cols=len(df.columns)), "ok")
        self._set_status(i18n.t("status.loaded", name=source_name,
                                rows=f"{len(df):,}", cols=len(df.columns)))
        self.chat.reset()

    # ==================== SQL 执行 ====================
    def _run_sql(self, sql):
        if self.loaded_df is None:
            self.workspace.show_msg(i18n.t("ws.need_data"), "warn")
            return

        def work():
            result, err = execute_sql(self.loaded_df, sql)
            if err:
                raise TaskFailed(err)
            return result

        def on_start():
            self._set_task(i18n.t("task.sql"))

        def on_success(result):
            self.result_df = result
            # 保留用户对原始列的勾选状态，新增列自动勾选
            old_vis = set(self.sidebar.get_visible_columns())
            checked = [c for c in result.columns
                       if (c in old_vis) or (c not in self.loaded_df.columns)]
            self.sidebar.set_columns(list(result.columns), checked=checked)
            self.workspace.set_data(apply_column_visibility(result, checked),
                                    page_size=self.settings.get("page_size", config.DEFAULT_PAGE_SIZE))
            self.workspace.show_msg(i18n.t("msg.sql_ok", rows=f"{len(result):,}",
                                           cols=len(result.columns)), "ok")
            self._set_status(i18n.t("status.sql_ok", rows=f"{len(result):,}",
                                    cols=len(result.columns)))

        def on_error(err):
            self.workspace.show_msg(err, "error")
            self._set_status(i18n.t("status.sql_fail"))

        def on_finish():
            self._set_task("")

        self.tasks.run(i18n.t("task.sql"), work, on_success=on_success, on_error=on_error,
                       on_start=on_start, on_finish=on_finish)

    def _reset_view(self):
        if self.loaded_df is None:
            return
        self.result_df = self.loaded_df.copy()
        self.sidebar.set_columns(list(self.loaded_df.columns))
        self.workspace.set_data(apply_column_visibility(self.result_df, self.sidebar.get_visible_columns()),
                                page_size=self.settings.get("page_size", config.DEFAULT_PAGE_SIZE))
        self._set_status(i18n.t("status.view_reset"))

    def _on_columns_changed(self, cols):
        if self.result_df is None:
            return
        self._last_checked = cols
        self.workspace.set_data(apply_column_visibility(self.result_df, cols),
                                page_size=self.settings.get("page_size", config.DEFAULT_PAGE_SIZE),
                                keep_page=True)

    def _on_page_size(self, n):
        self.settings.set("page_size", n)
        self.settings.save()

    # ==================== 导出 ====================
    def _export_csv(self, df):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title=i18n.t("dialog.export_title"),
            defaultextension=".csv",
            initialfile=f"data_view_{ts}.csv",
            filetypes=[(i18n.t("dialog.csv_file"), "*.csv")],
        )
        if not path:
            return

        def work():
            df.to_csv(path, index=False, encoding="utf-8-sig")
            return path

        def on_success(p):
            self.workspace.show_msg(i18n.t("msg.exported", path=p), "ok")
            self._set_status(i18n.t("status.exported", name=os.path.basename(p)))

        def on_error(err):
            self.workspace.show_msg(err, "error")

        self.tasks.run(i18n.t("task.export"), work, on_success=on_success, on_error=on_error)

    # ==================== AI 对话 ====================
    def _build_llm_client(self):
        cfg = self.sidebar.get_llm_config()
        if cfg["backend"] == "dify":
            if not cfg.get("api_key") or not cfg.get("dify_api_url"):
                raise TaskFailed(i18n.t("err.dify_config"))
            return LLMClient(backend="dify", api_key=cfg["api_key"],
                             dify_api_url=cfg["dify_api_url"])
        if cfg["backend"] == "ollama" and not cfg.get("model"):
            raise TaskFailed(i18n.t("err.ollama_no_model"))
        if not cfg.get("base_url") or not cfg.get("model"):
            raise TaskFailed(i18n.t("err.llm_config"))
        return LLMClient(backend=cfg["backend"], api_key=cfg.get("api_key", ""),
                         base_url=cfg["base_url"], model=cfg["model"])

    def _test_llm(self, cfg):
        def work():
            if cfg["backend"] == "dify":
                client = LLMClient(backend="dify", api_key=cfg.get("api_key", ""),
                                   dify_api_url=cfg.get("dify_api_url", ""))
            else:
                client = LLMClient(backend=cfg["backend"], api_key=cfg.get("api_key", ""),
                                   base_url=cfg.get("base_url", ""), model=cfg.get("model", ""))
            return client.test_connection()

        self.tasks.run(
            i18n.t("task.test"), work,
            on_success=lambda r: (
                self.sidebar.set_test_status(
                    i18n.t("llm.test_ok") if not r else r, ok=not r),
                self._set_status(i18n.t("llm.test_ok") if not r else r),
            ),
            on_error=lambda err: (
                self.sidebar.set_test_status(err, ok=False),
                self._set_status(err),
            ),
        )

    # ---------- Ollama 本地模型扫描 ----------
    def _on_backend_changed(self, backend):
        # 注意：Sidebar 构造期间也会触发此回调，那时 self.sidebar 尚未赋值，
        # 必须守卫；启动时的扫描由 __init__ 里的 after(600) 负责。
        if backend == "ollama" and hasattr(self, "sidebar"):
            self._scan_ollama()

    def _scan_ollama(self):
        # Ollama 专用地址（settings.json 独立配置，绝不用其他后端的 base_url）
        base_url = self.sidebar.get_ollama_base_url()
        self._set_status(i18n.t("status.ollama_scanning"))

        def work():
            models, err = list_ollama_models(base_url)
            if err:
                raise TaskFailed(err)
            return models

        def on_success(models):
            self.sidebar.set_ollama_models(models)
            if models:
                self._set_status(i18n.t("status.ollama_ok", n=len(models),
                                        model=models[0]))
            else:
                self._set_status(i18n.t("llm.scan_failed"))

        def on_error(err):
            self.sidebar.set_ollama_models([])
            self._set_status(err)

        self.tasks.run(i18n.t("status.ollama_scanning"), work,
                       on_success=on_success, on_error=on_error)

    # ---------- 对话流程 ----------
    def _on_chat_send(self, text):
        if self.loaded_df is None:
            self.chat.add_error(i18n.t("chat.need_data"))
            return
        self.chat.add_user(text)
        self.chat_history.append({"role": "user", "content": text})
        self.chat.set_thinking(True)
        self._set_task(i18n.t("task.ai"))

        # 主线程快照所有 UI 状态（Tk 控件非线程安全，工作线程禁止访问）
        try:
            llm = self._build_llm_client()
            prompt_cfg = self.sidebar.get_prompt_config()
        except TaskFailed as e:
            self.chat.set_thinking(False)
            self._set_task("")
            self.chat.add_error(str(e))
            return
        history_snapshot = list(self.chat_history[:-1])

        def work():
            tpl = prompt_cfg["template"]
            tpl_data = config.PROMPT_TEMPLATES[tpl]
            if prompt_cfg["system_prompt"]:
                sys_p = prompt_cfg["system_prompt"]
            elif i18n.current() == "en":
                sys_p = tpl_data.get("system_prompt_en", tpl_data["system_prompt"])
            else:
                sys_p = tpl_data["system_prompt"]
            custom = prompt_cfg["custom_rules"]
            header = i18n.t("prompt.custom_rules_header")
            custom_block = f"{header}\n{custom}\n" if custom else ""
            full_sys = sys_p.replace("{custom_rules}", custom_block).replace(
                "{schema}", get_schema_hint(self.loaded_df))
            return llm.nl2sql(text, full_sys, "", history_snapshot)

        def on_success(sql):
            self.chat.set_thinking(False)
            self._set_task("")
            if sql.startswith("❌"):
                self.chat.add_error(sql)
                self._set_status(i18n.t("status.ai_fail"))
                return
            self.chat.add_sql(sql)
            self.chat_history.append({"role": "assistant", "content": f"已生成SQL:\n{sql}"})
            self._set_status(i18n.t("status.ai_sql_ready"))

        def on_error(err):
            self.chat.set_thinking(False)
            self._set_task("")
            self.chat.add_error(err)

        self.tasks.run(i18n.t("task.ai"), work, on_success=on_success, on_error=on_error)

    def _adopt_sql_run(self, sql):
        self.workspace.set_sql(sql)
        self._run_sql(sql)

    def _adopt_sql_only(self, sql):
        self.workspace.set_sql(sql)
        self._set_status(i18n.t("snippets.toast_adopted"))

    def _on_chat_clear(self):
        self.chat_history = []
        self.chat.reset()
        self._set_status(i18n.t("status.chat_cleared"))

    # ==================== 主题 ====================
    def _toggle_theme(self):
        cur = ctk.get_appearance_mode()
        nxt = "Dark" if cur == "Light" else "Light"
        ctk.set_appearance_mode(nxt)
        self.settings.set("theme", nxt.lower())
        self.settings.save()
        self._refresh_theme_btn()
        # 手动刷新不受 appearance mode 自动接管的原生控件
        self.after(80, self._apply_manual_theme)

    def _refresh_theme_btn(self):
        light = ctk.get_appearance_mode() == "Light"
        self.theme_btn.configure(text=i18n.t("titlebar.theme_dark" if light else "titlebar.theme_light"))

    def _apply_manual_theme(self):
        try:
            if self.workspace.winfo_exists():
                self.workspace.apply_theme()
        except Exception:
            pass

    # ==================== 异常处理 ====================
    # 无害的“widget 已销毁”类错误：界面重建/关闭后残留的 after 回调触发，
    # 只打印不弹窗（弹窗反而会把主循环拖死，形成错误窗风暴）。
    _HARMLESS_TK_ERRORS = (
        "invalid command name",
        "application has been destroyed",
        "can't invoke",
    )

    def _on_tk_error(self, exc, val, tb):
        """Tk 回调异常：真实错误弹非模态窗（不用模态——会阻塞主循环），
        无害的销毁残留错误只打印。"""
        import traceback
        traceback.print_exception(exc, val, tb)
        msg = str(val)
        if any(h in msg for h in self._HARMLESS_TK_ERRORS):
            return
        self._show_error_window(msg)

    def _show_error_window(self, text):
        try:
            if hasattr(self, "_err_win") and self._err_win.winfo_exists():
                self._err_win.destroy()
            win = ctk.CTkToplevel(self)
            win.title(i18n.t("common.error_title"))
            win.attributes("-topmost", True)
            win.resizable(False, False)
            ctk.CTkLabel(win, text=i18n.t("common.error_body", err=text),
                         font=self._fonts.small, text_color=T.TEXT,
                         wraplength=420, justify="left").pack(padx=20, pady=(20, 10))
            ctk.CTkButton(win, text=i18n.t("common.ok"), width=80,
                          command=win.destroy).pack(pady=(0, 16))
            # 居中于主窗口
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - 500) // 2
            y = self.winfo_y() + (self.winfo_height() - 220) // 2
            win.geometry(f"500x220+{x}+{y}")
            self._err_win = win
        except Exception:
            pass

    # ==================== 关闭 ====================
    def _on_close(self):
        try:
            self.settings.set("window_geometry", self.geometry())
            self.settings.save()
        except Exception:
            pass
        self.destroy()
