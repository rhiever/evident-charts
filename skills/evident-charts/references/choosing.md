# Choosing the chart

Start with SEL-1, then the decision guide.

## Decision guide

Format: takeaway, data shape -> default | alternatives | avoid.

- Magnitude, 2-30 categories -> horizontal bar sorted by value, zero baseline | dot plot or lollipop (required when zero flattens the story); table if 4 or fewer values and exact numbers matter | pie, radar, bubble, 3D, alphabetical order
- Ranking, one time point -> sorted bar or dot plot with the items of interest highlighted; long lists show the top N, cutoff stated, plus a last "Other (N items)" bar on the same scale if the remainder matters | numbered table for league tables | unsorted bars, pie
- Rank by count and by rate -> two panels sharing rows | rate bars with count as the one context element | two unaligned rankings
- Change between exactly 2 points, many items -> dumbbell sorted by gap or end value | slope chart for about 10 or fewer items or when crossings matter; bump chart for many rank crossings; bar of the difference when the delta is the point | grouped bars with many pairs, two pies
- Change over time, 1-4 series -> line, direct-labeled | columns for about 8 or fewer discrete period totals; area for one series whose volume matters | a pie per year, stacked area when layers must be compared
- Change over time, 5+ series -> 1-3 highlighted lines over gray context, or small multiples on a shared y | heatmap (rows = series, x = time) when pattern beats exact values; horizon chart for experts | spaghetti with a many-color legend
- Part-to-whole, one whole, 6-10 parts or one dominant part -> sorted bar labeled with % | top parts plus "Other" in one stacked bar | pie, waffle that separates parts by gray shades
- Part-to-whole, one whole, 2-3 parts (max 5) -> single stacked bar, waffle, or one pie or donut | sorted bar labeled with % | pie with more than 5 slices, 3D or exploded pie
- Part-to-whole across groups or time -> 100% stacked bar with the key segment on the baseline, or small-multiple bars per component | line of each share over time | side-by-side pies, stacked area when middle layers matter
- Deviation from a reference -> diverging bar from zero or a labeled target | diverging stacked bar for Likert scales; surplus/deficit filled line | plain bars with the reference only in the text
- Distribution, one group -> histogram at a tested bin width | strip or dot plot for n under ~100; density curve | a single mean bar
- Distribution across 2-10 groups -> small n: strip or beeswarm, optional box overlay; large n: box, violin, or 2-3 overlaid densities | ridgeline for many groups; half-violin plus strip | bar of means with error bars
- Relationship, 2 quantitative -> scatterplot, plus a trend line when the trend is the point | hexbin or 2D density for large n; binned bars with n per bin for lay phone readers; connected scatter for two co-evolving series | dual-axis lines, bubble chart for a 2-variable story
- Pattern across 2 categorical dimensions -> heatmap with ordered rows and columns | small-multiple bars when exact values matter | heatmap when readers must compare precise values
- Where (geography is the story) -> choropleth of rates, or proportional symbols for counts | tile-grid map or cartogram; latitude or longitude as a scatter axis | raw-count choropleth, any map when geography is not the point
- Hierarchy with many leaves (hundreds) -> treemap | sorted bar of the top N plus "Other" | treemap under ~20 items, sunburst
- Flow between states -> Sankey | paired bars, slope chart | chord diagram for lay readers
- 1-2 headline numbers -> big-number text with context ("42%, up from 30%") | big numbers over a small, simple visual when a chart or image is required (LY-6) | a full-axis chart of two bars
- Precise lookup of many values -> sorted table, right-aligned numbers | table with inline bars or shading | a chart the reader decodes value by value
- Profile of 2-6 items on 3-12 attributes -> small-multiple bars or a dot matrix (attributes as rows, items as colored dots) | heatmap; parallel coordinates for experts | radar

## Channel ranking

Quantitative: position on a common scale > position on identical separate scales (small multiples) > length > angle, slope > area > volume, curvature > luminance, saturation.
Ordinal: position > luminance or saturation > ordered hue ramp > size. Nominal: position (grouping, facets) > hue > shape > texture.
Readers get summaries (mean, trend, outlier) at a glance but compare pairs slowly: make the takeaway a summary and annotate any pairwise comparison.

## LLM tendencies to distrust

Common wrong defaults: radar for comparison, treemap for hierarchy, sunburst or Sankey for looks; bars for trends, distributions, and relationships; stacked area for several series; library defaults taken as decisions (auto y-range, free facet scales, default bins, automatic legends, dataframe or alphabetical order, the default color cycle).

## Selection

SEL-1 [P] Before naming a chart, write the takeaway, the comparison that proves it (lookup, compare, rank, trend, distribution, relationship, part-to-whole, where), and the data shape (field types; counts of categories, series, and time points; n per group; counts vs rates vs shares). Break: exploratory or reference graphics with no single takeaway, labeled as such.
SEL-2 [P] Pick the chart family from takeaway type x data shape (decision guide), not from novelty, looks, or what was used last time; variety across a series of posts only breaks ties.
SEL-3 [P] Expressiveness: show every fact in the data and imply none that are absent: no order on nominal data, no continuity between discrete categories, no part-to-whole for values that do not sum to a whole.
SEL-4 [E] Lay audiences get familiar forms (bar, line, scatter, dot, table); an unfamiliar form (log axes, connected scatter, violin, horizon) only when it reveals the takeaway and one annotation can teach it. Break: expert or returning audiences; a form that is itself the story.

## Encoding

ENC-1 [E] Draw the title's measure as the marks, by position on a common aligned scale (a title about change plots change; text columns carry context only); send secondary variables to lower channels (Channel ranking). Break: a gestalt task ("where are the hot spots?") can use color; a simple fraction of one whole (PART-1).
ENC-2 [P] Prefer a dot plot or lollipop over bars when categories are many, when a non-zero range matters (H1), or when each category carries 2+ values. Break: short lay-audience series; counts where bar mass helps.
ENC-3 [E] No area (bubbles, treemap tiles, proportional symbols) for a comparison the reader must judge precisely; scale any area by H7. Break: order-of-magnitude spread; hierarchies with many leaves; counts on maps.
ENC-4 [E] No integral encodings of two quantities in one mark (width x height of a rectangle, two color dimensions); readers perceive the product. Break: the product is the quantity (Marimekko area = market size).
ENC-5 [P] One channel per data variable: remove each encoding in turn, and if the story survives, drop it. Break: a redundant channel for accessibility (shape backing color) or to emphasize the single takeaway.
ENC-6 [E] Cap encoded variables at 3-4, including x and y; facet, annotate, or move the rest to a second chart. Hue caps: C3.

## Comparison layout

CMP-1 [E] Put the values the reader must compare next to each other on one axis; decide what goes on x and what becomes color groups by the comparison that proves the takeaway.
CMP-2 [P] If the difference is the takeaway, plot the difference (delta bar, dumbbell, slope) instead of making readers subtract. Dumbbells: open marker = earlier, filled = later, a small two-item key, and a signed change column when values matter (VL-2). Break: levels matter as much as the gap; a dumbbell shows both.
CMP-3 [E] Overlay a few series for local comparisons; with 5+ series or comparisons spanning the chart, highlight 1-3 over gray context (C2) or use small multiples on a shared y. Break: mirrored small multiples for two-set comparisons. check: too-many-series
CMP-4 [T] A benchmark or aggregate shown among its components (All items, euro area, national average) is set apart: a dark gray bar (`text.axis` token) in the sorted order, or a labeled reference line (`ev.reference`); never styled as one more component.

## Time

TIME-1 [E] Draw a line only when x is ordered and continuous or evenly sampled; never connect nominal categories. Break: ordinal levels with a real sequence (age bands, Likert) when the trend across them is the point.
TIME-2 [E] About 8 or fewer discrete period totals compared one to one: columns. Break: trend emphasis across few points: line with markers.
TIME-3 [P] Time runs left to right on x with true spacing; show gaps in irregular sampling instead of equalizing them. Break: vertical timelines in mobile scroll stories.
TIME-4 [E] No stacked area when readers must compare any layer except the bottom one or the total. Break: total plus rough composition, 4 or fewer layers, key layer on the baseline. check: stacked-area
TIME-5 [E] Connected scatter only for two co-evolving series when the loop or path is the story, with the direction of time annotated.

## Part-to-whole

PART-1 [P] One pie or donut (equally good) only for 2-3 parts (max 5) of one whole when the story is a simple fraction; never 3D, exploded, or elliptical. Break: outlets where pies are the convention (elections, budgets), still 5 slices or fewer. check: pie-slices
PART-2 [E] Never compare parts across several pies; use a 100% stacked bar, grouped bars, or small-multiple bars.
PART-3 [E] Stacked bars: the most important segment sits on the common baseline, 5 or fewer segments, same order in every bar. Break: diverging stacked bars for Likert scales, centered on neutral.

## Distributions

DIST-1 [E] Compare group means with the observations (strip or beeswarm) and the mean marked, or a dot with an interval; never a bar of means (with or without error bars), and show the observations when n is small. Break: counts and totals, where bars are correct.
DIST-2 [E] For lay readers prefer strip, beeswarm, histogram, or density over box plots; a box plot gets the points overlaid or a one-time explanation. Break: technical audiences; many large-n groups.
DIST-3 [P] More than ~8 groups: ridgeline or small multiples ordered by median, not overlaid densities. Bin widths: H10.

## Relationships

REL-1 [E] Show a relationship between two quantitative variables with a scatterplot. Break: connected scatter for paired time series (TIME-5); binned plots for large n.
REL-2 [E] When the correlation or trend is the takeaway, add a fitted line or smoother and state r or the slope; readers underestimate moderate correlations. Break: very strong, obvious relationships.
REL-3 [P] Overplotted scatters (more than ~1-2k points): transparency, smaller marks, hexbin, or 2D density.
REL-4 [T] Correlation scatters: axes tightened to just past the data; a square plot box only when it costs no width (landscape canvases), never on portrait or narrow presets. check: plot-area-underused

## Maps

MAP-1 [P] Map only when the geographic pattern is the takeaway; for rank or magnitude use a sorted bar (optionally with a locator map), and when location stands in for a quantity (latitude), use it as a position axis. Break: readers must find their own region.
MAP-2 [P] Choropleths show rates or ratios (per capita, per area, %), never raw counts; show counts with proportional symbols (H13). Class breaks: H10.
MAP-3 [P] When region sizes mislead (large rural vs small dense units), use a tile-grid map or cartogram. Break: physical phenomena where land area is the point (weather, land use).

## Tables and numbers

TAB-1 [P] One or two headline numbers: big text with comparison context, not a chart. Break: a requested chart or an image-only format follows LY-6.
TAB-2 [E] Exact lookup across many items: a sorted table with right-aligned numbers, plus inline bars or shading if pattern matters too. Break: when the pattern is the takeaway, chart it and ship the table (A3).

## Scales

SCL-1 [P] Facets share one scale; if scales differ, say so on the chart. Break: shape-only stories (seasonality across very different magnitudes).
Baselines, y-range, log scales, and aspect ratio: H1, H2, H9, H6.
