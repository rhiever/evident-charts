# Changelog

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
