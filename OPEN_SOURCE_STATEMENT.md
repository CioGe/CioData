# CioData — Open Source Statement

> CioData · AI-assisted Data Filter
> Ask your data in plain language — no SQL required.

This statement follows the same approach as CioNote and **keeps the CioData branding**.

---

## 1. What is CioData

CioData is a **local-first** desktop tool (Python + CustomTkinter + Tkinter): load Excel / CSV / Databricks data, ask questions in plain language, and an LLM turns them into SQL that runs locally — paginated results and one-click CSV export. The top-right panel also ships a **SQL Snippet Storage** (10 slots to stash frequently-used SQL and adopt them into the editor in one click). Strictly read-only: your source data is never modified.

Key features:

| Feature | Description |
|---|---|
| Local-first | Data never leaves your machine; the app has no telemetry and reports nothing |
| Pluggable AI | OpenAI-compatible API / local Ollama models / Dify — three backends, isolated configs |
| Databricks read-only | Built-in connector + strict read-only validation (blocks writes, stacked statements, comment bypass, CTE smuggling) |
| Zero-install portable | Bundled Python 3.12 runtime, extract-and-run, USB-portable |
| Bilingual | UI fully paired (159 zh/en keys), one-click switch; **separate zh/en AI prompts** (`system_prompt` / `system_prompt_en`) |
| SQL Snippet Storage | 10 slots: name display + edit popup + adopt into the SQL editor, persisted in `settings.json` |

## 2. Open Source Scope

- **This repository publishes source code** (Python sources + docs + assets). Anyone may read, modify, and run it.
- **The portable bundle (the zip with the embedded Python runtime) is NOT part of the repository**; it is published only as a binary attachment on GitHub Releases, so users without Python can download and run it directly.
- `settings.json` (which holds your API Key / Databricks Token) is local user data and is **excluded from the repo** via `.gitignore`.

## 3. License

This project is released under the **MIT License** (see the `LICENSE` file).

- You may freely use, copy, modify, merge, distribute, and re-license it, including commercially.
- The only requirement: retain the original copyright notice and license text in copies, and **keep the "CioData" branding and a link to this statement**.

## 4. Branding & Trademark

- The name "CioData" and the icon (`assets/icon.png`, `assets/icon.ico`) are the project's identity.
- Forks and redistribution are welcome, but please **keep the branding**: do not publish modified builds under the official "CioData" name — suffix your variant (e.g., "YourName (based on CioData)").
- CioData belongs to the same author's "Cio" family alongside CioNote; each is open-sourced independently.

## 5. Third-Party Credits

CioData stands on the shoulders of giants. Thanks to these open-source projects (each under its own license):

| Dependency | Purpose | License |
|---|---|---|
| Python | Runtime | PSF License |
| pandas / numpy | Data processing | BSD |
| openpyxl | Excel read/write | MIT |
| CustomTkinter | Modern Tk UI | MIT |
| Pillow | Image / icon | HPND |
| requests | HTTP client | Apache-2.0 |
| databricks-sql-connector | Databricks connection | Apache-2.0 |
| Ollama / Dify (optional external services) | AI backends | Their respective licenses |

None of these projects' source is redistributed in this repository; copies bundled in the portable build remain the property of their respective authors, and the corresponding license texts are included (`runtime/`).

## 6. Privacy & Security

- The app **ships with no API Key**; all secrets are entered by the user and stored locally in `settings.json` (plain text, local use only). Do not share or commit a `settings.json` that contains your keys.
- Databricks queries are strictly read-only (multi-layer validation + a read-only connection) and will not alter your data warehouse.
- AI requests send **only** the selected column schema (field names + types + sample values) and your question text — **never the data content itself**. Whether that is acceptable depends on the privacy policy of the AI service you choose.

## 7. Disclaimer

This software is provided "as is", without any express or implied warranty. The author is not liable for any direct or indirect damage arising from its use. Evaluate it yourself and validate AI-generated SQL in a test environment before running it against production data.

## 8. Contributing

Issues and Pull Requests are welcome. Before submitting, please:

1. Keep Chinese/English UI strings in sync (`i18n.py` zh/en keys are one-to-one; currently 159 pairs);
2. Route all user-visible text through `i18n.t()` — no hardcoding;
3. Follow the existing code style (type hints and Chinese comments are both fine).
