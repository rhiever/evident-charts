# Changelog

## 0.2.2

- Added a portable plugin manifest, listing text, and EC icons.
- Clarified user overrides, tool requirements, and skipped checks. Review can use an allowed separate reviewer or self-review.
- Added a reproducible release ZIP builder and package tests.
- Updated installation guidance and added an acceptance checklist.

## 0.2.1

- Removed `check_data.py`. In test runs it raised false alarms and added nothing agents didn't already catch; the data checks are back to short written rules.
- `check_chart.py` now flags text on a line where a gray context line meets its accent-colored part, and text crossing a zero or reference line.

## 0.2.0

- `check_data.py` checks a data table before charting: total rows mixed with members, duplicate keys, trailing zero periods, status flags, sentinel codes, mixed units, gaps, frozen values.
- `check_svg.py` runs the overlap, clipping, text size, contrast, and color-blindness checks on SVG exports from Plotly, Vega-Lite/Altair, ggplot2, and D3 (needs Chrome).
- `check_chart.py` adds `number-format` (offset text like "1e6", fractional year ticks, mixed decimals), `category-order` (unsorted bars, lines across categories), `segment-edges` (touching fills with no border), and `invisible-arrow` (annotation arrows the house style hides).
- New rules: margins of error for poll leads, both absolute levels for relative risks, fitted lines inside the data, gaps in lines for missing periods, white edges between filled segments.

## 0.1.0

First release.

- Workflow for explanatory charts: check the data, write a one-line brief, pick the form, build, check, review, deliver.
- Rules tagged by evidence (`[E]`, `[P]`, `[T]`), with citations for every rule ID in `references/sources.md`.
- `check_chart.py` lints matplotlib charts: overlapping or clipped text, labels on data, bar baselines, dual axes, color-blind confusable series, contrast, plot shape, and more.
- `check_palette.py` tests palettes for color-blind safety and contrast.
- `evident.py` helper with presets for blog, X, LinkedIn, slides, reports, and phones.
- A visual review loop on the rendered chart before delivery, up to three rounds.
- Chart critique with ranked, rule-cited fixes.
- House themes for matplotlib, ggplot2, Plotly, Vega-Lite, and D3.
- Installs for Claude Code, Codex, Gemini CLI, and any agent that `npx skills` supports.
