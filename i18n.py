# -*- coding: utf-8 -*-
"""
i18n 国际化：中文(zh) / 英文(en) 全量界面字符串。
用法: t("sidebar.data_source") 或带参数 t("status.loaded", name=..., rows=..., cols=...)
切换语言: set_language("en") / set_language("zh")
新增字符串时务必两个语言都加（selfcheck 会校验键集合一致）。
"""

_STRINGS = {
    # ==================== 通用 ====================
    "zh": {
        "app.title": "CioData",
        "app.subtitle": "AI 辅助数据筛选器",
        "common.ok": "确定",
        "common.cancel": "取消",
        "common.error_title": "出现问题",
        "common.error_body": "发生了意外错误，程序将继续运行：\n\n{err}\n\n详细堆栈已写入控制台。",

        # ==================== 标题栏 ====================
        "titlebar.source": "数据源: {name}",
        "titlebar.theme_dark": "🌙 暗色",
        "titlebar.theme_light": "☀️ 浅色",
        "titlebar.lang_btn": "EN",

        # ==================== 侧栏 · 分区 ====================
        "sidebar.data_source": "📁 数据源",
        "sidebar.fields": "👁️ 显示字段",
        "sidebar.ai_model": "🤖 AI 模型",
        "sidebar.prompts": "🧠 提示词",

        # ==================== 侧栏 · 数据源 ====================
        "src.tab_file": "文件",
        "src.tab_db": "Databricks",
        "src.pick_file": "选择 Excel / CSV 文件...",
        "src.no_file": "未选择文件",
        "src.sheet": "Sheet",
        "src.sheet_placeholder": "(先选文件)",
        "src.load_limit": "最多加载",
        "src.load_file": "📥 加载文件",
        "src.load_sample": "🎲 加载示例销售数据",
        "src.reading": "正在读取 {name} ...",
        "src.picked": "已选择 {name}，点「加载文件」",
        "src.loading": "正在加载，请稍候...",
        "src.loaded": "✅ {name}\n{rows} 行 × {cols} 列",
        "src.limit.10000": "1万行（推荐，最流畅）",
        "src.limit.50000": "5万行",
        "src.limit.100000": "10万行",
        "src.limit.500000": "50万行",
        "src.limit.0": "不限制（小心内存）",

        # Databricks
        "db.host": "Server Hostname",
        "db.http_path": "HTTP Path",
        "db.token": "Access Token",
        "db.catalog": "Catalog",
        "db.schema": "Schema",
        "db.query": "SQL查询（仅SELECT）",
        "db.connect": "☁️ 连接Databricks",
        "db.install_hint": "首次使用需安装依赖：双击项目目录下的「安装Databricks依赖.bat」",

        # ==================== 侧栏 · 显示字段 ====================
        "fields.hint_empty": "加载数据后可勾选要展示的列",
        "fields.hint": "共 {n} 列 · 取消勾选仅在当前视图隐藏",
        "fields.select_all": "全选",
        "fields.invert": "反选",

        # ==================== 侧栏 · AI 模型 ====================
        "llm.backend.openai": "OpenAI 兼容 API（GPT / DeepSeek / 智谱 / 通义等）",
        "llm.backend.ollama": "Ollama 本地大模型",
        "llm.backend.dify": "Dify 应用 API",
        "llm.base_url": "Base URL",
        "llm.api_key": "API Key",
        "llm.model": "模型名称",
        "llm.scan_failed": "未检测到 Ollama 服务，请确认已安装并启动（默认 http://localhost:11434）",
        "llm.dify_url": "Dify API URL",
        "llm.dify_note": "Dify 应用的输出需为纯 SQL（可在 Dify 提示词中要求只输出SQL）",
        "llm.test": "测试连接",
        "llm.testing": "测试中...",
        "llm.test_ok": "✅ 连接正常",

        # ==================== 侧栏 · 提示词 ====================
        "prompt.template": "行业分析模板",
        "prompt.rules": "业务自定义规则（每行一条）",
        "prompt.adv_show": "🛠️ 编辑完整 system prompt",
        "prompt.adv_hide": "🛠️ 收起 system prompt 编辑",
        "prompt.adv_reset": "恢复模板默认",
        "prompt.tpl.general": "通用BI分析场景，适合日常数据查询",
        "prompt.tpl.sales": "订单/GMV/SKU/客单价等电商指标",
        "prompt.tpl.finance": "凭证/科目/借贷/账龄等财务场景",
        "prompt.tpl.growth": "DAU/留存/漏斗/ARPU等运营指标",
        "prompt.tpl.bi": "透视表/分位数/分箱/累计/移动平均",
        "prompt.custom_rules_header": "【业务自定义规则 - 必须严格遵守】",
        "prompt.custom_rules_placeholder": "（在此添加公司/业务自定义术语约定，每行一条，例如：\n• '大单' 指 订单金额 > 50000 元\n• '北区' 包含 北京、天津、河北、山西、内蒙古\n• 销售额字段统一使用'实付金额'列\n留空则不添加额外规则）",
        "task.busy": "正在执行「{name}」，请稍候完成",

        # ==================== 工作区 · SQL 编辑器 ====================
        "ws.sql_title": "📝 SQL 编辑器",
        "ws.sql_hint": "表名 df · SQLite 方言 · Ctrl+Enter 运行",
        "ws.run": "▶ RUN",
        "ws.reset_sql": "⏹ 重置SQL",
        "ws.table_title": "📋 数据展示",
        "ws.no_data": "暂无数据",
        "ws.empty_result": "查询结果为空",
        "ws.rows_info": "共 {total} 行 × {cols} 列   ·   当前第 {start}-{end} 行",
        "ws.page": "{page} / {pages}",
        "ws.page_zero": "0 / 0",
        "ws.prev": "◀ 上一页",
        "ws.next": "下一页 ▶",
        "ws.page_box": "页码",
        "ws.per_page": "每页",
        "ws.export": "💾 导出CSV",
        "ws.copied": "已复制: {text}",
        "ws.need_data": "请先加载数据",
        "ws.sql_empty": "SQL 为空",

        # ==================== 聊天面板 ====================
        "chat.title": "✨ AI 助手",
        "chat.clear": "清空",
        "chat.placeholder": ("用自然语言描述你的分析需求，例如：\n"
                             "· 筛选北京销售额大于2万的订单\n"
                             "· 按城市分组统计订单数和总销售额\n"
                             "· 新增一列毛利率=利润/销售额，降序"),
        "chat.input_hint": "Enter 发送 · Shift+Enter 换行",
        "chat.send": "发送",
        "chat.sending": "...",
        "chat.adopt_run": "⬅ 采用并执行",
        "chat.adopt_only": "仅填入编辑器",
        "chat.need_data": "请先加载数据再提问",

        # ==================== SQL 片段 DIY 存储 ====================
        "snippets.title": "🧩 SQL 语句 DIY 存储",
        "snippets.hint": "「采用」把语句送入 SQL 编辑器",
        "snippets.slot_prefix": "槽位",
        "snippets.edit": "编辑",
        "snippets.adopt": "采用",
        "snippets.dialog_title": "编辑 SQL 片段",
        "snippets.dialog_name": "名称（仅展示）",
        "snippets.dialog_name_ph": "给这个片段起个名字",
        "snippets.dialog_sql": "SQL 语句",
        "snippets.dialog_save": "保存",
        "snippets.dialog_cancel": "取消",
        "snippets.dialog_clear": "清空",
        "snippets.toast_saved": "✅ 已保存 SQL 片段",
        "snippets.toast_adopted": "📝 已把 SQL 送入编辑器，可手动运行",

        # ==================== 状态栏 / 任务 ====================
        "status.ready": "就绪 · 请先在左侧加载数据",
        "status.loaded": "已加载 {name} · {rows} 行 × {cols} 列 · 只读模式",
        "status.sql_ok": "SQL执行成功 · {rows} 行 × {cols} 列",
        "status.sql_fail": "SQL执行失败",
        "status.view_reset": "视图已重置",
        "status.chat_cleared": "对话已清空",
        "status.ai_sql_ready": "AI已生成SQL · 可点「采用并执行」",
        "status.ai_fail": "AI调用失败",
        "status.exported": "已导出 {name}",
        "status.ollama_scanning": "正在扫描 Ollama 本地模型...",
        "status.ollama_ok": "已找到 {n} 个本地模型，当前选中：{model}",
        "task.loading": "正在加载数据...",
        "task.sql": "执行SQL...",
        "task.ai": "AI生成SQL...",
        "task.export": "导出CSV...",
        "task.reading": "读取结构...",
        "task.test": "测试连接...",

        # ==================== 对话框 ====================
        "dialog.export_title": "导出当前视图为CSV",
        "dialog.pick_title": "选择数据文件",
        "dialog.file_data": "数据文件",
        "dialog.file_excel": "Excel",
        "dialog.file_csv": "CSV",
        "dialog.csv_file": "CSV 文件",

        # ==================== 核心模块错误消息 ====================
        "err.empty_sql": "SQL语句为空",
        "err.forbidden_kw": "❌ 检测到写操作关键字 `{kw}`，工具为只读模式，禁止修改数据",
        "err.multi_stmt": "❌ 仅支持单条 SELECT 查询语句",
        "err.only_select": "❌ 仅支持 SELECT / WITH(CTE) / EXPLAIN 查询语句",
        "err.sql_error": "❌ SQL执行错误: {e}",
        "err.sql_timeout": "❌ SQL执行超时（>{sec}秒），请优化查询或缩小数据范围",
        "err.excel_load": "❌ Excel加载失败: {e}",
        "err.no_openpyxl": "❌ 缺少 openpyxl，请执行: pip install openpyxl",
        "err.csv_load": "❌ CSV加载失败(编码{enc}): {e}",
        "err.csv_encoding": "❌ CSV编码无法识别，请尝试另存为UTF-8格式",
        "err.sheets": "❌ 读取sheet列表失败: {e}",
        "err.db_missing": ("❌ Databricks依赖未安装。请双击项目目录下的「安装Databricks依赖.bat」，\n"
                           "或在黑窗口执行: .venv\\Scripts\\python.exe -m pip install databricks-sql-connector\n\n"
                           "（若安装失败，多为系统缺少C++编译工具，建议改用Excel/CSV方式）"),
        "err.db_query": "❌ 仅支持 SELECT / WITH 查询（只读保护）",
        "err.db_readonly": ("❌ 安全拦截：本程序对 Databricks 只读，不允许任何写操作。\n\n"
                            "原因: {detail}\n\n"
                            "允许的语句：SELECT / WITH ... SELECT\n"
                            "禁止的语句：INSERT / UPDATE / DELETE / DROP / ALTER / CREATE /\n"
                            "            TRUNCATE / MERGE / OPTIMIZE / COPY 等，以及用分号拼接多条语句"),
        "err.db_connect": "❌ Databricks连接失败: {e}",
        "err.file_missing": "文件不存在: {path}",
        "err.only_xlsx": "❌ 仅支持 .xlsx / .xls / .csv 文件",
        "err.sample_missing": "未找到示例数据文件，请先运行: python generate_sample.py",
        "err.llm_config": "❌ 请先在左侧「AI 模型」中填写 Base URL 和模型名称",
        "err.ollama_no_model": "❌ 未选择模型。请确认 Ollama 已启动（切到 Ollama 后端会自动扫描本地模型，若模型列表为空请确认服务在运行）",
        "err.dify_config": "❌ 请先在左侧「AI 模型」中填写 Dify API URL 和 Key",
        "msg.loaded_ok": "✅ 已加载 {rows} 行 × {cols} 列",
        "msg.sql_ok": "✅ 执行成功：{rows} 行 × {cols} 列",
        "msg.exported": "✅ 已导出: {path}",
        "msg.busy": "正在执行「{name}」，请稍候完成",
        "msg.wait_task": "请等待当前任务完成后再切换",
    },
    # ==================== English ====================
    "en": {
        "app.title": "CioData",
        "app.subtitle": "AI-Powered Data Filter",
        "common.ok": "OK",
        "common.cancel": "Cancel",
        "common.error_title": "Something went wrong",
        "common.error_body": "An unexpected error occurred. The app will keep running:\n\n{err}\n\nStack trace was printed to the console.",

        # Titlebar
        "titlebar.source": "Source: {name}",
        "titlebar.theme_dark": "🌙 Dark",
        "titlebar.theme_light": "☀️ Light",
        "titlebar.lang_btn": "中文",

        # Sidebar sections
        "sidebar.data_source": "📁 Data Source",
        "sidebar.fields": "👁️ Visible Fields",
        "sidebar.ai_model": "🤖 AI Model",
        "sidebar.prompts": "🧠 Prompts",

        # Data source
        "src.tab_file": "File",
        "src.tab_db": "Databricks",
        "src.pick_file": "Choose Excel / CSV file...",
        "src.no_file": "No file selected",
        "src.sheet": "Sheet",
        "src.sheet_placeholder": "(pick a file first)",
        "src.load_limit": "Load limit",
        "src.load_file": "📥 Load File",
        "src.load_sample": "🎲 Load Sample Sales Data",
        "src.reading": "Reading {name} ...",
        "src.picked": "Selected {name} — click \"Load File\"",
        "src.loading": "Loading, please wait...",
        "src.loaded": "✅ {name}\n{rows} rows × {cols} cols",
        "src.limit.10000": "10K rows (recommended, smoothest)",
        "src.limit.50000": "50K rows",
        "src.limit.100000": "100K rows",
        "src.limit.500000": "500K rows",
        "src.limit.0": "Unlimited (watch memory)",

        # Databricks
        "db.host": "Server Hostname",
        "db.http_path": "HTTP Path",
        "db.token": "Access Token",
        "db.catalog": "Catalog",
        "db.schema": "Schema",
        "db.query": "SQL query (SELECT only)",
        "db.connect": "☁️ Connect Databricks",
        "db.install_hint": "First time? Double-click \"安装Databricks依赖.bat\" in the project folder to install the connector",

        # Fields
        "fields.hint_empty": "Load data to choose visible columns",
        "fields.hint": "{n} columns · uncheck to hide from view only",
        "fields.select_all": "All",
        "fields.invert": "Invert",

        # AI model
        "llm.backend.openai": "OpenAI-compatible API (GPT / DeepSeek / Zhipu / Qwen...)",
        "llm.backend.ollama": "Ollama (local models)",
        "llm.backend.dify": "Dify App API",
        "llm.base_url": "Base URL",
        "llm.api_key": "API Key",
        "llm.model": "Model",
        "llm.scan_failed": "Ollama service not detected. Make sure Ollama is installed and running (default http://localhost:11434)",
        "llm.dify_url": "Dify API URL",
        "llm.dify_note": "The Dify app should output pure SQL (ask for SQL-only in its prompt)",
        "llm.test": "Test Connection",
        "llm.testing": "Testing...",
        "llm.test_ok": "✅ Connected",

        # Prompts
        "prompt.template": "Industry template",
        "prompt.rules": "Business rules (one per line)",
        "prompt.adv_show": "🛠️ Edit full system prompt",
        "prompt.adv_hide": "🛠️ Collapse system prompt editor",
        "prompt.adv_reset": "Restore template default",
        "prompt.tpl.general": "General BI analysis for everyday queries",
        "prompt.tpl.sales": "Orders / GMV / SKU / AOV for e-commerce",
        "prompt.tpl.finance": "Vouchers / accounts / debit-credit / aging",
        "prompt.tpl.growth": "DAU / retention / funnel / ARPU metrics",
        "prompt.tpl.bi": "Pivot / quantiles / binning / cumulative / moving average",
        "prompt.custom_rules_header": "[Business Custom Rules - MUST be strictly followed]",
        "prompt.custom_rules_placeholder": "Add your company/business custom term conventions here, one per line, e.g.:\n- 'Big order' means order amount > 50000\n- 'North region' covers Beijing, Tianjin, Hebei, Shanxi, Inner Mongolia\n- Use the 'Actual Paid Amount' column for sales\nLeave empty to add no extra rules",
        "task.busy": "Task '{name}' is still running, please wait",

        # Workspace
        "ws.sql_title": "📝 SQL Editor",
        "ws.sql_hint": "Table df · SQLite dialect · Ctrl+Enter to run",
        "ws.run": "▶ RUN",
        "ws.reset_sql": "⏹ Reset SQL",
        "ws.table_title": "📋 Results",
        "ws.no_data": "No data",
        "ws.empty_result": "Query returned no rows",
        "ws.rows_info": "{total} rows × {cols} cols   ·   showing {start}-{end}",
        "ws.page": "{page} / {pages}",
        "ws.page_zero": "0 / 0",
        "ws.prev": "◀ Prev",
        "ws.next": "Next ▶",
        "ws.page_box": "Page",
        "ws.per_page": "Rows",
        "ws.export": "💾 Export CSV",
        "ws.copied": "Copied: {text}",
        "ws.need_data": "Please load data first",
        "ws.sql_empty": "SQL is empty",

        # Chat
        "chat.title": "✨ AI Assistant",
        "chat.clear": "Clear",
        "chat.placeholder": ("Describe what you want to analyze, e.g.:\n"
                             "· Orders in Beijing with sales over 20K\n"
                             "· Group by city: order count and total sales\n"
                             "· Add a margin column = profit/sales, descending"),
        "chat.input_hint": "Enter to send · Shift+Enter for newline",
        "chat.send": "Send",
        "chat.sending": "...",
        "chat.adopt_run": "⬅ Adopt & Run",
        "chat.adopt_only": "Fill editor only",
        "chat.need_data": "Load data before asking",

        # SQL Snippets (DIY storage)
        "snippets.title": "🧩 SQL Snippets",
        "snippets.hint": "Click Adopt to send SQL to the editor",
        "snippets.slot_prefix": "Slot",
        "snippets.edit": "Edit",
        "snippets.adopt": "Adopt",
        "snippets.dialog_title": "Edit SQL Snippet",
        "snippets.dialog_name": "Name (display only)",
        "snippets.dialog_name_ph": "Name this snippet",
        "snippets.dialog_sql": "SQL Statement",
        "snippets.dialog_save": "Save",
        "snippets.dialog_cancel": "Cancel",
        "snippets.dialog_clear": "Clear",
        "snippets.toast_saved": "✅ Snippet saved",
        "snippets.toast_adopted": "📝 SQL sent to editor — run it manually",

        # Status / tasks
        "status.ready": "Ready · Load data on the left to begin",
        "status.loaded": "Loaded {name} · {rows} rows × {cols} cols · read-only",
        "status.sql_ok": "SQL executed · {rows} rows × {cols} cols",
        "status.sql_fail": "SQL execution failed",
        "status.view_reset": "View reset",
        "status.chat_cleared": "Chat cleared",
        "status.ai_sql_ready": "SQL generated · click \"Adopt & Run\"",
        "status.ai_fail": "AI request failed",
        "status.exported": "Exported {name}",
        "status.ollama_scanning": "Scanning local Ollama models...",
        "status.ollama_ok": "Found {n} local model(s), selected: {model}",
        "task.loading": "Loading data...",
        "task.sql": "Running SQL...",
        "task.ai": "Generating SQL...",
        "task.export": "Exporting CSV...",
        "task.reading": "Reading structure...",
        "task.test": "Testing connection...",

        # Dialogs
        "dialog.export_title": "Export current view as CSV",
        "dialog.pick_title": "Select data file",
        "dialog.file_data": "Data files",
        "dialog.file_excel": "Excel",
        "dialog.file_csv": "CSV",
        "dialog.csv_file": "CSV files",

        # Core errors
        "err.empty_sql": "SQL is empty",
        "err.forbidden_kw": "❌ Write keyword `{kw}` detected. Read-only mode: data modification is blocked",
        "err.multi_stmt": "❌ Only a single SELECT statement is allowed",
        "err.only_select": "❌ Only SELECT / WITH(CTE) / EXPLAIN queries are supported",
        "err.sql_error": "❌ SQL execution error: {e}",
        "err.sql_timeout": "❌ SQL timed out (>{sec}s). Optimize the query or narrow the data range",
        "err.excel_load": "❌ Excel load failed: {e}",
        "err.no_openpyxl": "❌ openpyxl missing. Run: pip install openpyxl",
        "err.csv_load": "❌ CSV load failed (encoding {enc}): {e}",
        "err.csv_encoding": "❌ Could not detect CSV encoding. Try saving as UTF-8",
        "err.sheets": "❌ Failed to read sheet list: {e}",
        "err.db_missing": ("❌ Databricks connector not installed. Double-click \"安装Databricks依赖.bat\" "
                           "in the project folder, or run:\n"
                           "    .venv\\Scripts\\python.exe -m pip install databricks-sql-connector\n\n"
                           "(If it fails, your system may lack C++ build tools — use Excel/CSV instead)"),
        "err.db_query": "❌ Only SELECT / WITH queries are allowed (read-only)",
        "err.db_readonly": ("❌ Blocked: this app is read-only against Databricks.\n\n"
                            "Reason: {detail}\n\n"
                            "Allowed: SELECT / WITH ... SELECT\n"
                            "Blocked: INSERT / UPDATE / DELETE / DROP / ALTER / CREATE /\n"
                            "         TRUNCATE / MERGE / OPTIMIZE / COPY, and stacked statements"),
        "err.db_connect": "❌ Databricks connection failed: {e}",
        "err.file_missing": "File not found: {path}",
        "err.only_xlsx": "❌ Only .xlsx / .xls / .csv files are supported",
        "err.sample_missing": "Sample data file not found. Run: python generate_sample.py",
        "err.llm_config": "❌ Fill in Base URL and model name in \"AI Model\" first",
        "err.ollama_no_model": "❌ No model selected. Make sure Ollama is running (switching to the Ollama backend scans local models automatically; if the list is empty, confirm the service is up)",
        "err.dify_config": "❌ Fill in Dify API URL and Key in \"AI Model\" first",
        "msg.loaded_ok": "✅ Loaded {rows} rows × {cols} cols",
        "msg.sql_ok": "✅ Executed: {rows} rows × {cols} cols",
        "msg.exported": "✅ Exported: {path}",
        "msg.busy": "Busy with \"{name}\" — please wait",
        "msg.wait_task": "Please wait for the current task to finish",
    },
}

_current = "zh"
_missing = set()   # 记录缺失键，供 selfcheck 检查


def set_language(lang: str):
    global _current
    _current = lang if lang in _STRINGS else "zh"


def current() -> str:
    return _current


def get_in(key: str, lang: str) -> str:
    """取指定语言的字符串（用于跨语言比对，如占位符清理）。"""
    table = _STRINGS.get(lang, _STRINGS["zh"])
    return table.get(key, key)


def t(key: str, **kwargs) -> str:
    """取当前语言的字符串；支持 {name} 占位符。"""
    table = _STRINGS[_current]
    s = table.get(key)
    if s is None:
        _missing.add(key)
        s = key
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s


def missing_keys():
    return set(_missing)


def all_keys():
    return set(_STRINGS["zh"].keys())
