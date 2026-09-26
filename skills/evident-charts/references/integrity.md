# Integrity, uncertainty, accessibility

## Scales and geometry

H1 [E] Bars and filled areas start at zero; if zero flattens the story, use dots or a line (axis-break glyphs do not make a truncated bar honest). Break: deviation bars from a labeled reference (target, average); a full-context panel plus a zoomed inset. check: bar-baseline
H2 [E] Lines and dots default to a range that fits the data and the effect that matters, never zoomed until noise looks like a trend. Zero baseline only for a ratio of levels ("doubled", "half"); record highs and index charts get a labeled reference line (previous high; base = 100) instead. No area fill on a truncated axis (H1).
H3 [P] No dual y-axes; use stacked panels sharing x (LY-5) or index the series to a common base (H4). Break: pure unit relabeling of one quantity (Celsius and Fahrenheit). check: dual-axis
H4 [P] Indexed series: name the base on the chart ("2017 average = 100"), label real units at key points (start, peaks, latest), and pick a base period typical for every series, never an unusual low or high; prefer an annual average over a single month.
H5 [E] Never invert a value axis; higher values go up. Break: ranks, labeled "Rank (1 = best)"; physical conventions such as depth. check: inverted-axis
H6 [E] Aspect ratio is a claim: shape the plot area so the slopes that matter are neither near-flat nor near-vertical (45 degrees is a heuristic, not a law); change the plot box and y-range, never the data.
H7 [E] Area scales by area, not radius or diameter; never scale 2D icons by height for a 1D quantity; no perceptual compensation of circle sizes. Break: data spanning 5+ orders of magnitude may use log-scaled area, labeled "log scale".
H8 [E] No 3D, perspective, or depth effects on 1D or 2D data. Break: genuinely 3D data, still preferring 2D projections or small multiples. check: 3d-axes
H9 [E] Linear scales by default; log only when multiplicative change is the story, then print "log scale" on the axis, use real-value ticks (1, 10, 100), and add one reading aid ("each gridline is 10x"). check: log-unlabeled
H10 [E] Binning is a choice: try 2-3 histogram bin widths and keep one that shows real features without inventing any; choropleths use quantile or unclassed schemes with the same breaks across a series of maps. Break: natural bins (integer counts, years); meaningful thresholds (poverty line).

## What the numbers mean

H11 [T] Compute every number shown or claimed (annotations, ratios, shares, "x times") with code on the data, never from the picture or memory. Recompute supplied shares, totals, and rates and assert they match; parts sum to the published total before any part-to-whole chart. Drop total, subtotal, and duplicate rows, and for one level of a hierarchy (states within regions) its parents and children; a remainder (rest of world) is the aggregate minus its listed members. Link rows that split one event (across regions or legs) before counting. When a part is negative or outside the official total, plot the parts, keep the official total as denominator, and name the exclusions in the note.
H12 [P] Before plotting series together, confirm scope and unit match (nominal vs real, counts vs per capita, seasonal adjustment, calendar vs fiscal year, revised vs preliminary, subset vs broader basket); if not, find matching series, drop one, or split into panels. A latest period only a narrower measure covers is compared within that measure.
H13 [P] Normalize before comparing units of different size: per capita, per area, per customer. Fetch a missing denominator from the data's publisher and name it in the note; failing that, chart the publisher's rates. When size or stakes still differ, weight by size or state sizes in the subtitle or one callout (VL-2). A "which drives X" question asks for contribution (share of X or of its change), not rates. Break: the absolute count is the claim.
H14 [P] Money across years: adjust for inflation when a deflator is supplied or requested, stating base year and deflator ("2025 dollars, CPI-U"); otherwise do not fetch one unasked, and say "not adjusted for inflation" in the subtitle. Break: the claim is explicitly nominal.
H15 [P] Default to the full series; if you crop, state start and end in the subtitle and check that the headline survives a longer window. Compare a partial last period like-for-like (year to date, trailing 12 months). Break: a definition change makes earlier data incomparable; say so in a note.
H16 [P] Series breaks: a one-period swing that reverses at the next reading often reflects a change in method, sample, or definition; flag it in a note and never rest the takeaway on that point. Two estimates for one year (old and new method): keep the newer-method row and note the break. An aggregate whose membership changes gets a note and a mark at the change. When levels break, compute growth from supplied flows, as publishers do.
H17 [P] Provisional, preliminary, projected, or partial-period values are drawn distinct from final ones (open marker, dashed connector from the last final point) and labeled with status and period ("2025 provisional, 12 months to Nov"); a single provisional point needs only the open marker and label.
H18 [P] Cumulative totals are not rates: they only rise and hide slowdowns, so claims about change plot the per-period value or rate. Break: the claim is about the total ("passed 1 million"). check: cumulative-as-rate
H19 [P] A subgroup compared with a broad aggregate mixes the group effect with composition (age, region): name what the comparison isolates, and add a like-for-like cut where it helps.
H20 [P] When one axis is a ratio containing the other (revenue per employee vs employees), part of the relationship is arithmetic: say so in the note and keep the wording associational, never causal.
H21 [P] A difference of two rates is in percentage points. Pick one convention (precise "pp" with signed ticks, or signed "%" loosely for lay readers) and hold it across chart and prose; in text give both rates and name the gap ("5.6% vs 4.2%").
H22 [P] Use the comparison and periods the publisher or field reports (same period last year, calendar months or quarters, named members the audience acts on, never folded into "Other") so readers can match the release. Pool, smooth, roll, rebase, or group only when the standard view would mislead (swings larger than the effect), named in the subtitle; trailing windows shift events later; never smooth a long trend whose claim is the multi-year change. Break: the audience asked for the transformed view.
H23 [P] Rates and averages carry their n (subtitle range, labels on the small ones); set a minimum n, state it, and never rank groups too small for the gaps shown.
H24 [P] Check which records a statistic silently drops or miscodes (averages skip missing values; 0, 888, 999, or blank may mean "not estimated"; trailing future-dated zero rows are unreleased periods; frozen carried-forward values are not new readings) and count them back in, drop them, or name them. Use the field's standard threshold (long-term unemployed: 27+ weeks) or state why not.

## Uncertainty

U1 [E] When the headline compares estimates (polls, surveys, samples, models, forecasts), show their uncertainty; otherwise add a note line ("Counts, not estimates" or "Survey estimates; margins of error not published"). Two independent estimates differ only if |a - b| > sqrt(moe_a^2 + moe_b^2) at the publisher's level; a record without MOEs is hedged ("lowest estimate on record").
U2 [E] Label the interval type on the chart ("90% margin of error", "95% confidence interval"); use the publisher's confidence level (ACS: 90%) for intervals and significance, else 95%; never unlabeled whiskers or bands.
U3 [E] Match the interval to the question: claims about individuals ("will this help me?") show outcome spread (prediction interval or raw data), not only a CI of the mean. Break: purely population-level claims.
U4 [E] Single-outcome predictions use frequency framing: a quantile dotplot (20-50 dots) or an "X in 100" icon array, not a density curve or bare interval.
U5 [E] Static distributions: gradient or violin, not bar plus error bar (DIST-1); 20-50 static draws stand in for hypothetical outcome plots. Animation needs a pause or static fallback and at most 3 flashes per second.
U6 [E] Forecasts: a fan chart of nested bands (50/80/95%) attached to observed history, lighter as it widens, the forecast line styled apart from observed data; no hard-edged cone. Break: one band labeled with its coverage for a single interval.
U7 [T] Draw intervals and bands lighter and thinner than the point estimate, but still visible in grayscale. Break: when uncertainty is the story ("a toss-up"), make it prominent.

## Accessibility

A1 [E] Alt text in this order: chart type and axes in one clause; key numbers (extremes, start and end); the pattern in plain words. Context and cause go in the caption. Break: short alt limits drop the first clause.
A2 [E] Alt text and captions describe the data, not the visuals ("rose from 12% to 31%", not "the blue line goes up"), restating the claim with its numbers.
A3 [P] Ship the data: a CSV or table with every published chart. Break: social posts link the dataset in the post or reply.
A4 [P] Color is never the only channel: direct-label, or add shape, dash, or position where labels cannot reach. Break: decorative or redundant color. check: cvd, legend-direct-label
Text size: TY-2. Contrast and CVD: C12-C14.
