#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CioData 核心逻辑自检（无需UI，秒级完成）。
运行: python selfcheck.py
全部通过会打印 ALL PASSED；任一失败以非零退出。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

import config
from sql_engine import execute_sql, validate_sql, get_schema_hint, apply_column_visibility
from data_loader import load_excel, load_csv, list_excel_sheets
from llm_client import LLMClient

_PROJECT = os.path.dirname(os.path.abspath(__file__))
_PASS, _FAIL = 0, 0


def check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✅ {name}")
    else:
        _FAIL += 1
        print(f"  ❌ {name}  {detail}")


def main():
    print("=" * 56)
    print("CioData 核心逻辑自检")
    print("=" * 56)

    # ---------- 1. SQL引擎 ----------
    print("\n[1] SQL 引擎（只读保护 + 执行）")
    df = pd.DataFrame({
        "城市": ["北京", "上海", "北京", "广州"],
        "销售额": [100, 200, 300, 400],
        "利润": [10, 20, 30, 40],
    })
    df_backup = df.copy()

    ok, msg = validate_sql("SELECT * FROM df")
    check("合法SELECT通过", ok, msg)
    for kw_sql in ["INSERT INTO df VALUES (1)", "UPDATE df SET x=1", "DELETE FROM df",
                   "DROP TABLE df", "ALTER TABLE df ADD c", "CREATE TABLE t (a)",
                   "TRUNCATE df", "REPLACE INTO df VALUES(1)", "ATTACH DATABASE 'x' AS y",
                   "PRAGMA journal_mode=WAL", "SELECT 1; DROP TABLE df",
                   "SELECT/*x*/1; DELETE FROM df"]:
        ok, _ = validate_sql(kw_sql)
        check(f"拦截写操作/堆叠: {kw_sql[:24]}", not ok)
    ok, _ = validate_sql("SELECT * FROM df WHERE 备注 = 'a;b -- DROP'")
    check("字符串内分号/关键字不误伤", ok)
    ok, _ = validate_sql("WITH t AS (SELECT 1 AS a) SELECT * FROM t")
    check("CTE(WITH)放行", ok)

    res, err = execute_sql(df, "SELECT 城市, SUM(销售额) AS 总 FROM df GROUP BY 城市 ORDER BY 总 DESC")
    check("分组聚合执行", not err and len(res) == 3 and res.iloc[0]["总"] == 400, err)
    res, err = execute_sql(df, "SELECT *, CASE WHEN 销售额>200 THEN '大' ELSE '小' END AS 类型 FROM df")
    check("CASE WHEN计算列", not err and res.iloc[0]["类型"] == "小", err)
    check("执行后原df不变", df.equals(df_backup))
    res, err = execute_sql(df, "SELECT * FROM df WHERE 城市 = '不存在的城市'")
    check("空结果正常返回", not err and len(res) == 0, err)
    res, err = execute_sql(df, "SELECT 不存在的列 FROM df")
    check("错误SQL返回错误信息", bool(err) and err.startswith("❌"), err)

    hint = get_schema_hint(df)
    check("schema提示包含表名和列", "df" in hint and "城市" in hint and "销售额" in hint)

    vis = apply_column_visibility(df, ["城市"])
    check("列可见性返回副本子集", list(vis.columns) == ["城市"] and len(df.columns) == 3)

    # ---------- 2. 数据加载 ----------
    print("\n[2] 数据加载（Excel / CSV）")
    sample = os.path.join(_PROJECT, "示例销售数据.xlsx")
    if os.path.exists(sample):
        sheets, err = load_excel(sample, sheet_name=0)
        check("加载示例Excel", not err and len(next(iter(sheets.values()))) == 500, err)
        names, err = list_excel_sheets(sample)
        check("读取sheet列表", not err and len(names) >= 1, err)
    else:
        print("  ⚠️ 示例文件不存在，跳过（可运行 generate_sample.py 生成）")

    csv_path = os.path.join(os.environ.get("TEMP", "/tmp"), "_CioData_selfcheck.csv")
    with open(csv_path, "w", encoding="gbk") as f:
        f.write("城市,销售额\n北京,100\n上海,200\n")
    df2, err = load_csv(csv_path)
    check("GBK编码CSV加载", not err and len(df2) == 2, err)
    try:
        os.remove(csv_path)
    except OSError:
        pass

    # ---------- 3. LLM输出清理 ----------
    print("\n[3] LLM 输出清理（SQL提取）")
    cases = [
        ("```sql\nSELECT * FROM df;\n```", "SELECT * FROM df"),
        ("SELECT * FROM df;", "SELECT * FROM df"),
        ("<think>我需要分析...</think>\nSELECT 城市 FROM df", "SELECT 城市 FROM df"),
        ("好的，这是您要的SQL：\nSELECT * FROM df WHERE 销售额 > 100\nLIMIT 10", "SELECT * FROM df WHERE 销售额 > 100\nLIMIT 10"),
        ("```\nSELECT 1\n```", "SELECT 1"),
    ]
    for raw, expect in cases:
        got = LLMClient._extract_sql(raw)
        check(f"提取: {raw[:22].replace(chr(10), ' ')}", got == expect, f"得到: {got!r}")

    # ---------- 4. i18n 与配置 ----------
    print("\n[4] i18n 与配置")
    import i18n
    zh_keys = set(i18n._STRINGS["zh"].keys())
    en_keys = set(i18n._STRINGS["en"].keys())
    check("中英键集合一致", zh_keys == en_keys,
          f"仅中文: {zh_keys - en_keys} / 仅英文: {en_keys - zh_keys}")
    i18n.set_language("zh")
    check("中文默认", i18n.t("ws.run") == "▶ RUN")
    i18n.set_language("en")
    check("英文切换", i18n.t("ws.prev") == "◀ Prev")
    _, err = validate_sql("DELETE FROM df")
    check("英文错误消息", err.startswith("❌") and "Write keyword" in err, err)
    i18n.set_language("zh")

    check("模板数量=5", len(config.PROMPT_TEMPLATES) == 5)
    for name, tpl in config.PROMPT_TEMPLATES.items():
        ok = "{schema}" in tpl["system_prompt"] and "{custom_rules}" in tpl["system_prompt"]
        check(f"模板占位符完整: {name}", ok)
        # 模板名/描述必须走 i18n：i18n.t() 缺键时原样返回键名，据此可判定漏翻
        nk = tpl.get("name_key", "")
        check(f"模板名称已国际化: {name}", bool(nk) and i18n.t(nk) != nk)
        dk = tpl.get("desc_key", "")
        check(f"模板描述已国际化: {name}", bool(dk) and i18n.t(dk) != dk)
    check("默认SQL表名为df", "df" in config.DEFAULT_SQL)
    check("后端含ollama", "ollama" in config.LLM_BACKENDS and "local" not in config.LLM_BACKENDS)
    for v, k in config.ROW_LIMIT_OPTIONS:
        check(f"行数上限i18n键存在: {k}", k in zh_keys and k in en_keys)

    # UI 代码里写死的 i18n key 必须都在词表里（新增文案最容易只改中文）
    import re as _re
    ui_missing = []
    _here = os.path.dirname(os.path.abspath(__file__))
    for fn in ("ui/chart_window.py", "ui/data_table.py", "ui/workspace.py"):
        path = os.path.join(_here, fn)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        for key in sorted(set(_re.findall(r'i18n\.t\(\s*["\']([^"\']+)["\']', src))):
            if key not in zh_keys or key not in en_keys:
                ui_missing.append(f"{fn}:{key}")
    check("UI 硬编码 i18n 键都已配置", not ui_missing, "；".join(ui_missing[:6]))

    # 图表类型/聚合/排序是拼 key 的，词表里不能缺项
    dyn_missing = []
    for fam, items in (("chart.type", ("bar", "line", "pie", "scatter")),
                       ("chart.agg", ("sum", "mean", "count", "max", "none")),
                       ("chart.sort", ("desc", "asc", "none"))):
        for it in items:
            k = f"{fam}.{it}"
            if k not in zh_keys or k not in en_keys:
                dyn_missing.append(k)
    check("图表动态 i18n 键齐全", not dyn_missing, "；".join(dyn_missing))

    # ---------- 5. Ollama 模型扫描（mock requests） ----------
    print("\n[5] Ollama 本地模型扫描")
    from llm_client import list_ollama_models
    import requests as _rq

    class _FakeResp:
        def __init__(self, data, status=200):
            self._data, self.status_code = data, status

        def json(self):
            return self._data

    orig_get = _rq.get
    try:
        _rq.get = lambda url, timeout=5: _FakeResp(
            {"models": [{"name": "qwen2.5:latest"}, {"name": "llama3:8b"}]})
        models, err = list_ollama_models("http://localhost:11434/v1")
        check("原生api/tags解析", not err and models == ["qwen2.5:latest", "llama3:8b"], f"{models} {err}")

        def _fallback(url, timeout=5):
            if url.endswith("/api/tags"):
                raise _rq.exceptions.ConnectionError("refused")
            return _FakeResp({"data": [{"id": "qwen2.5"}, {"id": "deepseek-r1"}]})
        _rq.get = _fallback
        models, err = list_ollama_models("http://localhost:11434/v1")
        check("回退/v1/models解析", not err and models == ["qwen2.5", "deepseek-r1"], f"{models} {err}")

        def _down(url, timeout=5):
            raise _rq.exceptions.ConnectionError("refused")
        _rq.get = _down
        models, err = list_ollama_models("http://localhost:11434/v1")
        check("服务不可用返回错误", not models and bool(err), f"{models} {err}")
    finally:
        _rq.get = orig_get

    # ---------- 6. 图表引擎 ----------
    print("\n[6] 图表引擎")
    charting = None
    try:
        import charting as _charting
        charting = _charting
        check("charting 可导入", True)
    except Exception as e:
        check("charting 可导入", False, e)

    if charting is not None:
        cdf = pd.DataFrame({
            "城市": ["北京", "上海", "北京", "广州", "上海", "北京"],
            "销售额": [100.0, 200.0, 150.0, 80.0, 120.0, 90.0],
            "利润": [10.0, 20.0, 15.0, 8.0, 12.0, 9.0],
            "日期": ["2024-01-01", "2024-01-02", "2024-01-03",
                     "2024-02-01", "2024-02-02", "2024-02-03"],
        })
        prof = charting.infer_profile(cdf)
        kinds = {c["name"]: c["kind"] for c in prof["columns"]}
        check("数值列识别", kinds.get("销售额") == "number", kinds)
        check("文本列识别", kinds.get("城市") == "text", kinds)
        check("字符串日期识别", kinds.get("日期") == "date", kinds)

        sp = charting.suggest(prof)
        check("智能出图选中销售额", sp.y == "销售额", sp)
        check("有日期列时默认折线", sp.ctype == "line", sp)

        # 四种图都必须能生成，且只有一个坐标区
        for ct, x, y, agg in (("bar", "城市", "销售额", "sum"),
                              ("line", "日期", "销售额", "sum"),
                              ("pie", "城市", "销售额", "sum"),
                              ("scatter", "销售额", "利润", "none")):
            try:
                fig, notes = charting.build_figure(
                    cdf, charting.ChartSpec(ct, x=x, y=y, agg=agg), theme="light")
                ok = fig is not None and len(fig.axes) == 1
                fig.clear()
            except Exception as e:
                ok, notes = False, str(e)
            check(f"{ct} 图可生成", ok, notes)

        # 空数据必须抛错，而不是画一张空图糊弄用户
        try:
            charting.build_figure(cdf.iloc[0:0],
                                  charting.ChartSpec("bar", x="城市", y="销售额"))
            empty_ok = False
        except ValueError:
            empty_ok = True
        check("空数据抛 ValueError", empty_ok)

        check("检测到中文字体", charting.ensure_fonts())

        big = pd.DataFrame({"x": range(20000), "y": range(20000)})
        sub, sampled = charting.sample_rows(big, 5000)
        check("散点大数据自动采样", sampled and len(sub) <= 5000, len(sub))

        # 配置可序列化（供 UI 记住上次选择）
        spec2 = charting.ChartSpec.from_dict(sp.as_dict())
        check("图表配置可往返序列化",
              spec2.ctype == sp.ctype and spec2.x == sp.x and spec2.y == sp.y, spec2)

    # ---------- 7. 设置分家与旧版迁移 ----------
    print("\n[7] 设置分家与迁移自愈")
    import json
    import tempfile
    from settings import Settings

    tmp = os.path.join(tempfile.gettempdir(), "_da_settings_test.json")
    try:
        # 模拟被 v3.1 bug 污染的 settings.json：ollama 后端但 base_url 是 openai 的
        polluted = {
            "llm_backend": "ollama",
            "llm_base_url": "https://api.openai.com/v1",
            "llm_api_key": "sk-old",
            "llm_model": "gpt-4o-mini",
        }
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(polluted, f, ensure_ascii=False)
        s = Settings(path=tmp)
        check("迁移后被污染的URL恢复", s.get("ollama_base_url") == "http://localhost:11434/v1",
              s.get("ollama_base_url"))
        check("迁移后不把gpt-4o-mini塞给ollama", s.get("ollama_model") != "gpt-4o-mini",
              s.get("ollama_model"))
        check("迁移后旧key搬到openai键", s.get("openai_api_key") == "sk-old")
        check("迁移后共享URL键恢复默认",
              s.get("llm_base_url") in ("", "https://api.openai.com/v1"))

        # 正常新配置：三套独立键互不影响
        s2 = Settings(path=tmp)
        s2.set_many({"llm_backend": "ollama", "ollama_base_url": "http://localhost:11434/v1",
                     "ollama_model": "qwen2.5:latest"})
        s2.save()
        s3 = Settings(path=tmp)
        check("ollama配置独立持久化", s3.get("ollama_model") == "qwen2.5:latest")
        check("openai配置默认值不受污染",
              s3.get("openai_base_url") == "https://api.openai.com/v1")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    print("\n" + "=" * 56)
    if _FAIL == 0:
        print(f"ALL PASSED ✅  ({_PASS} 项通过)")
        return 0
    print(f"存在失败项 ❌  ({_PASS} 通过 / {_FAIL} 失败)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
