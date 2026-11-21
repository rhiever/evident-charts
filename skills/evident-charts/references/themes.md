# Themes

House look for stacks without a JSON theme. Write a block to a file in a scratch folder and load it by absolute path, as its header comment shows. A D3 page that ships inlines the CSS and keeps the tokens module beside the page. Sizes mirror `assets/presets.json`.

## evident.mplstyle

```text
# evident-charts house look for matplotlib.
# Usage: plt.style.use("evident.mplstyle")
# Sizes below are the blog preset (8 x 6 in canvas). For other destinations take
# sizes from presets.json (pt = pct/100 * width_in * 72).
# Accent #D55E00 (text #C15500), alt accent #0072B2, context gray #BDBDBD.

font.family:          sans-serif     # first installed font in font.sans-serif wins; DejaVu Sans ships with matplotlib
font.sans-serif:      Helvetica Neue, Helvetica, Arial, Liberation Sans, DejaVu Sans
font.size:            11.5
text.color:           595959

figure.figsize:       8, 6
figure.dpi:           100
figure.facecolor:     white
figure.titlesize:     18.4
figure.titleweight:   bold

savefig.dpi:          200
savefig.facecolor:    white
savefig.bbox:         standard
savefig.pad_inches:   0

axes.facecolor:       white
axes.edgecolor:       8C8C8C
axes.linewidth:       0.8
axes.spines.top:      False
axes.spines.right:    False
axes.grid:            True
axes.grid.axis:       y
axes.axisbelow:       True
axes.titlesize:       10.9
axes.titleweight:     bold
axes.titlecolor:      333333
axes.titlelocation:   left
axes.titlepad:        8
axes.labelsize:       10.9
axes.labelcolor:      595959
axes.labelpad:        6
axes.xmargin:         0.02
axes.ymargin:         0.04
axes.unicode_minus:   True
axes.prop_cycle:      cycler('color', ['0072B2', 'D55E00', '009E73', 'CC79A7', 'E69F00', '56B4E9'])

grid.color:           E6E6E6
grid.linewidth:       0.8
grid.linestyle:       -

xtick.color:          8C8C8C
xtick.labelcolor:     595959
xtick.labelsize:      10.9
xtick.major.size:     4
xtick.major.width:    0.8
xtick.minor.visible:  False
ytick.color:          8C8C8C
ytick.labelcolor:     595959
ytick.labelsize:      10.9
ytick.major.size:     4
ytick.major.width:    0.8
ytick.minor.visible:  False

lines.linewidth:      1.6
lines.markersize:     8
lines.solid_capstyle: butt
lines.solid_joinstyle: round
lines.dash_capstyle:  butt

patch.linewidth:      0
patch.edgecolor:      white
scatter.edgecolors:   white

legend.frameon:       False
legend.fontsize:      10.9
legend.labelcolor:    595959
legend.handlelength:  1.2
legend.borderaxespad: 0

image.cmap:           viridis
date.converter:       concise
```

## theme_evident.R

```r
# evident-charts house theme for ggplot2 (>= 3.4, uses `linewidth`).
# Sizes mirror assets/presets.json (type % of canvas width). Verified with R 4.5 and ggplot2 4.0.
# Usage:
#   source("theme_evident.R")
#   p <- ggplot(df, aes(year, value, colour = country)) + geom_line() +
#     scale_colour_highlight("US") + theme_evident("blog") +
#     labs(title = "Takeaway title", subtitle = "What and units", caption = "Source: X")
#   ggsave_evident(p, "chart.png", "blog")
library(ggplot2)

evident_colors <- list(
  accent = "#D55E00", accent_text = "#C15500", alt = "#0072B2", gray = "#BDBDBD",
  ink = "#333333", dark = "#595959", muted = "#767676", grid = "#E6E6E6", spine = "#8C8C8C"
)
evident_okabe_ito <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9")

# width_in, height_in, dpi, type % (title, subtitle, label, annotation, source), margin % of width
evident_presets <- list(
  blog            = list(w = 8,    h = 6,      dpi = 200, type = c(3.2, 2.2, 1.9, 2.0, 1.6), m = 4.5),
  social   = list(w = 10.8, h = 10.8,   dpi = 200, type = c(4.6, 3.0, 2.8, 2.9, 2.2), m = 6),
  social_portrait = list(w = 10.8, h = 13.5,   dpi = 200, type = c(4.6, 3.0, 2.8, 2.9, 2.2), m = 6),
  slide           = list(w = 19.2, h = 10.8,   dpi = 200, type = c(3.75, 2.5, 2.1, 2.3, 1.6), m = 4.5),
  report          = list(w = 6.25, h = 4.6875, dpi = 300, type = c(2.9, 2.35, 2.0, 2.1, 2.0), m = 2),
  mobile          = list(w = 3.6,  h = 4.5,    dpi = 300, type = c(5.6, 3.9, 3.6, 3.6, 3.4), m = 4.5)
)

# Font size in pt for a type role at a destination (annotate(size = ) wants mm: divide by ggplot2::.pt).
evident_size <- function(role = c("title", "subtitle", "label", "annotation", "source"), dest = "blog") {
  role <- match.arg(role)
  p <- evident_presets[[dest]]
  unname(p$type[match(role, c("title", "subtitle", "label", "annotation", "source"))] / 100 * p$w * 72)
}

# base_family "sans" is Helvetica/Arial on most devices (Liberation Sans or DejaVu Sans on bare Linux); pass a brand font to override.
theme_evident <- function(dest = "blog", base_family = "sans") {
  p <- evident_presets[[dest]]
  sz <- function(role) evident_size(role, dest)
  lab <- sz("label")
  hair <- 0.14 / 100 * p$w * 72 / ggplot2::.pt # grid and axis line width, mm
  pad <- p$m / 100 * p$w * 72                  # outer margin, pt
  k <- evident_colors
  theme_minimal(base_size = lab, base_family = base_family) +
    theme(
      text = element_text(colour = k$dark),
      plot.title = element_text(size = sz("title"), face = "bold", colour = k$ink, hjust = 0,
                                lineheight = 1.1, margin = margin(b = 0.45 * sz("subtitle"))),
      plot.subtitle = element_text(size = sz("subtitle"), colour = k$muted, hjust = 0,
                                   margin = margin(b = 1.6 * lab)),
      plot.caption = element_text(size = sz("source"), colour = k$muted, hjust = 0,
                                  margin = margin(t = 1.1 * lab)),
      plot.title.position = "plot",
      plot.caption.position = "plot",
      axis.text = element_text(size = lab, colour = k$dark),
      axis.title = element_text(size = lab, colour = k$dark),
      axis.line = element_line(colour = k$spine, linewidth = hair),
      axis.ticks = element_line(colour = k$spine, linewidth = hair),
      axis.ticks.length = unit(0.35 * lab, "pt"),
      panel.grid.major.x = element_blank(),
      panel.grid.minor = element_blank(),
      panel.grid.major.y = element_line(colour = k$grid, linewidth = hair),
      legend.position = "top",
      legend.justification = "left",
      legend.title = element_blank(),
      legend.text = element_text(size = lab, colour = k$dark),
      strip.text = element_text(size = lab, face = "bold", colour = k$ink, hjust = 0),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA),
      plot.margin = margin(pad, pad, 0.6 * pad, pad)
    )
}

# Horizontal bars / dot plots: light grid on the value (x) axis, keep the category axis line.
theme_evident_hbar <- function() {
  theme(panel.grid.major.y = element_blank(),
        panel.grid.major.x = element_line(colour = evident_colors$grid),
        axis.line.x = element_blank(), axis.ticks.y = element_blank())
}

# Up to ~12 bars with geom_text value labels: drop the value axis and its grid (VL-1).
# Blank the specific grid elements: theme_evident() sets them, and they override a blank panel.grid.
theme_evident_value_labels <- function(horizontal = TRUE) {
  none <- element_blank()
  if (horizontal) {
    theme(axis.text.x = none, axis.title.x = none, axis.ticks.x = none, axis.line.x = none,
          panel.grid.major.x = none, panel.grid.major.y = none, panel.grid.minor = none)
  } else {
    theme(axis.text.y = none, axis.title.y = none, axis.ticks.y = none, axis.line.y = none,
          panel.grid.major.x = none, panel.grid.major.y = none, panel.grid.minor = none)
  }
}

# Highlight + gray: named levels get the accents in order, every other level gets context gray.
scale_colour_highlight <- function(highlight, accents = c(evident_colors$accent, evident_colors$alt), ...) {
  scale_colour_manual(values = setNames(accents[seq_along(highlight)], highlight),
                      na.value = evident_colors$gray, guide = "none", ...)
}
scale_fill_highlight <- function(highlight, accents = c(evident_colors$accent, evident_colors$alt), ...) {
  scale_fill_manual(values = setNames(accents[seq_along(highlight)], highlight),
                    na.value = evident_colors$gray, guide = "none", ...)
}
scale_colour_evident <- function(...) scale_colour_manual(values = evident_okabe_ito, ...)
scale_fill_evident <- function(...) scale_fill_manual(values = evident_okabe_ito, ...)

# Sequential: viridis trimmed at the light end so marks stay visible on white.
scale_fill_evident_seq <- function(...) scale_fill_viridis_c(end = 0.85, ...)

# Diverging with a symmetric domain [-m, 0, m] so equal distances get equal color steps; negatives red as in
# palettes.json.
scale_fill_evident_div <- function(m, low = "#B2182B", high = "#2166AC", ...) {
  scale_fill_gradient2(low = low, mid = "#F7F7F7", high = high, midpoint = 0, limits = c(-m, m), ...)
}

# Save at the preset's canvas size and dpi; prints the absolute path.
ggsave_evident <- function(plot, path, dest = "blog", ...) {
  p <- evident_presets[[dest]]
  ggsave(path, plot, width = p$w, height = p$h, units = "in", dpi = p$dpi, bg = "white", ...)
  message(normalizePath(path))
  invisible(path)
}
```

## evident_d3.css

```css
/* evident-charts house look for D3/SVG charts. Put class="ev-chart" on the <svg>.
   Colors are literal (house values). Sizes are SVG user units for an 800-wide viewBox (blog);
   evApply(svg, dest) in evident_d3_tokens.js sets --ev-* for other presets. Each sized rule
   repeats a literal first so SVG renderers without var() support (librsvg, Inkscape) still work. */
.ev-chart { font-family: "Helvetica Neue", Helvetica, Arial, "Liberation Sans", "DejaVu Sans", sans-serif; background: #fff; }
.ev-chart text { fill: #595959; font-size: 15.2px; font-size: var(--ev-label, 15.2px); font-variant-numeric: tabular-nums; }
.ev-chart .ev-title { fill: #333333; font-weight: 700; font-size: 25.6px; font-size: var(--ev-title, 25.6px); }
.ev-chart .ev-subtitle { fill: #767676; font-size: 17.6px; font-size: var(--ev-subtitle, 17.6px); }
.ev-chart .ev-source, .ev-chart .ev-note { fill: #767676; font-size: 12.8px; font-size: var(--ev-source, 12.8px); }
.ev-chart .ev-annotation { fill: #595959; font-size: 16px; font-size: var(--ev-annotation, 16px); }
.ev-chart .ev-annotation-line { stroke: #595959; fill: none; stroke-width: 1.1px; stroke-width: var(--ev-hair, 1.1px); }

/* d3.axisLeft/axisBottom output (CSS beats the axis's font-size/fill attributes) */
.ev-axis .domain, .ev-axis .tick line { stroke: #8C8C8C; stroke-width: 1.1px; stroke-width: var(--ev-hair, 1.1px); }
.ev-axis .tick text { fill: #595959; }
.ev-axis--bare .domain, .ev-axis--bare .tick line { display: none; }  /* category axis, or value axis replaced by labels */
.ev-grid .domain, .ev-grid .tick text { display: none; }
.ev-grid .tick line { stroke: #E6E6E6; stroke-width: 1.1px; stroke-width: var(--ev-hair, 1.1px); }

/* marks: highlight + gray */
.ev-chart .ev-context { stroke: #BDBDBD; fill: #BDBDBD; }
.ev-chart .ev-accent { stroke: #D55E00; fill: #D55E00; }
.ev-chart .ev-alt { stroke: #0072B2; fill: #0072B2; }
.ev-chart path.ev-series { fill: none; stroke-linejoin: round; stroke-linecap: butt; stroke-width: 2.2px; stroke-width: var(--ev-line, 2.2px); }
.ev-chart path.ev-series.ev-accent, .ev-chart path.ev-series.ev-alt { stroke-width: 4.4px; stroke-width: var(--ev-accent-line, 4.4px); }
.ev-chart .ev-segment { stroke: #FFFFFF; stroke-width: 1px; } /* stack segments, pie slices, tiles (C17) */
.ev-chart line.ev-stem { stroke: #BDBDBD; stroke-linecap: butt; stroke-width: 3.1px; stroke-width: calc(var(--ev-line, 2.2px) * 1.4); }
.ev-chart text.ev-label { fill: #767676; stroke: none; }
.ev-chart text.ev-label.ev-accent { fill: #C15500; font-weight: 700; }
.ev-chart text.ev-label.ev-alt { fill: #0072B2; font-weight: 700; }
```

## evident_d3_tokens.js

```js
// evident-charts tokens for D3 (ES module). type and strokes mirror assets/presets.json (% of canvas width); margins are fractions of width.
export const EV = {
  accent: "#D55E00", accentText: "#C15500", alt: "#0072B2", gray: "#BDBDBD",
  ink: "#333333", dark: "#595959", muted: "#767676", grid: "#E6E6E6", spine: "#8C8C8C",
  okabeIto: ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"],
  presets: {
    blog: { width: 800, height: 600, scale: 2, type: { title: 3.2, subtitle: 2.2, label: 1.9, annotation: 2.0, source: 1.6 },
      strokes: { line: 0.28, accent_line: 0.55, marker: 1.4, grid: 0.14 }, margins: { left: 0.05, right: 0.04, top: 0.05, bottom: 0.03 } },
    social: { width: 1080, height: 1080, scale: 2, type: { title: 4.6, subtitle: 3.0, label: 2.8, annotation: 2.9, source: 2.2 },
      strokes: { line: 0.28, accent_line: 0.58, marker: 1.6, grid: 0.13 }, margins: { left: 0.07, right: 0.05, top: 0.05, bottom: 0.03 } },
    social_portrait: { width: 1080, height: 1350, scale: 2, type: { title: 4.6, subtitle: 3.0, label: 2.8, annotation: 2.9, source: 2.2 },
      strokes: { line: 0.28, accent_line: 0.58, marker: 1.6, grid: 0.13 }, margins: { left: 0.07, right: 0.05, top: 0.05, bottom: 0.03 } },
    slide: { width: 1920, height: 1080, scale: 2, type: { title: 3.75, subtitle: 2.5, label: 2.1, annotation: 2.3, source: 1.6 },
      strokes: { line: 0.22, accent_line: 0.45, marker: 1.2, grid: 0.1 }, margins: { left: 0.05, right: 0.04, top: 0.045, bottom: 0.03 } },
    report: { width: 600, height: 450, scale: 4, type: { title: 2.9, subtitle: 2.35, label: 2.0, annotation: 2.1, source: 2.0 },
      strokes: { line: 0.3, accent_line: 0.6, marker: 1.6, grid: 0.15 }, margins: { left: 0.02, right: 0.02, top: 0.02, bottom: 0.015 } },
    mobile: { width: 360, height: 450, scale: 3, type: { title: 5.6, subtitle: 3.9, label: 3.6, annotation: 3.6, source: 3.4 },
      strokes: { line: 0.4, accent_line: 0.8, marker: 2.2, grid: 0.2 }, margins: { left: 0.05, right: 0.04, top: 0.05, bottom: 0.035 } },
  },
};

// Size in SVG units (viewBox width = preset width) of a type role (font size) or stroke role (line, accent_line, marker, grid).
export const evSize = (role, dest = "blog") => {
  const p = EV.presets[dest];
  return Math.round((p.type[role] ?? p.strokes[role]) * p.width) / 100;
};

// Apply a preset's sizes to an <svg class="ev-chart"> (CSS custom properties from evident_d3.css).
export function evApply(svg, dest = "blog") {
  const p = EV.presets[dest];
  svg.attr("viewBox", `0 0 ${p.width} ${p.height}`);
  for (const role of Object.keys(p.type)) svg.style(`--ev-${role}`, `${evSize(role, dest)}px`);
  svg.style("--ev-line", `${evSize("line", dest)}px`).style("--ev-accent-line", `${evSize("accent_line", dest)}px`)
     .style("--ev-hair", `${evSize("grid", dest)}px`);
  return svg;
}

// Highlight + gray color accessor: evColor(["US"])(d.name).
export const evColor = (highlight = [], accents = [EV.accent, EV.alt]) => (name) => {
  const i = highlight.indexOf(name);
  return i >= 0 && i < accents.length ? accents[i] : EV.gray;
};

// Diverging color with a symmetric domain so 0 sits at the neutral midpoint.
// d3.interpolateRdBu runs red (0) to blue (1): domain [-m, 0, m] maps negatives red, positives blue.
export const evDiverging = (d3, values) => {
  const m = d3.max(values, (v) => Math.abs(v));
  return d3.scaleDiverging(d3.interpolateRdBu).domain([-m, 0, m]);
};
```
