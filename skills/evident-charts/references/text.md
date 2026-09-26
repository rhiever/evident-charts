# Text, labels, and layout

## Titles and subtitles

TI-1 [E] Title answers the question as asked, in its terms ("which regions drive X": contribution, not growth), with a claim the data supports for every item shown, not only a summary statistic; the subtitle qualifies. A premise the data contradicts gets the strongest true finding, never a bare negation. Contested or politically charged readings get a descriptive title and neutral subtitle. Break: reference or lookup charts meant for readers to find their own answer. check: default-title
TI-2 [E] The feature the title claims is the most salient thing on the chart (accented, annotated, sorted to stand out); if it is buried, redesign; words cannot rescue it. When another feature outshines the claim (a peak beats the endpoint change), add a labeled reference line or re-frame the title.
TI-3 [E] Title and annotations claim only what the data shows: no causal verbs unless the data isolates the cause, no intensifiers ("soared", "collapsed") the numbers do not justify. Opinion goes in the body text.
TI-4 [P] One complete sentence within the preset's two-line budget (`ev.fits_title`; `ev.fits_subtitle` for the subtitle), broken at a phrase boundary; one claim may carry one supporting number ("71%, three times the runner-up"). Plain words first; exact definitions go in the subtitle or notes. Break: hero cards take a kicker (LY-6); social thumbnails whose post text repeats the title may use a fragment. check: title-too-long
TI-5 [P] Title top-left, aligned to the canvas edge rather than centered over the axes, the largest and boldest text. Break: academic figures whose caption, or slides whose title placeholder, carries the title; never both.
TI-6 [P] Subtitle states what was measured: measure, units, geography, time span, adjustments (inflation, per capita, seasonal). Drop it only when the axes already say all of this.
TI-7 [P] State units where readers will find them: on every tick label, or in the axis title or subtitle; never on only some ticks. Omit self-evident axis titles (Year, category names); never show raw column names. check: missing-axis-label

## Annotation

AN-1 [E] Annotate the story, not the chart: each callout a phrase or short sentence on a feature the argument needs (peak, crossover, outlier, event); a rise or overtake story marks the crossings or rank changes it rests on. Default 1-3; more only when each carries a needed number, fewer on small screens (LY-2). Callout numbers follow H11.
AN-2 [E] Place text by what it says: the pattern in the title, numbers at the mark they describe (an average gets its own mark), context at its date, encoding notes ("dashed = forecast") at the relevant mark or axis. Break: on mobile, numbered notes may move below the chart.
AN-3 [P] Put each callout in empty space near its target; arrow tips land on the exact computed coordinate, no leader crosses an unrelated series, and stat notes go in an empty corner, not where a fit line ends. Place all callouts, render once, and fix every collision in one pass. check: text-overlap, text-on-line, text-on-area
AN-4 [T] Skip the arrowhead when the segment is too short to read as direction. Lollipop and dumbbell stems stop at the marker center.

## Labels and legends

LB-1 [P] Label series directly at the data, no legend: line names at each endpoint in the line's color, with a thin leader when nudged apart; bar and dot categories on the axis; stacked-area names inside the areas; scatter groups beside their cluster. Break: 5-6+ series whose labels collide get a compact horizontal key at the top, no box or title; maps and small multiples may share one color scale. check: legend-direct-label, text-overlap, text-on-area
LB-2 [P] In dense charts label only the story items and a few references; leave the rest unlabeled gray or give context lines one shared group label ("All other regions"; `ev.label_lines(group=...)`). Break: under ~15 points, label all of interest.
LB-3 [T] Each point label sits beside its own point, closer to it than to any other, in checked empty space: under ~20 labels place them by hand (`ev.label_points`), 20+ use a repel layout (libraries.md). check: text-overlap, label-ambiguous

## Value labels

VL-1 [P] Up to about 10-12 marks whose labels fit (a sorted bar chart, a few dots): value labels on the marks replace the value axis, its spine, and its gridlines. More marks: keep the value axis and label only the values VL-2 calls for. Never both. Axis-free dots and intervals keep a light zero or reference line as an anchor. Break: slide bars read as a table, each value quoted aloud, label every row that fits (presets.json `bar_rows`). check: value-labels-and-axis
VL-2 [P] Show the numbers the requested comparison needs: the highlighted mark, the peak discussed, reference lines, context marks when their labels fit, and values in line end labels when the question compares series. Context (n, size) goes in the subtitle or one callout; a text column (`ev.columns`) only when the comparison needs a value per row.

## Gridlines and axes

GR-1 [E] Light gridlines on the value axis only (a scatter has two), sparse, behind the data; none on the category axis, no minor grids. check: spines-gridlines
GR-2 [P] Spines left and bottom only, in the light spine token. check: spines-gridlines
GR-3 [P] All text horizontal: rotate the chart (horizontal bars), never the labels; thin or shorten time ticks ('05, Q1). check: tick-crowding
GR-4 [P] Bars get a visible zero baseline; categorical axes drop tick marks.

## Declutter

DC-1 [P] Remove ink that carries no information (backgrounds, borders, redundant axis titles, legend boxes, minor ticks, duplicated labels), never information the reader would want: light value gridlines, units, values that answer the question, needed annotations, the source line.
DC-2 [E] Never alter the marks: no rounded or pointed bar ends, shadows, gradient fills, perspective, or icons replacing bar ends.
DC-3 [E] Icons only when they are the data (one icon = one unit); no decorative imagery in the plot area.

## Highlighting and hierarchy

HI-1 [E] One chart, one message, emphasis per C2. Answer every part of the request: in one chart when an annotation or second measure can carry it, otherwise in aligned panels, each titled with its claim. When the data answers only part of the question, the subtitle or note says what it leaves out.
HI-2 [P] At most three text levels (plus LY-6 headline numbers): the title largest and bold, everything else regular, sized by presets.json roles and colored by palettes.json text tokens. Reading order: title, subtitle, highlighted data, annotations, source.
HI-3 [E] Default to a general audience: takeaway title, direct labels, plain units, one line explaining any unusual encoding (log scale, index = 100). Experts may get denser forms (SEL-4), never fewer units, sources, or scale disclosures.

## Sorting

SO-1 [P] Sort unordered categories by value or by the takeaway comparison; keep natural order for time and ordinal levels. Break: long lookup lists (alphabetical); a fixed order shared across charts in one piece.
SO-2 [E] Legend entries, keys, stack segments, end-of-line labels, and panels follow the visual order of the data.

## Number formatting

NF-1 [P] Round to the precision the story needs, with the same decimals across an axis or label set (12.8k, not 12,831).
NF-2 [P] Abbreviate large numbers (k, M, bn; words in titles for lay readers); never an offset or scientific-notation label ("1e6").
NF-3 [T] Dates look like dates: integer years without separators or decimals, abbreviated months, the year on the first label only.
Percent vs percentage points: H21.

## Source and notes

SRC-1 [P] Every chart carries a source line citing publisher and dataset ("Source: <publisher>, <dataset>"; codes or table numbers only when the data carries them; never a file name), plus a notes line for reader-facing facts the data or a verified source supports: definitions, exclusions, adjustments, provisional values, gaps, and data added from outside the user's files (a denominator, a deflator). Source bottom-left, any credit bottom-right; shorten rather than crowd. Identify an unnamed source (series IDs, column names, notes, domain knowledge), and state your confidence in the reply; if you cannot, ask. For what the files cannot confirm (a revision, a prior value), check the publisher's previous release or documentation, noted as added data; if unreachable, say so in the reply. check: missing-source, process-note
SRC-2 [P] The chart is a finished product: nothing addressed to the user goes on it ("confirm", "inferred", "add before publishing", TODOs, caveats about your own process, caveats you could not verify); those go in the reply. check: process-note

## Typography

TY-1 [T] One sans-serif family with lining, tabular figures; regular and bold only. House default: the font stack in the `assets/` style and theme files; a brand font overrides.
TY-2 [P] Text at least 12 px at the destination's final display width (11 px absolute), not at authoring size; the presets.json type scales meet this. check: small-text
TY-3 [P] Sentence case, no all-caps sentences, left-aligned text blocks.

## Layout

LY-1 [P] Author at the destination preset's canvas (presets.json). Rows past its `bar_rows` may take a taller canvas at the same width (`ev.figure(dest, rows=n)`), except on fixed-height presets (slide, social, social_portrait): show fewer rows (group the rest) or split across panels. The plot area itself, not only the canvas, stays between 3.5:1 and 1:2 (width:height; row charts may run taller); where a fixed-height title block squeezes it, cut title and subtitle to one line each (`ev.fits_title(text, dest, lines=1)`), or export the chart with `ev.titles(fig, None, source=...)` and put the title in the slide's title placeholder. Never rescale an image to a new destination, which changes every text-to-canvas ratio. Break: a long series whose detail needs the width (H6); small multiples and LY-6 cards. check: plot-aspect
LY-2 [P] When crowded, especially on small screens, cut before shrinking: fewer annotations (or numbered notes below), ticks, series, and shorter labels, horizontal bars or a taller aspect; shrink type last. Leave white space; the plot area, not text or empty margins, gets most of the canvas. check: plot-area-tiny, plot-area-underused
LY-3 [T] Reserve explicit margins and never crop flush to content (libraries.md); keep title and subtitle tight as one block with more space before the plot. check: text-clipped
LY-4 [P] Small multiples: one template, a shared scale (SCL-1), left-aligned panel titles, panels ordered by value, a common reference line (the national figure) in every panel, and labels or the shared key in the first panel only.
LY-5 [P] Panels with different units (replacing a dual axis, H3): stacked on a shared x, each with its own honest y scale and a panel title naming measure and unit, the story panel first, no legend.
LY-6 [T] When 1-2 numbers are the story (TAB-1) and the user asked for a chart, set them large under the title, each with a short context label, unless the chart already shows them. Any supporting visual stays small (a third of the canvas or less) and simple (one part-of-whole bar, a sparkline); a full chart competes with the number. One hook number (social cards): short kicker title, the number at `stats_size="hero"` with a one-line takeaway caption; no sentence title or subtitle repeating it.
