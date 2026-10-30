<p align="center">
  <img src="assets/icon.png" width="96" alt="CioData logo"/>
</p>

<h1 align="center">CioData · AI 辅助数据筛选器</h1>

<p align="center">
  <b>用自然语言问数据，一条 SQL 都不用写。</b>
</p>

<p align="center">
  中文 · <a href="README.md">English</a> &nbsp;|&nbsp; 纯本地运行 &nbsp;|&nbsp; 零安装便携版 &nbsp;|&nbsp; MIT 开源
</p>

---

CioData 是一个**本地运行**的桌面小工具（Python + CustomTkinter + Tkinter）：把 Excel / CSV / Databricks 的数据加载进来，用大白话向 AI 提问，它生成 SQL、本地执行、分页展示，并支持一键导出 CSV。全程只读，**绝不改动你的原始数据**。

---

## 🚀 快速启动

### 方式一：便携版（推荐，免装 Python）

1. 到 GitHub **Releases** 下载 `CioData_portable_win64.zip`
2. 解压到任意位置（**不要在压缩包预览里双击**）
3. 双击 `启动 CioData.bat`（或 `portable_launcher.py`）
4. 首次自动体检，约几秒后桌面窗口打开 ✅

> 便携版已内置 Python 3.12.10 运行时 + Databricks 连接器，U 盘可携带，没装 Python 的电脑也能跑。

### 方式二：源码运行（开发者）

```bash
git clone <your-fork-or-this-repo>
cd CioData
python launcher.py             # 自动创建 .venv、装依赖（多镜像回退）后启动
# 或直接双击 run.bat（Windows）
python selfcheck.py            # 核心逻辑自检（20+ 项）
```

`launcher.py` 使用**本机 Python**（推荐 3.12；3.9–3.12 均可，`customtkinter` 在 3.12 上最稳），自动创建本地 `.venv`、按 `requirements.txt` 安装依赖（清华/阿里/官方镜像自动回退），然后启动应用。

需要连 Databricks：双击 **`install_databricks.bat`** 一键装连接器（源码版）。

---

## 🧩 功能一览

| 模块 | 说明 |
|------|------|
| 📁 数据源 | 本地 Excel(.xlsx/.xls)/CSV；Databricks SQL 连接（便携版内置，源码版一键装） |
| 📝 SQL 编辑器 | 行号 + 关键字高亮，Ctrl+Enter 运行，SQLite 方言 |
| 📋 结果表格 | 分页 / 点表头排序 / 双击单元格复制 / 一键导 CSV（UTF-8 BOM） |
| 🤖 AI 对话 | 自然语言 → SQL，一键「采用并执行」或「仅采用」 |
| 🧩 **SQL 语句 DIY 存储** | **右侧 10 个槽位**：名称显示 + 编辑弹窗（自定义名称/语句）+ 采用（一键置入编辑器） |
| 🧠 AI 后端 | OpenAI 兼容 API / Ollama 本地模型 / Dify，三种互不污染 |
| 🧠 提示词 | 5 套行业模板 + 自定义业务术语规则 + 高级 system prompt 编辑；**中英文提示词各自独立** |
| 👁️ 显示字段 | 勾选控制展示列，只影响视图不动数据 |
| 🌙 主题 / 🌐 语言 | 浅色/暗色一键切换；中文/English 界面切换（状态不丢） |

### 新增：SQL 语句 DIY 存储（v3.4）

右侧上半区新增 10 个槽位，把常用 SQL 存起来随时取用：

- **名称**：仅展示，在编辑弹窗里改
- **编辑**：弹窗自定义名称 + SQL 语句，点「保存」入库
- **采用**：一键把存储的 SQL 送入 SQL 编辑器，供你随后手动执行（空槽自动禁用）

数据持久化在 `settings.json` 的 `sql_snippets`，关掉软件再开仍在。

---

## 🔒 只读保证

数据加载即深拷贝；SQL 在独立内存 SQLite 库执行；写操作（INSERT/UPDATE/DELETE/DROP…）语法层直接拦截；对 Databricks 的查询强制只读（多层校验 + 连接层 `read_only` 双保险）；代码里没有任何回写原始文件的逻辑。导出的 CSV 永远是新文件。

---

## 📊 示例数据

仓库内置两份可直接打开的演示数据，用于快速体验（均为 500 行销售订单：订单日期 / 城市 / 渠道 / 商品 / 类目 / 客户等级 / 单价 / 数量 / 折扣 / 成本 / 销售额 / 利润）：

| 文件 | 语言 | 生成脚本 |
|------|------|------|
| [示例销售数据.xlsx](示例销售数据.xlsx) | 中文 | `python generate_sample.py` |
| [sample_sales_data_en.xlsx](sample_sales_data_en.xlsx) | English | `python generate_sample_en.py` |

加载后随便用大白话提问，例如「北京地区利润最高的前 10 个商品」。

---

## 📦 依赖

| 包 | 用途 |
|---|---|
| pandas / numpy | 数据处理 |
| openpyxl | 读 .xlsx |
| requests | LLM API 调用 |
| customtkinter | 桌面 UI |
| Pillow | 图像 / 图标 |
| databricks-sql-connector | Databricks 连接（便携版内置） |
| Ollama / Dify（可选外部服务） | AI 后端 |

---

## 📖 详细说明

- [README.md](README.md) — English README 英文说明
- [使用手册.md](使用手册.md) — 图文使用指南
- [便携版说明.md](便携版说明.md) — 便携版打包与运行
- [CioData_开源声明.md](CioData_开源声明.md) — 开源声明（中文）
- [OPEN_SOURCE_STATEMENT.md](OPEN_SOURCE_STATEMENT.md) — open-source statement (English)
- [LICENSE](LICENSE) — MIT 许可证

---

## 🛠️ 代码结构

```
CioData/
├── main.py              # 入口
├── launcher.py          # 源码版启动器（venv + 依赖自检 + 多镜像安装）
├── config.py            # 配置中心 + 5 套双语提示词模板
├── settings.py          # settings.json 持久化
├── i18n.py              # 中英文界面字符串（159 键全量配对）
├── data_loader.py       # Excel/CSV/Databricks 加载
├── sql_engine.py        # SQLite 内存引擎 + 只读校验 + 超时保护
├── llm_client.py        # OpenAI 兼容 / Dify 客户端 + Ollama 模型扫描
├── ui/                  # CustomTkinter 界面
│   ├── app.py           # 主窗口编排（含语言切换重建、窗口图标）
│   ├── sidebar.py       # 左侧配置区
│   ├── workspace.py     # SQL 编辑器 + 结果表格
│   ├── chat_panel.py    # AI 对话
│   ├── sql_snippets.py  # SQL 语句 DIY 存储（10 槽位）
│   ├── sql_editor.py    # 行号 + 高亮编辑器
│   ├── data_table.py    # 分页排序表格
│   └── ...
├── selfcheck.py         # 自检（20+ 项）
├── generate_sample.py   # 中文示例数据生成
├── generate_sample_en.py# 英文示例数据生成
├── assets/              # 图标（icon.png / icon.ico）
├── run.bat              # 源码版启动器（Windows）
├── run.sh               # 源码版启动器（macOS / Linux）
└── install_databricks.bat # Databricks 连接器一键安装
```

> 注：便携版启动器 `启动 CioData.bat` / `portable_launcher.py` 依赖内置 `runtime/`（数 GB），**仅随 GitHub Release 附件 `CioData_portable_win64.zip` 分发，不纳入本仓库**。本仓库只含源码，需用本机 Python 3.12 运行（见上方「方式二：源码运行」）。

---

## 📜 开源声明

本项目以 **MIT License** 发布（见 [LICENSE](LICENSE)），**保留 "CioData" 冠名**。

### 许可证
你可以自由使用、复制、修改、合并、分发、再授权，包括商用。唯一要求：在副本中保留原版权声明与许可证文本，并保留 "CioData" 冠名及本声明链接。

### 冠名与商标
允许 fork 与二次分发，但请**保留冠名**：不得以 "CioData" 官方名义发布修改版；修改版请在名称中加以区分（如 "XXX（基于 CioData）"）。

### 开源范围
- **本仓库开源的是源码**（Python 源文件 + 文档 + 资源），可查阅、修改、自行运行。
- **便携版（含内置 Python 运行时的 zip）不作为仓库内容**，仅作为 GitHub Release 的二进制附件发布，方便免装 Python 的用户。
- `settings.json`（含 API Key / Databricks Token）属用户本地数据，**不入库**，已在 `.gitignore` 排除。

### 隐私与安全
- 程序**不内置任何 API Key**，所有密钥由用户自行填写，保存在本地 `settings.json`（明文，仅本机使用）。请勿把填写过密钥的 `settings.json` 分享或提交。
- AI 请求只发送：你选中的列结构（字段名 + 类型 + 示例值）与你的问题文本；**不会上传数据内容本身**——是否接受取决于你所选 AI 服务自身的隐私政策。
- 对 Databricks 的查询强制只读（多层校验 + 连接层 `read_only`），不会改动你的数据仓库。
- 无任何遥测。

### 免责声明
本程序按"现状"提供，不附带任何明示或默示的担保。作者不对因使用本程序产生的任何直接或间接损失负责。使用前请自行评估并在测试环境验证 AI 生成的 SQL。

### 参与贡献
欢迎 Issue 与 Pull Request。提交前请：
1. 保持中英双语文案同步（`i18n.py` 中 zh/en 键一一对应，当前 159 组）；
2. 新增可见文案必须走 `i18n.t()`，不允许硬编码；
3. 遵循现有代码风格（类型提示、中文注释均可）。

---

## 🙏 第三方依赖致谢

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

以上项目均未随本仓库再分发其源码；便携版中包含的副本，其版权归各自作者所有，相应许可证文本已随附。
