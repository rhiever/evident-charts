# Critique

Review any chart (image, code, or both) and return prioritized, evidence-backed fixes. Vision judgments are noisy: message first, then measurements, then binary checks with quoted evidence.

Follow the user's instructions and host permissions. Run only available checks; distinguish measured results, visual judgments, and things not verified. Preserve explicit rule overrides and report their consequences.

## Inputs

- Image only: judge the pixels and say which checks cannot be verified (computed numbers, scope, units).
- Code (preferred with the image): render and lint a scratch copy (the script may overwrite its own files) and critique the render. Cross-check annotation numbers against the data, and period words in the title ("since 2020") against the date filter. Code that will not run gets static checks only; say so.
- A URL or interactive chart: ask for a screenshot or use a browser tool.
- No image-viewing tool: use code/spec checks if available, mark visual review skipped, and request an accessible image only when needed. Do not invent a recovered message, findings, alt text, or scores. Image-only inputs cannot verify numbers against source data.

## Procedure

1. Recover the message before anything else: from the image alone, write the one sentence a reader would take away and compare it with the intended point (the title, the user's words, the surrounding text). A mismatch or no clear message is the top finding. If the data disproves the intended headline, the fix follows TI-1.
2. Run available deterministic checks by absolute path from the installed skill: matplotlib `python <skill-dir>/scripts/check_chart.py <chart.py> --json`; other stacks `python <skill-dir>/scripts/check_svg.py <chart.svg> --json [--spec <fig.json | chart.vg.json>]` on an SVG export with live text. Without Chrome, only supported spec checks run; without a spec, skip SVG checks. Image only: run `check_palette.py` when exact series hexes can be obtained; do not claim measured colors from guessed hexes. Without Python, skip script checks. Report which ran and which did not.
3. Walk the checklist. Every "no" quotes the element it is about (label, axis, bar, region); a finding without evidence does not count.
4. Inspect dense regions (label clusters, legends, small text) at 2x.
5. An allowed fresh-context reviewer (Review loop) may run steps 1, 3, and 4; otherwise self-review when the image is viewable, or mark visual review skipped.

## Checklist

Each item names the rule to cite.

- Analysis: H22 standard comparison, any transform named; H15 window justified, partial periods like-for-like; H23 n shown, tiny samples unranked; H24 no dropped or miscoded records, standard thresholds; H13 size shown; H11 nothing counted twice, split events linked, every number matches the data; H25 relative changes give both absolute levels.
- Message: TI-1 title answers the question as asked; HI-1 every part of the request answered; TI-2 the claim is the most visible element; TI-6 subtitle gives what, units, and when.
- Form: SEL-2 form fits takeaway and data shape; ENC-1 marks encode the title's measure on a common position scale; TIME-1 lines only over ordered x; PART-2 no pies compared across groups; ENC-6 at most 3-4 encoded variables.
- Integrity: H1 bars and areas from zero; H2 line range fits the claim; H3 no dual y-axis; H5 no inverted value axis; H8 no 3D; H7 areas scaled by area; H14 money across years adjusted or labeled unadjusted; H9 log scale labeled; U1 uncertainty shown when comparing estimates; H26 fitted lines stay inside the data; TIME-6 gaps left as gaps.
- Text: LB-1 direct labels where they fit; VL-1 value labels on about 12 or fewer marks, never with the value axis; VL-2 the numbers the comparison needs are shown; AN-1 and AN-3 annotations the story needs, pointing at exact data; TI-7 units stated once; text-overlap and text-clipped clean; TY-2 text at least 12 px at display size; SRC-1 source names publisher and dataset, notes state only supported facts; SRC-2 no process notes or TODOs on the chart.
- Color: C1 palette type matches the data; C2 accent on gray only when one element is the story, otherwise meaningful groups; C3 at most 4 hues by default; A4 not color alone; C12 and C14 pass CVD and contrast; C11 no rainbow; C17 filled segments separated.
- Accessibility: A1 alt text or caption available; A3 data table or CSV linkable.

## Severity

- P0: misleads or states a wrong number.
- P1: the point does not land, or text is unreadable.
- P2: slows reading.
- P3: polish.
Tiebreak: would a careful reader draw a wrong conclusion or no conclusion? Yes means at least P1.

## Output

Five issues by default, most severe first, plus every further P0; plain text:

```
Chart critique: <file(s)>
Method: <rendered from script | image only | static code/spec only>; checks: <which ran | none>; review: <self | fresh context | skipped: reason>
Recovered message: "<sentence | unavailable>" | Intended: "<sentence | unknown>" | <MATCH | MISMATCH | NOT CHECKABLE>

[P0] <rule ID> [tag] <what is wrong>
  Where: <element>
  Fix: <concrete change in the user's library>
  Break: <escape hatch, if one applies>

Also fixed: <lesser issues the rebuild also addresses, one line>
Works: <1-2 things the chart does well>
Passed: <checks actually run and passed>
Failed: <checks actually run and failed, including user-required deviations>
Skipped: <checks or review omitted and why>
Not checkable: <rule IDs and why>
```

No aggregate score; if a number is wanted, report `checks passed: N/M applicable`.

## Review loop

Build workflow step 6, after the deterministic checks pass. Vision judges are noisy and go easy on their own work, so the reviewer sees only what a reader sees.

- Reviewer: a new fresh-context subagent with vision only when the user and host allow delegation and you are not a subagent. Give only the prompt below: PNG paths, the user's request verbatim, the destination. Never the code, data, brief, your reasoning, or earlier findings.
- Fallback (delegation unavailable or prohibited, or you are a subagent): self-review with the same prompt. Reopen the PNG with your image viewer; judge the pixels, not your memory of the code. Without image access, skip visual review and explain why; do not score unseen pixels.
- Round: fix P0/P1 issues in one batch within the user's instructions, re-render, rerun available checks, review again. Retain user-required deviations as findings. Stop when no fixable P0/P1 remains; after round 3, deliver and list what remains.
- P2/P3: fix only when cheap and uncontroversial. Never undo an earlier round's fix on taste. A finding contradicted by the data or a passing check loses; log it as rejected.
- Scores track progress across rounds; findings, not scores, drive fixes.
- Log, one line in the delivery reply: `Review: <N> rounds (<fresh context | self | skipped: reason>); fixed: <...>; remaining: <none | ...>`. Rubric scores are optional visual judgments, never verification results.

```
Review this chart as a skeptical outside reader seeing it for the first time. You have not seen its code or data. Do not edit files or ask questions.
Images: <absolute PNG paths>
Request: "<user's request, verbatim>"
Destination: <preset>, read at <display_px> px wide
Open each image with your image viewer. Rubric: <skill dir>/references/critique.md, sections Checklist and Severity (if unreadable: P0 misleads or wrong number; P1 point does not land or text unreadable; P2 slows reading; P3 polish).
1. From the image alone, write the one sentence a reader takes away; compare it with what the request asks. A mismatch or no clear message is the top finding.
2. Walk the checklist; zoom 2x on dense regions (label clusters, legends, small text). Checks the image cannot show go under Not checkable.
3. Score 1-5: story (the takeaway lands at a glance), honesty (nothing misleads), polish (clean, legible, nothing collides or clips), fit (size, text, and density suit the destination).
Return plain text:
Recovered message: "<sentence>" | Asked: "<sentence>" | MATCH or MISMATCH
Scores: story N, honesty N, polish N, fit N
[P0-P3] <rule ID> <problem> | Where: <exact element, quoting its text> | Fix: <concrete change>
(every P0 and P1, then up to 5 total, most severe first; no finding without a quoted element)
Not checkable: <rule IDs>
```

## Fixing

If the user asked for fixes, apply them; otherwise ask. With code or data: apply all fixes in one batch, re-render, rerun the checks, show both versions with `python scripts/side_by_side.py <before.png> <after.png> -o <compare.png> --labels Before After`, and print absolute paths. With only an image, offer to rebuild the chart if the user can supply the data.
