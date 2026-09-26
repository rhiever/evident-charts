---
name: evident-charts
description: >-
  Makes explanatory charts whose point is evident, using evidence-tagged dataviz
  rules. Use whenever you create, revise, restyle, or review a chart, plot,
  graph, or figure meant to show a reader something: matplotlib, seaborn,
  pandas .plot, ggplot2, Plotly, Altair/Vega-Lite, D3, or any PNG/SVG chart for
  a blog, report, paper, slide, newsletter, or social post. Starts from sound
  analysis of the data, picks the chart type from the takeaway and data shape,
  and runs deterministic checks (overlaps, baselines, dual axes, palettes).
  Also use for "critique this chart", "why does this plot look bad", "make this
  figure better", or a pasted chart image.
license: MIT
metadata:
  author: Randy Olson
  version: "0.1.0"
---

# evident-charts

Charts that make one point a reader gets at a glance. Paths are relative to this skill's directory (Claude Code: `${CLAUDE_SKILL_DIR}`); run `scripts/` with the project's Python.

Critique, review, or a chart image with a question: follow `references/critique.md`; otherwise the workflow below.

## Rules

Rule lines read `ID [tag] rule. Break: escape. check: name`. `[E]` experimental evidence: break only with a stated reason. `[P]` practitioner consensus: break for a clear reason. `[T]` taste: bend freely. A project's style guide overrides the house look (`assets/`) and `[T]` rules, never `[E]` integrity rules. `check:` names a `scripts/check_chart.py` check; `palette` means `scripts/check_palette.py`. Citations: `references/sources.md`, only when asked why.

## Workflow

1. **Analyze.** Load the data, print summary stats, confirm units and scope, run the checks below.
2. **Brief** in one line: `Takeaway: <claim the data supports> | Audience: <lay/expert> | Destination: <preset>`. The takeaway answers every part of the request (HI-1). Ask at most two questions, only if the takeaway is ambiguous. Presets (`assets/presets.json`): `blog` (default), `mobile` (phone, phone-read newsletters), `social` (X), `social_portrait` (LinkedIn, Instagram), `slide` (deck), `report` (print, memos, docs).
3. **Choose the form** from the takeaway and data shape; open `references/choosing.md` only when the form is not obvious. It may be a table or one hero number over a sparkline or part bar (`stats_size="hero"`, LY-6). Render alternatives (`references/candidates.md`) only when unsure between two honest forms.
4. **Build** in the project's stack; otherwise Python + matplotlib with `scripts/evident.py` (other stacks: `references/libraries.md`). Fit title and subtitle with `ev.fits_title` and `ev.fits_subtitle`.
5. **Check.** matplotlib: `python scripts/check_chart.py <chart.py> --dest <preset>` (includes color-blindness and contrast); other stacks: `python scripts/check_palette.py "<hex,...>" --role <role> --mark <mark>`. Fix all failures together.
6. **Review** the rendered PNG, never the code (`references/critique.md`, Review loop): a fresh-context subagent given only the PNG, request, and destination, else a self-review of the reopened image. Fix every P0 and P1, re-render, recheck, re-review; stop at a round without P0/P1, at most 3 rounds.
7. **Deliver** the format asked for (`report` may add a PDF): absolute paths to the image and script; the brief; analysis choices a reader should know (any transform, exclusions, thresholds, minimum n); how you identified the source, your confidence, and anything unconfirmed (SRC-1); alt text (A1); any rule broken, with the reason; the one-line review log.

## Analysis checks

- Use the field's standard comparison: same period last year, calendar months or quarters, named members the audience acts on, standard thresholds; pool, smooth, roll, or rebase only when it would mislead, named in the subtitle (H22, H24).
- Flag a preliminary last point, never pool it away; compare a partial last period like-for-like (year to date, trailing 12 months, or within the only measure covering it) (H17, H15, H12).
- Parts sum to the published total; remainder = aggregate minus members; check duplicates, sentinel codes (0, 888, 999, blank), future-dated zero rows (unreleased), split events, and frozen values; compute every number from the data (H11, H24).
- Show n or intervals for small samples, never rank tiny ones; test survey differences at the publisher's MOE level (H23, U1).

## Chart defaults

- Title answers the question as asked ("what drives X": contribution, not rate; H13); subtitle qualifies it and gives what, units, and when; source line names the real publisher and dataset, a note any data you added; nothing addressed to the user on the chart (TI-1, TI-6, SRC-1, SRC-2).
- Marks encode the title's measure by position on a common scale; lines only over ordered x (ENC-1, TIME-1).
- Bars from zero; lines use a range that fits the data (zero only for ratio claims); no dual y-axes, 3D, inverted value axes, or rainbow colormaps (H1, H2, H3, H8, H5, C11).
- One accent on gray when one element is the story; otherwise color meaningful groups; at most 4 hues (C2, C3).
- Direct labels over legends (LB-1). Up to about 10-12 marks: value labels replace the value axis, never both; show the numbers the comparison needs; context columns only if needed (VL-1, VL-2).
- Units on every tick or in the axis title; light value gridlines only; remove ink that carries no information; leave white space; text at least 12 px at display size (TI-7, GR-1, DC-1, TY-2).

## Files

Read a reference only when its decision comes up.

| File | Read when |
|---|---|
| `references/integrity.md` | An analysis, axis, scale, uncertainty, or accessibility question |
| `references/text.md` | Titles, labels, annotation, layout |
| `references/color.md` | A color decision beyond the defaults |
| `scripts/evident.py` | Optional matplotlib helper; its docstring is the usage |
| `assets/presets.json`, `assets/palettes.json` | Destination sizes and type scale; house colors |
