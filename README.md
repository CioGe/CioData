<p align="center">
  <img src="assets/icon.png" width="96" alt="CioData logo"/>
</p>

<h1 align="center">CioData · AI-assisted Data Filter</h1>

<p align="center">
  <b>Ask your data in plain language — no SQL required.</b>
</p>

<p align="center">
  <a href="README.zh-CN.md">中文</a> · English &nbsp;|&nbsp; Local-first &nbsp;|&nbsp; Zero-install portable build &nbsp;|&nbsp; MIT
</p>

---

CioData is a **local-first** desktop tool (Python + CustomTkinter + Tkinter). Load Excel / CSV / Databricks data, ask in plain language, and an LLM turns it into SQL that runs locally — paginated results and one-click CSV export. Strictly read-only: your source data is never modified.

---

## 🚀 Quick Start

### Option A: Portable (recommended, no Python needed)

1. Download `CioData_portable_win64.zip` from GitHub **Releases**
2. Unzip anywhere (**don't double-click from inside the archive preview**)
3. Double-click `启动 CioData.bat` (or `portable_launcher.py`)
4. On first launch it self-checks, then the desktop window opens in a few seconds ✅

> The portable bundle already embeds the Python 3.12.10 runtime + the Databricks connector — run it from a USB stick, no Python install required.

### Option B: From Source (developers)

```bash
git clone <your-fork-or-this-repo>
cd CioData
python launcher.py             # auto-creates .venv, installs deps (mirror fallback), then runs
# or: double-click run.bat (Windows)
python selfcheck.py            # core self-checks (20+ items)
```

`launcher.py` uses your **system Python** (3.9–3.12 recommended; 3.12 best for `customtkinter`), creates a local `.venv`, installs `requirements.txt` with mirror fallback, and starts the app.

To connect Databricks on the source build, double-click **`install_databricks.bat`** (one-click connector installer).

---

## 🧩 Features

| Module | Description |
|------|------|
| 📁 Data Source | Local Excel(.xlsx/.xls)/CSV; Databricks SQL (built-in in portable, installable for source) |
| 📝 SQL Editor | Line numbers + keyword highlighting, Ctrl+Enter to run, SQLite dialect |
| 📋 Results Table | Pagination / click header to sort / double-click a cell to copy / one-click CSV export (UTF-8 BOM) |
| 🤖 AI Chat | Natural language → SQL, one-click "Adopt & Run" or "Adopt only" |
| 🧩 **SQL Snippet Storage** | **10 slots** on the top-right: name display + edit popup + adopt into editor |
| 🧠 AI Backend | OpenAI-compatible API / local Ollama / Dify, three isolated backends |
| 🧠 Prompts | 5 industry templates + custom business-term rules + advanced system-prompt editor; **separate zh/en prompts** |
| 👁️ Visible Fields | Toggle columns to show; view-only, never touches data |
| 🌙 Theme / 🌐 Language | One-click light/dark toggle; Chinese/English UI switch (state preserved) |

### New: SQL Snippet Storage (v3.4)

The top-right panel offers **10 snippet slots** to stash frequently-used SQL:

- **Name**: display-only (edited in the popup)
- **Edit**: popup to set name + SQL, saved on "Save"
- **Adopt**: one click drops the stored SQL into the editor for you to run (empty slots disabled)

Persisted in `settings.json` → `sql_snippets`; survives restarts.

---

## 🔒 Read-Only Guarantee

Data is deep-copied on load; SQL runs in an isolated in-memory SQLite database; write operations (INSERT/UPDATE/DELETE/DROP…) are blocked at the syntax level; Databricks access is strictly read-only (multi-layer validation + read-only connection); there is no code path that writes back to the original file. Exported CSVs are always brand-new files.

---

## 📊 Sample Data

The repo ships two ready-to-open demo datasets (500 sales-order rows each: order date / city / channel / product / category / customer level / unit price / quantity / discount / cost / sales amount / profit):

| File | Language | Generator |
|------|----------|-----------|
| [示例销售数据.xlsx](示例销售数据.xlsx) | Chinese | `python generate_sample.py` |
| [sample_sales_data_en.xlsx](sample_sales_data_en.xlsx) | English | `python generate_sample_en.py` |

Load one and ask in plain language, e.g. *"top 10 products by profit in Beijing"*.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| pandas / numpy | Data processing |
| openpyxl | Read .xlsx |
| requests | LLM API calls |
| customtkinter | Desktop UI |
| Pillow | Image / icon |
| databricks-sql-connector | Databricks (built-in in portable) |
| Ollama / Dify (optional external services) | AI backends |

---

## 📖 Documentation

- [README.zh-CN.md](README.zh-CN.md) — 中文说明 Chinese README
- [使用手册.md](使用手册.md) — illustrated user manual (Chinese)
- [便携版说明.md](便携版说明.md) — portable build & run guide (Chinese)
- [OPEN_SOURCE_STATEMENT.md](OPEN_SOURCE_STATEMENT.md) — open-source statement
- [LICENSE](LICENSE) — MIT license

---

## 🛠️ Project Structure

```
CioData/
├── main.py              # entry point
├── launcher.py          # source launcher (venv + dependency self-check + mirror install)
├── config.py            # config center + 5 bilingual prompt templates
├── settings.py          # settings.json persistence
├── i18n.py              # zh/en UI strings (159 fully-paired keys)
├── data_loader.py       # Excel/CSV/Databricks loading
├── sql_engine.py        # in-memory SQLite engine + read-only checks + timeout
├── llm_client.py        # OpenAI-compatible / Dify client + Ollama model scan
├── ui/                  # CustomTkinter UI
│   ├── app.py           # main window (language-switch rebuild, window icon)
│   ├── sidebar.py       # left config panel
│   ├── workspace.py     # SQL editor + results table
│   ├── chat_panel.py    # AI chat
│   ├── sql_snippets.py  # SQL snippet storage (10 slots)
│   ├── sql_editor.py    # line-numbered highlighted editor
│   ├── data_table.py    # paginated sortable table
│   └── ...
├── selfcheck.py         # core self-checks (20+ items)
├── generate_sample.py   # Chinese sample-data generator
├── generate_sample_en.py# English sample-data generator
├── assets/              # icon (icon.png / icon.ico)
├── run.bat              # source launcher (Windows)
├── run.sh               # source launcher (macOS / Linux)
└── install_databricks.bat # one-click Databricks connector installer
```

> Note: the portable launcher `启动 CioData.bat` / `portable_launcher.py` relies on the bundled `runtime/` (several GB) and is **distributed only as the GitHub Release attachment `CioData_portable_win64.zip`**, not as repo content. This repo contains source only and runs on your local Python 3.12 (see "Option B: From Source").

---

## 📜 Open Source Statement

Released under the **MIT License** (see [LICENSE](LICENSE)), **keeping the "CioData" branding**.

### License
You may use, modify, and distribute freely, including commercially, provided the copyright notice, the **"CioData" branding**, and a link to this statement are retained.

### Trademark
Forks and redistribution are welcome, but modified builds must **not** be published under the official "CioData" name — suffix your variant (e.g., "YourName (based on CioData)").

### Scope
- **This repository ships source** (Python source files + docs + assets) — readable, modifiable, runnable yourself.
- **The portable bundle (zip with the embedded Python runtime) is not repo content**; it is published only as a GitHub Release binary attachment for users who don't want to install Python.
- `settings.json` (holds API keys / Databricks tokens) is user-local data and is **never committed** (excluded in `.gitignore`).

### Privacy & Security
- The app ships **no built-in API keys**; all keys are entered by you and stored locally in `settings.json` (plain text, local use only). Never share or commit a `settings.json` that contains keys.
- AI requests send only the **column schema** (field name + type + sample values) of the columns you select, plus your question text. The **data content itself is never uploaded** — whether that is acceptable depends on the privacy policy of the AI service you choose.
- Databricks access is strictly read-only (multi-layer validation + connection-level `read_only`); your warehouse is never modified.
- No telemetry of any kind.

### Disclaimer
Provided "as is", without warranty of any kind. Validate AI-generated SQL before running it against production data.

### Contributing
Issues and Pull Requests are welcome. Before submitting:
1. Keep zh/en copy in sync (`i18n.py` pairs zh/en keys one-to-one; currently 159 groups);
2. Any user-visible string must go through `i18n.t()` — no hard-coding;
3. Follow the existing code style (type hints and Chinese comments are fine).

---

## 🙏 Credits

CioData stands on the shoulders of giants. Thanks to these open-source projects (each under its own license):

| Dependency | Purpose | License |
|---|---|---|
| Python | Runtime | PSF License |
| pandas / numpy | Data processing | BSD |
| openpyxl | Excel read/write | MIT |
| CustomTkinter | Modern Tk UI | MIT |
| Pillow | Image / icon | HPND |
| requests | HTTP client | Apache-2.0 |
| databricks-sql-connector | Databricks | Apache-2.0 |
| Ollama / Dify (optional external services) | AI backends | their own licenses |

None of these projects re-distribute their source with this repository; copies bundled inside the portable build remain the property of their respective authors, with license texts included.
