# -*- coding: utf-8 -*-
"""
数据加载模块：Excel(.xlsx/.xls) / CSV / Databricks。
所有数据加载后立即 .copy()，与源文件断开引用；源文件只读，绝不回写。
Databricks 为可选依赖，未安装时给出友好提示而不是崩溃。

【只读保证】
Databricks 查询在发出去之前，必须通过 sql_engine.validate_sql() 的完整校验：
  - 只允许 SELECT / WITH / EXPLAIN 开头
  - 拦截 INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/MERGE/COPY 等写操作
  - 拦截分号堆叠语句（SELECT 1; DROP TABLE x 这类）
  - 注释先剥掉再校验，防止 /* */ 绕过
另外连接层带 read_only 标记，双保险。
"""

import pandas as pd
from typing import Tuple, Optional

import i18n

_CSV_ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin1"]


def load_excel(file_obj, sheet_name=None, nrows: Optional[int] = None) -> Tuple[dict, str]:
    """
    加载Excel文件（file_obj 可以是路径或文件对象）。
    sheet_name 指定单个 sheet；None 时读取全部 sheet 返回 dict。
    返回 ({sheet_name: DataFrame}, 错误信息)
    """
    try:
        sheets = pd.read_excel(
            file_obj,
            sheet_name=sheet_name,
            nrows=nrows,
            engine="openpyxl",
        )
        if not isinstance(sheets, dict):
            name = sheet_name or "Sheet1"
            sheets = {name: sheets}
        sheets = {k: v.copy() for k, v in sheets.items()}
        return sheets, ""
    except ImportError:
        return {}, i18n.t("err.no_openpyxl")
    except Exception as e:
        return {}, i18n.t("err.excel_load", e=e)


def load_csv(file_obj, nrows: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], str]:
    """加载CSV，自动尝试 utf-8/gbk 等编码。file_obj 可以是路径或文件对象。"""
    last_err = ""
    for enc in _CSV_ENCODINGS:
        try:
            df = pd.read_csv(file_obj, encoding=enc, nrows=nrows)
            return df.copy(), ""
        except UnicodeDecodeError:
            if hasattr(file_obj, "seek"):
                try:
                    file_obj.seek(0)
                except Exception:
                    pass
            continue
        except Exception as e:
            last_err = i18n.t("err.csv_load", enc=enc, e=e)
            break
    if last_err:
        return None, last_err
    return None, i18n.t("err.csv_encoding")


# ---------- Databricks连接（可选依赖） ----------

def is_databricks_available() -> bool:
    try:
        from databricks import sql  # noqa: F401
        return True
    except ImportError:
        return False


def load_from_databricks(
    host: str,
    http_path: str,
    token: str,
    catalog: str,
    schema: str,
    query: str,
) -> Tuple[Optional[pd.DataFrame], str]:
    """通过 Databricks SQL Connector 执行查询，结果拉到本地 DataFrame（只读）。"""
    if not is_databricks_available():
        return None, i18n.t("err.db_missing")

    # 严格的只读校验：拦截写操作、堆叠语句、注释绕过、CTE 绕过
    from sql_engine import validate_readonly_query
    ok, msg = validate_readonly_query(query)
    if not ok:
        return None, i18n.t("err.db_readonly", detail=msg)

    try:
        # databricks-sql-connector 4.x 在没装 pyarrow 时会打一条 WARNING。
        # 本程序用标准 fetchall() 取数，不需要 arrow/cloud fetch，
        # 这条提示只会干扰用户，压到 ERROR 级。
        import logging as _logging
        _logging.getLogger("databricks.sql.client").setLevel(_logging.ERROR)

        from databricks import sql
        with sql.connect(
            server_hostname=host,
            http_path=http_path,
            access_token=token,
            catalog=catalog,
            schema=schema,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return df.copy(), ""
    except Exception as e:
        return None, i18n.t("err.db_connect", e=e)


# ---------- Excel sheet 列表 ----------

def list_excel_sheets(file_obj) -> Tuple[list, str]:
    """列出Excel所有sheet名称。"""
    try:
        xls = pd.ExcelFile(file_obj, engine="openpyxl")
        return xls.sheet_names, ""
    except Exception as e:
        return [], i18n.t("err.sheets", e=e)
