---
name: evident-charts
description: >-
  Use when creating, revising, or reviewing explanatory data charts for a
  blog, report, paper, slide, newsletter, or social post. Includes matplotlib,
  seaborn, pandas .plot, ggplot2, Plotly, Altair/Vega-Lite, D3, and PNG/SVG
  charts. Also use for "critique this chart", "why does this plot look bad",
  or "make this figure better" with a chart image. Not for unrelated coding,
  software architecture diagrams, or non-data illustrations.
license: MIT
metadata:
  author: Randy Olson
  version: "0.2.4"
---

# evident-charts

Charts that make one point a reader gets at a glance. `<skill-dir>` is this skill's folder: `${CLAUDE_SKILL_DIR}` where the host fills it in, else the folder holding this SKILL.md (in claude.ai chat, its copy in the sandbox), never the working directory.

This edition checks charts by reviewing the render against the rules and the critique checklist; it has no measurement scripts. The full edition at https://github.com/rhiever/evident-charts adds scripted checks.

Critique, review, or a chart image with a question: follow `references/critique.md`; otherwise the workflow below.

## Host and user instructions

- User instructions and host requirements take precedence over this skill, including its evidence rules. Preserve an explicit override, explain the consequence briefly, and report the rule deviation and any failed check; do not silently replace the requested chart.
- Use only available, permitted tools. Review a rendered image when the host can view it. Report checks run, failed, skipped, and not checkable, with reasons; measured text overlap, clipping, contrast, and color-vision simulation are not checkable here. A partial check is not a full pass.
- Use a fresh reviewer only when delegation and vision are available and allowed by the user and host. Otherwise self-review; if no image can be viewed, mark visual review skipped. Do not install tools or delegate outside the host's permissions.

## Rules

Rule lines read `ID [tag] rule. Break: escape`. `[E]` experimental evidence: break only with a stated reason. `[P]` practitioner consensus: break for a clear reason. `[T]` taste: bend freely. A project's style guide overrides the house look (`assets/`, `references/themes.md`) and `[T]` rules; retain integrity guidance unless explicitly overridden. Citations: `references/sources.md`, only when asked why.

## Workflow

1. **Analyze.** Load the data, print summary stats, confirm units and scope, run the checks below.
2. **Brief** in one line: `Takeaway: <claim the data supports> | Audience: <lay/expert> | Destination: <preset>`. The takeaway answers every part of the request (HI-1). Ask at most two questions, only if the takeaway is ambiguous. Presets (`assets/presets.json`): `blog` (default), `mobile` (phone, phone-read newsletters), `social` (X), `social_portrait` (LinkedIn, Instagram), `slide` (deck), `report` (print, memos, docs).
3. **Choose the form** from the takeaway and data shape; open `references/choosing.md` only when the form is not obvious. It may be a table or one hero number over a sparkline or part bar (LY-6). Render alternatives (`references/candidates.md`) only when unsure between two honest forms.
4. **Build** in the project's stack; otherwise Python + matplotlib (house look and traps per stack: `references/libraries.md`). Keep title and subtitle within the preset's `title_chars_2_lines` and `subtitle_chars_2_lines`.
5. **Check** the render at 2x in dense regions (labels, legends, small text): no text overlaps or clips, every number matches the data, and colors come from `assets/palettes.json` within their use notes (contrast precomputed; Okabe-Ito is color-blind safe by design). Fix failures together, except explicit user overrides; retain those findings in the report.
6. **Review** the rendered PNG, never the code (`references/critique.md`, Review loop), using an allowed fresh reviewer or self-review. Fix P0/P1 issues within the user's instructions, re-render, recheck, re-review; stop when none remain to fix, at most 3 rounds. Report unresolved findings and skipped work.
7. **Deliver** the format asked for (`report` may add a PDF): absolute paths to available outputs; the brief; analysis choices a reader should know (any transform, exclusions, thresholds, minimum n); source confidence and anything unconfirmed (SRC-1); alt text when the image is viewable (A1); deviations; checks run, failed, skipped, or not checkable; the one-line review log. Never claim an output was rendered or inspected when it was not.

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
| `assets/presets.json`, `assets/palettes.json` | Destination sizes and type scale; house colors |
