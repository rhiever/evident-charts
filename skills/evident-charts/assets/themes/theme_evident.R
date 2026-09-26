# evident-charts house theme for ggplot2 (>= 3.4, uses `linewidth`).
# Sizes mirror ../presets.json (type % of canvas width). Verified with R 4.5 and ggplot2 4.0.
# Usage:
#   source("<skill>/assets/themes/theme_evident.R")
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

# Diverging with a symmetric domain [-m, 0, m] so equal distances get equal color steps.
scale_fill_evident_div <- function(m, low = "#2166AC", high = "#B2182B", ...) {
  scale_fill_gradient2(low = low, mid = "#F7F7F7", high = high, midpoint = 0, limits = c(-m, m), ...)
}

# Save at the preset's canvas size and dpi; prints the absolute path.
ggsave_evident <- function(plot, path, dest = "blog", ...) {
  p <- evident_presets[[dest]]
  ggsave(path, plot, width = p$w, height = p$h, units = "in", dpi = p$dpi, bg = "white", ...)
  message(normalizePath(path))
  invisible(path)
}
