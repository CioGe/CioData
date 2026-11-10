# -*- coding: utf-8 -*-
"""
图表弹窗：单例、非模态，随数据/主题变化自动重绘。

与 charting.py 的分工：
  charting 负责「数据 → Figure」，本文件只负责「Figure → 界面 + 控件」。
这样图表逻辑可以在无 GUI 环境下被 selfcheck 直接测试。
"""

import os
import tkinter.filedialog as filedialog

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from . import theme as T
from .widgets import FontsHolder, GhostButton, PrimaryButton, SubtleButton, HLine
import charting
import i18n

WINDOW_W = 900
WINDOW_H = 660
FIG_W = 8.4
FIG_H = 4.9

TOPN_OPTIONS = tuple(charting.TOP_N_CHOICES) + (0,)   # 0 = 全部


def _theme_key():
    return "dark" if ctk.get_appearance_mode() == "Dark" else "light"


class ChartWindow(ctk.CTkToplevel):
    """单例图表窗口。由 App._open_chart 创建，App 持有引用。"""

    def __init__(self, master, df, spec=None, settings=None, on_closed=None, **kw):
        super().__init__(master, **kw)
        self._fonts = FontsHolder.get()
        self._on_closed = on_closed
        self._settings = settings
        self.df = df
        self._fig = None
        self._canvas = None
        self._pending = False
        self._dirty_note = False     # 是否需要在顶部提示「列已变更」
        self._closed = False
        self._resize_job = None
        self._last_wh = (0, 0)

        # 显示名 → 内部 key 的反查表（ComboBox 传值不可靠，统一走映射）
        self._type_labels = {i18n.t(f"chart.type.{k}"): k for k in charting.CHART_TYPES}
        self._agg_labels = {i18n.t(f"chart.agg.{k}"): k
                            for k in ("sum", "mean", "count", "max", "none")}
        self._sort_labels = {i18n.t(f"chart.sort.{k}"): k
                             for k in ("desc", "asc", "none")}

        self.title(i18n.t("chart.window_title",
                          rows=f"{len(df):,}", cols=len(df.columns)))
        self.configure(fg_color=T.BG)
        self.transient(master)
        self.resizable(True, True)
        self.minsize(760, 560)

        # 智能默认：先看有没有上次用过的配置，没有才按当前数据推断
        prof = charting.infer_profile(df)
        self._profile = prof
        if spec is not None:
            self.spec = spec.copy()
        else:
            self.spec = self._restore_or_suggest(prof)
        self._has_numeric = any(c["kind"] == "number" for c in prof["columns"])

        self._build()
        self._apply_spec_to_widgets()
        self._redraw()

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Configure>", self._on_configure)
        self.after(60, self._center_on_parent)
        self.after(120, self.focus_force)

    # ==================== 布局 ====================
    def _build(self):
        root = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        root.pack(fill="both", expand=True, padx=14, pady=12)

        # ---------- 类型 ----------
        top = ctk.CTkFrame(root, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=i18n.t("chart.field.type"), font=self._fonts.small,
                     text_color=T.TEXT_2, width=54, anchor="w").pack(side="left")
        self.type_seg = ctk.CTkSegmentedButton(
            top, values=list(self._type_labels.keys()),
            command=self._on_type, height=30, width=396,
            font=self._fonts.small, corner_radius=T.RADIUS_SM,
            selected_color=T.ACCENT, selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.SURFACE_2, unselected_hover_color=T.HOVER,
            text_color=T.TEXT, fg_color=T.SURFACE_2, border_width=0,
        )
        self.type_seg.pack(side="left")

        # 数值标签开关放同一行右侧，省一行高度给图
        self.values_var = ctk.BooleanVar(value=self.spec.show_values)
        self.values_cb = ctk.CTkCheckBox(
            top, text=i18n.t("chart.show_values"), variable=self.values_var,
            command=self._on_values, height=24, font=self._fonts.small,
            text_color=T.TEXT, checkbox_width=16, checkbox_height=16,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            border_color=T.BORDER_STRONG, border_width=1,
        )
        self.values_cb.pack(side="right")

        # ---------- 字段行 ----------
        fields = ctk.CTkFrame(root, fg_color="transparent")
        fields.pack(fill="x", pady=(10, 0))

        def _mk(parent, key, width=150):
            ctk.CTkLabel(parent, text=i18n.t(key), font=self._fonts.tiny,
                         text_color=T.TEXT_2, anchor="w").pack(side="left", padx=(0, 4))
            m = ctk.CTkOptionMenu(
                parent, values=["-"], width=width, height=28,
                font=self._fonts.small, dropdown_font=self._fonts.small,
                fg_color=T.SURFACE_2, button_color=T.SURFACE_2,
                button_hover_color=T.HOVER, text_color=T.TEXT,
                dropdown_hover_color=T.HOVER, corner_radius=T.RADIUS_SM,
            )
            m.pack(side="left", padx=(0, 12))
            return m

        self.x_menu = _mk(fields, "chart.field.x", 142)
        self.y_menu = _mk(fields, "chart.field.y", 142)
        self.agg_menu = _mk(fields, "chart.field.agg", 100)
        self.sort_menu = _mk(fields, "chart.field.sort", 86)
        self.top_menu = _mk(fields, "chart.field.topn", 70)

        self.x_menu.configure(command=self._on_x)
        self.y_menu.configure(command=self._on_y)
        self.agg_menu.configure(command=self._on_agg)
        self.sort_menu.configure(command=self._on_sort)
        self.top_menu.configure(command=self._on_top)

        # ---------- 提示条 ----------
        self.note_label = ctk.CTkLabel(root, text="", font=self._fonts.tiny,
                                      text_color=T.TEXT_2, anchor="w",
                                      justify="left", wraplength=WINDOW_W - 60)
        self.note_label.pack(fill="x", pady=(8, 4))

        # ---------- 画布 ----------
        self.plot_host = ctk.CTkFrame(root, fg_color=T.SURFACE, corner_radius=T.RADIUS,
                                      border_width=1, border_color=T.BORDER)
        self.plot_host.pack(fill="both", expand=True)

        # ---------- 底栏 ----------
        HLine(root).pack(fill="x", pady=(10, 8))
        bottom = ctk.CTkFrame(root, fg_color="transparent")
        bottom.pack(fill="x")
        self.scope_label = ctk.CTkLabel(
            bottom, text=i18n.t("chart.scope", rows=f"{len(self.df):,}"),
            font=self._fonts.tiny, text_color=T.TEXT_3, anchor="w")
        self.scope_label.pack(side="left")

        self.save_btn = PrimaryButton(bottom, text=i18n.t("chart.save_png"),
                                      command=self._save, height=30, width=104)
        self.save_btn.pack(side="right")
        self.refresh_btn = GhostButton(bottom, text=i18n.t("chart.refresh"),
                                       command=self._redraw, height=30, width=80)
        self.refresh_btn.pack(side="right", padx=(0, 8))

    # ==================== 配置记忆 ====================
    def _restore_or_suggest(self, prof):
        """优先恢复上次配置；列已不在当前数据里就退回按数据推断的默认。"""
        saved = None
        if self._settings is not None:
            raw = self._settings.get("chart_prefs")
            if isinstance(raw, dict) and raw:
                saved = raw
        if not saved:
            return charting.suggest(prof)

        spec = charting.ChartSpec.from_dict(saved)
        names = {c["name"] for c in prof["columns"]}
        nums = {c["name"] for c in prof["columns"] if c["kind"] == "number"}
        # 列被改名/换数据源时不能硬套旧配置，否则打开就是一张空图
        if spec.x is not None and spec.x not in names:
            return charting.suggest(prof)
        if spec.y is not None and spec.y not in names:
            return charting.suggest(prof)
        if spec.ctype == "scatter" and not (spec.x in nums and spec.y in nums):
            return charting.suggest(prof)
        if spec.agg != "count" and spec.ctype != "scatter" and spec.y not in nums:
            return charting.suggest(prof)
        return spec

    def _save_prefs(self):
        """只写内存，落盘统一放到 close()（避免每动一次下拉就写一次盘）。"""
        if self._settings is not None:
            self._settings.set("chart_prefs", self.spec.as_dict())

    # ==================== 尺寸跟随 ====================
    def _on_configure(self, event):
        """窗口缩放后延迟重排；子控件触发的 Configure 一律忽略。"""
        if event.widget is not self:
            return
        wh = (event.width, event.height)
        if wh == self._last_wh:
            return
        self._last_wh = wh
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(180, self._apply_size)

    def _plot_figsize(self):
        """按画布实际像素算 figsize（dpi=100，1 英寸 = 100 px）。"""
        w = self.plot_host.winfo_width()
        h = self.plot_host.winfo_height()
        w = w if w > 200 else int(FIG_W * 100)
        h = h if h > 160 else int(FIG_H * 100)
        return max(w / 100.0, 3.2), max(h / 100.0, 2.0)

    def _apply_size(self):
        """只改 Figure 尺寸并重绘，不重建 Figure —— 重建会整块闪一下。"""
        self._resize_job = None
        if self._closed or self._fig is None or self._canvas is None:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        try:
            self._fig.set_size_inches(*self._plot_figsize())
            self._fig.tight_layout(pad=1.3)
            self._canvas.draw_idle()
        except Exception:
            pass

    # ==================== 控件 ↔ spec ====================
    def _col_names(self):
        return [str(c) for c in self.df.columns]

    def _numeric_names(self):
        return [c["name"] for c in self._profile["columns"] if c["kind"] == "number"]

    def _refresh_options(self):
        """数据变化后重建下拉候选值。"""
        cols = self._col_names()
        nums = self._numeric_names()
        none_label = i18n.t("chart.axis.none")
        self.x_menu.configure(values=cols or [none_label])
        self.y_menu.configure(values=nums + [none_label])
        self.agg_menu.configure(values=list(self._agg_labels.keys()))
        self.sort_menu.configure(values=list(self._sort_labels.keys()))
        self.top_menu.configure(values=[i18n.t("chart.topn.all")] +
                               [str(n) for n in charting.TOP_N_CHOICES])

    def _apply_spec_to_widgets(self):
        self._refresh_options()
        self.type_seg.set(i18n.t(f"chart.type.{self.spec.ctype}"))
        self.x_menu.set(self.spec.x if self.spec.x else i18n.t("chart.axis.none"))
        self.y_menu.set(self.spec.y if self.spec.y else i18n.t("chart.axis.none"))
        self.agg_menu.set(i18n.t(f"chart.agg.{self.spec.agg}"))
        self.sort_menu.set(i18n.t(f"chart.sort.{self.spec.sort}"))
        all_label = i18n.t("chart.topn.all")
        self.top_menu.set(str(self.spec.top_n) if self.spec.top_n else all_label)
        self.values_var.set(self.spec.show_values)
        self._sync_enabled()

    def _sync_enabled(self):
        """散点图不使用聚合/排序/TopN；饼图不使用排序。"""
        if self.spec.ctype == "scatter":
            self.agg_menu.configure(state="disabled")
            self.sort_menu.configure(state="disabled")
            self.top_menu.configure(state="disabled")
            self.values_cb.configure(state="disabled")
        else:
            self.agg_menu.configure(state="normal")
            self.sort_menu.configure(state="normal")
            self.top_menu.configure(state="normal")
            self.values_cb.configure(state="normal")
            if self.spec.ctype == "pie":
                self.top_menu.configure(state="disabled")
                self.sort_menu.configure(state="disabled")

    def _on_type(self, label):
        # 找不到映射时保持原类型：绝不能静默跳成柱状图
        self.spec.ctype = self._type_labels.get(label, self.spec.ctype)
        # 散点强制「不聚合」，切回其它类型时要恢复，否则柱状图会变成每行一根柱
        if self.spec.ctype != "scatter" and self.spec.agg == "none":
            self.spec.agg = "sum"
        # 饼图/柱状需要 Y；散点需要两个数值列
        if self.spec.ctype == "scatter" and len(self._numeric_names()) >= 2:
            nums = self._numeric_names()
            if not (self.spec.x in nums and self.spec.y in nums):
                # Y 用最像「结果指标」的列，X 用次之——否则可能画成「数量 vs 单价」
                ranked = sorted(
                    [c for c in self._profile["columns"] if c["kind"] == "number"],
                    key=lambda c: -charting.metric_score(c))
                names = [c["name"] for c in ranked]
                self.spec.y = names[0]
                self.spec.x = next((n for n in names[1:] if n != names[0]), None)
                if self.spec.x is None:
                    self.spec.x = next(n for n in nums if n != self.spec.y)
            self.spec.agg = "none"
            self.spec.sort = "none"
            self.spec.top_n = 0
        elif self.spec.ctype == "pie":
            # 饼图要低基数维度：当前 X 太碎（如逐日日期）就自动换成类别最少的文本列，
            # 否则会画出一块占 70%+ 的「其他」
            cur = next((c for c in self._profile["columns"]
                        if c["name"] == self.spec.x), None)
            if cur is None or cur["nunique"] > charting.MAX_PIE_SLICES:
                cands = [c for c in self._profile["columns"]
                         if c["kind"] == "text"
                         and 0 < c["nunique"] <= charting.MAX_PIE_SLICES]
                if cands:
                    self.spec.x = min(cands, key=lambda c: c["nunique"])["name"]
            self.spec.sort = "desc"
            self.spec.top_n = 0
        elif self.spec.ctype == "bar":
            # 柱子最多 30 根，X 基数远超这个量级（如逐日日期）时自动换低基数维度
            cur = next((c for c in self._profile["columns"]
                        if c["name"] == self.spec.x), None)
            if cur is not None and cur["nunique"] > charting.MAX_BARS * 3:
                cands = [c for c in self._profile["columns"]
                         if c["kind"] == "text"
                         and 0 < c["nunique"] <= charting.CATEGORY_LIMIT]
                if cands:
                    self.spec.x = min(cands, key=lambda c: c["nunique"])["name"]
                    cur = min(cands, key=lambda c: c["nunique"])
            # 从饼图/散点切回来时 Top N 是 0，恢复成默认 Top 10
            if not self.spec.top_n:
                self.spec.top_n = charting.normalize_top_n(
                    10, cur["nunique"] if cur else None)
        elif self.spec.ctype == "line":
            # 折线是趋势图：有日期列就用日期做 X，按时间升序
            dates = [c["name"] for c in self._profile["columns"]
                     if c["kind"] == "date"]
            if dates and self.spec.x not in dates:
                self.spec.x = dates[0]
            if self.spec.x is None and dates:
                self.spec.x = dates[0]
            self.spec.sort = "asc"
            self.spec.top_n = 0
        self._apply_spec_to_widgets()
        self._redraw()

    def _on_x(self, label):
        self.spec.x = None if label == i18n.t("chart.axis.none") else label
        self._clamp_top_n()
        self._apply_spec_to_widgets()
        self._redraw()

    def _clamp_top_n(self):
        """换 X 后类别数可能变小，Top N 要跟着回落到合法值。"""
        if not self.spec.top_n or self.spec.x is None:
            return
        cur = next((c for c in self._profile["columns"]
                    if c["name"] == self.spec.x), None)
        if cur is not None and cur["nunique"] < self.spec.top_n:
            self.spec.top_n = charting.normalize_top_n(
                self.spec.top_n, cur["nunique"])

    def _on_y(self, label):
        self.spec.y = None if label == i18n.t("chart.axis.none") else label
        self._redraw()

    def _on_agg(self, label):
        self.spec.agg = self._agg_labels.get(label, self.spec.agg)
        self._redraw()

    def _on_sort(self, label):
        self.spec.sort = self._sort_labels.get(label, self.spec.sort)
        self._redraw()

    def _on_top(self, label):
        if label == i18n.t("chart.topn.all"):
            self.spec.top_n = 0
        else:
            try:
                self.spec.top_n = int(label)
            except ValueError:
                pass
        self._redraw()

    def _on_values(self):
        self.spec.show_values = bool(self.values_var.get())
        self._redraw()

    # ==================== 重绘 ====================
    def _redraw(self):
        """合并同一轮事件里的多次请求，避免一次操作重绘多次。"""
        if self._closed or self._pending:
            return
        self._pending = True
        self.after_idle(self._do_redraw)

    def _do_redraw(self):
        self._pending = False
        if self._closed or not self.winfo_exists():
            return
        try:
            fig, notes = charting.build_figure(
                self.df, self.spec, theme=_theme_key(),
                figsize=self._plot_figsize())
        except ValueError as e:
            self._show_error(str(e))
            return

        self._swap_canvas(fig)
        self._set_notes(notes)
        self._save_prefs()
        # 首次绘制时 plot_host 可能还没完成布局，尺寸校正一次
        self.after(60, self._apply_size)

    def _swap_canvas(self, fig):
        # 先销毁旧画布并把旧 Figure 的内容清空，否则连开连关会持续吃内存
        if self._canvas is not None:
            try:
                self._canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas = None
        if self._fig is not None:
            try:
                self._fig.clear()
            except Exception:
                pass
        self._fig = fig
        self._canvas = FigureCanvasTkAgg(fig, master=self.plot_host)
        widget = self._canvas.get_tk_widget()
        widget.configure(bg=T.resolve(T.SURFACE))
        widget.pack(fill="both", expand=True, padx=4, pady=4)
        self._canvas.draw()

    def _set_notes(self, notes):
        parts = list(notes)
        if self._dirty_note:
            parts.insert(0, i18n.t("chart.col_changed"))
        if self.spec.ctype == "scatter":
            parts.append(i18n.t("chart.scatter_note"))
        if not charting.ensure_fonts():
            parts.append(i18n.t("chart.no_cjk_font"))
        self.note_label.configure(text="　·　".join(parts),
                                  text_color=T.WARNING if self._dirty_note else T.TEXT_2)

    def _show_error(self, msg):
        # 出错时保留上一张图，只把提示打到提示条
        self.note_label.configure(
            text=i18n.t("chart.err.build", err=msg), text_color=T.ERROR)

    # ==================== 外部事件 ====================
    def on_data_changed(self, df):
        """SQL 结果 / 字段勾选变化后调用，保持窗口与图随动。"""
        if self._closed or df is None:
            return
        old_cols = set(self._col_names())
        new_cols = {str(c) for c in df.columns}
        self.df = df
        # 列没变就不用重扫类型（10 万行全表 nunique 有明显开销）
        if new_cols != old_cols:
            self._profile = charting.infer_profile(df)
        else:
            self._profile["n_rows"] = len(df)

        self.title(i18n.t("chart.window_title",
                          rows=f"{len(df):,}", cols=len(df.columns)))
        self.scope_label.configure(text=i18n.t("chart.scope", rows=f"{len(df):,}"))

        # 用户选中的列被取消勾选/改了别名 → 重算智能默认，而不是留一张空图
        invalid = bool(self.spec.x and self.spec.x not in new_cols) or \
                  bool(self.spec.y and self.spec.y not in new_cols)
        self._dirty_note = invalid
        if invalid:
            self.spec = charting.suggest(self._profile)

        self._has_numeric = any(c["kind"] == "number" for c in self._profile["columns"])
        self._apply_spec_to_widgets()
        self._redraw()

    def on_theme_changed(self):
        if self._closed:
            return
        self._redraw()

    # ==================== 导出 ====================
    def _save(self):
        if self._fig is None:
            return
        name = self._default_filename()
        path = filedialog.asksaveasfilename(
            parent=self,
            title=i18n.t("chart.save_dialog"),
            defaultextension=".png",
            initialfile=name,
            filetypes=[(i18n.t("chart.png_file"), "*.png")],
        )
        if not path:
            return
        try:
            charting.save_png(self._fig, path)
        except Exception as e:
            self.note_label.configure(
                text=i18n.t("chart.err.build", err=str(e)), text_color=T.ERROR)
            return
        self.note_label.configure(text=i18n.t("chart.msg.saved", path=path),
                                  text_color=T.SUCCESS)

    def _default_filename(self):
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        kind = i18n.t(f"chart.type.{self.spec.ctype}")
        safe = "".join(ch for ch in kind if ch.isalnum()) or "chart"
        return f"chart_{safe}_{ts}.png"

    # ==================== 生命周期 ====================
    def _center_on_parent(self):
        try:
            self.update_idletasks()
            pw, ph = self.master.winfo_width(), self.master.winfo_height()
            px, py = self.master.winfo_rootx(), self.master.winfo_rooty()
            w = max(WINDOW_W, self.winfo_reqwidth())
            h = max(WINDOW_H, self.winfo_reqheight())
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            try:
                self.geometry(f"{WINDOW_W}x{WINDOW_H}")
            except Exception:
                pass

    def close(self):
        """显式关闭：释放画布与 Figure，并通知 App 置空引用。"""
        if self._closed:
            return
        self._closed = True
        # 先把本次配置落盘，下次打开还是这套
        self._save_prefs()
        if self._settings is not None:
            try:
                self._settings.save()
            except Exception:
                pass
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
            self._resize_job = None
        try:
            if self._canvas is not None:
                self._canvas.get_tk_widget().destroy()
        except Exception:
            pass
        try:
            if self._fig is not None:
                self._fig.clear()
        except Exception:
            pass
        self._canvas = None
        self._fig = None
        try:
            self.destroy()
        except Exception:
            pass
        if self._on_closed:
            try:
                self._on_closed()
            except Exception:
                pass
