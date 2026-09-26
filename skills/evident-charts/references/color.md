# Color

Pick colors by data type, then verify. Hex values, token roles, ramps, and per-library names live in `assets/palettes.json`; refer to tokens by name.

## Palette type

C1 [P] Classify before picking colors: nominal categories get categorical hues; ordered magnitudes and ordered categories (age bands, tiers) get a sequential ramp; values around a meaningful midpoint (zero, target, average) get a diverging one. check: palette

## Highlight and categories

C2 [E] Highlight + gray when one element is the story: the `accent` token (vermillion) carries it and the rest is `context_gray`, context labels and values still shown (VL-2); `accent_alt` (blue) when warm would read as alarm; at most two accents. Benchmarks among components: CMP-4. Break: when the question is about the whole set ("every country fell"), its composition, or several live options, color meaningful groups (fossil vs clean) or every item within C3.
C3 [P] Categorical: the palettes.json slots in order, each within its use note; 4 hues by default, 7 at most; beyond that merge into "Other", highlight one, or facet. Break: 5-7 hues on a line chart only when every series is direct-labeled. check: too-many-series, palette
C4 [P] Override library default cycles (palettes.json `library_names`) with the house list; avoid ColorBrewer Set1, Set2, and Dark2 beyond 3 classes.
C5 [E] One color mapping per piece: a category keeps its color in every chart; maps in a series share classes and legend.
C6 [E] Use semantically resonant colors when a category has a strong association (party colors, blue for water, brand colors); otherwise color implies no meaning. Break: drop resonance when the pair fails CVD (red/green for loss/gain) and use blue/orange plus labels.
C7 [T] Match affect to subject: no cheerful palettes on grave topics; red does not mean bad in every culture.

## Sequential and diverging

C8 [E] Sequential ramps are monotonic in lightness, darker = more on light backgrounds; choose among the palettes.json sequential ramps by their use notes, and never reverse one for looks. Break: a domain convention (bathymetry), stated in the legend title. check: palette
C9 [T] Bars, dots, or lines colored by value on white use the trimmed ramp (`viridis.hex_marks`) or a mid-gray outline; heatmaps and choropleths keep the full ramp.
C10 [P] Diverging: a light, neutral midpoint exactly on the meaningful value, never the data mean; symmetric domain with arms of equal lightness (palettes.json `diverging`; per-library traps in libraries.md). check: palette
C11 [E] No rainbow colormaps in explanatory charts (palettes.json `sequential.banned`), nor Spectral on sequential data. check: rainbow-cmap

## CVD, contrast, grayscale

C12 [E] CVD-safe by construction: no pair that collapses under protan or deutan simulation may be the only distinction, and lightness differs too; simulate protan, deutan, and tritan before shipping. Break: red/green is acceptable when labels, position, or shape carry the same distinction and lightness differs. check: cvd, palette
C13 [E] Small marks (thin lines, small points, small text) need bigger color differences, especially in lightness: enlarge the marks or widen the difference, never separate them by hue alone at similar lightness. check: palette
C14 [P] Contrast against the background: text at least 4.5:1 (3:1 for large text, 18 pt or 14 pt bold); marks needed to read the point at least 3:1. Break: context gray may fall below 3:1 only when the focal data is accented and direct-labeled; sequential steps cannot all pass, so label them or ship the table. check: contrast, text-on-area, palette
C15 [P] The takeaway survives a grayscale render: accent and context differ in lightness, not only hue; slots that share lightness (vermillion and bluish green) pair only with direct labels. check: palette
C16 [T] Light background only. A required dark background gets its own palette (never an inversion) and a rerun of every check against it.

## Acting on color checks

For matplotlib, check_chart.py runs cvd, contrast, and text-on-area on the colors actually drawn. Other stacks: run check_palette.py on any color outside the house tokens. Fix every FAIL; resolve each WARN with direct labels or a data table, or say in one line why it is acceptable.
