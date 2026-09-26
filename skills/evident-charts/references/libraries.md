# Libraries

The house look per stack, plus traps that silently break a rule. Each theme file's header comment shows its usage. Sizes come from `assets/presets.json` (its `_doc` gives the units and the pt formula); symmetric diverging idioms per library are in palettes.json `library_names.centered_midpoint`.

## matplotlib (default stack)

- Helper `scripts/evident.py` (optional; the rules hold without it): its module docstring is the usage example. Also `ev.size(role)` (points for any preset role), `ev.text_color(c)` (text-safe variant of a mark color); each docstring gives the arguments.
- `ev.titles()` wraps the title and subtitle to 2 lines at a phrase boundary and warns when any text block needs more; force a break with `\n`; `ev.save()` refits the layout.
- Layout fit covers grid subplots only. Colorbars: prefer `ax.inset_axes` or a direct-labeled legend strip.
- Without the helper: `plt.style.use(f"{SKILL_DIR}/assets/evident.mplstyle")` (blog sizes), set `figsize` and font sizes from the preset, place the title block with `fig.text(..., va="top")`, and reserve room with `fig.subplots_adjust(...)`.

Pitfalls:
- Never `savefig(bbox_inches="tight")`: it crops the reserved margins. `tight_layout` and `constrained_layout` ignore `fig.text` title blocks and overlap them. Reserve margins with `subplots_adjust` (or `ev.save`).
- Percent and currency ticks: set clean steps first (`MultipleLocator(5)` or `MaxNLocator(steps=[1,2,5,10])`), then format with `PercentFormatter(decimals=0)` or `StrMethodFormatter`; formatting auto ticks with `{:.0f}%` rounds 12.5 to "12%" and mislabels the axis.
- `scatter(s=...)` is marker area in pt^2, not radius: set `s` proportional to the value (or to `log(value)`, labeled "log scale"); `s ∝ value**2` or `(log v)**2` exaggerates.
- Lollipop, dumbbell, and paired-dot stems: `solid_capstyle="butt"` (`capstyle="butt"` for `hlines`/`vlines`); the style sheet already sets butt for `plot` lines.
- Dense point labels (20+): `adjustText` (optional), with sampled trend-line points in the avoid arrays: `adjust_text(texts, x=np.r_[x, lx], y=np.r_[y, ly])`. Layout is stochastic: loop `np.random.seed(n)` until `check_chart.py` reports 0 text overlaps, hardcode that seed, and re-search after any limit or aspect change.
- `TwoSlopeNorm(vcenter=0, vmin=a, vmax=b)` with `|a| != |b|` stretches each side to full saturation (-1 looks as extreme as +3); use it only when that is intended and stated.
- Horizontal bars without value labels: move the grid to x with `ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)`.
- Dates: the style sets the concise date converter; on narrow canvases also cap ticks with `ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=4))`.
- seaborn and pandas `.plot`: create axes with `ev.figure`, pass `ax=ax`, and remove any auto legend (`ax.get_legend().remove()`) before direct labeling.

## ggplot2

`assets/themes/theme_evident.R`: `source()` it, then `+ theme_evident(dest)` and `ggsave_evident(p, path, dest)`.

- Also provides `theme_evident_hbar()` (grid on x), `theme_evident_value_labels(horizontal = TRUE)`, `scale_colour_evident()`/`scale_fill_evident()` (Okabe-Ito), `scale_fill_evident_seq()`, `scale_fill_evident_div(m)`, and `evident_size(role, dest)` in pt (divide by `ggplot2::.pt` for `geom_text(size = )`).
- Title and caption align to the plot edge (`plot.title.position = "plot"`). Direct labels: `geom_text(data = last_points, hjust = 0, nudge_x = ...)` plus `coord_cartesian(clip = "off")` and extra right `plot.margin`; `scale_colour_highlight()` also colours text, so give context-line labels `colour = evident_colors$dark`; `ggrepel::geom_text_repel(direction = "y", seed = 1)` for collisions.

Pitfalls:
- Facets: keep the default `scales = "fixed"` (SCL-1); `"free"`/`"free_y"` gives each panel its own axis.
- Zooming: `scale_y_continuous(limits = ...)` drops out-of-range data (bars vanish, stats are recomputed). Zoom lines with `coord_cartesian(ylim = ...)`; seat bars with `scale_y_continuous(expand = expansion(mult = c(0, 0.05)))`.
- `ggsave` without width and height uses the device size, not the preset; use `ggsave_evident`.
- `scale_fill_gradient2(midpoint = 0)` centers the colors but not the legend, and `scale_fill_distiller(palette = "RdBu")` does not center on 0: give either `limits = c(-m, m)` (`scale_fill_evident_div(m)`).

## Plotly

`assets/themes/evident_plotly.json` (blog preset, legend off; its `_doc` shows loading, two-line titles, and the subtitle fallback for Plotly < 5.23).

- Source line: `fig.add_annotation(text="Source: ...", xref="paper", yref="paper", x=0, y=0, yshift=-50, xshift=40 - margin_l, xanchor="left", yanchor="top", showarrow=False, font=dict(size=12.8, color="#767676"))`; `xshift` keeps it on the title's edge when `margin.l` is above 40. Export with `fig.write_image("chart.png", scale=2)` (needs `kaleido`).
- Direct labels: `add_annotation(x=last_x, y=last_y, xanchor="left", xshift=6, showarrow=False)`. Annotations stretch the autorange, so pin the axis to the data (`range=[x0, x1]`) and grow `margin.r` to fit them.
- Horizontal bars: `fig.update_yaxes(nticks=0, showgrid=False, ticks="", automargin=False)` (the template's `nticks` skips category labels) with `margin.l` = 40 + longest label (about 8.4 px per character) + 8, so labels start on the title's edge (automargin pushes them to the canvas edge). Value axis: `visible=False` when value labels replace it, else `showgrid=True`.

Pitfalls:
- Bar autorange includes zero, but an explicit `range=` on a bar axis (often copied from a line chart) truncates; keep `range[0] = 0` for bars.
- `textposition="outside"` value labels get clipped at the autorange edge: set `cliponaxis=False` and widen the value range, or hide the value axis (`visible=False`; hiding only tick labels and grid leaves its line and ticks) when labels replace it.
- Diverging: set `zmid=0` (heatmap) or `cmid=0` (marker colors); explicit `zmin`/`zmax` of unequal magnitude with no mid shifts the neutral color off 0.

## Vega-Lite / Altair

`assets/themes/evident_vegalite.json` (its `$comment` shows how to merge the config). Altair 5.5+: `alt.theme.register("evident", enable=True)(lambda: alt.theme.ThemeConfig(cfg))`, where `cfg` is the whole file minus `$comment`; older Altair: `alt.themes.register("evident", lambda: cfg)` then `alt.themes.enable("evident")`. Export: `chart.save("chart.png", scale_factor=2)` (needs `vl-convert-python`).

- Single and layered views fill 800x600 including titles (autosize fit); a chart-level `width`/`height` is also the total size. Concat and facet ignore fit: set each view's `width`/`height`.

- Grid on the y axis only and band axes drop ticks and grid; horizontal bars need `axis: {grid: true}` on x.
- Title is `{text, subtitle}`; the source goes in a text layer or the host page caption. Highlight + gray: `color: {condition: {test: "datum.name === 'US'", value: "#D55E00"}, value: "#BDBDBD"}`, with line width via `size` under the same condition.

Pitfalls:
- `scale.zero` defaults to true for quantitative position scales, pulling lines and dots to zero and flattening them: set `scale: {zero: false}` for lines and dots when justified, never for bars.
- An explicit `scale.domain` on a bar axis that excludes zero truncates bars without warning.
- `scale.domainMid: 0` puts the neutral color at 0 but keeps asymmetric extremes; set `domain: [-m, m]` too.
- Temporal x from integer years: use `type: "temporal"` with `timeUnit: "year"` or `axis: {format: "d"}`, or years print as 2,000.

## D3

- `assets/themes/evident_d3.css`: `class="ev-chart"` on the `<svg>`, plus classes `ev-title ev-subtitle ev-source ev-annotation ev-axis ev-axis--bare ev-grid ev-context ev-accent ev-alt ev-series ev-label ev-stem`.
- `assets/themes/evident_d3_tokens.js`: `EV` colors and presets (type, strokes, margins), `evApply(svg, dest)` sets the viewBox and size variables, `evSize(role, dest)` (type or stroke role), `evColor(highlight)(name)`, `evDiverging(d3, values)`.
- Standalone SVG or PNG: inline the CSS as a `<style>` child of the `<svg>` and set `width`/`height`. Renderers without `var()` support (librsvg's `rsvg-convert`, Inkscape) fall back to blog sizes: export other presets with a browser renderer or set sizes as attributes.

Pitfalls:
- `d3.scaleDiverging().domain([min, 0, max])` with unequal |min| and |max| stretches each side independently: use `[-m, 0, m]` (`evDiverging`). `d3.interpolateRdBu` runs red to blue; reverse the domain if positives should be red.
- `d3.scaleLinear().domain(d3.extent(values))` on bars drops zero: use `[0, d3.max(values)]` (`.nice()` is fine).
- Circle radius takes `d3.scaleSqrt` (area ∝ value); `scaleLinear` on radius exaggerates.
- d3-axis writes `font-size="10"` and `fill="currentColor"` attributes; the CSS overrides them, inline styles would not.
