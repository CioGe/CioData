<p align="center">
  <img src="assets/icon.png" width="96" alt="CioData logo"/>
</p>

<h1 align="center">CioData · AI 辅助数据筛选器</h1>

<p align="center">
  <b>用自然语言问数据，一条 SQL 都不用写。</b><br/>
  <i>Ask your data in plain language — no SQL required.</i>
</p>

<p align="center">
  English · 中文 一键切换 ｜ 纯本地运行 ｜ 零安装便携版 ｜ MIT 开源
</p>

---

CioData 是一个**本地运行**的桌面小工具（Python + CustomTkinter + Tkinter）：把 Excel / CSV / Databricks 的数据加载进来，用大白话向 AI 提问，它生成 SQL、本地执行、分页展示，并支持一键导出 CSV。全程只读，**绝不改动你的原始数据**。

CioData is a **local-first** desktop tool (Python + CustomTkinter + Tkinter). Load Excel / CSV / Databricks data, ask in plain language, and an LLM turns it into SQL that runs locally — paginated results, one-click CSV export. Strictly read-only: your source data is never modified.


---

## 🚀 快速启动 · Quick Start

### 方式一：便携版（推荐，免装 Python） · Portable (recommended, no Python needed)

1. 到 GitHub **Releases** 下载 `CioData_portable_win64.zip`
2. 解压到任意位置（**不要在压缩包预览里双击**）
3. 双击 `启动 CioData.bat`（或 `portable_launcher.py`）
4. 首次自动体检，约几秒后桌面窗口打开 ✅

1. Grab `CioData_portable_win64.zip` from GitHub **Releases**
2. Unzip anywhere (**don't double-click from inside the archive preview**)
3. Double-click `启动 CioData.bat` (or `portable_launcher.py`)
4. First launch self-checks, then the desktop window opens in a few seconds ✅

> 便携版已内置 Python 3.12.10 运行时 + Databricks 连接器，U 盘可携带，拔了 Python 的电脑也能跑。
> The portable bundle already embeds the Python 3.12.10 runtime + the Databricks connector — run it from a USB stick, no Python install required.

### 方式二：源码运行（开发者） · From Source (developers)

```bash
git clone <your-fork-or-this-repo>
cd CioData
pip install -r requirements.txt
python main.py                 # 直接跑 / run directly
# 或 / or  双击 run.bat
python selfcheck.py            # 核心逻辑自检（20+ 项）/ core self-checks
```

需要连 Databricks：双击 **install_databricks.bat** 一键装连接器（源码版）。
To connect Databricks on the source build, double-click **install_databricks.bat**.

---

## 🧩 功能一览 · Features

| 模块 Module | 说明 Description |
|------|------|
| 📁 数据源 Data Source | 本地 Excel(.xlsx/.xls)/CSV；Databricks SQL 连接（便携版内置，源码版一键装） / Local Excel(.xlsx/.xls)/CSV; Databricks SQL (built-in in portable, one-click for source) |
| 📝 SQL 编辑器 SQL Editor | 行号 + 关键字高亮，Ctrl+Enter 运行，SQLite 方言 / Line numbers + highlight, Ctrl+Enter to run, SQLite dialect |
| 📋 结果表格 Results | 分页 / 点表头排序 / 双击单元格复制 / 一键导 CSV(UTF-8 BOM) / Paginate / sort / copy cell / CSV export |
| 🤖 AI 对话 AI Chat | 自然语言 → SQL，一键「采用并执行」或「仅采用」 / NL → SQL, one-click "Adopt & Run" or "Adopt only" |
| 🧩 **SQL 语句 DIY 存储** SQL Snippets | **右侧 10 个槽位**：名称显示 + 编辑弹窗（自定义名称/语句）+ 采用（一键置入 SQL 编辑器）/ **10 slots**: name display + edit popup + adopt into editor |
| 🧠 AI 后端 AI Backend | OpenAI 兼容 API / Ollama 本地模型 / Dify，三种互不污染 / OpenAI-compatible API / Ollama local / Dify |
| 🧠 提示词 Prompts | 5 套行业模板 + 自定义业务术语规则 + 高级 system prompt 编辑；**中英文提示词各自独立** / 5 industry templates + custom rules + advanced editor; **separate zh/en prompts** |
| 👁️ 显示字段 Visible Fields | 勾选控制展示列，只影响视图不动数据 / Toggle columns; view-only |
| 🌙 主题 / 🌐 语言 Theme / Language | 浅色/暗色一键切换；中文/English 界面切换（状态不丢）/ Light/dark toggle; zh/en switch (state preserved) |

### 新增：SQL 语句 DIY 存储（v3.4）· New: SQL Snippet Storage (v3.4)

右侧上半区新增 10 个槽位，把常用 SQL 存起来随时取用：

- **名称**：仅展示，在编辑弹窗里改
- **编辑**：弹窗自定义名称 + SQL 语句，点「保存」入库
- **采用**：一键把存储的 SQL 送入 SQL 编辑器，供你随后手动执行（空槽自动禁用）

数据持久化在 `settings.json` 的 `sql_snippets`，关掉软件再开仍在。

The top-right panel now offers **10 snippet slots** to stash frequently-used SQL:

- **Name**: display-only (edited in the popup)
- **Edit**: popup to set name + SQL, saved on "Save"
- **Adopt**: one click drops the stored SQL into the editor for you to run (empty slots disabled)

Persisted in `settings.json` → `sql_snippets`; survives restarts.

---

## 🔒 只读保证 · Read-Only Guarantee

数据加载即深拷贝；SQL 在独立内存 SQLite 库执行；写操作（INSERT/UPDATE/DELETE/DROP…）语法层直接拦截；对 Databricks 的查询强制只读（多层校验 + 连接层 read_only 双保险）；代码里没有任何回写原始文件的逻辑。导出的 CSV 永远是新文件。

Data is deep-copied on load; SQL runs in an isolated in-memory SQLite database; write operations (INSERT/UPDATE/DELETE/DROP…) are blocked at the syntax level; Databricks access is strictly read-only (multi-layer validation + read-only connection); there is no code path that writes back to the original file. Exported CSVs are always brand-new files.

---

## 📊 示例数据 · Sample Data

仓库内置两份可直接打开的演示数据，用于快速体验（均为 500 行销售订单：订单日期 / 城市 / 渠道 / 商品 / 类目 / 客户等级 / 单价 / 数量 / 折扣 / 成本 / 销售额 / 利润）：

| 文件 File | 语言 Lang | 生成脚本 Generator |
|------|------|------|
| [示例销售数据.xlsx](示例销售数据.xlsx) | 中文 | `python generate_sample.py` |
| [sample_sales_data_en.xlsx](sample_sales_data_en.xlsx) | English | `python generate_sample_en.py` |

加载后随便用大白话提问，例如「北京地区利润最高的前 10 个商品」。
Each file holds 500 sales-order rows. Load it and ask in plain language, e.g. *"top 10 products by profit in Beijing"*.

---

## 📦 依赖 · Dependencies

| 包 Package | 用途 Purpose |
|---|---|
| pandas / numpy | 数据处理 Data processing |
| openpyxl | 读 .xlsx Read .xlsx |
| requests | LLM API 调用 LLM API calls |
| customtkinter | 桌面 UI Desktop UI |
| Pillow | 图像 / 图标 Image / icon |
| databricks-sql-connector | Databricks 连接（便携版内置）Databricks (built-in in portable) |
| Ollama / Dify（可选外部服务） | AI 后端 AI backends |

---

## 📖 详细说明 · Full Documentation

- [使用手册.md](使用手册.md) — 图文使用指南 User manual
- [便携版说明.md](便携版说明.md) — 便携版打包与运行 Portable build & run
- [README_EN.md](README_EN.md) — 英文版说明 English README
- [OPEN_SOURCE_STATEMENT.md](OPEN_SOURCE_STATEMENT.md) — 英文开源声明 English statement

---

## 🛠️ 代码结构 · Project Structure

```
CioData/
├── main.py              # 入口 entry point
├── launcher.py          # 源码版启动器（venv+依赖自检+多镜像安装）source launcher
├── config.py            # 配置中心 + 5 套双语提示词模板 config + bilingual prompts
├── settings.py          # settings.json 持久化 persistence
├── i18n.py              # 中英文界面字符串（159 键全量配对）zh/en strings (159 fully paired)
├── data_loader.py       # Excel/CSV/Databricks 加载 loading
├── sql_engine.py        # SQLite 内存引擎 + 只读校验 + 超时保护 engine
├── llm_client.py        # OpenAI 兼容/Dify 客户端 + Ollama 模型扫描 LLM client
├── ui/                  # CustomTkinter 界面 UI
│   ├── app.py           # 主窗口编排（含语言切换重建、窗口图标）main window
│   ├── sidebar.py       # 左侧配置区 left config panel
│   ├── workspace.py     # SQL 编辑器 + 结果表格 editor + results
│   ├── chat_panel.py    # AI 对话 AI chat
│   ├── sql_snippets.py  # SQL 语句 DIY 存储（10 槽位）snippet storage
│   ├── sql_editor.py    # 行号 + 高亮编辑器 editor
│   ├── data_table.py    # 分页排序表格 table
│   └── ...
├── selfcheck.py         # 自检 self-checks
├── generate_sample.py   # 中文示例数据 sample-data (zh)
├── generate_sample_en.py # 英文示例数据 sample-data (en)
├── assets/              # 图标 icon (icon.png / icon.ico)
├── run.bat                # 源码版启动器（Windows）source launcher
├── run.sh                 # 源码版启动器（macOS / Linux）source launcher
└── install_databricks.bat # Databricks 连接器一键安装 Databricks installer
```

> 注：便携版启动器 `启动 CioData.bat` / `portable_launcher.py` 依赖内置 `runtime/`（数 GB），**仅随 GitHub Release 附件 `CioData_portable_win64.zip` 分发，不纳入本仓库**。本仓库只含源码，需用本机 Python 3.12 运行（见上方「方式二：源码运行」）。

---

## 📜 开源声明 · Open Source Statement

本项目以 **MIT License** 发布（见 [LICENSE](LICENSE)），**保留 "CioData" 冠名**。

This project is released under the **MIT License** (see [LICENSE](LICENSE)), **keeping the "CioData" branding**.

### 许可证 License
你可以自由使用、复制、修改、合并、分发、再授权，包括商用。唯一要求：在副本中保留原版权声明与许可证文本，并保留 "CioData" 冠名及本声明链接。
You may use, modify, and distribute freely, including commercially, provided the copyright notice, the **"CioData" branding**, and a link to this statement are retained.

### 冠名与商标 Trademark
允许 fork 与二次分发，但请**保留冠名**：不得以 "CioData" 官方名义发布修改版；修改版请在名称中加以区分（如 "XXX（基于 CioData）"）。
Forks and redistribution are welcome, but modified builds must **not** be published under the official "CioData" name — suffix your variant (e.g., "YourName (based on CioData)").

### 开源范围 Scope
- **本仓库开源的是源码**（Python 源文件 + 文档 + 资源），可查阅、修改、自行运行。
- **便携版（含内置 Python 运行时的 zip）不作为仓库内容**，仅作为 GitHub Release 的二进制附件发布，方便免装 Python 的用户。
- `settings.json`（含 API Key / Databricks Token）属用户本地数据，**不入库**，已在 `.gitignore` 排除。
- The repository contains source only; the portable bundle is published as a Release attachment, not as repo content. Never commit `settings.json` — it stores your keys in plain text.

### 隐私与安全 Privacy & Security
- 程序**不内置任何 API Key**，所有密钥由用户自行填写，保存在本地 `settings.json`（明文，仅本机使用）。请勿把填写过密钥的 `settings.json` 分享或提交。
- AI 请求只发送：你选中的列结构（字段名 + 类型 + 示例值）与你的问题文本；**不会上传数据内容本身**——是否接受取决于你所选 AI 服务自身的隐私政策。
- 对 Databricks 的查询强制只读（多层校验 + 连接层 read_only），不会改动你的数据仓库。
- No telemetry. AI requests only include column schema + your question, never the data itself. Databricks access is strictly read-only.

### 免责声明 Disclaimer
本程序按"现状"提供，不附带任何明示或默示的担保。作者不对因使用本程序产生的任何直接或间接损失负责。使用前请自行评估并在测试环境验证 AI 生成的 SQL。
Provided "as is", without warranty of any kind. Validate AI-generated SQL before running it against production data.

### 参与贡献 Contributing
欢迎 Issue 与 Pull Request。提交前请：
1. 保持中英双语文案同步（`i18n.py` 中 zh/en 键一一对应，当前 159 组）；
2. 新增可见文案必须走 `i18n.t()`，不允许硬编码；
3. 遵循现有代码风格（类型提示、中文注释均可）。

---

## 🙏 第三方依赖致谢 · Credits

CioData 站在巨人的肩膀上，感谢以下开源项目（各依赖以其自身许可证为准）：

| 依赖 Dependency | 用途 Purpose | 许可证 License |
|---|---|---|
| Python | 运行时 Runtime | PSF License |
| pandas / numpy | 数据处理 Data processing | BSD |
| openpyxl | Excel 读写 | MIT |
| CustomTkinter | 现代化 Tk 界面 UI | MIT |
| Pillow | 图像 / 图标 Image / icon | HPND |
| requests | HTTP 客户端 HTTP client | Apache-2.0 |
| databricks-sql-connector | Databricks 连接 | Apache-2.0 |
| Ollama / Dify（可选外部服务） | AI 后端 AI backends | 各自官方许可 |

以上项目均未随本仓库再分发其源码；便携版中包含的副本，其版权归各自作者所有，相应许可证文本已随附。
