# Candidates: optional, when genuinely unsure

Use only when 2+ honest forms from choosing.md fit the takeaway and you cannot tell which reads faster.

## Generate

- 2-3 forms that differ in chart family or comparison layout; palette, font, or orientation variants do not count.
- Build each quickly with the real data and the same brief and title; signal, not polish.
- Save in the chart script's folder as `candidates/<slug>_A.png`, `_B.png`, print absolute paths, and view them together with `scripts/side_by_side.py`. Choose from the renders, never from code.

## Compare

Self-scores inflate, so compare pairs, quoting visible evidence (label, bar, region) for each question:

1. Message: judging only from the image, which delivers the takeaway faster?
2. Encoding: is the proving comparison on a common position scale (ENC-1), with color emphasizing what the question is about (C2)?
3. Expressiveness: does either imply something false (SEL-3)?
4. Audience: familiar, or teachable with one annotation (SEL-4)?
5. Fit: at destination size, do labels fit? Fix fit problems first; reject a form only for what survives the fix.
6. Integrity: honest baseline, scale, and aspect?

Ask again in swapped order; a winner needs both orders to agree. Otherwise break the tie by integrity, then message, familiarity, and fewer marks. `check_chart.py` failures override judgment. With three, compare the strongest two first.

## Continue

State the choice in one line: `Chose B (<form>) over A (<form>): <deciding evidence>.` If the loser showed something the reader needs (a number, a context group, a reference line), carry it into the winner. Polish only the winner.
