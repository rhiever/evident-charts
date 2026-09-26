# evident-charts

An agent skill for charts that make one point a reader gets at a glance.

![A colleague's chart ranking raw electric-car counts on an unlabeled log scale, next to the version evident-charts produced after critiquing it: battery-electric share of new cars by country](examples/hero.png)

## Install

Claude Code:

```
/plugin marketplace add rhiever/evident-charts
/plugin install evident-charts@evident-charts
```

Cursor and other agents that support Agent Skills:

```
npx skills add rhiever/evident-charts
```

GitHub CLI (Copilot, Claude Code, Cursor, Codex, Gemini CLI):

```
gh skill install rhiever/evident-charts evident-charts --agent claude-code --scope user
```

Codex:

```
codex plugin marketplace add rhiever/evident-charts
codex plugin add evident-charts@evident-charts
```

Gemini CLI:

```
gemini extensions install https://github.com/rhiever/evident-charts --auto-update
```

## Use

Ask for a chart the way you already do. The skill loads by itself whenever your agent makes or reviews a chart.

- "Chart this CSV to show the main trend."
- "Make a LinkedIn chart of revenue by region from sales.csv."
- "Critique this chart and list fixes." (attach the PNG, the script, or both)

## What it does

- Checks the data before charting it: totals mixed in with their parts, duplicate rows, placeholder codes, preliminary or partial periods. It uses the comparison the publisher reports, such as the same month last year.
- Picks the chart form from the takeaway and the shape of the data. Sometimes the answer is a table or one big number. When two forms are close, it renders both and compares the images.
- Runs scripted checks instead of trusting its own eyes. For matplotlib that means overlapping or clipped text, text over filled areas, bars that skip zero, dual axes, rainbow colormaps, small text, and the contrast and color-blind safety of the colors actually drawn. For other libraries, it tests the palette the same way.
- Delivers a finished chart. The title states the takeaway and the source line names the real publisher. Nothing on the image is a note to you. Alt text and the script path come back in the reply.
- Critiques any chart, from an image or from code, with the top five issues ranked P0 to P3, plus every other P0. Each one cites a rule, points at the exact element, and gives a fix in your library. When you ask, it applies the fixes and, given the code or data, shows before and after side by side.

## The problem it fixes

Charts from coding agents tend to share the same tells:

- A title that names the topic ("Revenue by region") instead of saying what the data shows
- A legend where direct labels would fit
- Rainbow colormaps
- Bars that start above zero
- Two y-axes on one chart
- Numbers in annotations that were never checked against the data
- A source line that was guessed, or copied from the file name
- Process notes or TODOs left on the image

## Rules and evidence

Every rule has a tag for how well it is supported: `[E]` experimental evidence, `[P]` practitioner consensus, `[T]` taste or convention.
Your project's style guide or brand theme overrides the house look and any `[T]` rule, but never an `[E]` integrity rule.
Citations for each rule ID are in [`references/sources.md`](skills/evident-charts/references/sources.md).

## Works with

- Libraries: matplotlib (the default, with a helper and a lint script), seaborn, pandas `.plot`, ggplot2, Plotly, Vega-Lite and Altair, and D3. Themes for ggplot2, Plotly, Vega-Lite, and D3 are in [`assets/themes/`](skills/evident-charts/assets/themes/).
- Agents: Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, and any agent `npx skills` or `gh skill` can install into.
- Sizes: presets for blog, X, LinkedIn and Instagram, slides, reports, and mobile.

## Update

```
claude plugin marketplace update evident-charts && claude plugin update evident-charts@evident-charts   # Claude Code
npx skills update evident-charts                                                                         # npx skills
gh skill update evident-charts                                                                           # GitHub CLI
codex plugin marketplace upgrade evident-charts                                                          # Codex
gemini extensions update evident-charts                                                                  # Gemini CLI
```

## License

MIT. Built by [Randy Olson](https://randalolson.com).
