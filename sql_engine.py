# -*- coding: utf-8 -*-
"""
SQL引擎模块：Python标准库 sqlite3 内存引擎（零C扩展依赖）。
对外接口与 v2.0 完全一致：execute_sql(df, sql) -> (DataFrame, 错误信息)
所有操作都是只读视图，不修改传入的 df。
"""

import re
import sqlite3
import threading
import pandas as pd
from typing import Tuple

from config import SQL_TIMEOUT_SECONDS
import i18n

# ---------- SQL安全校验（只读保护） ----------
# 只列「一旦出现就一定是写操作/危险操作」的词，避免误伤正常查询。
# 注意：不要放 SHOW/DESCRIBE/CACHE 这类本身只读的命令，
# 也不要放 SET/USE（它们常出现在字符串或列名里，会误判）。
_FORBIDDEN_KEYWORDS = [
    # 标准 DML / DDL
    "INSERT", "UPDATE", "DELETE", "DROP",
    "ALTER", "CREATE", "TRUNCATE", "REPLACE",
    "MERGE", "UPSERT",
    # 权限与库级运维
    "ATTACH", "DETACH", "VACUUM", "PRAGMA",
    "GRANT", "REVOKE", "ANALYZE", "REINDEX",
    # Databricks / Spark SQL 特有写操作
    "OPTIMIZE", "ZORDER", "FSCK", "REPAIR", "MSCK",
    "RESTORE", "CONVERT",
    "COPY", "OVERWRITE", "LOAD", "EXPORT",
]
_ALLOWED_PREFIX = ("SELECT", "WITH", "EXPLAIN")

# Databricks 额外收紧：WITH 子句只能是 SELECT，不能包住写操作
_WRITE_IN_CTE = ("INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "DROP", "ALTER")


def _strip_comments(sql: str) -> str:
    """去掉 -- 行注释和 /* */ 块注释（不破坏字符串字面量中的内容）。"""
    literals = []

    def _protect(m):
        literals.append(m.group(0))
        return f"\x00{len(literals) - 1}\x00"

    sql = re.sub(r"'(?:[^']|'')*'", _protect, sql)
    sql = re.sub(r'"(?:[^"]|"")*"', _protect, sql)
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"\x00(\d+)\x00", lambda m: literals[int(m.group(1))], sql)
    return sql


def _mask_literals(sql: str) -> str:
    """把字符串/标识符字面量替换为空串，避免字面量内容干扰安全校验。"""
    masked = re.sub(r"'(?:[^']|'')*'", "''", sql)
    masked = re.sub(r'"(?:[^"]|"")*"', '""', masked)
    return masked


def validate_readonly_query(sql: str) -> Tuple[bool, str]:
    """
    严格的只读校验，专用于 Databricks 远程查询。

    比 validate_sql() 更严的地方：
      1. 只允许 SELECT / WITH 开头（不允许 EXPLAIN，远程库上没必要）
      2. 分号堆叠一律拒绝（Databricks 协议支持多语句，分号后会被执行）
      3. WITH 子句内部不允许出现写操作关键字（防 WITH x AS (...) DELETE）
      4. 先剥注释再校验，防 /* */ 绕过
      5. 引号内的字符串不参与关键字匹配，防 'DELETE' 这类字面量误伤

    返回 (是否通过, 错误信息)。通过时错误信息为 ""。
    """
    if not sql or not sql.strip():
        return False, i18n.t("err.empty_sql")

    # 去掉结尾多余分号（单个结尾分号是合法的）
    s = sql.strip()
    while s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        return False, i18n.t("err.empty_sql")

    # 剥注释 → 遮蔽字面量，两步都在副本上做，不影响原语句
    check_src = _strip_comments(s)
    masked = _mask_literals(check_src)
    s_upper = masked.upper().strip()

    # 1) 必须是只读开头
    if not s_upper.startswith(("SELECT", "WITH")):
        return False, i18n.t("err.only_select")

    # 2) 任何位置出现写操作关键字都拒绝
    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", s_upper):
            return False, i18n.t("err.forbidden_kw", kw=kw)

    # 3) 禁止堆叠语句：遮蔽后的语句中间不允许再有分号
    if ";" in masked:
        return False, i18n.t("err.multi_stmt")

    # 4) WITH 开头时，CTE 体内不允许写操作（双保险，正常已被第 2 条拦住）
    if s_upper.startswith("WITH"):
        for kw in _WRITE_IN_CTE:
            if re.search(r"\b" + kw + r"\b", s_upper):
                return False, i18n.t("err.forbidden_kw", kw=kw)

    return True, ""


def validate_sql(sql: str) -> Tuple[bool, str]:
    """校验SQL是否为只读查询。"""
    if not sql or not sql.strip():
        return False, i18n.t("err.empty_sql")
    s = sql.strip().rstrip(";").strip()
    if not s:
        return False, i18n.t("err.empty_sql")
    check_src = _strip_comments(s)
    # 关键字与堆叠语句检查都在遮蔽字面量后的副本上进行，防止误伤
    masked = _mask_literals(check_src)
    s_upper = masked.upper()
    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", s_upper):
            return False, i18n.t("err.forbidden_kw", kw=kw)
    if ";" in masked:
        return False, i18n.t("err.multi_stmt")
    if not s_upper.startswith(_ALLOWED_PREFIX):
        return False, i18n.t("err.only_select")
    return True, ""


def execute_sql(df: pd.DataFrame, sql: str) -> Tuple[pd.DataFrame, str]:
    """
    在 df 上执行SQL，返回（结果DataFrame, 错误信息）。
    df 会被注册到内存SQLite中名为 "df" 的临时表，不修改原df。
    带执行超时保护（默认60秒）， watchdog 线程 interrupt 中断慢查询。
    """
    ok, msg = validate_sql(sql)
    if not ok:
        return df, msg

    conn = sqlite3.connect(":memory:")
    watchdog = None

    def _arm_watchdog():
        def _fire():
            try:
                conn.interrupt()  # 中断正在执行的SQL，抛出 OperationalError: interrupted
            except Exception:
                pass
        timer = threading.Timer(SQL_TIMEOUT_SECONDS, _fire)
        timer.daemon = True
        timer.start()
        return timer

    try:
        watchdog = _arm_watchdog()
        df.to_sql("df", conn, index=False, if_exists="replace")
        result = pd.read_sql_query(sql, conn)
        return result, ""
    except sqlite3.OperationalError as e:
        if "interrupt" in str(e).lower():
            return df, i18n.t("err.sql_timeout", sec=SQL_TIMEOUT_SECONDS)
        return df, i18n.t("err.sql_error", e=e)
    except Exception as e:
        return df, i18n.t("err.sql_error", e=e)
    finally:
        if watchdog is not None:
            watchdog.cancel()
        conn.close()


def get_schema_hint(df: pd.DataFrame, sample_rows: int = 3) -> str:
    """
    生成表结构提示给LLM：列名+类型+示例值+总行数。
    SQLite方言提示，帮助LLM生成正确的SQLite语法。
    """
    lines = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample_vals = df[col].dropna().head(sample_rows).tolist()
        sample_str = ", ".join([repr(v) for v in sample_vals]) if sample_vals else "(无数据)"
        lines.append(f"  - `{col}` ({dtype}) 示例值: {sample_str}")
    hint = (
        f"表名: `df` (SQLite数据库，共 {len(df):,} 行)\n"
        "字段列表：\n" + "\n".join(lines) + "\n\n"
        "SQL语法提示：使用SQLite方言，支持标准SELECT/WHERE/GROUP BY/ORDER BY/LIMIT，"
        "支持CASE WHEN/CAST/COALESCE/字符串函数/聚合函数(SUM/AVG/COUNT/MAX/MIN)；"
        "不支持方括号[]列名，请用反引号或双引号包裹含空格的列名；"
        "字符串拼接用 || 而非 CONCAT；"
        "当前日期函数可用 date('now') / datetime('now')。"
    )
    return hint


def apply_column_visibility(df: pd.DataFrame, visible_cols) -> pd.DataFrame:
    """根据勾选列返回视图DataFrame（副本子集），不影响原数据。非法列名自动忽略。"""
    if not visible_cols:
        return df.copy()
    valid = [c for c in visible_cols if c in df.columns]
    if not valid:
        return df.copy()
    return df[valid].copy()
