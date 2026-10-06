# evident-charts

Helps coding agents make clear, honest charts and review them with the checks their tools support. Works in Claude Code, Codex, Cursor, and other agents that support skills.

![A typical draft ranking raw electric-car counts on a log scale it never mentions, next to the version evident-charts produced after critiquing it: battery-electric share of new cars by country](examples/hero.png)

<sub>Left: a typical draft, with raw counts on a log scale, the EU total ranked among its own members, and rainbow colors that mean nothing. Right: the same data after evident-charts critiqued and rebuilt it.</sub>

## Use

Ask for a chart the way you already do. Your agent can load the skill when making or reviewing a data chart.

```text
Chart sales.csv for a LinkedIn post on which regions grew fastest.
Make one slide showing where our budget went last year.
Critique this chart and fix it.        (attach the PNG, the script, or both)
```

## What it does

- Checks the data for totals mixed with their parts, duplicate rows, and placeholder values.
- Chooses a chart that fits the point you want to make.
- Writes the takeaway as the title and cites the data publisher.
- Checks for overlapping labels, misleading axes, and color problems. It checks matplotlib directly and other libraries through an SVG export.
- Reviews the image, using a separate reviewer when allowed or self-review otherwise, for up to 3 rounds.
- Returns ranked fixes when you ask for a critique, and reports anything it could not check.

## Why

Charts from coding agents tend to share the same tells:

- A title that names the topic ("Revenue by region") instead of saying what the data shows
- A legend where labels on the data would fit, and rainbow colors that mean nothing
- Bars that start above 0, or 2 y-axes on a chart
- Numbers in annotations that were never checked against the data
- A guessed source line, or the file name used as the source
- Leftover notes like "TODO" or "confirm" on the image

evident-charts checks these problems with scripts and a review of the rendered image. The checks depend on your agent's tools; skipped checks are reported.

## Install

### Claude Code

```text
/plugin marketplace add rhiever/evident-charts
/plugin install evident-charts@evident-charts
```

### Cursor and other [Agent Skills](https://agentskills.io) agents

```text
npx skills add rhiever/evident-charts
```

### GitHub CLI

Set `--agent` to `claude-code`, `codex`, `cursor`, `gemini`, `github-copilot`, or `antigravity`.

```text
gh skill install rhiever/evident-charts evident-charts --agent claude-code --scope user
```

### Codex

```text
codex plugin marketplace add rhiever/evident-charts
codex plugin add evident-charts@evident-charts
```

### Gemini CLI

The `--auto-update` flag keeps it current.

```text
gemini extensions install https://github.com/rhiever/evident-charts --auto-update
```

## Requirements

- Python 3.10+ runs the check scripts. matplotlib checks also need matplotlib and numpy.
- SVG layout checks need Chrome or Chromium. Set `CHROME_PATH` if the checker cannot find it. Your chart library may need an extra package to export SVG.
- Image review needs an agent that can view images. A separate reviewer is optional.

Without Chrome, supported chart-spec checks can still run. Without Python, the agent can review a viewable image but cannot run the scripts. It reports skipped checks and whether it used self-review. An installation of Plotly or Kaleido does not guarantee Chrome is installed.

## Update

| Installed with | Update command |
|---|---|
| Claude Code | `claude plugin marketplace update evident-charts && claude plugin update evident-charts@evident-charts` |
| npx skills | `npx skills update evident-charts` |
| GitHub CLI | `gh skill update evident-charts` |
| Codex | `codex plugin marketplace upgrade evident-charts && codex plugin add evident-charts@evident-charts` |
| Gemini CLI | `gemini extensions update evident-charts` (automatic with `--auto-update`) |

## How the rules work

Each rule has a tag: `[E]` experimental evidence, `[P]` practitioner consensus, or `[T]` taste. Your instructions take precedence. The agent reports requested deviations and any failed checks. Your project's style guide can replace the default look. Citations are in [`references/sources.md`](skills/evident-charts/references/sources.md).

## Works with

- Libraries: matplotlib, seaborn, pandas `.plot`, ggplot2, Plotly, Vega-Lite and Altair, and D3. Themes are in [`assets/themes/`](skills/evident-charts/assets/themes/).
- Sizes: presets for blogs, X, LinkedIn and Instagram, slides, reports, and phones.

## Release package

Build the plugin ZIP with Python; the builder needs no extra packages:

```sh
python3 scripts/build_release.py
```

The ZIP is saved as `dist/evident-charts-<version>.zip`. It contains the manifests, skill resources, icons, and license, with README assets. Private notes and development files are excluded. See the [acceptance checklist](docs/acceptance.md) for testing an unpacked installation.

The root manifest uses the [Agent Plugins format](https://developers.openai.com/plugins/build/plugins), with Claude and Codex compatibility manifests included. For public submission, upload the ZIP through the [OpenAI developer dashboard](https://developers.openai.com/plugins/deploy/submission), then complete its checks and review.

## Contributing

Issues and pull requests are welcome. [AGENTS.md](https://github.com/rhiever/evident-charts/blob/main/AGENTS.md) covers the tests and the rule format; changes are listed in the [changelog](CHANGELOG.md).

## License

[MIT](LICENSE). Built by [Randy Olson](https://randalolson.com).
