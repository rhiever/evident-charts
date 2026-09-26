"""evident-charts house look for matplotlib: destination presets, title block, direct labels, value labels, save.

Optional sugar; charts must follow the skill's rules with or without it. Typical use:

    import sys; sys.path.insert(0, "<skill>/scripts"); import evident as ev
    fig, ax = ev.figure("blog")                      # or social, social_portrait, slide, report, mobile; height=, rows=n
    c = ev.colors(names, highlight="US")             # dict name -> color: accent for the story, gray for context
    ...plot...
    ev.label_lines(ax, highlight="US")                # or ev.value_labels(ax, bars) for <= 12 bars
    ev.reference(ax, 4.2, "Average 4.2")              # labeled average/benchmark line; ev.callout labels one point
    ev.columns(ax, names, [("n", n, ev.num(compact=True))])  # context column, only when the comparison needs it
    ev.label_points(ax, x, y, names, highlight="US")  # scatter: short labels beside their dots
    ev.strip(ax, groups, values, highlight="US")      # dot strip per category; ev.provisional marks a preliminary point
    ev.fits_title("Takeaway title", "blog")           # (fits, chars_over): what titles() and check_chart measure; lines=1
    ev.titles(fig, "Takeaway title", subtitle="What and units", source="Source: X")  # stats=[("17.1%", "Q2")]
    ev.titles(fig, "Short kicker", stats=[("+57%", "One-line takeaway")], stats_size="hero", source="Source: X")
    ev.plot_aspect(fig)                               # (ax, width/height, "wide"|"tall"|None); titles() warns outside the band
    ev.save(fig, "out/chart.png")                     # refits margins, saves at preset dpi, prints the path
"""
from __future__ import annotations

import colorsys
import decimal
import json
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import to_hex, to_rgb
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

ASSETS = Path(__file__).resolve().parent.parent / "assets"
_PRESETS_JSON = json.loads((ASSETS / "presets.json").read_text())
PRESETS = {k: v for k, v in _PRESETS_JSON.items() if not k.startswith("_")}
ASPECT = _PRESETS_JSON["_plot_aspect"]  # plot box width / height band: widest, tallest
STYLE = str(ASSETS / "evident.mplstyle")

ACCENT, ACCENT_TEXT, ALT = "#D55E00", "#C15500", "#0072B2"
GRAY, INK, DARK, MUTED = "#BDBDBD", "#333333", "#595959", "#767676"
GRID, SPINE = "#E6E6E6", "#8C8C8C"
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
_TEXT_VARIANT = {ACCENT.lower(): ACCENT_TEXT, GRAY.lower(): MUTED}
_BREAK_BEFORE = set("and but or as while since because than after before from to in on at for with without despite "
                    "when where which that by until over under across through into among versus vs even yet so".split())
_NO_BREAK_AFTER = set("a an the of to in on at for by with and or but from than as its their his her our your my no not "
                      "per vs e.g i.e is are was were".split())
_ABBREV = set("vs e.g i.e etc approx est mr mrs ms dr st no jan feb mar apr jun jul aug sep sept oct nov dec".split())
_CUR = {"dest": "blog"}


def _state(fig):
    """Return the per-figure layout state, creating it for figures not made by figure()."""
    if not hasattr(fig, "_evident"):
        fig._evident = {"dest": _CUR["dest"], "head": [], "foot": [], "relayout": []}
    return fig._evident


def size(role, fig=None):
    """Return the size in points for a type or stroke role (title, subtitle, stat, label, annotation, source, line, marker, ...)."""
    p = PRESETS[_state(fig)["dest"] if fig is not None else _CUR["dest"]]
    pct = p["type"].get(role, p["strokes"].get(role))
    if pct is None and role == "stat":
        pct = 1.5 * p["type"]["title"]  # big-number row under the subtitle, unless the preset defines one
    if pct is None:
        raise KeyError(f"unknown role {role!r}")
    width_in = fig.get_figwidth() if fig is not None else p["width_in"]
    return pct / 100 * width_in * 72


def _font_family():
    """Installed members of the style's sans-serif stack, DejaVu Sans last: glyphs missing from the first font
    (arrows, check marks) fall back per glyph instead of rendering as boxes."""
    have = {f.name for f in font_manager.fontManager.ttflist}
    fams = [f for f in plt.rcParams["font.sans-serif"] if f in have and f != "DejaVu Sans"]
    return fams + ["DejaVu Sans"]


def figure(dest="blog", nrows=1, ncols=1, height=None, rows=None, **subplots_kw):
    """Create a figure styled and sized for a destination preset; returns (fig, ax_or_axes).

    height (inches = canvas px / 100) resizes the canvas at the preset width; never fig.set_size_inches afterwards.
    rows=n (bar or strip rows in the tallest panel) sizes the height so n rows get 1.6 label sizes each once titles()
    places the title block (titles and save refit it; never shorter than the preset). Fixed-height presets (slide,
    social, social_portrait) warn and keep their height: show fewer rows or split panels."""
    if dest not in PRESETS:
        raise ValueError(f"dest must be one of {sorted(PRESETS)}")
    p, _CUR["dest"] = PRESETS[dest], dest
    plt.style.use(STYLE)
    plt.rcParams["font.family"] = _font_family()
    lab, grid = size("label"), size("grid")
    h = p["height_in"] + max(0, (rows or 0) - p["bar_rows"]) * 1.6 * 1.2 * lab / 72 if height is None else height
    if h != p["height_in"] and p.get("fixed_height"):
        warnings.warn(f"{dest} has a fixed height: show fewer rows (group the rest) or split across panels")
        h, rows = p["height_in"], None
    plt.rcParams.update({
        "font.size": size("annotation"), "axes.labelsize": lab, "axes.titlesize": lab, "legend.fontsize": lab,
        "xtick.labelsize": lab, "ytick.labelsize": lab, "lines.linewidth": size("line"),
        "lines.markersize": size("marker"), "grid.linewidth": grid, "axes.linewidth": grid,
        "xtick.major.width": grid, "ytick.major.width": grid, "xtick.major.size": lab * .35,
        "ytick.major.size": lab * .35, "xtick.major.pad": lab * .35, "ytick.major.pad": lab * .35,
        "axes.labelpad": lab * .5, "axes.titlepad": lab * .8, "figure.titlesize": size("title")})
    fig, ax = plt.subplots(nrows, ncols, figsize=(p["width_in"], h), dpi=100, **subplots_kw)
    fig._evident = {"dest": dest, "head": [], "foot": [], "relayout": [], "rows": rows if height is None else None}
    m = p["margins"]
    fig.subplots_adjust(left=m["left"] + .08, right=1 - m["right"] - .02, bottom=.12, top=.8)
    return fig, ax


def _width(t, s, r):
    """Measure the rendered width of string s in text object t's font, in pixels."""
    t.set_text(s)
    return t.get_window_extent(renderer=r).width


def _greedy(t, text, maxw, r):
    """Greedy word wrap of text to maxw pixels; explicit newlines are kept."""
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            trial = f"{line} {w}".strip()
            if line and _width(t, trial, r) > maxw:
                out.append(line)
                line = w
            else:
                line = trial
        out.append(line)
    return "\n".join(out)


def _abbrev(word):
    """True if a word ending in a period is an abbreviation (U.S., e.g., vs.), not a sentence end."""
    w = word.strip("(\"')").lower()
    return bool(re.fullmatch(r"(\w\.){2,}", w)) or w.rstrip(".") in _ABBREV


def _esc(s):
    """Escape $ so matplotlib prints it instead of starting mathtext ($5 and $10 stay literal)."""
    return s if s is None else re.sub(r"(?<!\\)\$", r"\\$", str(s))


def _split2(t, text, maxw, r):
    """Text on one line, its best 2-line break within maxw px (phrase boundaries preferred), or None if it needs more."""
    if "\n" in text:
        lines = text.split("\n")
        return text if len(lines) <= 2 and all(_width(t, ln, r) <= maxw for ln in lines) else None
    if _width(t, text, r) <= maxw:
        return text
    words, best = text.split(), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa, wb = _width(t, a, r), _width(t, b, r)
        if max(wa, wb) > maxw:
            continue
        prev, nxt = words[i - 1].lower(), words[i].lower().strip("(\"'.")
        cost = abs(wa - wb) / maxw + (.1 if wa < wb else 0) + (1 if i == len(words) - 1 else 0)
        cost -= (.7 if re.search(r"[.!?]$", prev) and not _abbrev(prev) else .45 if re.search(r"[,;:]$", prev)
                 else .25 if nxt in _BREAK_BEFORE else 0)
        cost += .6 if prev.strip(",;:").rstrip(".") in _NO_BREAK_AFTER else 0
        cost += .6 if re.fullmatch(r"[\d.,$%+-]+", prev.replace("\\$", "$")) else 0
        if best is None or cost < best[0]:
            best = (cost, f"{a}\n{b}")
    return best[1] if best else None


def _over(t, text, maxw, r, lines=2):
    """Characters to cut so text fits on `lines` (1 or 2) lines of maxw px: 0 if it fits, else length minus the longest
    fitting word prefix."""
    def fits(s):
        return _split2(t, s, maxw, r) is not None if lines == 2 else "\n" not in s and _width(t, s, r) <= maxw
    if fits(text):
        return 0
    words, lo, hi = text.split(), 0, len(text.split()) - 1
    while lo < hi:  # longest word prefix that still fits
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if fits(" ".join(words[:mid])) else (lo, mid - 1)
    return len(text.replace("\\$", "$")) - len(" ".join(words[:lo]).replace("\\$", "$"))


def _wrap2(t, text, maxw, r, role="title"):
    """Break text into at most 2 balanced lines; if it needs more, warn with the characters to cut and wrap greedily."""
    out = _split2(t, text, maxw, r)
    if out is not None:
        return out
    n, cut = len(text.replace("\\$", "$")), _over(t, text, maxw, r)
    warnings.warn(f"{role} needs more than 2 lines at this size: cut about {cut} characters "
                  f"({n} now, ~{n - cut} fits): {text[:40]!r}")
    return _greedy(t, text, maxw, r)


def _block(fig, dest):
    """Usable title-block width in px for a figure at a preset (canvas width minus left and right margins)."""
    m = PRESETS[dest]["margins"]
    return fig.bbox.width * (1 - m["left"] - m["right"])


def _fits(text, role, dest, fig, lines=2):
    if fig is None:
        p = PRESETS[dest]
        with plt.style.context(STYLE):  # the house font stack figure() uses
            f = Figure(figsize=(p["width_in"], p["height_in"]), dpi=100)
            return _fits(text, role, dest, f, lines)
    dest = _state(fig)["dest"] if dest is None else dest
    r = fig.canvas.get_renderer() if hasattr(fig.canvas, "get_renderer") else FigureCanvasAgg(fig).get_renderer()
    p = PRESETS[dest]
    t = fig.text(0, 0, "", fontsize=p["type"][role] / 100 * fig.get_figwidth() * 72, linespacing=1.15,
                 weight="bold" if role == "title" else "normal")
    try:
        over = _over(t, _esc(text), _block(fig, dest), r, lines)
    finally:
        t.remove()
    return over == 0, over


def fits_title(text, dest="blog", fig=None, lines=2):
    """(fits, chars_over): does text fit the title's 2 lines (or lines=1) at dest, measured exactly as titles() wraps it."""
    return _fits(text, "title", dest if fig is None else None, fig, lines)


def fits_subtitle(text, dest="blog", fig=None, lines=2):
    """(fits, chars_over) for a subtitle's 2 lines (or lines=1) at dest, measured exactly as titles() wraps it."""
    return _fits(text, "subtitle", dest if fig is None else None, fig, lines)


def titles(fig, title, subtitle=None, source=None, note=None, credit=None, stats=None, stats_size="row"):
    """Place title, subtitle, big-number row (stats=[(value, caption[, color])]), note, source and credit; refit the axes.

    stats_size: "row" (1.5x the title) for supporting numbers; "hero" (3.5x the title, shrunk to fit the width) when
    one number is the hook and must outrank the title; or a size in points. title=None leaves the title to the slide or
    post. Warns when the plot left over falls outside the presets.json plot_aspect band."""
    st, r = _state(fig), fig.canvas.get_renderer()
    st["titles"] = (dict(title=title, subtitle=subtitle, source=source, note=note, credit=credit, stats=stats,
                         stats_size=stats_size), tuple(fig.get_size_inches()))
    p, (W, H) = PRESETS[st["dest"]], (fig.bbox.width, fig.bbox.height)
    for t in st["head"] + st["foot"]:
        t.remove()
    st["head"], st["foot"] = [], []
    title, subtitle, source, note, credit = map(_esc, (title, subtitle, source, note, credit))
    m = {k: v * W for k, v in p["margins"].items()}
    maxw, x, px = _block(fig, st["dest"]), m["left"] / W, fig.dpi / 72

    def put(y, s, role, wrap, **kw):
        t = fig.text(x, y / H, "", fontsize=size(role, fig), linespacing=1.15, **kw)
        t.set_text(wrap(t, s, maxw, r, role) if wrap is _wrap2 else wrap(t, s, maxw, r))
        if wrap is _greedy and s and t.get_text().count("\n") > s.count("\n") + 1:
            warnings.warn(f"{role} line wraps past 2 lines, shorten it: {s[:40]!r}")
        return t

    y = H - m["top"]
    for s, role, kw in ((title, "title", dict(weight="bold", color=INK)), (subtitle, "subtitle", dict(color=MUTED))):
        if s:
            t = put(y, s, role, _wrap2, va="top", **kw)
            st["head"].append(t)
            y = t.get_window_extent(r).y0 - .45 * size("subtitle", fig) * px
    if stats:
        hero = stats_size == "hero"
        big = size("stat", fig) if stats_size == "row" else 3.5 * size("title", fig) if hero else float(stats_size)
        cap = size("subtitle" if hero else "label", fig)
        while True:
            row, x0 = [], m["left"]
            for val, caption, *col in stats:
                v = fig.text(x0 / W, y / H, _esc(val), fontsize=big, weight="bold", va="top",
                             color=text_color(col[0]) if col else INK)
                c = fig.text(x0 / W, (v.get_window_extent(r).y0 - .3 * cap * px) / H, "", fontsize=cap,
                             color=MUTED, va="top")
                c.set_text(_greedy(c, _esc(caption), max(maxw - (x0 - m["left"]), .25 * maxw), r))  # wrap to the canvas
                row += [v, c]
                x0 += max(v.get_window_extent(r).width, c.get_window_extent(r).width) + .8 * big * px
            used = x0 - .8 * big * px - m["left"]
            if not hero or used <= maxw or big <= 1.6 * size("title", fig):
                break
            for t in row:
                t.remove()
            big = max(big * maxw / used * .98, 1.6 * size("title", fig))  # captions may still wrap the row
        st["head"] += row
        if used > maxw:
            warnings.warn("stats row is wider than the canvas: use fewer or shorter stats")
    y = m["bottom"]
    if credit:
        c = fig.text(1 - m["right"] / W, y / H, credit, fontsize=size("source", fig), color=MUTED, ha="right", va="bottom")
        st["foot"].append(c)
        maxw -= c.get_window_extent(r).width + 2 * size("source", fig) * px
    for s in (source, note):
        if s:
            t = put(y, s, "source", _greedy, va="bottom", color=MUTED)
            st["foot"].append(t)
            y = t.get_window_extent(r).y1 + .35 * size("source", fig) * px
    _fit(fig)
    _size_rows(fig)
    if not st.get("sizing") and not stats:
        _warn_aspect(fig)
    return st["head"] + st["foot"]


def _rows_chart(ax):
    """Horizontal bars or category rows (dot strips): their height follows the row count, so any height is fine."""
    if any(getattr(c, "orientation", None) == "horizontal" for c in ax.containers):
        return True
    if not ax.yaxis.get_visible():
        return False
    labels = [re.sub(r"\\mathdefault\{(.*?)\}", r"\1", s).strip("$ ")
              for s in ax.yaxis.get_major_formatter().format_ticks(ax.yaxis.get_majorticklocs())]
    labels = [s for s in labels if s]
    return bool(labels) and all(re.search(r"[A-Za-z]{2,}", s) or not re.search(r"\d", s) for s in labels)


def plot_aspect(fig):
    """(ax, width / height, "wide" | "tall" | None) for the figure's one main plot, judged against the presets.json
    plot_aspect band; None when there is no single plot to judge (small multiples, only insets or hand-placed axes,
    a fixed data aspect such as a map or pie, a sparkline with its axes off). Category-row charts are never tall."""
    axes = [a for a in fig.axes if a.get_visible() and a.get_subplotspec() is not None
            and getattr(a, "_colorbar", None) is None and (a.lines or a.collections or a.patches or a.images)]
    if len({tuple(np.round(a.get_position().bounds, 3)) for a in axes}) != 1:  # twin axes share one box
        return None
    ax = axes[0]
    if ax.name != "rectilinear" or ax.get_aspect() != "auto" or not ax.axison:
        return None
    b = ax.get_window_extent(fig.canvas.get_renderer())
    if b.height < 1 or b.width < 1:
        return None
    ratio = b.width / b.height
    verdict = "wide" if ratio > ASPECT["widest"] else "tall" if ratio < ASPECT["tallest"] and not _rows_chart(ax) else None
    return ax, ratio, verdict


def _warn_aspect(fig):
    """Warn when the plot left beside the title block and labels falls outside the plot_aspect band."""
    got = plot_aspect(fig)
    if not got or not got[2]:
        return
    dest, (_, ratio, verdict) = _state(fig)["dest"], got
    if verdict == "tall":
        warnings.warn(f"plot area is 1:{1 / ratio:.1f}, taller than 1:{1 / ASPECT['tallest']:g}: use a shorter canvas "
                      "(ev.figure(dest, height=...)) or horizontal bars")
    elif PRESETS[dest].get("fixed_height"):
        warnings.warn(f"plot area is {ratio:.1f}:1, wider than {ASPECT['widest']:g}:1 on the fixed-height {dest} canvas: "
                      "cut the title and subtitle to one line each (ev.fits_title(text, dest, lines=1), "
                      "ev.fits_subtitle), or export the chart without them (ev.titles(fig, None, source=...)) and put "
                      "the title in the slide's title placeholder or the post text")
    else:
        warnings.warn(f"plot area is {ratio:.1f}:1, wider than {ASPECT['widest']:g}:1: cut the title block or give the "
                      "canvas more height (ev.figure(dest, height=...))")


def _size_rows(fig):
    """figure(rows=n): set the canvas height so the tallest row-like panel gives each row 1.6 label sizes."""
    st = _state(fig)
    n, p = st.get("rows"), PRESETS[st["dest"]]
    if not n or st.get("sizing") or p.get("fixed_height"):
        return
    st["sizing"] = True
    try:
        for _ in range(4):
            fig.canvas.draw()  # settle autoscaled limits
            spans = [(abs(np.diff(a.get_ylim())[0]), a.bbox.height) for a in fig.axes
                     if a.get_visible() and a.get_subplotspec() is not None]
            spans = [s for s in spans if .5 * n <= s[0] <= n + 3]  # one data unit per row
            if not spans:
                return
            span, have = max(spans)
            h = max(p["height_in"], fig.get_figheight() + (1.6 * size("label", fig) * fig.dpi / 72 * span - have) / fig.dpi)
            if abs(h - fig.get_figheight()) * fig.dpi < 1:
                return
            fig.set_size_inches(fig.get_figwidth(), h, forward=False)
            if "titles" in st:
                titles(fig, **st["titles"][0])
            else:
                _fit(fig)
    finally:
        st["sizing"] = False


def _fit(fig, passes=3):
    """Move the subplot grid so tick labels, direct labels and annotations sit inside the margins and title block."""
    st, r = _state(fig), fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    m = {k: v * W for k, v in PRESETS[st["dest"]]["margins"].items()}
    lab = size("label", fig) * fig.dpi / 72
    top = min((t.get_window_extent(r).y0 - 1.6 * lab for t in st["head"]), default=H - m["top"])
    bot = max((t.get_window_extent(r).y1 + 1.1 * lab for t in st["foot"]), default=m["bottom"])
    axes = [a for a in fig.axes if a.get_visible() and a.get_subplotspec() is not None]
    if not axes:
        return
    for _ in range(passes):
        for f in st["relayout"]:
            f()
        A = Bbox.union([a.get_window_extent(r) for a in axes])
        T = Bbox.union([a.get_tightbbox(r) for a in axes])
        left, right = m["left"] + A.x0 - T.x0, W - m["right"] - (T.x1 - A.x1)
        bottom, top_ = bot + A.y0 - T.y0, top - (T.y1 - A.y1)
        if right - left < .2 * W or top_ - bottom < .2 * H:
            warnings.warn("labels leave under 20% of the canvas for the plot: shorten labels or titles")
            right, top_ = max(right, left + .2 * W), max(top_, bottom + .2 * H)
        fig.subplots_adjust(left=left / W, right=right / W, bottom=bottom / H, top=top_ / H, **_gaps(axes, r, lab))
    for f in st["relayout"]:
        f()


def _gaps(axes, r, lab):
    """Return hspace/wspace that keep neighboring panels' labels one label-height apart.

    Only what faces the gap counts: right/bottom overhangs of panels with a neighbor after them and left/top
    overhangs of panels with a neighbor before them, so the first column's category labels never widen the gap."""
    nrows, ncols = axes[0].get_subplotspec().get_gridspec().get_geometry()
    out, pos = {}, [a.get_position() for a in axes]
    A, T, S = [a.get_window_extent(r) for a in axes], [a.get_tightbbox(r) for a in axes], [a.get_subplotspec() for a in axes]

    def most(vals):
        return max([0.0, *vals])
    if nrows > 1:
        gap = (most(a.y0 - t.y0 for a, t, s in zip(A, T, S) if s.rowspan.stop < nrows)
               + most(t.y1 - a.y1 for a, t, s in zip(A, T, S) if s.rowspan.start > 0) + .8 * lab)
        span = (max(p.y1 for p in pos) - min(p.y0 for p in pos)) * axes[0].figure.bbox.height
        out["hspace"] = gap / max((span - (nrows - 1) * gap) / nrows, 1)
    if ncols > 1:
        gap = (most(t.x1 - a.x1 for a, t, s in zip(A, T, S) if s.colspan.stop < ncols)
               + most(a.x0 - t.x0 for a, t, s in zip(A, T, S) if s.colspan.start > 0) + 1.2 * lab)
        span = (max(p.x1 for p in pos) - min(p.x0 for p in pos)) * axes[0].figure.bbox.width
        out["wspace"] = gap / max((span - (ncols - 1) * gap) / ncols, 1)
    return out


def _contrast(c, bg="#FFFFFF"):
    """WCAG contrast ratio of color c against bg."""
    def lum(x):
        v = [ch / 12.92 if ch <= .03928 else ((ch + .055) / 1.055) ** 2.4 for ch in to_rgb(x)]
        return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
    hi, lo = sorted((lum(c), lum(bg)), reverse=True)
    return (hi + .05) / (lo + .05)


def _saturated(c):
    """True if a color reads as a hue rather than gray."""
    return colorsys.rgb_to_hls(*to_rgb(c))[2] > .15


def text_color(c):
    """Return a text-safe (>= 4.5:1 on white) variant of a mark color; gray marks map to the muted text gray."""
    h = to_hex(c).lower()
    if h in _TEXT_VARIANT:
        return _TEXT_VARIANT[h]
    if not _saturated(c):
        return h if _contrast(h) >= 4.5 else MUTED
    hh, l, s = colorsys.rgb_to_hls(*to_rgb(c))
    while _contrast(colorsys.hls_to_rgb(hh, l, s)) < 4.5 and l > 0:
        l -= .01
    return to_hex(colorsys.hls_to_rgb(hh, max(l, 0), s))


def colors(names, highlight=None, accents=(ACCENT, ALT), one_accent=False):
    """Return a dict name -> color: highlighted names get the accents in order (one_accent=True: all share the first
    accent, for a highlighted group), every other name context gray."""
    hl = [highlight] if isinstance(highlight, str) else list(highlight or [])
    accents = (accents[0],) * len(hl) if one_accent else accents
    if len(hl) > len(accents):
        warnings.warn(f"highlight at most {len(accents)} series; the rest stay gray")
    return {n: accents[hl.index(n)] if n in hl[:len(accents)] else GRAY for n in names}


def _spread(ys, sep):
    """Nudge label centers apart (sep: one height per label) with minimal total displacement."""
    ys = np.asarray(ys, float)
    order = np.argsort(ys)
    h = np.broadcast_to(np.asarray(sep, float), ys.shape)[order]
    c = np.concatenate([[0.0], np.cumsum((h[:-1] + h[1:]) / 2)])
    z, blocks = ys[order] - c, []
    for k in range(len(z)):
        blocks.append([k, 1, z[k]])
        while len(blocks) > 1 and blocks[-2][2] > blocks[-1][2]:
            (st, n0, m0), (_, n1, m1) = blocks[-2], blocks[-1]
            blocks[-2:] = [[st, n0 + n1, (m0 * n0 + m1 * n1) / (n0 + n1)]]
    fit = np.empty(len(z))
    for st, n, m in blocks:
        fit[st:st + n] = m
    out = np.empty(len(z))
    out[order] = fit + c
    return out


def _names(v):
    """Normalize None, one name, or several names to a set."""
    return {v} if isinstance(v, str) else set(v or [])


def _num(fmt, v):
    """Format v with a format string or callable, using a true minus sign."""
    return re.sub(r"-(?=[$\u20ac\u00a3\d.])", "\u2212", fmt(v) if callable(fmt) else fmt.format(v))


def num(decimals=0, prefix="", suffix="", sign=False, compact=False):
    """Number formatter for any fmt= argument: rounds half up (28.45 -> 28.5, as publishers round, where
    "{:.1f}" gives 28.4); compact=True scales to k, M, bn (12831 -> 12.8k with decimals=1); sign=True adds + to gains."""
    def fmt(v):
        d, unit = decimal.Decimal(repr(float(v))), ""
        for scale, u in ((10 ** 9, "bn"), (10 ** 6, "M"), (10 ** 3, "k")) if compact else ():
            if abs(d) >= scale:
                d, unit = d / scale, u
                break
        q = d.quantize(decimal.Decimal(1).scaleb(-decimals), rounding=decimal.ROUND_HALF_UP)
        return f"{'-' if q < 0 else '+' if sign and q > 0 else ''}{prefix}{abs(q):,}{unit}{suffix}"
    return fmt


def _line_xy(ln):
    """A line's full data, including a last point provisional() split off into its own dashed segment."""
    full = getattr(ln, "_evident_xy", None)
    return np.asarray(full if full is not None else ln.get_xydata(), float)


def label_lines(ax, lines=None, highlight=None, pad=None, values=False, reference=None, group=None, two_line=False):
    """Label lines at their last point, spread apart with leaders; values=True/format appends the end value; reference is dark bold.

    two_line=True puts the value under the name (narrow canvases, long names). group={"Other regions": [line names]}
    gives those context lines one shared label at the median of their ends."""
    fig = ax.figure
    if lines is None:
        lines = [ln for ln in ax.get_lines() if not ln.get_label().startswith("_")]
    items = list(lines.items()) if isinstance(lines, dict) else [(ln.get_label(), ln) for ln in lines]
    hl, ref, group = _names(highlight), _names(reference), dict(group or {})
    members = {n: g for g, names in group.items() for n in names}
    ring = any(getattr(ln, "_evident_xy", None) is not None for _, ln in items)  # provisional open markers
    pad = size("label", fig) * .4 + (size("marker", fig) / 2 if ring else 0) if pad is None else pad
    lab = size("label", fig)
    data, pooled = [], {}
    for name, ln in items:
        xy = _line_xy(ln)
        xy = xy[np.isfinite(xy).all(axis=1)]
        if len(xy) and name in members:
            pooled.setdefault(members[name], []).append((ln, xy[-1]))
        elif len(xy):
            data.append((name, ln, xy[-1], False))
    for g, got in pooled.items():
        e = np.array([end for _, end in got])
        data.append((g, got[0][0], np.array([e[:, 0].max(), np.median(e[:, 1])]), True))
    fmt = values if isinstance(values, str) or callable(values) else None
    if values is True:
        top = max((abs(e[1]) for _, _, e, _ in data), default=0)
        fmt = "{:,.0f}" if top >= 100 else "{:,.1f}" if top >= 1 else "{:,.2f}"
    ends, texts = [], []
    for name, ln, end, is_group in data:
        col = DARK if name in ref else ln.get_color() if (_saturated(ln.get_color()) or name not in hl) else ACCENT
        if name in hl:
            ln.set_zorder(max(ln.get_zorder(), 3))
        ends.append(end)
        sep = "\n" if two_line else " "
        texts.append(ax.annotate(_esc(f"{name}{sep}{_num(fmt, end[1])}" if fmt and not is_group else name), xy=end, xytext=(pad, 0),
                                 textcoords="offset points", va="center", ha="left", fontsize=lab,
                                 color=text_color(col), weight="bold" if name in hl | ref else "normal",
                                 annotation_clip=False,
                                 arrowprops=dict(arrowstyle="-", color=SPINE, lw=size("grid", fig), relpos=(0, .5),
                                                 shrinkA=lab * .2, shrinkB=lab * .15)))

    def place():
        ax.get_ylim()  # settle lazy autoscaling before reading transData
        ys = np.array([ax.transData.transform(e)[1] for e in ends])
        h = np.array([lab * fig.dpi / 72 * (t.get_text().count("\n") + 1) for t in texts])
        moved = _spread(ys, 1.2 * h) - ys
        lead = np.abs(moved) > .5 * h
        dx = pad + lab * 1.2 * lead.any()  # room for leaders; the label column stays aligned
        for t, dy, on in zip(texts, moved, lead):
            t.xyann = (dx, dy * 72 / fig.dpi)
            t.arrow_patch.set_visible(bool(on))
    if texts:
        place()
        _state(fig)["relayout"].append(place)
    return texts


def callout(ax, x, y, text, where="above", color=None, marker=True, box=False):
    """Label one data point with short text above/below/left/right or diagonally (e.g. above_right); returns the Text.

    marker=False labels a point another helper already drew (a provisional open dot); box=True sets the text on a
    white box where it must cross gridlines or marks."""
    fig = ax.figure
    gap = size("label", fig) * .8
    off, ha, va = {"above": ((0, gap), "center", "bottom"), "below": ((0, -gap), "center", "top"),
                   "left": ((-gap, 0), "right", "center"), "right": ((gap, 0), "left", "center"),
                   "above_right": ((gap * .7, gap * .7), "left", "bottom"), "above_left": ((-gap * .7, gap * .7), "right", "bottom"),
                   "below_right": ((gap * .7, -gap * .7), "left", "top"), "below_left": ((-gap * .7, -gap * .7), "right", "top")}[where]
    if marker:
        ax.plot([x], [y], "o", ms=size("label", fig) * .55, color=color or DARK, zorder=4, clip_on=False)
    return ax.annotate(_esc(text), xy=(x, y), xytext=off, textcoords="offset points", ha=ha, va=va,
                       fontsize=size("annotation", fig), color=text_color(color) if color else DARK,
                       annotation_clip=False, bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none") if box else None)


def reference(ax, value, label, axis="y", color=DARK, at=None):
    """Labeled reference line (average, target, benchmark) at value across the plot; returns the label Text.

    The label sits past the axes end (right of a horizontal line for axis="y", above a vertical one for axis="x"), or
    with at= inside the plot beside the line at that position (an x value; for axis="x" a y value or row name: pick an
    empty row or gap). Any value label or callout the line crosses gets a white gap, so the line never runs through text."""
    fig = ax.figure
    horiz = axis == "y"
    ln = (ax.axhline if horiz else ax.axvline)(value, color=color, lw=size("line", fig) * .6, ls=(0, (4, 3)),
                                               zorder=1.5, label="_reference")
    pad = size("label", fig) * .4
    if at is None:
        xy, xycoords = ((1, value), ("axes fraction", "data")) if horiz else ((value, 1), ("data", "axes fraction"))
        off, ha, va = ((pad, 0), "left", "center") if horiz else ((0, pad), "center", "bottom")
    else:
        pos = ax.convert_xunits(at) if horiz else _row_positions(ax, [at])[0]
        xy, xycoords = ((pos, value), "data") if horiz else ((value, pos), "data")
        off, ha, va = ((0, pad), "left", "bottom") if horiz else ((pad, 0), "left", "center")
    t = ax.annotate(_esc(label), xy=xy, xycoords=xycoords, xytext=off, textcoords="offset points", ha=ha, va=va,
                    fontsize=size("annotation", fig), color=text_color(color), annotation_clip=False,
                    bbox=None if at is None else dict(boxstyle="square,pad=0.1", fc="white", ec="none"))

    def gap():
        r = fig.canvas.get_renderer()
        at = ax.transData.transform((0, value) if horiz else (value, 0))[1 if horiz else 0]
        for s in ax.texts:
            b = s.get_window_extent(r)
            if s is not t and s.get_visible() and (b.y0 <= at <= b.y1 if horiz else b.x0 <= at <= b.x1):
                s.set_bbox(dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
    gap()
    _state(fig)["relayout"].append(gap)
    return t


def label_points(ax, x, y, names, offsets=None, highlight=None):
    """Label scatter dots beside their points (default right); offsets={name: 'left'|'above'|'below'|(dx_pt, dy_pt)}; returns the Texts."""
    fig, offsets = ax.figure, offsets or {}
    gap = size("marker", fig) / 2 + size("label", fig) * .35
    sides = {"right": ((gap, 0), "left", "center"), "left": ((-gap, 0), "right", "center"),
             "above": ((0, gap), "center", "bottom"), "below": ((0, -gap), "center", "top")}
    cmap = colors(list(names), highlight)
    texts = []
    for xi, yi, name in zip(x, y, names):
        o = offsets.get(name, "right")
        if isinstance(o, str):
            off, ha, va = sides[o]
        else:
            off = o
            ha = "left" if o[0] > 0 else "right" if o[0] < 0 else "center"
            va = "bottom" if o[1] > 0 else "top" if o[1] < 0 else "center"
        hl = cmap[name] != GRAY
        texts.append(ax.annotate(_esc(name), xy=(xi, yi), xytext=off, textcoords="offset points", ha=ha, va=va,
                                 fontsize=size("label", fig), color=text_color(cmap[name]) if hl else DARK,
                                 weight="bold" if hl else "normal", annotation_clip=False))
    return texts


def value_labels(ax, bars, fmt="{:,.0f}", warn=True, emphasize=False):
    """Label each bar (<= 12; warn=False if deliberate) with its value and drop the value axis and gridlines they replace.

    fmt is a format string or a callable.

    Highlighted bars get bold, accent-colored values; category tick labels stay plain unless emphasize=True.
    Value-axis limits you set before or after this call are kept."""
    fig, patches = ax.figure, list(bars)
    if warn and len(patches) > 12:
        warnings.warn("more than 12 bars: keep the value axis and annotate only headline values")
    horiz = getattr(bars, "orientation", None) == "horizontal"
    vals = np.asarray(bars.datavalues, float)
    emph = [_saturated(p.get_facecolor()) for p in patches]
    mixed = any(emph) and not all(emph)
    labels = [_esc(_num(fmt, v)) for v in vals]
    texts = ax.bar_label(bars, labels=labels, padding=size("label", fig) * .35, fontsize=size("label", fig))
    for t, p, e in zip(texts, patches, emph):
        t.set_color(text_color(p.get_facecolor()) if mixed and e else MUTED if mixed else DARK)
        t.set_weight("bold" if mixed and e else "normal")
    key, cat_axis = ("x", ax.yaxis) if horiz else ("y", ax.xaxis)
    (ax.xaxis if horiz else ax.yaxis).set_visible(False)
    ax.grid(False)
    ax.tick_params(axis="y" if horiz else "x", length=0)
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(side == "bottom" and not horiz and vals.min() >= 0)
    if horiz or vals.min() < 0:  # keep a visible zero baseline (GR-4)
        (ax.axvline if horiz else ax.axhline)(0, color=SPINE, lw=size("grid", fig), zorder=1)
    centers = [p.get_y() + p.get_height() / 2 if horiz else p.get_x() + p.get_width() / 2 for p in patches]
    lo, hi = min(0, vals.min()), max(0, vals.max())
    get_lim, set_lim = (ax.get_xlim, ax.set_xlim) if horiz else (ax.get_ylim, ax.set_ylim)
    sibs = (ax.get_shared_x_axes() if horiz else ax.get_shared_y_axes()).get_siblings(ax)
    mine = ax.__dict__.setdefault("_evident_lim", {})  # key -> limits this helper last set, or None once the user owns them
    if key not in mine and not (ax.get_autoscalex_on() if horiz else ax.get_autoscaley_on()):
        mine[key] = None

    def need():
        r = fig.canvas.get_renderer()
        ext = max((t.get_window_extent(r).width if horiz else t.get_window_extent(r).height) for t in texts)
        f = (ext + size("label", fig) * .6 * fig.dpi / 72) / max(ax.bbox.width if horiz else ax.bbox.height, 1)
        f_hi, f_lo = (f if vals.max() > 0 else 0), (f if vals.min() < 0 else 0)
        rng = (hi - lo) / max(1 - f_hi - f_lo, .2)
        return lo - f_lo * rng, hi + f_hi * rng
    ax.__dict__.setdefault("_evident_need", {}).setdefault(key, []).append(need)

    def fit_labels():
        last = mine.get(key, False)
        if last is None or (last is not False and not np.allclose(get_lim(), last)):
            mine[key] = None  # limits set by the user win
            return
        needs = [f() for a in sibs for f in getattr(a, "_evident_need", {}).get(key, [])]  # shared axes fit all panels
        set_lim(min(n[0] for n in needs), max(n[1] for n in needs))
        for a in sibs:
            a.__dict__.setdefault("_evident_lim", {})[key] = tuple(get_lim())

    def emphasize_ticks():  # restyles only this axes' own tick labels, resetting reused ticks
        base = plt.rcParams[f"{'y' if horiz else 'x'}tick.labelcolor"]
        base = plt.rcParams[f"{'y' if horiz else 'x'}tick.color"] if base == "inherit" else base
        for loc, tl in zip(cat_axis.get_ticklocs(), cat_axis.get_ticklabels()):
            hit = [k for k, c in enumerate(centers) if abs(c - loc) < 1e-6 and emph[k]]
            tl.set_color(text_color(patches[hit[0]].get_facecolor()) if hit else base)
            tl.set_weight("bold" if hit else "normal")
    hooks = [fit_labels] + ([emphasize_ticks] if emphasize and mixed else [])
    for f in hooks:
        f()
    _state(fig)["relayout"] += hooks
    return texts


def columns(ax, rows, cols, gap=None):
    """Text columns right of a horizontal chart: cols=[(header, values[, fmt[, colors]]), ...], one value per row.

    Use one only when the requested comparison needs a value per row; otherwise a subtitle clause or one callout.
    rows are the plotted y positions, or category names (a categorical axis or y tick labels, as ev.strip sets).
    fmt is a format string ("{:+.1f}") or any callable value -> str, such as ev.num(1) (round half up) or
    ev.num(compact=True) (k, M, bn). colors is one color per cell or a callable value -> color (made text-safe).
    Columns sit fixed points right of the axes edge (numbers right-aligned, headers above the plot) and move with it
    on re-layout; returns the Texts."""
    fig = ax.figure
    lab, r, pt = size("label", fig), fig.canvas.get_renderer(), 72 / fig.dpi
    ys = _row_positions(ax, rows)
    gap = lab * 1.2 if gap is None else gap
    probe = fig.text(0, 0, "", fontsize=lab)
    x, texts = gap, []
    for header, values, *opt in cols:
        cells = [_esc(_num(opt[0] if opt else "{}", v)) for v in values]
        tint = opt[1] if len(opt) > 1 else None
        tints = [tint(v) if callable(tint) else tint[i] if tint is not None else None for i, v in enumerate(values)]
        header = _esc(header)
        x += max(_width(probe, s, r) * pt for s in [header, *cells])
        texts.append(ax.annotate(header, xy=(1, 1), xycoords="axes fraction", xytext=(x, lab * .5),
                                 textcoords="offset points", ha="right", va="bottom", fontsize=lab, color=MUTED,
                                 annotation_clip=False))
        texts += [ax.annotate(s, xy=(1, y), xycoords=("axes fraction", "data"), xytext=(x, 0), textcoords="offset points",
                              ha="right", va="center", fontsize=lab, color=text_color(c) if c else DARK,
                              annotation_clip=False)
                  for s, y, c in zip(cells, ys, tints)]
        x += gap
    probe.remove()
    return texts


def _row_positions(ax, rows):
    """y positions for rows given as numbers or category names (categorical units first, then y tick labels)."""
    rows = list(rows)
    if not any(isinstance(v, str) for v in rows):
        return np.atleast_1d(np.asarray(ax.yaxis.convert_units(rows), float))
    mapping = getattr(ax.yaxis.get_units(), "_mapping", {})
    ticks = {t.get_text(): loc for loc, t in zip(ax.get_yticks(), ax.get_yticklabels())}
    missing = [v for v in rows if v not in mapping and v not in ticks]
    if missing:
        raise ValueError(f"rows not on the y axis (neither a category nor a tick label): {missing}")
    return np.array([mapping[v] if v in mapping else ticks[v] for v in rows], float)


_highlight_colors = colors


def strip(ax, groups, values, order=None, colors=None, highlight=None, median=True, resolution=None, max_stack=None):
    """Dot strip per category row (first on top): equal values stack symmetrically to fit the row, over a median tick.

    Dots shrink so the tallest stack fits its row; max_stack=k sizes dots for k and squeezes taller stacks into the row
    (overlapping) instead, so a few heavily rounded values do not shrink every dot."""
    fig, groups, values = ax.figure, np.asarray(groups), np.asarray(values, float)
    cats = list(order) if order is not None else list(dict.fromkeys(groups.tolist()))
    cmap = colors if colors is not None else _highlight_colors(cats, highlight) if highlight else dict.fromkeys(cats, ALT)
    n, rows, tallest = len(cats), [], 1
    for i, cat in enumerate(cats):
        v = values[(groups == cat) & np.isfinite(values)]
        v = np.round(v / resolution) * resolution if resolution else v
        _, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
        rank = np.empty(len(v))
        rank[np.argsort(inv, kind="stable")] = np.arange(len(v)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        y = n - 1 - i
        sc = ax.scatter(v, np.full(len(v), y, float), color=cmap.get(cat, GRAY), linewidths=0, zorder=3, clip_on=False)
        rows.append((sc, y, rank - (cnt[inv] - 1) / 2, cnt[inv]))
        tallest = max(tallest, cnt.max(initial=1))
        if median and len(v):
            ax.plot([np.median(v)] * 2, [y - .45, y + .45], color=INK, lw=size("line", fig), zorder=2, label="_median")
    ax.set_ylim(-.5, n - .5)
    ax.set_yticks(range(n), cats[::-1])
    ax.tick_params(axis="y", length=0)
    ax.grid(False, axis="y")
    ax.grid(True, axis="x")
    ax.spines["left"].set_visible(False)

    k = tallest if max_stack is None else max(1, min(tallest, max_stack))

    def fit():
        row = ax.bbox.height / n
        d = min(size("marker", fig) * fig.dpi / 72, .85 * row / k)
        for sc, y, slot, cnt in rows:
            sc.set_sizes([(.9 * d * 72 / fig.dpi) ** 2])
            off = np.asarray(sc.get_offsets(), float).copy()
            off[:, 1] = y + slot * d / row * np.minimum(1, (k - 1) / np.maximum(cnt - 1, 1))
            sc.set_offsets(off)
    fit()
    _state(fig)["relayout"].append(fit)
    return [sc for sc, *_ in rows]


def _mark_provisional(ax, a, b, color, lw, z):
    """Dashed connector from final point a to provisional point b, plus an open marker at b."""
    fig = ax.figure
    if a is not None:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=(0, (3, 2)), zorder=z, label="_provisional")
    ax.plot([b[0]], [b[1]], "o", ms=size("marker", fig), mfc="white", mec=color, mew=max(size("line", fig), .6 * lw),
            zorder=z + 1, clip_on=False, label="_provisional")


def provisional(ax, x=None, y=None, prev_x=None, prev_y=None, color=None, label=None):
    """Draw provisional values as an open marker, dashed from the last final point; returns the label Text or None.

    One point: provisional(ax, x, y, prev_x, prev_y, label="2025 provisional"). Every series: provisional(ax) makes each
    labeled line's last point provisional; say so once in the subtitle or note. label_lines still labels the full line."""
    fig = ax.figure
    lines = [ln for ln in ax.get_lines() if not ln.get_label().startswith("_")]
    if x is None:
        skipped = [ln for ln in ax.get_lines() if ln.get_label().startswith("_") and len(ln.get_xydata()) > 1
                   and not ln.get_label().startswith(("_provisional", "_median", "_reference"))
                   and ln.get_linestyle() not in ("None", "none", "", " ")]
        if skipped:
            warnings.warn(f"provisional() skipped {len(skipped)} unlabeled line(s): plot them with label=... or mark "
                          "them one at a time with provisional(ax, x, y, prev_x, prev_y)")
        for ln in lines:
            if getattr(ln, "_evident_xy", None) is not None:
                continue
            xy = _line_xy(ln)
            idx = np.nonzero(np.isfinite(xy).all(axis=1))[0]
            if len(idx) < 2:
                warnings.warn(f"provisional() skipped {ln.get_label()!r}: fewer than 2 finite points")
                continue
            ln._evident_xy = xy
            ln.set_data(*xy[:idx[-1]].T)
            _mark_provisional(ax, xy[idx[-2]], xy[idx[-1]], ln.get_color(), ln.get_linewidth(), ln.get_zorder())
        return None
    pt = (ax.convert_xunits(x), ax.convert_yunits(y))
    prev = None if prev_x is None else (ax.convert_xunits(prev_x), ax.convert_yunits(prev_y))
    owner = None
    for ln in lines if prev is not None else []:
        xy = _line_xy(ln)
        xy = xy[np.isfinite(xy).all(axis=1)]
        if len(xy) and np.allclose(xy[-1], np.asarray(prev, float)):
            owner = ln
            ln._evident_xy = np.vstack([xy, [pt]])  # label_lines labels the provisional end
            break
    ref = owner or (ax.lines[-1] if ax.lines else None)
    color = color or (ref.get_color() if ref is not None else DARK)
    lw = owner.get_linewidth() if owner is not None else size("line", fig)
    _mark_provisional(ax, prev, pt, color, lw, owner.get_zorder() if owner is not None else 3)
    if label:
        return ax.annotate(_esc(label), xy=(x, y), xytext=(size("marker", fig) / 2 + size("label", fig) * .35, 0),
                           textcoords="offset points", ha="left", va="center", fontsize=size("label", fig),
                           color=text_color(color), annotation_clip=False)
    return None


def save(fig, path, **savefig_kw):
    """Refit the layout and save at the preset's size and dpi (never bbox tight); prints and returns the absolute path."""
    if savefig_kw.get("bbox_inches") == "tight":
        raise ValueError("bbox_inches='tight' crops the reserved margins; the layout is already fitted")
    st = _state(fig)
    if "titles" in st and tuple(fig.get_size_inches()) != st["titles"][1]:
        if fig.get_figwidth() != st["titles"][1][0]:
            warnings.warn("canvas width changed after ev.figure: type sizes follow the preset width; use "
                          "ev.figure(dest, height=...) for a taller canvas, never set_size_inches")
        titles(fig, **st["titles"][0])  # re-place the title block for the new canvas size
    _fit(fig)
    _size_rows(fig)
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    savefig_kw.setdefault("dpi", PRESETS[st["dest"]]["export_dpi"])
    savefig_kw.setdefault("facecolor", "white")
    fig.savefig(path, **savefig_kw)
    print(path)
    return path
