# CioData 开源声明 / Open Source Statement

> CioData · AI 辅助数据筛选器（AI-assisted Data Filter）
> 用自然语言问数据，一条 SQL 都不用写。 / Ask your data in plain language — no SQL required.

本声明参照 CioNote 的开源口径撰写，**保留 CioData 冠名**。
This statement follows the same approach as CioNote and **keeps the CioData branding**.

---

## 一、CioData 是什么

CioData 是一个本地运行的桌面小工具（Python + CustomTkinter + Tkinter）：
把 Excel / CSV / Databricks 的数据加载进来，用自然语言向 AI 提问，它生成 SQL、
本地执行、分页展示，并支持一键导出 CSV。右侧还内置 **SQL 语句 DIY 存储**（10 个槽位，
存常用 SQL、一键采用到编辑器），全程只读，绝不改动原始数据。

核心特性：

| 特性 | 说明 |
|---|---|
| 纯本地运行 | 数据不出本机，程序本身无任何遥测、不上报 |
| AI 接入任选 | OpenAI 兼容 API / Ollama 本地模型 / Dify，三种后端配置互不污染 |
| Databricks 只读 | 内置连接器 + 严格只读校验（拦截写操作、堆叠语句、注释绕过、CTE 夹带） |
| 零安装便携版 | 自带 Python 3.12 运行时，解压即用，U 盘可携带 |
| 中英双语 | 界面 159 键全量配对、一键切换；AI 提示词中英文各自独立（system_prompt / system_prompt_en） |
| SQL 片段存储 | 右侧 10 槽位，名称显示 + 编辑弹窗 + 采用到 SQL 编辑器，持久化于 settings.json |

## 二、开源范围

- **本仓库开源的是源码**（Python 源文件 + 文档 + 资源），任何人可以查阅、修改、自行运行。
- **便携版（含内置 Python 运行时的 zip）不作为仓库内容**，仅作为 GitHub Release 的二进制附件发布，
  便于免装 Python 的用户直接下载使用。
- `settings.json`（含 API Key / Databricks Token）属于用户本地数据，**不入库**，已在 `.gitignore` 排除。

## 三、许可证

本项目以 **MIT License** 发布（见 `LICENSE` 文件）。

- 你可以自由使用、复制、修改、合并、分发、再授权，包括商用。
- 唯一要求：在副本中保留原版权声明与许可证文本，**保留 "CioData" 冠名及本声明链接**。

## 四、冠名与商标

- "CioData" 名称与图标（`assets/icon.png`、`assets/icon.ico`）是本项目的标识。
- 允许 fork 与二次分发，但请**保留冠名**：不得以 "CioData" 官方名义发布修改版；
  修改版请在名称中加以区分（如 "XXX（基于 CioData）"）。
- 与 CioNote 同属同一作者的 Cio 系列工具，各自独立开源、互不捆绑。

## 五、第三方依赖致谢

CioData 站在巨人的肩膀上，感谢以下开源项目（各依赖以其自身许可证为准）：

| 依赖 | 用途 | 许可证 |
|---|---|---|
| Python | 运行时 | PSF License |
| pandas / numpy | 数据处理 | BSD |
| openpyxl | Excel 读写 | MIT |
| CustomTkinter | 现代化 Tk 界面 | MIT |
| Pillow | 图像 / 图标 | HPND |
| requests | HTTP 客户端 | Apache-2.0 |
| databricks-sql-connector | Databricks 连接 | Apache-2.0 |
| Ollama / Dify（可选外部服务） | AI 后端 | 各自官方许可 |

以上项目均未随本仓库再分发其源码；便携版中包含的副本，其版权归各自作者所有，
相应的许可证文本已随附（`runtime/` 内）。

## 六、隐私与安全

- 程序**不内置任何 API Key**，所有密钥由用户自行填写，保存在本地 `settings.json`（明文，仅本机使用）。
  请勿把填写过密钥的 `settings.json` 分享给他人或提交到仓库。
- 对 Databricks 的查询强制只读（多层校验 + 连接层 read_only 双保险），不会改动你的数据仓库。
- AI 请求只发送：你选中的列结构（字段名 + 类型 + 示例值）与你的问题文本；
  **不会上传数据内容本身**——是否接受取决于你所选 AI 服务自身的隐私政策。

## 七、免责声明

本程序按"现状"提供，不附带任何明示或默示的担保。作者不对因使用本程序产生的任何
直接或间接损失负责。使用前请自行评估并在测试环境验证 AI 生成的 SQL。

## 八、参与贡献

欢迎 Issue 与 Pull Request。提交前请：

1. 保持中英双语文案同步（`i18n.py` 中 zh/en 键一一对应）；
2. 新增可见文案必须走 `i18n.t()`，不允许硬编码；
3. 遵循现有代码风格（类型提示、中文注释均可）。

---

# English Summary

**CioData** is a local-first desktop tool that turns natural-language questions into
SQL over Excel / CSV / Databricks data, built with Python + CustomTkinter.

- **License**: MIT (see `LICENSE`). You may use, modify, and distribute freely, including commercially,
  provided the copyright notice, the **"CioData" branding**, and a link to this statement are retained.
- **Trademark**: Forks and redistribution are welcome, but modified builds must not be published
  under the official "CioData" name — suffix your variant (e.g., "YourName (based on CioData)").
- **Scope**: The repository contains source only; the portable bundle (embedded Python runtime) is
  published as a Release attachment, not as repo content. Never commit `settings.json` — it stores
  your API keys in plain text.
- **Privacy**: No telemetry. AI requests only include column schema + your question, never the data itself.
  Databricks access is strictly read-only (multi-layer validation + read-only connection).
- **Warranty**: Provided "as is", without warranty of any kind. Validate AI-generated SQL before
  running it against production data.
