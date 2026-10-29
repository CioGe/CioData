<p align="center">
  <img src="assets/icon.png" width="96" alt="CioData logo"/>
</p>

<h1 align="center">CioData · AI-assisted Data Filter</h1>

<p align="center">
  <b>Ask your data in plain language — no SQL required.</b>
</p>

<p align="center">
  One-click Chinese / English UI · Local-first · Zero-install portable build · MIT
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
pip install -r requirements.txt
python main.py                 # run directly
python selfcheck.py            # core self-checks (20+ items)
```

To connect Databricks on the source build, install the connector separately (see the Chinese docs / portable notes).

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

## 📊 Sample Data

Try it instantly with the bundled sample datasets:

- `示例销售数据.xlsx` — Chinese sample (500 sales orders)
- `sample_sales_data_en.xlsx` — English sample (500 sales orders)

Both share the same 13-column schema (Order ID, Date, City, Channel, Product, Category, Customer Level, Unit Price, Quantity, Discount, Cost, Sales Amount, Profit) so you can test NL2SQL prompts out of the box.

---

## 📖 Documentation

- [README.md](README.md) — 中文 / bilingual main readme
- [OPEN_SOURCE_STATEMENT.md](OPEN_SOURCE_STATEMENT.md) — full open-source statement (this file's Chinese counterpart: `CioData_开源声明.md`)
- [使用手册.md](使用手册.md) — illustrated user manual (Chinese)
- [便携版说明.md](便携版说明.md) — portable build & run guide (Chinese)

---

## 🛠️ Project Structure

```
CioData/
├── main.py              # entry point
├── launcher.py          # launcher (venv + dependency self-check)
├── portable_launcher.py # portable launcher (file-channel self-check)
├── config.py            # config center + bilingual prompt templates
├── settings.py          # settings.json persistence
├── i18n.py              # zh/en UI strings (159 fully-paired keys)
├── data_loader.py       # Excel/CSV/Databricks loading
├── sql_engine.py        # in-memory SQLite engine + read-only checks + timeout
├── llm_client.py        # OpenAI-compatible / Dify client + Ollama scan
├── ui/                  # CustomTkinter UI
│   ├── app.py           # main window (language-switch rebuild, window icon)
│   ├── sidebar.py       # left config panel
│   ├── workspace.py     # SQL editor + results table
│   ├── chat_panel.py    # AI chat
│   ├── sql_snippets.py  # SQL snippet storage (10 slots)
│   ├── sql_editor.py    # line-numbered highlighted editor
│   ├── data_table.py    # paginated sortable table
│   └── ...
├── selfcheck.py         # self-checks
├── generate_sample.py   # Chinese sample generator
└── generate_sample_en.py# English sample generator
```

---

## 📜 Open Source Statement

Released under the **MIT License** (see [LICENSE](LICENSE)), **keeping the "CioData" branding**.

- **License**: free to use, modify, and distribute (including commercially) as long as the copyright notice, the **"CioData" branding**, and a link to this statement are retained.
- **Trademark**: forks welcome, but don't publish modified builds under the official "CioData" name — suffix your variant.
- **Scope**: repository = source only; the portable zip is a Release attachment, not repo content. Never commit `settings.json`.
- **Privacy**: no telemetry; AI requests send only column schema + your question, never the data itself. Databricks access is strictly read-only.
- **Warranty**: provided "as is". Validate AI-generated SQL before running it against production data.

Full text: [OPEN_SOURCE_STATEMENT.md](OPEN_SOURCE_STATEMENT.md).

---

## 🙏 Credits

Thanks to Python, pandas, numpy, openpyxl, CustomTkinter, Pillow, requests, databricks-sql-connector, Ollama, and Dify — see the statement for the full license list.
