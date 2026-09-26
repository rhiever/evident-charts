# Sources by rule ID

Citations behind each rule; read only when a user asks why or a critique must justify a call.
Marks: (2nd) confirmed only through a secondary source; (preprint) not peer reviewed; (book) paraphrased, not re-checked; [UNVERIFIED] could not be verified. "Olson skill" = Randy Olson's earlier beautiful-charts-with-ai skill (references/03-visualize.md, 04-evaluate.md). "house call" = the author's deliberate default, not a research finding.

Frequently cited
- C&M 1984: Cleveland & McGill 1984, JASA 79(387). https://doi.org/10.1080/01621459.1984.10478080
- Heer & Bostock 2010: Crowdsourcing graphical perception, CHI. https://doi.org/10.1145/1753326.1753357
- Talbot 2014: Talbot, Setlur & Anand 2014, Four experiments on the perception of bar charts, IEEE TVCG. https://doi.org/10.1109/TVCG.2014.2346320
- PSPI 2021: Franconeri, Padilla, Shah, Zacks & Hullman 2021, The science of visual data communication, Psychological Science in the Public Interest 22(3). https://doi.org/10.1177/15291006211051956
- FT: Financial Times Visual Vocabulary. https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
- data-to-viz: Holtz & Healy, From Data to Viz and its caveats pages. https://www.data-to-viz.com/ and https://www.data-to-viz.com/caveats.html
- Wilke: Wilke 2019, Fundamentals of Data Visualization, O'Reilly (chapter noted per rule). https://clauswilke.com/dataviz/
- Urban: Urban Institute Data Visualization Style Guide. https://urbaninstitute.github.io/graphics-styleguide/
- BBC: BBC bbplot R package (bbc_style, finalise_plot). https://github.com/bbc/bbplot
- Muth 2022 text: Datawrapper blog, What to consider when using text in data visualizations. https://www.datawrapper.de/blog/text-in-data-visualizations
- Muth 2022 fonts: Datawrapper blog, Which fonts to use for your charts and tables. https://www.datawrapper.de/blog/fonts-for-data-visualization
- Muth 2018: Datawrapper blog, What to consider when creating line charts. https://www.datawrapper.de/blog/line-charts
- Ajani 2022: Ajani et al. 2022, Declutter and focus, IEEE TVCG. https://doi.org/10.1109/TVCG.2021.3068337
- Correll 2020: Correll, Bertini & Franconeri 2020, Truncating the y-axis: threat or menace?, CHI. https://doi.org/10.1145/3313831.3376222
- Pandey 2015: Pandey et al. 2015, How deceptive are deceptive visualizations?, CHI. https://doi.org/10.1145/2702123.2702608
- GAF: UK Government Analysis Function, Data visualisation: colours (updated 12 Feb 2026). https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-colours-in-charts/
- WCAG: W3C WCAG 2.2 (SC 1.4.1, 1.4.3, 1.4.11, 2.3.1). https://www.w3.org/TR/WCAG22/
- Chartability: Elavsky, Bennett & Moritz 2022, CGF 41(3). https://doi.org/10.1111/cgf.14522 ; heuristics https://chartability.github.io/POUR-CAF/

## choosing.md

Decision guide: FT; data-to-viz; Wilke; Vessey 1991 (text/tables for lookup), Decision Sciences 22(2) https://doi.org/10.1111/j.1540-5915.1991.tb00344.x ; Albo et al. 2016 (radar least effective), IEEE TVCG https://doi.org/10.1109/TVCG.2015.2467322 ; Kong, Heer & Agrawala 2010 (treemaps only at high density), IEEE TVCG https://doi.org/10.1109/TVCG.2010.186 ; Heer, Kong & Agrawala 2009 (horizon), CHI https://doi.org/10.1145/1518701.1518897 ; slope and bump charts: FT (Ranking, Change over Time); count-and-rate, top-N plus "Other", and binned-bar entries: house call.
Channel ranking: C&M 1984; Heer & Bostock 2010; Talbot 2014; Mackinlay 1986, ACM TOG https://doi.org/10.1145/22949.22950 ; Munzner 2014, Visualization Analysis and Design https://www.cs.ubc.ca/~tmm/vadbook/ ; Kim & Heer 2018, CGF https://doi.org/10.1111/cgf.13409 ; Saket, Endert & Demiralp 2019, IEEE TVCG https://doi.org/10.1109/TVCG.2018.2829750 ; Correll et al. 2012 (color wins a gestalt task), CHI https://doi.org/10.1145/2207676.2208556 ; Szafir et al. 2016 (ensemble tasks), Journal of Vision https://doi.org/10.1167/16.5.11 ; PSPI 2021.
LLM tendencies: Wang, Gordon, Battle & Heer 2024, DracoGPT, arXiv 2408.06845 (IEEE VIS 2024) https://arxiv.org/abs/2408.06845 ; Salim & Mueller 2026 (radar ranked first for comparison; small GPT models only), arXiv 2607.02455 (preprint) https://arxiv.org/abs/2607.02455 ; Luo et al. 2025, nvBench 2.0, arXiv 2503.12880 (preprint) https://arxiv.org/abs/2503.12880 ; Ansari, Bansal & Zhou 2026, ChartDesign, arXiv 2605.16274 (preprint) https://arxiv.org/abs/2605.16274 ; library defaults as house call: practitioner observation, no controlled study.

SEL-1: Munzner 2009 https://doi.org/10.1109/TVCG.2009.111 ; Munzner 2014.
SEL-2: FT; data-to-viz. Variety as tiebreaker: house call workflow.
SEL-3: Mackinlay 1986 https://doi.org/10.1145/22949.22950 ; Munzner 2014.
SEL-4: PSPI 2021 (37% of US adults misread scatterplots, citing Pew 2015 (2nd)); Haroz, Kosara & Franconeri 2016, connected scatterplot, IEEE TVCG https://doi.org/10.1109/TVCG.2015.2502587
ENC-1: C&M 1984; Heer & Bostock 2010; Talbot 2014; Mackinlay 1986; Saket et al. 2019 https://doi.org/10.1109/TVCG.2018.2829750 ; Kim & Heer 2018 https://doi.org/10.1111/cgf.13409 ; task-dependent ranking and gestalt escape: Correll et al. 2012 (see Channel ranking). Measure drawn as marks: house call.
ENC-2: Cleveland 1984, dot charts, The American Statistician https://doi.org/10.1080/00031305.1984.10483224 ; Correll 2020; FT.
ENC-3: C&M 1984; Heer & Bostock 2010; Kong, Heer & Agrawala 2010 https://doi.org/10.1109/TVCG.2010.186
ENC-4: PSPI 2021 (integral vs separable dimensions).
ENC-5: Olson skill (one encoding per data dimension); PSPI 2021 (redundant coding for color blindness).
ENC-6: PSPI 2021 (a comparison spans about 4 variables, citing Halford et al. 2007 (2nd)); Kim & Heer 2018; cap value from house call; bubble charts with 4-6 variables: Olson skill.
CMP-1: C&M 1984; Talbot 2014; Shah & Freedman 2011, Topics in Cognitive Science https://doi.org/10.1111/j.1756-8765.2009.01066.x ; PSPI 2021.
CMP-2: PSPI 2021 ("shortcut comparisons by adding direct depictions of the deltas"); FT. Dumbbell marker and key conventions: house call.
CMP-3: Javed, McDonnel & Elmqvist 2010, IEEE TVCG https://doi.org/10.1109/TVCG.2010.162 ; Ondov et al. 2019, IEEE TVCG https://doi.org/10.1109/TVCG.2018.2864884 ; Jardine et al. 2020, IEEE TVCG https://doi.org/10.1109/TVCG.2019.2934786 ; PSPI 2021; data-to-viz (spaghetti chart). The 5+ series threshold is practitioner judgment.
CMP-4: house call.
TIME-1: Zacks & Tversky 1999, Memory & Cognition https://doi.org/10.3758/BF03201236 ; Shah & Freedman 2011.
TIME-2: Zacks & Tversky 1999; FT.
TIME-3: FT; data-to-viz.
TIME-4: C&M 1984; Talbot 2014; data-to-viz.
TIME-5: Haroz, Kosara & Franconeri 2016 https://doi.org/10.1109/TVCG.2015.2502587
PART-1: Spence & Lewandowsky 1991, Applied Cognitive Psychology https://doi.org/10.1002/acp.2350050106 ; Skau & Kosara 2016 (donut as accurate as pie), CGF https://doi.org/10.1111/cgf.12888 ; Kosara & Skau 2016 (pie variants raise error), EuroVis short https://doi.org/10.2312/eurovisshort.20161167 ; Kosara 2019, IEEE VIS short https://doi.org/10.1109/VISUAL.2019.8933547 ; Wilke ch. 10 https://clauswilke.com/dataviz/visualizing-proportions.html ; slice cap from house call. Evidence on pies conflicts; see C&M 1984.
PART-2: C&M 1984; Wilke ch. 10.
PART-3: C&M 1984; Talbot 2014; Indratmo et al. 2018, Visual Informatics https://doi.org/10.1016/j.visinf.2018.09.002
DIST-1: Newman & Scholl 2012, Psychonomic Bulletin & Review https://doi.org/10.3758/s13423-012-0247-5 ; Correll & Gleicher 2014, IEEE TVCG https://doi.org/10.1109/TVCG.2014.2346298 ; Weissgerber et al. 2015, PLOS Biology https://doi.org/10.1371/journal.pbio.1002128 ; Kerns & Wilmer 2021, Bar-Tip Limit error, Journal of Vision https://doi.org/10.1167/jov.21.12.17
DIST-2: Lem et al. 2013, Learning and Instruction https://doi.org/10.1016/j.learninstruc.2013.01.001 ; Lem et al. 2014 (experts too), Psychologica Belgica https://doi.org/10.5334/pb.az ; Matejka & Fitzmaurice 2017, CHI https://doi.org/10.1145/3025453.3025912
DIST-3: data-to-viz (too many distributions).
REL-1: Rensink & Baldridge 2010, CGF https://doi.org/10.1111/j.1467-8659.2009.01694.x ; Harrison et al. 2014, IEEE TVCG https://doi.org/10.1109/TVCG.2014.2346979 ; Kay & Heer 2016, IEEE TVCG https://doi.org/10.1109/TVCG.2015.2467671
REL-2: Rensink & Baldridge 2010; Harrison et al. 2014.
REL-3: data-to-viz (overplotting).
REL-4: Olson skill (relational charts); full width on narrow canvases: house call.
MAP-1: FT (Spatial); Datawrapper Academy, choropleth maps https://academy.datawrapper.de/article/134-what-to-consider-when-creating-choropleth-maps ; Olson skill (latitude as an axis).
MAP-2: FT (choropleth for rate, proportional symbol for count); Datawrapper Academy.
MAP-3: FT (cartograms); Datawrapper Academy.
TAB-1: Vessey 1991 https://doi.org/10.1111/j.1540-5915.1991.tb00344.x ; chart-requested break: house call.
TAB-2: Vessey 1991; Saket et al. 2019.
SCL-1: Ondov et al. 2019; Javed et al. 2010.

## text.md

presets.json and the 12 px floor: house call; Urban (web sizes); Muth 2022 fonts (under 12 px likely too small); Apple Human Interface Guidelines, typography, 11 pt minimum (2nd) https://developer.apple.com/design/human-interface-guidelines/typography ; Microsoft Support, accessible PowerPoint, 18 pt (2nd) https://support.microsoft.com/en-us/accessibility/powerpoint/make-your-powerpoint-presentations-accessible-to-people-with-disabilities ; social image sizes from third-party aggregators (2nd), re-verify at publish time.

TI-1: Borkin et al. 2016, Beyond memorability, IEEE TVCG https://doi.org/10.1109/TVCG.2015.2467732 (fixation details 2nd) ; Kong, Liu & Karahalios 2018, CHI https://doi.org/10.1145/3173574.3174012 ; Kong, Liu & Karahalios 2019, CHI https://doi.org/10.1145/3290605.3300576 ; Wanzer et al. 2021 (lower effort, no accuracy gain), Evaluation and Program Planning https://doi.org/10.1016/j.evalprogplan.2020.101896 ; Ajani 2022; Urban; Wilke ch. 22. Contested-topic fallback: house call, from Kong 2018 and 2019. Answering the question as asked with qualifications in the subtitle, and holding for every item shown: house call.
TI-2: Kim, Setlur & Agrawala 2021, CHI https://doi.org/10.1145/3411764.3445443 ; Ajani 2022.
TI-3: Kong et al. 2018, 2019; Stokes, Bearfield & Hearst 2024, IEEE TVCG https://doi.org/10.1109/TVCG.2023.3338451 ; Hullman & Diakopoulos 2011, Visualization rhetoric, IEEE TVCG https://doi.org/10.1109/TVCG.2011.255 ; neutral labels when the data does not isolate a cause: Olson skill (numerical audit).
TI-4: Lim, Pandey, Wang & Quadri 2026 (longer titles improved agreement), arXiv 2609.17485 (preprint) https://arxiv.org/abs/2609.17485 ; Muth 2022 text; Wilke ch. 29; character budget per preset and the hero-card kicker: house call.
TI-5: BBC; Muth 2022 text; Wilke ch. 22 (one title, in the image or the caption). Slide title placeholder as the caption: house call.
TI-6: Urban; Muth 2022 text; BBC.
TI-7: Wilke ch. 22; BBC (no axis titles by default); Urban; axis-title policy from house call; units on ticks: Muth 2022 text; all ticks or none: house call.
AN-1: Stokes, Setlur, Cogley, Satyanarayan & Hearst 2022, IEEE TVCG https://doi.org/10.1109/TVCG.2022.3209383 ; Stokes & Hearst 2022, arXiv 2209.10789 (workshop) https://arxiv.org/abs/2209.10789 ; Ajani 2022; Segel & Heer 2010, IEEE TVCG https://doi.org/10.1109/TVCG.2010.179 ; Ren et al. 2017, ChartAccent, PacificVis https://doi.org/10.1109/PACIFICVIS.2017.8031599 ; default budget, not a cap, and marking crossings in overtake stories: house call.
AN-2: Stokes et al. 2022 (Guideline 3); numbers at the mark they describe: house call.
AN-3: Olson skill (annotation positioning; batch the annotation review).
AN-4: Olson skill (arrowhead gating, line caps).
LB-1: Wilke ch. 20; Urban; Muth 2018; Muth 2022 text; PSPI 2021; mechanism: Chandler & Sweller 1991, Cognition and Instruction https://doi.org/10.1207/s1532690xci0804_2 ; Ginns 2006 meta-analysis, Learning and Instruction https://doi.org/10.1016/j.learninstruc.2006.10.001 ; Carpenter & Shah 1998, JEP: Applied https://doi.org/10.1037/1076-898X.4.2.75 ; Huestegge & Philipp 2011 (2nd), Attention, Perception & Psychophysics https://doi.org/10.3758/s13414-011-0155-1 ; compact key: Riechelmann & Huestegge 2018 https://doi.org/10.3758/s13414-018-1484-0 ; BBC (legend top). No head-to-head experiment of direct labels vs legend exists. Leaders for nudged end labels: house call.
LB-2: Leo 2019, Mistakes, we've drawn a few, The Economist on Medium https://medium.economist.com/mistakes-weve-drawn-a-few-8cdd8a42d368
LB-3: Olson skill (adjustText with seed search).
VL-1: Urban (omit y-axis labels and gridlines with data labels); Wilke ch. 6; Ajani 2022; Borkin et al. 2016 (redundancy helps); threshold (about 10-12 marks), the slide-table break, and anchoring axis-free dots: house call.
VL-2: Muth 2018; Knaflic 2015, Storytelling with Data (book). Context values, change column, end-label values, and context columns only when needed: house call.
GR-1: Heer & Bostock 2010 (gridlines improved accuracy; alpha 0.2 safe; dense grids on small charts hurt); Bartram & Stone 2011, Whisper, don't scream, IEEE TVCG https://doi.org/10.1109/TVCG.2010.237 ; Wilke ch. 23; BBC.
GR-2: BBC; Urban; Tufte 1983/2001, The Visual Display of Quantitative Information (book); Wilke ch. 23.
GR-3: Wilke ch. 6.
GR-4: Urban; BBC R cookbook (2nd) https://bbc.github.io/rcookbook/
DC-1: Ajani 2022; Tufte 1983/2001 (book); Wilke ch. 23; Healy 2018, Data Visualization ch. 1 https://socviz.co/01-look-at-data.html ; counter-evidence: Bateman et al. 2010, CHI https://doi.org/10.1145/1753326.1753716 ; Borkin et al. 2013, IEEE TVCG https://doi.org/10.1109/TVCG.2013.234 ; Inbar, Tractinsky & Meyer 2007 (2nd) https://doi.org/10.1145/1362550.1362587 ; Kosara 2016, BELIV https://doi.org/10.1145/2993901.2993909 ; Parsons & Shukla 2020, arXiv 2009.02634 https://arxiv.org/abs/2009.02634 ; rubric framing from house call.
DC-2: Skau, Harrison & Kosara 2015, CGF https://doi.org/10.1111/cgf.12634 ; Borgo et al. 2012, IEEE TVCG https://doi.org/10.1109/TVCG.2012.197
DC-3: Haroz, Kosara & Franconeri 2015, ISOTYPE, CHI https://doi.org/10.1145/2702123.2702275 ; Burns et al. 2022, IEEE TVCG https://doi.org/10.1109/TVCG.2021.3092680
HI-1: Ajani 2022; Healey & Enns 2012, IEEE TVCG https://doi.org/10.1109/TVCG.2011.127 ; PSPI 2021; Muth 2018; Wilke ch. 29; Leo 2019. Answering every part of the request, and saying what the data leaves out: house call.
HI-2: Muth 2022 text; Urban; BBC; Borkin et al. 2016; Carpenter & Shah 1998; Segel & Heer 2010.
HI-3: Shah & Freedman 2011; Galesic & Garcia-Retamero 2011, Graph literacy, Medical Decision Making https://doi.org/10.1177/0272989X10373805 ; PSPI 2021; Lee, Kim & Kwon 2017, VLAT, IEEE TVCG https://doi.org/10.1109/TVCG.2016.2598920 ; Peck, Ayuso & El-Etr 2019, CHI https://doi.org/10.1145/3290605.3300474
SO-1: Wilke ch. 6; Urban; FT; Bell 2018, Pew small multiples https://www.pewresearch.org/decoded/2018/12/20/how-pew-research-center-uses-small-multiple-charts/ ; data-to-viz (order your data).
SO-2: Huestegge & Philipp 2011 (2nd); Riechelmann & Huestegge 2018; Wilke ch. 20; Urban.
NF-1: Muth 2022 text; Few 2012, Show Me the Numbers (book).
NF-2: Muth 2022 text; newsroom house styles (Economist, FT).
NF-3: Convention.
SRC-1: Urban (source and notes lines); BBC (finalise_plot); Olson skill (footer). Dataset codes only when present, notes limited to supported facts, naming added data, and prior-release checks: house call.
SRC-2: house call (finished charts carry no process notes).
TY-1: Muth 2022 fonts; Urban; house font from house call. Sans vs serif legibility at chart sizes is untested.
TY-2: Wilke ch. 24; Urban; Muth 2022 fonts; Chartability (small text); GAF; Apple HIG (2nd); Microsoft (2nd).
TY-3: Muth 2022 text.
LY-1: Urban (fixed widths); BBC (640 x 450 px). Plot-area shape: Tufte 1983, The Visual Display of Quantitative Information (horizontal, about 50% wider than tall, unless the data suggest a shape) (2nd: https://guypursey.com/blog/202001041530-tufte-principles-visual-display-quantitative-information ); Wilke ch. 3 (aspect ratio sets which differences show) https://clauswilke.com/dataviz/coordinate-systems-axes.html ; banking is data-dependent, not a fixed ratio: Cleveland, McGill & McGill 1988; Heer & Agrawala 2006 (wide banked views for fine-scale detail); Talbot, Gerth & Hanrahan 2012 (DOIs under H6); Wang et al. 2018, IEEE TVCG https://doi.org/10.1109/TVCG.2017.2787113 ; data.europa.eu data visualisation guide, line chart aspect ratios https://data.europa.eu/apps/data-visualisation-guide/line-chart-aspect-ratios ; bar-chart height follows bar count: Datawrapper Academy https://www.datawrapper.de/academy/i-cant-customize-the-height-of-the-visualization . bar_rows limits, the 3.5:1 to 1:2 band, and the slide title-placeholder escape: house call.
LY-2: Muth 2022 text; Kim, Moritz & Hullman 2021, CGF https://doi.org/10.1111/cgf.14321 ; Hoffswell, Li & Liu 2020, CHI https://doi.org/10.1145/3313831.3376777 White space for the plot area: house call.
LY-3: Olson skill (explicit margins, no tight bbox).
LY-4: Bell 2018; Wilke ch. 21; Tufte 1990, Envisioning Information (book); BBC.
LY-5: Few 2008 on dual axes (perceptualedge.com); Datawrapper, dual-axis alternatives https://www.datawrapper.de/blog/dualaxis ; panel layout is a house call.
LY-6: house call (big numbers over a small, simple visual; one hook number: kicker, hero number, one-line caption).

## color.md

Tokens: house call; Okabe & Ito, Color Universal Design https://jfly.uni-koeln.de/color/ ; viridis (CC0) https://github.com/BIDS/colormap ; ColorBrewer schemes and colorblind flags (Apache-2.0) https://github.com/axismaps/colorbrewer
check_palette metrics: Sharma, Wu & Dalal 2005, CIEDE2000, Color Research & Application https://doi.org/10.1002/col.20070 ; Machado, Oliveira & Fernandes 2009 https://doi.org/10.1109/TVCG.2009.113 ; Ottosson 2020, OKLab (blog) https://bottosson.github.io/posts/oklab/ ; Kovesi 2015, arXiv 1509.03700 https://arxiv.org/abs/1509.03700 . All dE thresholds are calibrations, not findings.

C1: Harrower & Brewer 2003, The Cartographic Journal https://doi.org/10.1179/000870403235002042 ; Brewer, Hatchard & Harrower 2003, CaGIS https://doi.org/10.1559/152304003100010929
C2: Healey & Enns 2012 https://doi.org/10.1109/TVCG.2011.127 ; GAF (focus charts); Ajani 2022. The specific recipe is taste. Group coloring when the whole composition is the question: house call.
C3: GAF (4 as best practice); Okabe & Ito; Wong 2011, Nature Methods https://doi.org/10.1038/nmeth.1618 ; Wilke ch. 19 https://clauswilke.com/dataviz/color-pitfalls.html ; Haroz & Whitney 2012, IEEE TVCG https://doi.org/10.1109/TVCG.2012.233 ; Kim & Heer 2018; Healey 1996, IEEE Visualization https://doi.org/10.1109/VISUAL.1996.568118 (the "about 7 colors" figure is [UNVERIFIED]). Caps 4 and 7 are conventions set in house call.
C4: ColorBrewer flags (Dark2, Set2 safe only at 3 classes; Set1 "maybe"); library sources checked 2026-09-25 (matplotlib, Vega, Vega-Lite, plotly.py). Alternate cycle: Petroff 2021, arXiv 2107.02270 https://arxiv.org/abs/2107.02270
C5: Brewer & Pickle 2002 (matched legends about 28% more accurate), Annals of the AAG https://doi.org/10.1111/1467-8306.00310
C6: Lin et al. 2013, CGF https://doi.org/10.1111/cgf.12127
C7: Bartram, Patra & Stone 2017, CHI https://doi.org/10.1145/3025453.3026041 . Cultural meaning is convention.
C8: Liu & Heer 2018, CHI https://doi.org/10.1145/3173574.3174172 ; Nuñez, Anderton & Renslow 2018 (cividis), PLOS ONE https://doi.org/10.1371/journal.pone.0199239 ; Crameri, Shephard & Heron 2020, Nature Communications https://doi.org/10.1038/s41467-020-19160-7 ; Schloss et al. 2019 (dark is more), IEEE TVCG https://doi.org/10.1109/TVCG.2018.2865147
C9: Taste; contrast of viridis and Blues light ends computed with the WCAG formula in research file 02.
C10: Brewer et al. 2003; Moreland 2009, ISVC https://doi.org/10.1007/978-3-642-10520-3_9 ; per-arm stretching verified in library sources (research file 02).
C11: Liu & Heer 2018; Borland & Taylor 2007, IEEE CG&A https://doi.org/10.1109/MCG.2007.323435 ; Crameri et al. 2020. Dissent: Reda, Nalawade & Ansah-Koi 2018, CHI https://doi.org/10.1145/3173574.3173846 ; Reda & Szafir 2021, IEEE TVCG https://doi.org/10.1109/TVCG.2020.3030439 . Outright ban in explanatory mode is a house call.
C12: Birch 2012 (about 8% of men, 0.4% of women of European descent), JOSA A https://doi.org/10.1364/JOSAA.29.000313 ; Machado et al. 2009 https://doi.org/10.1109/TVCG.2009.113 ; Okabe & Ito; Wong 2011.
C13: Szafir 2018, IEEE TVCG https://doi.org/10.1109/TVCG.2017.2744359 ; Hye, McNutt & Isaacs 2026 (replication), arXiv 2608.24789 (preprint) https://arxiv.org/abs/2608.24789 ; Stone, Szafir & Setlur 2014, Color and Imaging Conference https://doi.org/10.2352/CIC.2014.22.1.art00045
C14: WCAG SC 1.4.3 and 1.4.11; Chartability (low contrast); GAF (sequential palettes cannot all meet 3:1). Context-gray escape from house call.
C15: GAF; Tol, Colour schemes https://sronpersonalpages.nl/~pault/
C16: Schloss et al. 2019; WCAG. Scope from house call.

## integrity.md

H1: Pandey 2015; Correll 2020; Yang, Vargas-Restrepo, Stanley & Marsh 2021 (effect persists after warnings), JARMAC https://doi.org/10.1016/j.jarmac.2020.10.002 ; inset escape: Isenberg et al. 2011, dual-scale charts, IEEE TVCG https://doi.org/10.1109/TVCG.2011.160
H2: Correll 2020 (choose scale from meaningful effect size); Witt 2019 (about 1.5 SD range), Meta-Psychology https://doi.org/10.15626/MP.2018.895 ; context: Long & Kay 2024, CHI https://doi.org/10.1145/3613904.3642102 ; Driessen et al. 2022, PLOS ONE https://doi.org/10.1371/journal.pone.0265823 . Zero only for ratio claims, and reference lines for records and indexes: house call.
H3: Few 2008, Dual-scaled axes in graphs https://www.perceptualedge.com/articles/visual_business_intelligence/dual-scaled_axes.pdf ; Lo et al. 2022, Misinformed by visualization, CGF https://doi.org/10.1111/cgf.14559 ; data-to-viz (dual axes); Olson skill. No controlled experiment on dual y-axes exists.
H4: Datawrapper, dual-axis alternatives https://www.datawrapper.de/blog/dualaxis ; base-period and rate cautions are a house call.
H5: Pandey 2015 (79% misread an inverted axis); Woodin, Winter & Padilla 2022, IEEE TVCG https://doi.org/10.1109/TVCG.2021.3088343
H6: Cleveland, McGill & McGill 1988, JASA https://doi.org/10.1080/01621459.1988.10478598 ; Heer & Agrawala 2006, IEEE TVCG https://doi.org/10.1109/TVCG.2006.163 ; Pandey 2015 (aspect distortion had the largest effect); against 45 degrees as optimal: Talbot, Gerth & Hanrahan 2012, IEEE TVCG https://doi.org/10.1109/TVCG.2012.196 ; Talbot, Gerth & Hanrahan 2011, IEEE TVCG https://doi.org/10.1109/TVCG.2011.167 ; Healy 2018 ch. 1.
H7: Flannery 1971, The Canadian Cartographer https://doi.org/10.3138/J647-1776-745H-3667 (the 0.57 compensation exponent is [UNVERIFIED]); C&M 1984; Heer & Bostock 2010; Pandey 2015; log-area escape from Olson skill.
H8: Siegrist 1996, Behaviour & IT https://doi.org/10.1080/014492996120300 ; Fischer 2000, Applied Cognitive Psychology https://doi.org/10.1002/(SICI)1099-0720(200003/04)14:2<151::AID-ACP629>3.0.CO;2-Z ; Zacks et al. 1998, JEP: Applied https://doi.org/10.1037/1076-898X.4.2.119
H9: Menge et al. 2018 (ecologists 93% correct linear vs 56% log-log), Nature Ecology & Evolution https://doi.org/10.1038/s41559-018-0610-7 ; Romano et al. 2020, Health Economics https://doi.org/10.1002/hec.4143 ; attitudes unaffected: Sevi et al. 2020, Canadian Journal of Political Science https://doi.org/10.1017/S000842392000030X
H10: Correll, Li, Kindlmann & Scheidegger 2019 (bins can hide flaws), IEEE TVCG https://doi.org/10.1109/TVCG.2018.2864907 ; Brewer & Pickle 2002 (quantiles best for general map reading); data-to-viz (histogram bin size).
H11: Olson skill (numerical audit). Negative or out-of-total parts (plot parts, keep the official denominator) one hierarchy level at a time, parts-sum and remainder checks, and linking split events: house call.
H12: Olson skill (unit comparability check); narrower-measure comparison: house call.
H13: FT; Datawrapper Academy; Olson skill (unit comparability). Cartographic consensus. Size weighting, sizes in the subtitle, and denominators from the same publisher: house call. Contribution vs rate: BEA contributions-to-growth tables.
H14: Olson skill; statistical-agency practice. "Not adjusted" subtitle instead of an unrequested deflator: house call.
H15: Cairo 2019, How Charts Lie (book, not independently checked); like-for-like partial periods: agency year-to-date practice.
H16: statistical-agency practice on series breaks (e.g., BLS and Census notes on methodology changes); changing-composition aggregates: statistical-agency practice (e.g., Eurostat euro area series in evolving composition); wording is a house call. Duplicate estimates: U.S. Census Bureau CPS ASEC income reports (two estimates for 2013 and 2017); keeping the newer method: house call. Growth from flows when levels break: agency practice (e.g., Federal Reserve Z.1 and ECB monetary statistics compute growth from transactions).
H17: statistical-agency practice for provisional and projected data (e.g., CDC VSRR, BLS preliminary estimates); drawing convention is a house call. Single-point simplification: house call.
H18: Practitioner consensus from COVID-19 reporting; no single citable source.
H19: Olson skill (confound check).
H20: arithmetic (spurious correlation of ratios with a shared term): Pearson 1897, Proc. Royal Society of London 60:489-498 https://doi.org/10.1098/rspl.1896.0076 ; wording is a house call.
H21: Olson skill (difference-of-rates axes).
H22: agency practice (Census and BLS same-period-last-year headlines; ONS three-month averages for noisy months); transforms only when the standard view misleads: house call; trailing-window lag: arithmetic.
H23: Wainer 2007, The most dangerous equation (small samples dominate extremes), American Scientist https://www.americanscientist.org/article/the-most-dangerous-equation ; statistical-agency flags for small-n rates (e.g., NCHS, fewer than 20 events).
H24: U.S. Bureau of Labor Statistics, Current Population Survey definitions (long-term unemployed: 27+ weeks); dropped-record, sentinel-code, unreleased-period, and carried-forward checks: house call.
U1: Hullman 2020, Why authors don't visualize uncertainty (3% of inference charts showed it), IEEE TVCG https://doi.org/10.1109/TVCG.2019.2934287 ; mandatory-when-comparing policy from house call. Difference test from published MOEs: U.S. Census Bureau 2020, Understanding and Using American Community Survey Data https://www.census.gov/programs-surveys/acs/library/handbooks/general.html ; hedged records: house call.
U2: Belia, Fidler, Williams & Cumming 2005, Psychological Methods https://doi.org/10.1037/1082-989X.10.4.389 ; Cumming & Finch 2005, American Psychologist https://doi.org/10.1037/0003-066X.60.2.170 ; publisher's level: U.S. Census Bureau 2020 (U1).
U3: Hofman, Goldstein & Hullman 2020, CHI https://doi.org/10.1145/3313831.3376454
U4: Kay, Kola, Hullman & Munson 2016, CHI https://doi.org/10.1145/2858036.2858558 ; Fernandes et al. 2018, CHI https://doi.org/10.1145/3173574.3173718
U5: Correll & Gleicher 2014; Hullman, Resnick & Adar 2015, PLOS ONE https://doi.org/10.1371/journal.pone.0142444 ; Kale et al. 2019, IEEE TVCG https://doi.org/10.1109/TVCG.2018.2864909 ; Hofman et al. 2020; animation limits: WCAG SC 2.3.1, Chartability (seizure risk).
U6: Padilla, Ruginski & Creem-Regehr 2017, Cognitive Research: Principles and Implications https://doi.org/10.1186/s41235-017-0076-1 ; Britton, Fisher & Whitley 1998, Bank of England Quarterly Bulletin https://www.bankofengland.co.uk/-/media/boe/files/quarterly-bulletin/1998/the-inflation-report-projections-understanding-the-fan-chart.pdf ; Spiegelhalter, Pearson & Short 2011, Science https://doi.org/10.1126/science.1191181
U7: Taste, informed by Hullman 2020 (fear of overwhelming viewers drives omission).
A1: Lundgard & Satyanarayan 2022, four-level model, IEEE TVCG https://doi.org/10.1109/TVCG.2021.3114770
A2: Jung et al. 2022, IEEE TVCG https://doi.org/10.1109/TVCG.2021.3114846 ; Kim, Setlur & Agrawala 2021.
A3: Chartability (no table).
A4: WCAG SC 1.4.1; Chartability (color used alone).

## Workflow (SKILL.md, candidates.md, critique.md review loop; no rule ID)

Ask at most 2 targeted questions: Meng et al. 2026, DV-World (asking helped 9 of 10 models; quality beats quantity), arXiv 2604.25914 (preprint) https://arxiv.org/abs/2604.25914 ; Luo et al. 2025, nvBench 2.0.
Render 2-3 genuinely different candidates, only when unsure (house call from blind comparisons with a no-skill baseline, which also set analysis first): Dibia 2023, LIDA, arXiv 2303.02927 https://arxiv.org/abs/2303.02927 ; Kim, Ahn, Myers & Bach 2023, arXiv 2310.09617 https://arxiv.org/abs/2310.09617 . No controlled study of best-of-N chart selection exists.
Look at the pixels: Yang et al. 2024, MatPlotAgent (visual feedback raised GPT-4), ACL Findings 2024, arXiv 2402.11453 https://arxiv.org/abs/2402.11453 ; DV-World image-tool ablation.
Pairwise judging with a rubric, discount self-scores: Xie et al. 2025, VisJudge-Bench (rubric-prompted GPT-5 r = 0.43 with experts; models inflate scores), arXiv 2510.22373 (preprint) https://arxiv.org/abs/2510.22373 Carrying the loser's key point into the winner: house call.
Visual review loop (fresh-context reviewer given only the render, request, and destination; fix P0/P1; at most 3 rounds): house call from the Olson skill's Tufte-test loop; looking at pixels helps: MatPlotAgent (above); fresh context, findings over scores, and the round cap because vision judges are noisy and inflate scores: VisJudge-Bench (above).
