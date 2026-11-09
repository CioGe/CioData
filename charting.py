# -*- coding: utf-8 -*-
"""
图表引擎：列类型推断 → 智能选图 → 聚合 → 生成 Figure。

设计要点：
1. 只用 matplotlib 的 OO API（Figure），**不 import pyplot**。
   pyplot 带全局状态和隐式后端选择，弹窗里反复重绘容易叠图，
   也会和 customtkinter 抢 Tk 后端。纯 Figure 与后端完全解耦：
   既能挂到 FigureCanvasTkAgg 上显示，也能被 selfcheck 直接调用。
2. 不做 UI 操作，所有错误以异常抛出，由调用方翻译成界面提示。
3. 列类型判断沿用 data_table._sort_key 的策略：只有「整列都能转且不新增空值」
   才认可转换，避免 errors="coerce" 把脏数据静默吞成空值。
"""

import warnings

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib import font_manager
import matplotlib

import i18n

# ---------- 常量 ----------
CHART_TYPES = ("bar", "line", "pie", "scatter")
AGG_OPS = ("sum", "mean", "count", "max", "none")

MAX_PIE_SLICES = 12      # 饼图最多扇区数
MAX_BARS = 30            # 柱状图最多柱子数
MAX_LINE_POINTS = 400    # 折线最多折点数，超出抽稀
SCATTER_SAMPLE_MAX = 5000  # 散点最多点数
CATEGORY_LIMIT = 20      # 认为「低基数分类」的上限

EXPORT_DPI = 200

# 与 theme.py 主色呼应的克制色板（不用 matplotlib 默认的饱和色）
PALETTE = (
    "#5254E8", "#7C9EF5", "#F0A05A", "#5FBF9F",
    "#E46E6E", "#9B7BD4", "#C4B45A", "#6FA8DC",
    "#D98BA8", "#8FBF6F",
)

# 图表主题（不走 rcParams 全局，逐 Figure 设置，避免影响其他模块）
THEMES = {
    "light": {
        "fig": "#FFFFFF", "ax": "#FFFFFF", "text": "#23232B",
        "muted": "#6E6E78", "grid": "#E9E9EF", "spine": "#D4D4DB",
    },
    "dark": {
        "fig": "#1E1E24", "ax": "#1E1E24", "text": "#EFEFF3",
        "muted": "#A6A6B0", "grid": "#2E2E38", "spine": "#3A3A46",
    },
}

# 中文字体候选（Windows 优先雅黑/黑体，Linux/macOS 兜底）
FONT_CANDIDATES = (
    "Microsoft YaHei", "Microsoft YaHei UI", "SimHei", "DengXian",
    "PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC",
    "WenQuanYi Micro Hei", "DejaVu Sans",
)

_font_ready = None   # None=未探测, True=有中文字体, False=无


# ==================== 字体 ====================
def ensure_fonts():
    """配置 matplotlib 字体，返回是否存在中文字体。

    首次调用要扫描系统字体（约 1~3 秒），结果缓存；重复调用无开销。
    """
    global _font_ready
    if _font_ready is not None:
        return _font_ready
    try:
        installed = {f.name for f in font_manager.fontManager.ttflist}
    except Exception:
        installed = set()
    chosen = [n for n in FONT_CANDIDATES if n in installed]
    has_cjk = any(n != "DejaVu Sans" for n in chosen)
    matplotlib.rcParams["font.sans-serif"] = (chosen or ["DejaVu Sans"]) + ["DejaVu Sans"]
    matplotlib.rcParams["font.family"] = "sans-serif"
    # 雅黑等中文字体缺 U+2212，负号会变方框
    matplotlib.rcParams["axes.unicode_minus"] = False
    _font_ready = has_cjk
    return _font_ready


# ==================== 列类型推断 ====================
def _col(df, name):
    """按列名取 Series；列名重复时只取第一个，避免返回 DataFrame。"""
    s = df[name]
    if isinstance(s, pd.DataFrame):
        return s.iloc[:, 0]
    return s


def _strict_numeric(s):
    """整列能转数值且不新增空值时才返回转换结果，否则 None。"""
    orig_na = int(s.isna().sum())
    try:
        num = pd.to_numeric(s, errors="coerce")
    except Exception:
        return None
    if int(num.isna().sum()) != orig_na:
        return None
    return num


def _strict_datetime(s):
    """整列能解析成日期且不新增空值时才返回，否则 None。"""
    orig_na = int(s.isna().sum())
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dt = pd.to_datetime(s, errors="coerce")
    except Exception:
        return None
    if int(dt.isna().sum()) != orig_na:
        return None
    # 全 NaT 的列没有意义
    if int(dt.notna().sum()) == 0:
        return None
    return dt


def _nunique(s):
    try:
        return int(s.nunique(dropna=True))
    except Exception:
        return 0


def infer_profile(df):
    """扫描 DataFrame，返回每列的类型画像。

    返回 {"n_rows": int, "columns": [ {name, kind, nunique, na} ... ]}
    kind 取值：number / date / text
    """
    cols = []
    for name in df.columns:
        s = _col(df, name)
        kind = "text"
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            kind = "number"
        elif pd.api.types.is_datetime64_any_dtype(s):
            kind = "date"
        else:
            if _strict_numeric(s) is not None:
                kind = "number"
            elif _strict_datetime(s) is not None:
                kind = "date"
        cols.append({
            "name": str(name),
            "kind": kind,
            "nunique": _nunique(s),
            "na": int(s.isna().sum()),
        })
    return {"n_rows": int(len(df)), "columns": cols}


class ChartSpec:
    """一次出图的完整配置。字段都可被 UI 改写。"""

    __slots__ = ("ctype", "x", "y", "agg", "sort", "top_n", "show_values")

    def __init__(self, ctype="bar", x=None, y=None, agg="sum",
                 sort="desc", top_n=10, show_values=False):
        self.ctype = ctype if ctype in CHART_TYPES else "bar"
        self.x = x
        self.y = y
        self.agg = agg if agg in AGG_OPS else "sum"
        self.sort = sort if sort in ("desc", "asc", "none") else "desc"
        self.top_n = int(top_n) if top_n else 0
        self.show_values = bool(show_values)

    def copy(self):
        return ChartSpec(self.ctype, self.x, self.y, self.agg,
                         self.sort, self.top_n, self.show_values)

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            return cls()
        return cls(d.get("ctype", "bar"), d.get("x"), d.get("y"),
                   d.get("agg", "sum"), d.get("sort", "desc"),
                   d.get("top_n", 10), d.get("show_values", False))

    def __repr__(self):
        return (f"ChartSpec({self.ctype}, x={self.x!r}, y={self.y!r}, "
                f"agg={self.agg}, sort={self.sort}, top_n={self.top_n})")


# 更像「结果指标」的列名关键词及权重（命中多个取最高分，不叠加）
_METRIC_HINTS = {
    "销售额": 4, "营业额": 4, "gmv": 4, "sales": 4,
    "金额": 3, "额": 3, "收入": 3, "营收": 3, "利润": 3, "毛利": 3,
    "amount": 3, "revenue": 3, "profit": 3, "margin": 3,
    "销量": 2, "人数": 2, "次数": 2, "时长": 2, "总量": 2,
    "总": 1, "成本": 1, "cost": 1, "数量": 1, "count": 1,
    "qty": 1, "quantity": 1, "score": 1, "value": 1,
}
# 更像「派生比率」的列名关键词：默认不选作主指标
_RATIO_HINTS = (
    "单价", "折扣", "比率", "率", "均价", "百分比", "price", "discount",
    "rate", "ratio", "percent", "pct",
)


def metric_score(col_profile):
    """给数值列打分，分数越高越适合当默认 Y 轴。"""
    name = col_profile["name"].lower()
    hits = [w for h, w in _METRIC_HINTS.items() if h in name]
    score = max(hits) if hits else 0
    if any(h in name for h in _RATIO_HINTS):
        score -= 2
    # 连续值比离散小整数更像指标
    if col_profile["nunique"] > 20:
        score += 1
    return score


def suggest(profile):
    """按数据画像给出默认图表配置（智能出图）。

    返回 ChartSpec；x/y 可能为 None（调用方据此判断不可绘图）。
    """
    num_cols = [c for c in profile["columns"] if c["kind"] == "number"]
    # 按「像不像度量指标」排序，同分保持原列序（sorted 稳定）
    num_cols = sorted(num_cols, key=lambda c: -metric_score(c))
    nums = [c["name"] for c in num_cols]
    dates = [c["name"] for c in profile["columns"] if c["kind"] == "date"]
    cats = [c["name"] for c in profile["columns"]
            if c["kind"] == "text"] + dates

    # 1) 日期 + 数值 → 折线
    if dates and nums:
        cat = min(cats, key=lambda n: next(
            c["nunique"] for c in profile["columns"] if c["name"] == n)) if cats else None
        x = dates[0] if dates[0] in cats else cat
        return ChartSpec("line", x=x, y=nums[0], agg="sum", sort="asc", top_n=0)

    if nums:
        # 2) 低基数分类 + 数值 → 柱状（饼图需要额外条件）
        low_cats = [c for c in profile["columns"]
                    if c["kind"] == "text" and 0 < c["nunique"] <= CATEGORY_LIMIT]
        if low_cats:
            cat = min(low_cats, key=lambda c: c["nunique"])
            # 3) 只有这两列时，占比最直观 → 饼图
            if len(profile["columns"]) == 2 and cat["nunique"] <= MAX_PIE_SLICES:
                return ChartSpec("pie", x=cat["name"], y=nums[0],
                                 agg="sum", sort="desc", top_n=0)
            return ChartSpec("bar", x=cat["name"], y=nums[0],
                             agg="sum", sort="desc",
                             top_n=min(10, cat["nunique"]))

        # 4) 两个以上数值 → 散点（用最像指标的列作 Y，另一个作 X）
        if len(nums) >= 2:
            return ChartSpec("scatter", x=nums[1], y=nums[0],
                             agg="none", sort="none", top_n=0)

        # 5) 只有数值 → 按行号画柱状
        return ChartSpec("bar", x=None, y=nums[0],
                         agg="none", sort="none", top_n=0)

    # 6) 全是文本 → 退化为「计数分布」，用第一列做分类
    if profile["columns"]:
        cat = min(profile["columns"], key=lambda c: c["nunique"])
        return ChartSpec("bar", x=cat["name"], y=None,
                         agg="count", sort="desc", top_n=10)
    return ChartSpec("bar", x=None, y=None, agg="count", sort="desc", top_n=10)


# ==================== 数据整理 ====================
def _agg_label(agg):
    return i18n.t(f"chart.agg.{agg}")


def _num_fmt(lang):
    """坐标轴数值格式：中文用「万/亿」，英文用 K/M/B，避免科学计数法。"""
    def _trim(v, unit):
        s = f"{v:.1f}".rstrip("0").rstrip(".")
        return f"{s}{unit}"

    def f(v, _pos=None):
        a = abs(v)
        if lang == "zh":
            if a >= 1e8:
                return _trim(v / 1e8, "亿")
            if a >= 1e4:
                return _trim(v / 1e4, "万")
        else:
            if a >= 1e9:
                return _trim(v / 1e9, "B")
            if a >= 1e6:
                return _trim(v / 1e6, "M")
            if a >= 1e3:
                return _trim(v / 1e3, "K")
        if float(v) == int(v):
            return f"{int(v):,}"
        return f"{v:.2f}"
    return FuncFormatter(f)


def _thin_ticks(ax, labels, max_ticks=12):
    """按容器宽度抽稀 X 轴刻度位置（隐藏 label 但留着刻度线会形成黑齿）。"""
    n = len(labels)
    step = max(1, int(np.ceil(n / max_ticks)))
    ticks = list(range(0, n, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([labels[i] for i in ticks])
    return len(ticks)


def sample_rows(df, max_n=SCATTER_SAMPLE_MAX):
    """等距抽样，保持数据分布形状；返回 (df, 是否抽样)。"""
    n = len(df)
    if n <= max_n or max_n <= 0:
        return df, False
    step = int(np.ceil(n / max_n))
    return df.iloc[::step].copy(), True


def _agg_frame(df, x, y, agg, sort, top_n, notes):
    """按 X 分组聚合 Y，返回 (labels, values, n_rows_before)。"""
    if x is None and y is not None and agg == "none":
        # 没有 X：按行号，不聚合
        vals = pd.to_numeric(_col(df, y), errors="coerce")
        keep = vals.notna()
        n_drop = int((~keep).sum())
        if n_drop:
            notes.append(i18n.t("chart.note.drop_na", n=n_drop))
        vals = vals[keep]
        labels = [str(i + 1) for i in range(len(vals))]
        return labels, vals.tolist(), len(vals)

    if x is None:
        raise ValueError(i18n.t("chart.err.no_x"))

    xs = _col(df, x)
    if agg == "count":
        sub = df.loc[xs.notna()]
        if y is None or y not in df.columns:
            g = sub.groupby(x, dropna=True, observed=True).size()
        else:
            g = sub.groupby(x, dropna=True, observed=True)[y].count()
        labels, values = list(g.index.astype(str)), g.tolist()
    elif agg == "none":
        ys = pd.to_numeric(_col(df, y), errors="coerce")
        keep = xs.notna() & ys.notna()
        n_drop = int((~keep).sum())
        if n_drop:
            notes.append(i18n.t("chart.note.drop_na", n=n_drop))
        labels = xs[keep].astype(str).tolist()
        values = ys[keep].tolist()
    else:
        ys = pd.to_numeric(_col(df, y), errors="coerce")
        keep = xs.notna() & ys.notna()
        n_drop = int((~keep).sum())
        if n_drop:
            notes.append(i18n.t("chart.note.drop_na", n=n_drop))
        tmp = pd.DataFrame({"__x": xs[keep].astype(str), "__y": ys[keep]})
        g = tmp.groupby("__x", sort=False, observed=True)["__y"].agg(agg)
        labels, values = list(g.index), g.tolist()

    n_total = len(labels)
    # 排序
    if sort in ("desc", "asc"):
        pairs = sorted(zip(labels, values), key=lambda p: p[1],
                       reverse=(sort == "desc"))
        labels = [p[0] for p in pairs]
        values = [p[1] for p in pairs]
    # Top N
    if top_n and top_n > 0 and n_total > top_n:
        notes.append(i18n.t("chart.note.top_n", shown=top_n, total=n_total))
        labels, values = labels[:top_n], values[:top_n]
    return labels, values, n_total


# ==================== 绘图 ====================
def _style_axes(ax, th, lang):
    ax.set_facecolor(th["ax"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(th["spine"])
    ax.tick_params(colors=th["muted"], labelsize=9, length=3)
    ax.grid(True, color=th["grid"], linewidth=0.8, axis="y", zorder=0)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(_num_fmt(lang))
    ax.xaxis.label.set_color(th["muted"])
    ax.yaxis.label.set_color(th["muted"])


def _rotate_xticks(ax, n):
    if n > 6:
        for lb in ax.get_xticklabels():
            lb.set_rotation(30)
            lb.set_horizontalalignment("right")


def build_figure(df, spec, theme="light", figsize=(8.4, 4.9)):
    """按配置生成 Figure。

    返回 (fig, notes)。notes 是已本地化的提示文本列表（采样/截断/空值等）。
    数据不可绘制时抛 ValueError，消息已本地化。
    """
    lang = i18n.current()
    ensure_fonts()
    th = THEMES.get(theme, THEMES["light"])

    if df is None or len(df) == 0:
        raise ValueError(i18n.t("chart.err.empty"))

    fig = Figure(figsize=figsize, dpi=100)
    fig.patch.set_facecolor(th["fig"])
    ax = fig.add_subplot(111)
    notes = []

    if spec.ctype == "scatter":
        _draw_scatter(ax, df, spec, th, lang, fig, notes)
    elif spec.ctype == "pie":
        _draw_pie(fig, ax, df, spec, th, lang, notes)
    elif spec.ctype == "line":
        _draw_line(ax, df, spec, th, lang, notes)
    else:
        _draw_bar(ax, df, spec, th, lang, notes)

    fig.patch.set_facecolor(th["fig"])
    try:
        fig.tight_layout(pad=1.3)
    except Exception:
        pass
    return fig, notes


def _draw_bar(ax, df, spec, th, lang, notes):
    # 只有「计数」允许不选 Y（按 X 的出现次数画）
    if spec.y is None and spec.agg != "count":
        raise ValueError(i18n.t("chart.err.no_y"))
    labels, values, n_total = _agg_frame(
        df, spec.x, spec.y, spec.agg, spec.sort, spec.top_n, notes)
    if not labels:
        raise ValueError(i18n.t("chart.err.no_valid"))

    if len(labels) > MAX_BARS:
        notes.append(i18n.t("chart.note.too_many_bars",
                            shown=MAX_BARS, total=len(labels)))
        labels, values = labels[:MAX_BARS], values[:MAX_BARS]

    idx = np.arange(len(labels))
    # 同一维度用统一主色：颜色不承载信息，避免 8 种颜色互相干扰
    bars = ax.bar(idx, values, color=PALETTE[0], width=0.68, zorder=3,
                  edgecolor="none")
    shown_ticks = _thin_ticks(ax, labels)
    _style_axes(ax, th, lang)
    _rotate_xticks(ax, shown_ticks)

    ax.set_xlabel(spec.x or i18n.t("chart.row_index"), color=th["muted"])
    if spec.y is None:
        ylabel = _agg_label("count")
    elif spec.agg in ("none", "count"):
        ylabel = spec.y
    elif lang == "zh":
        ylabel = f"{spec.y}（{_agg_label(spec.agg)}）"
    else:
        ylabel = f"{spec.y} ({_agg_label(spec.agg)})"
    ax.set_ylabel(ylabel, color=th["muted"])

    if spec.show_values and len(labels) <= 15:
        fmt = _num_fmt(lang)
        for b, v in zip(bars, values):
            ax.annotate(fmt(v), (b.get_x() + b.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=8, color=th["muted"])


def _draw_line(ax, df, spec, th, lang, notes):
    if spec.y is None:
        raise ValueError(i18n.t("chart.err.no_y"))
    if spec.x is None:
        raise ValueError(i18n.t("chart.err.no_x"))

    xs = _col(df, spec.x)
    dt = _strict_datetime(xs) if not pd.api.types.is_datetime64_any_dtype(xs) else xs
    is_date = dt is not None

    labels, values, n_total = _agg_frame(
        df, spec.x, spec.y, spec.agg if spec.agg != "none" else "none",
        "none", 0, notes)

    # 折线：按 X 升序（日期按时间，文本按原序）
    if spec.agg != "none" or is_date:
        order = sorted(range(len(labels)), key=lambda i: (
            pd.to_datetime(labels[i], errors="coerce")
            if is_date else labels[i]))
        if is_date:
            pairs = [(pd.to_datetime(labels[i], errors="coerce"), values[i]) for i in order]
            pairs = [p for p in pairs if p[0] is not None and not pd.isna(p[0])]
            pairs.sort(key=lambda p: p[0])
            labels = [p[0].strftime("%Y-%m-%d") for p in pairs]
            values = [p[1] for p in pairs]

    if len(values) > MAX_LINE_POINTS:
        notes.append(i18n.t("chart.note.thinned",
                            shown=MAX_LINE_POINTS, total=len(values)))
        step = int(np.ceil(len(values) / MAX_LINE_POINTS))
        labels = labels[::step]
        values = values[::step]

    idx = np.arange(len(values))
    dense = len(values) > 60
    ax.plot(idx, values, color=PALETTE[0], linewidth=1.8,
            marker=None if dense else "o", markersize=3.6,
            markerfacecolor=PALETTE[0], zorder=3)
    # 点少时加淡填充做面积感；点多时填色会糊成一片
    if len(values) <= 120 and values:
        ax.fill_between(idx, values, min(0, min(values)),
                        color=PALETTE[0], alpha=0.08, zorder=2)
    shown_ticks = _thin_ticks(ax, labels)
    _style_axes(ax, th, lang)
    _rotate_xticks(ax, shown_ticks)

    ax.set_xlabel(spec.x, color=th["muted"])
    ax.set_ylabel(spec.y, color=th["muted"])


def _draw_pie(fig, ax, df, spec, th, lang, notes):
    # 不选 Y 时按「计数」看构成
    agg = spec.agg if spec.agg not in ("none", "count") else "sum"
    if spec.y is None:
        agg = "count"
    labels, values, n_total = _agg_frame(
        df, spec.x, spec.y, agg, "desc", 0, notes)

    # 负值/零值不能进饼图
    pairs = [(l, v) for l, v in zip(labels, values) if v and v > 0]
    dropped = len(labels) - len(pairs)
    if dropped:
        notes.append(i18n.t("chart.note.pie_skip", n=dropped))
    if not pairs:
        raise ValueError(i18n.t("chart.err.pie_no_positive"))

    if len(pairs) > MAX_PIE_SLICES:
        head = pairs[:MAX_PIE_SLICES]
        rest = sum(v for _, v in pairs[MAX_PIE_SLICES:])
        pairs = head + [(i18n.t("chart.other"), rest)]
        notes.append(i18n.t("chart.note.pie_other", n=MAX_PIE_SLICES))

    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]

    ax.set_facecolor(th["ax"])
    wedges, _texts, autotexts = ax.pie(
        values, labels=None, colors=colors, startangle=90,
        counterclock=False,
        autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
        pctdistance=0.75,
        wedgeprops={"width": 0.55, "edgecolor": th["ax"], "linewidth": 1.5},
        textprops={"color": th["text"], "fontsize": 9},
    )
    for t in autotexts:
        t.set_color("#FFFFFF")
        t.set_fontsize(8.5)
        t.set_fontweight("bold")

    # 图例放右侧，长标签不挤图
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
              frameon=False, fontsize=9, labelcolor=th["text"])
    ax.set_aspect("equal")
    ax.set_title(i18n.t("chart.pie_title", y=spec.y or spec.x,
                        agg=_agg_label(agg)),
                 color=th["text"], fontsize=11, pad=12)
    _ = fig


def _draw_scatter(ax, df, spec, th, lang, fig, notes):
    if spec.x is None or spec.y is None:
        raise ValueError(i18n.t("chart.err.scatter_need_xy"))

    xs_all = _strict_numeric(_col(df, spec.x))
    ys_all = _strict_numeric(_col(df, spec.y))
    if xs_all is None or ys_all is None:
        raise ValueError(i18n.t("chart.err.scatter_numeric"))

    keep = xs_all.notna() & ys_all.notna()
    n_drop = int((~keep).sum())
    if n_drop:
        notes.append(i18n.t("chart.note.drop_na", n=n_drop))
    sub = pd.DataFrame({"__x": xs_all[keep], "__y": ys_all[keep]})
    if len(sub) == 0:
        raise ValueError(i18n.t("chart.err.no_valid"))

    sub, sampled = sample_rows(sub, SCATTER_SAMPLE_MAX)
    if sampled:
        notes.append(i18n.t("chart.note.sampled",
                            shown=f"{len(sub):,}", total=f"{int(keep.sum()):,}"))

    ax.scatter(sub["__x"], sub["__y"], s=16, color=PALETTE[0], alpha=0.55,
               edgecolors="none", zorder=3)
    _style_axes(ax, th, lang)
    ax.set_xlabel(spec.x, color=th["muted"])
    ax.set_ylabel(spec.y, color=th["muted"])
    ax.xaxis.set_major_formatter(_num_fmt(lang))
    _ = fig


# ==================== 导出 ====================
def save_png(fig, path, dpi=EXPORT_DPI):
    """保存为 PNG。用固定 dpi 而非 fig.dpi，避免高缩放屏上尺寸漂移。"""
    fig.savefig(path, format="png", dpi=dpi,
                facecolor=fig.get_facecolor(), bbox_inches="tight",
                pad_inches=0.12)
    return path


def is_available():
    """matplotlib 是否可用（供 UI 决定按钮是否置灰）。"""
    try:
        import matplotlib  # noqa: F401
        return True
    except Exception:
        return False
