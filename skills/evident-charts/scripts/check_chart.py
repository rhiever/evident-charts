#!/usr/bin/env python3
"""Deterministic linter for matplotlib chart scripts.

Executes the chart script in-process (Agg backend; Figure.savefig and show are
patched, but everything else runs, so files the script writes another way, such
as data exports or images composed with PIL, are really written: lint a scratch
copy of the script and its inputs), captures its figures, and reports design
problems as terse, machine-friendly findings.

Usage:
  python check_chart.py path/to/chart.py [--cwd DIR] [--json]
                        [--dest blog|social|social_portrait|slide|report|mobile] [--verbose]
  python check_chart.py --list-checks

Exit codes: 0 no fails (warns allowed), 1 at least one fail,
2 missing file, script error, or no figures produced.

Not implemented: bubble-area. Matplotlib's scatter `s` is already an area
(points^2), so the classic "radius scaled by value" mistake leaves no
reliable trace on the artist; any heuristic would be guesswork.
"""

from __future__ import annotations

import argparse
import colorsys
import contextlib
import io
import json
import math
import os
import re
import runpy
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.cbook import STEP_LOOKUP_MAP  # noqa: E402
from matplotlib.collections import LineCollection, PathCollection, PolyCollection, QuadMesh  # noqa: E402
from matplotlib.colors import CenteredNorm, TwoSlopeNorm, to_hex, to_rgba  # noqa: E402
from matplotlib.container import BarContainer  # noqa: E402
from matplotlib.contour import ContourSet  # noqa: E402
from matplotlib.image import AxesImage  # noqa: E402
from matplotlib.legend import Legend  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.markers import MarkerStyle  # noqa: E402
from matplotlib.patches import FancyArrowPatch, PathPatch, Polygon, Rectangle, Wedge  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from matplotlib.text import Annotation, Text  # noqa: E402

# ---------------------------------------------------------------------------
# Tunable constants. Lengths in points are converted to pixels with fig.dpi.
# ---------------------------------------------------------------------------

# small-text: display width (px) the whole figure is shown at, per destination,
# and the minimum rendered font em-size (px) at that width.
DEST_WIDTH_PX = {"blog": 800, "slide": 1920, "social": 1080, "social_portrait": 1080, "report": 600, "mobile": 360}
DEST_MIN_TEXT_PX = {"blog": 12, "slide": 12, "social": 12, "social_portrait": 12, "report": 12, "mobile": 12}
# tick-crowding: fixed-height presets cannot grow for more category rows; bar_rows is how many fit.
DEST_FIXED_HEIGHT, DEST_BAR_ROWS = set(), {}
# plot-area-underused: canvas side margins (fraction of width) per destination, and the narrow destinations checked.
DEST_MARGINS = {}
NARROW_DESTS = {"mobile", "social", "social_portrait"}
# Prefer the skill's destination presets when present.
try:
    _presets = json.loads((Path(__file__).resolve().parent.parent / "assets" / "presets.json").read_text())
    for _name, _p in _presets.items():
        if not _name.startswith("_") and "display_px" in _p:
            DEST_WIDTH_PX[_name] = _p["display_px"]
            DEST_MIN_TEXT_PX[_name] = _p.get("min_text_px", 12)
            DEST_BAR_ROWS[_name] = _p.get("bar_rows")
            DEST_MARGINS[_name] = (_p["margins"]["left"], _p["margins"]["right"])
            if _p.get("fixed_height"):
                DEST_FIXED_HEIGHT.add(_name)
except (OSError, ValueError):
    pass
# title-too-long measures with evident.fits_title, the same 2-line fit ev.titles() wraps with; plot-aspect uses
# evident.plot_aspect and the presets.json plot_aspect band, as ev.titles() warns with.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evident import ASPECT, fits_title, plot_aspect  # noqa: E402
# cvd, contrast, and text-on-area reuse check_palette's color math and floors: CVD pairs must differ by
# CVD_FACTOR x the mark's DE_FLOOR (V6), text meets TEXT_MIN (V2), marks MARK_MIN / INVISIBLE (V3).
from check_palette import (CVD_FACTOR, DE_FLOOR, INVISIBLE, MARK_MIN, TEXT_MIN, TEXT_MIN_LARGE,  # noqa: E402
                           Color, contrast, de)

TEXT_OVERLAP_MIN_PT = 1.0      # unrotated texts: min horizontal overlap to fail
TEXT_OVERLAP_MIN_FRAC = 0.15   # rotated texts: overlap area / smaller box area to fail
TEXT_LINE_PAD_PT = 1.0         # shrink text boxes by this before line tests
TEXT_LINE_MIN_PATH_PT = 4.0    # min length of line inside a text box to fail
ENDPOINT_MIN_RADIUS_PT = 6.0   # endpoint exemption radius floor (see below)
CANVAS_TOLERANCE_PX = 1.0      # text may poke this far past the canvas edge
TICK_ROTATION_MAX_DEG = 30.0
TICK_MIN_GAP_PT = 2.0          # adjacent tick labels closer than this: crowded
MAX_LINE_COLORS = 6
MAX_CATEGORICAL_COLORS = 8
MAX_PIE_WEDGES = 5
NEUTRAL_SATURATION = 0.15      # colors below this saturation count as gray
# label-ambiguous: distances are gaps from a scatter marker's edge to the
# nearest edge of the label's glyph box, each padded by LABEL_PAD_FRAC of one
# label line height so a label touching its dot does not make ratios explode.
LABEL_AMBIG_RATIO = 1.25       # rival gap <= this x own gap: nearly equidistant
LABEL_PAD_FRAC = 0.5
LABEL_GATE_RADII = 3.0         # labels farther than 3 marker radii + 1 line height from every dot are notes
LABEL_SAME_POINT_FRAC = 1.0    # dots closer than this x own radius read as one blob (or one dot redrawn)
LABEL_MAX_WORDS = 4            # longer texts are callouts about a region, not names of one dot
LABEL_DENSE_DOTS = 2           # free text (no known own dot) lying on this many dots is lettering over a field
LEADER_TOL_PT = 4.0            # leader end within dot radius + this lands on the dot
TITLE_MAX_LINES = 2
# value-labels-and-axis: a numeric text within a bar's width and along its length (or up to this many
# line heights past either end) whose number matches the bar's value is a value label. Warn when at
# least VALUE_LABEL_MIN_BARS bars and VALUE_LABEL_MIN_FRAC of all bars are labeled (headline labels
# on a few of many bars are allowed) and the value axis still shows numeric ticks.
VALUE_LABEL_REACH_LINES = 2.5
VALUE_LABEL_MIN_BARS = 2
VALUE_LABEL_MIN_FRAC = 0.5

# process-note: agent-to-user process language and data file names. Past tenses such as "confirmed
# cases" or "verified accounts" are reader-facing and allowed.
PROCESS_RE = re.compile(
    r"\b(confirm|to be confirmed|inferred|add before publishing|todo|tbd|placeholder|verify|not stated in)\b", re.I)
DATA_FILE_RE = re.compile(r"\b[\w.-]+\.(csv|tsv|xlsx?|json|parquet)\b", re.I)
# missing-source: "Source:" anywhere in a text, or a line (or a " | "-separated part) starting "Source" or "Data:".
SOURCE_RE = re.compile(r"\bsources?\s*:|(^\s*|[|\u00b7\u2022]\s*)(sources?\b|data\s*:)", re.I | re.M)
# cumulative-as-rate: a series that only rises (a running total) under a label that promises a rate or share.
RATE_RE = re.compile(r"%|\b(rates?|share|per|percent(age)?)\b", re.I)
CUMULATIVE_RE = re.compile(r"\b(cumulative|to date|year-to-date|ytd|ever|all-time|so far|running total|accumulated)\b",
                           re.I)
CUMULATIVE_MIN_POINTS = 6      # shorter series rise monotonically by chance
CUMULATIVE_START_MULT = 2.0    # a running total of n similar periods starts near 1/n of its end: allow this multiple
CUMULATIVE_STEP_FRAC = 0.8     # and increase on at least this share of steps (plateaus are not running totals)
STACK_MAX_LAYERS = 2           # stacked-area: more layers than this warn
PLOT_TINY_FRAC = 0.15          # plot-area-tiny: axes narrower or shorter than this share of the figure (per 3 panels)
PLOT_UNDERUSED_FRAC = 0.65     # plot-area-underused: one plot box narrower than this share of the usable width...
PLOT_EMPTY_FRAC = 0.15         # ...while its labels leave at least this share of the usable width empty at the sides
# cvd: a text names a series when it contains the series' label (or, unlabeled, shares its hue within
# HUE_MATCH_DEG) and sits within DIRECT_LABEL_REACH_LINES of its own line heights of the mark, nearer it than the rival.
DIRECT_LABEL_REACH_LINES = 2.0
HUE_MATCH_DEG = 15.0
LARGE_TEXT_PT, LARGE_BOLD_PT = 18.0, 14.0   # contrast: WCAG large text gets TEXT_MIN_LARGE
# text-on-area: fills lighter than this alpha (confidence bands, shading) are context, not data regions; text counts as
# on the fills when this share of its glyph box is; backdrops differing by DE_FLOOR["area"] or more are an edge.
FILL_MIN_ALPHA = 0.3
AREA_OVERLAP_FRAC = TEXT_OVERLAP_MIN_FRAC
LOG_WORD_RE = re.compile(r"\blog(arithmic)?(?![a-z])", re.I)
RANK_RE = re.compile(r"\b(rank|depth)|\b\d+(st|nd|rd|th)\b", re.I)   # H5 escape hatches: ranks, ordinals, depth

RAINBOW_CMAPS = {"jet", "rainbow", "hsv", "gist_rainbow", "nipy_spectral", "gist_ncar"}
SPECTRAL_CMAPS = {"Spectral"}

CHECKS = {
    "text-overlap": ("fail", "Two visible text boxes intersect (titles, labels, ticks, ...), a legend covers text, "
                             "text covers a data marker, or text straddles a bar edge or lies on another bar."),
    "text-on-line": ("fail", "Text sits on a data line, 2-point segment, or annotation arrow."),
    "text-on-area": ("fail", "Unboxed text over filled data (area/stack layers, heatmap cells, pie wedges) straddles "
                             "an edge between fills, or sits inside one fill below text contrast (4.5:1, large 3:1)."),
    "cvd": ("fail", "Two data hues in one axes collapse under protan/deutan simulation (check_palette V6 floor) with "
                    "nothing else telling them apart (direct labels, dash, marker, hatch, mark type, bar position); "
                    "warn when redundantly encoded or tritan-only."),
    "contrast": ("fail", "Text below 4.5:1 (large text 3:1) against what is behind it, or a colored line/point below "
                         "1.5:1; warn: colored line/point below 3:1 and not direct-labeled, or a fill below 1.5:1 "
                         "without an outline."),
    "text-clipped": ("fail", "Text extends beyond the figure canvas or its clip box."),
    "bar-baseline": ("fail", "Bar value axis excludes zero or is log-scaled."),
    "dual-axis": ("warn", "Twin axes plot data on two different y (or x) scales."),
    "pie-slices": ("warn", "Pie present; more than 5 slices is a stronger warning."),
    "rainbow-cmap": ("fail", "Rainbow colormap (jet, hsv, ...); Spectral on diverging data is a warn."),
    "3d-axes": ("fail", "3D projection used."),
    "legend-direct-label": ("warn", "Line chart legend with <=4 entries; label lines directly."),
    "missing-axis-label": ("warn", "Numeric axis with no label and no unit in ticks or title, or a unit on only "
                                   "some of its ticks."),
    "default-title": ("warn", "Missing title (suptitle, figure text, or ax.set_title; similar titles on several panels "
                              "are panel titles), or a descriptive 'X by Y' title instead of a takeaway (a short "
                              "kicker over a larger hero number passes)."),
    "small-text": ("warn", "Text renders below the destination's minimum pixel size."),
    "tick-crowding": ("warn", "Tick labels rotated past 30 degrees or nearly touching."),
    "too-many-series": ("warn", ">6 line colors or >8 categorical colors in one axes."),
    "spines-gridlines": ("warn", "All four spines plus gridlines on both axes (heavy default styling)."),
    "label-ambiguous": ("warn", "Scatter point label sits nearer another dot than its own, or about equally near two."),
    "process-note": ("fail", "Chart text addressed to the user (confirm, TODO, inferred, ...) or a data file name."),
    "missing-source": ("warn", "No text contains 'Source:' or has a line (or ' | ' part) starting 'Source' or 'Data:'."),
    "value-labels-and-axis": ("warn", "Bars carry value labels while the value axis ticks are also shown."),
    "title-too-long": ("warn", "Title wraps past 2 lines or does not fit 2 lines at the destination (ev.fits_title)."),
    "inverted-axis": ("fail", "Value axis inverted, and its label and ticks do not say 'rank'."),
    "log-unlabeled": ("fail", "Log-scaled axis; no axis label, title, subtitle, or in-axes note says 'log'."),
    "cumulative-as-rate": ("fail", "A series (line or area layer) only ever rises, like a running total, but its "
                                   "axis label or title promises a rate, share, %, or per-unit value."),
    "stacked-area": ("warn", "Stacked area (stackplot or stacked fill_between) with 3+ layers: only the bottom layer "
                             "has a flat baseline."),
    "plot-area-underused": ("warn", "Mobile and social presets: a single plot box under 65% of the usable canvas "
                                    "width with 15%+ of it left empty beside the axes (a square aspect on a narrow "
                                    "canvas, hand-set margins)."),
    "plot-area-tiny": ("fail", "A plot panel under 15% of the figure's width or height (collapsed by long labels "
                               "or margins); the threshold scales down for grids of more than 3 panels."),
    "plot-aspect": ("warn", f"The one main plot box is wider than {ASPECT['widest']:g}:1 or taller than "
                            f"1:{1 / ASPECT['tallest']:g} (horizontal-bar and category-row charts may run taller); "
                            "small multiples, insets, sparklines, fixed-aspect maps, and big-number cards are skipped."),
}


@dataclass
class Finding:
    check: str
    severity: str
    where: str
    detail: str
    fix: str


@dataclass
class TextRec:
    obj: Text
    kind: str          # tick, axis_label, title, legend, annotation, text, figtext
    ax: object | None
    axis: str | None   # "x"/"y" for ticks and axis labels
    label: str
    size: float        # font size in points
    zorder: float
    cx: float
    cy: float
    w: float
    h: float
    angle: float
    aabb: tuple
    knockout: bool     # opaque bbox, stroke halo, or framed legend behind text
    # Per-line boxes (x0, y0, x1, y1) for unrotated text, so the empty corners
    # of a multi-line, centered label are not treated as ink.
    lines: list = field(default_factory=list)
    poly: list = field(default_factory=list)  # rotated text only

    @property
    def rotated(self) -> bool:
        return self.angle % 90 != 0

    def shapes(self, pad: float = 0.0) -> list:
        """Convex CCW polygons covering the text, shrunk by `pad` px sideways
        and by at least 12% of the line height vertically (descent/leading
        space that rarely holds ink)."""
        if self.rotated:
            vpad = max(pad, 0.12 * self.h)
            return [rect_poly(self.cx, self.cy, max(self.w - 2 * pad, 0.0), max(self.h - 2 * vpad, 0.0), self.angle)]
        out = []
        for x0, y0, x1, y1 in self.lines:
            vpad = max(pad, 0.12 * (y1 - y0)) if pad else 0.0
            if x1 - x0 > 2 * pad and y1 - y0 > 2 * vpad:
                out.append([(x0 + pad, y0 + vpad), (x1 - pad, y0 + vpad), (x1 - pad, y1 - vpad), (x0 + pad, y1 - vpad)])
        return out


# ---------------------------------------------------------------------------
# Geometry helpers (pure Python floats; polygons are CCW lists of (x, y)).
# ---------------------------------------------------------------------------

def rect_poly(cx, cy, w, h, angle_deg=0.0):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    hw, hh = w / 2, h / 2
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def poly_area(poly):
    n = len(poly)
    if n < 3:
        return 0.0
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2


def clip_poly(subject, clip):
    """Sutherland-Hodgman clip of `subject` by convex CCW polygon `clip`."""
    out = list(subject)
    n = len(clip)
    for i in range(n):
        if not out:
            break
        ax_, ay_ = clip[i]
        bx_, by_ = clip[(i + 1) % n]

        def side(p):
            return (bx_ - ax_) * (p[1] - ay_) - (by_ - ay_) * (p[0] - ax_)

        inp, out = out, []
        prev = inp[-1]
        for cur in inp:
            sc, sp = side(cur), side(prev)
            if sc >= 0:
                if sp < 0:
                    t = sp / (sp - sc)
                    out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
                out.append(cur)
            elif sp >= 0:
                t = sp / (sp - sc)
                out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            prev = cur
    return out


def seg_clip_convex(p0, p1, poly):
    """Cyrus-Beck: parameter interval (t0, t1) of segment p0->p1 inside the
    convex CCW polygon, or None."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    n = len(poly)
    for i in range(n):
        ax_, ay_ = poly[i]
        bx_, by_ = poly[(i + 1) % n]
        nx, ny = -(by_ - ay_), bx_ - ax_  # inward normal for CCW
        num = nx * (p0[0] - ax_) + ny * (p0[1] - ay_)
        den = nx * dx + ny * dy
        if den == 0:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return t0, t1


def circle_interval(p0, p1, c, r):
    """Parameter interval of segment p0->p1 inside circle (c, r), or None."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    fx, fy = p0[0] - c[0], p0[1] - c[1]
    a = dx * dx + dy * dy
    cc = fx * fx + fy * fy - r * r
    if a == 0:
        return (0.0, 1.0) if cc <= 0 else None
    b = 2 * (fx * dx + fy * dy)
    disc = b * b - 4 * a * cc
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t0, t1 = max((-b - sq) / (2 * a), 0.0), min((-b + sq) / (2 * a), 1.0)
    return (t0, t1) if t0 < t1 else None


def snip(s: str, n: int = 40) -> str:
    s = " / ".join(part.strip() for part in s.strip().splitlines() if part.strip())
    return f"'{s[:n - 3]}...'" if len(s) > n else f"'{s}'"


def is_neutral(color) -> bool:
    r, g, b, a = to_rgba(color)
    if a == 0:
        return True
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    return s < NEUTRAL_SATURATION or v < 0.15


def color_key(color) -> str:
    return to_hex(to_rgba(color), keep_alpha=False)


# ---------------------------------------------------------------------------
# Running the chart script
# ---------------------------------------------------------------------------

class ScriptError(Exception):
    def __init__(self, tail: str):
        super().__init__(tail)
        self.tail = tail


@contextlib.contextmanager
def patched_matplotlib():
    """Capture figures, block file output and GUI calls."""
    created, saved, save_kwargs = [], [], {}
    orig_init = matplotlib.figure.Figure.__init__
    orig_savefig = matplotlib.figure.Figure.savefig
    plt.switch_backend("Agg")
    orig = {"show": plt.show, "pause": plt.pause, "use": matplotlib.use}

    def init(self, *a, **kw):
        orig_init(self, *a, **kw)
        created.append(self)

    def savefig(self, fname=None, *a, **kw):
        if self not in saved:
            saved.append(self)
        save_kwargs[id(self)] = kw

    matplotlib.figure.Figure.__init__ = init
    matplotlib.figure.Figure.savefig = savefig
    plt.show = lambda *a, **k: None
    plt.pause = lambda *a, **k: None
    matplotlib.use = lambda *a, **k: None  # scripts may request a GUI backend
    try:
        yield created, saved, save_kwargs
    finally:
        matplotlib.figure.Figure.__init__ = orig_init
        matplotlib.figure.Figure.savefig = orig_savefig
        plt.show, plt.pause = orig["show"], orig["pause"]
        matplotlib.use = orig["use"]


def run_script(chart: Path, cwd: Path | None, verbose: bool = False):
    chart = chart.resolve()
    workdir = cwd.resolve() if cwd else chart.parent
    old_cwd, old_argv, old_path = os.getcwd(), sys.argv, list(sys.path)
    os.chdir(workdir)
    sys.argv = [str(chart)]
    sys.path.insert(0, str(chart.parent))
    sink = sys.stderr if verbose else io.StringIO()
    old_dwb, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ in chart dirs
    try:
        with patched_matplotlib() as (created, saved, save_kwargs):
            try:
                with contextlib.redirect_stdout(sink):
                    runpy.run_path(str(chart), run_name="__main__")
            except SystemExit as e:
                if e.code not in (0, None):
                    raise ScriptError(f"script exited with code {e.code}")
            except Exception:
                tail = "".join(traceback.format_exc().splitlines(keepends=True)[-12:])
                raise ScriptError(tail)
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv
        sys.path[:] = old_path
        sys.dont_write_bytecode = old_dwb
    # Saved figures are the deliverables; if none were saved, check every
    # non-empty figure the script created.
    figs = saved or [f for f in created if f.axes or f.texts]
    return figs, save_kwargs


# ---------------------------------------------------------------------------
# Figure inventory
# ---------------------------------------------------------------------------

def drawn_ticks(axis):
    try:
        return axis._update_ticks()  # exactly the ticks draw() would render
    except Exception:
        return axis.get_major_ticks()


def text_has_knockout(t: Text) -> bool:
    patch = t.get_bbox_patch()
    if patch is not None and patch.get_visible():
        fc = patch.get_facecolor()
        if fc[3] * (patch.get_alpha() if patch.get_alpha() is not None else 1.0) >= 0.8:
            return True
    return any(isinstance(pe, patheffects.Stroke) for pe in (t.get_path_effects() or []))


def legend_has_frame(leg: Legend) -> bool:
    frame = leg.get_frame()
    return leg.get_frame_on() and frame.get_facecolor()[3] * (frame.get_alpha() or 1.0) >= 0.8


def line_boxes(t: Text, bb, angle: float, renderer) -> list:
    """Split an unrotated multi-line text box into one box per line, each as
    wide as its own line and aligned per the text's multialignment."""
    whole = [(bb.x0, bb.y0, bb.x1, bb.y1)]
    lines = t.get_text().split("\n")
    if angle != 0 or len(lines) < 2 or t.get_usetex():
        return whole
    try:
        malign = t._get_multialignment() if hasattr(t, "_get_multialignment") else t.get_horizontalalignment()
        prop = t.get_fontproperties()
        rh = bb.height / len(lines)
        out = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            sub, ismath = t._preprocess_math(line)
            w = renderer.get_text_width_height_descent(sub, prop, ismath=ismath)[0]
            x0 = bb.x0 if malign == "left" else bb.x1 - w if malign == "right" else (bb.x0 + bb.x1 - w) / 2
            y1 = bb.y1 - i * rh
            out.append((x0, y1 - rh, x0 + w, y1))
        return out or whole
    except Exception:
        return whole


def collect_texts(fig, renderer) -> list[TextRec]:
    role = {}
    hidden = set()
    for ax in fig.axes:
        if getattr(ax, "name", "") == "3d":
            # 3D axes are flagged by 3d-axes; their projected tick labels
            # would only add noise to the text checks (small-text reads them via texts_3d).
            leg = ax.get_legend()
            keep = {id(t) for t in [ax.title, *(leg.get_texts() + [leg.get_title()] if leg else [])]}
            hidden.update(id(t) for t in ax.findobj(match=Text) if id(t) not in keep)
            continue
        for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            shown = ax.axison and axis.get_visible() and ax.get_visible()
            drawn = {id(t) for t in drawn_ticks(axis)} if shown else set()
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                for lab in (tick.label1, tick.label2):
                    if id(tick) in drawn and tick.get_visible():
                        role[id(lab)] = ("tick", ax, name)
                    else:
                        hidden.add(id(lab))
            role[id(axis.label)] = ("axis_label", ax, name)
            role[id(axis.get_offset_text())] = ("tick", ax, name) if shown else ("hidden", ax, name)
        for t in (ax.title, getattr(ax, "_left_title", None), getattr(ax, "_right_title", None)):
            if t is not None:
                role[id(t)] = ("title", ax, None)
    legends = [(ax.get_legend(), ax) for ax in fig.axes if ax.get_legend()] + [(lg, None) for lg in fig.legends]
    legend_knock = {}
    for leg, ax in legends:
        for t in list(leg.get_texts()) + [leg.get_title()]:
            role[id(t)] = ("legend", ax, None) if leg.get_visible() else ("hidden", ax, None)
            legend_knock[id(t)] = legend_has_frame(leg)
    for attr, kind in (("_suptitle", "title"), ("_supxlabel", "axis_label"), ("_supylabel", "axis_label")):
        t = getattr(fig, attr, None)
        if t is not None:
            role[id(t)] = (kind, None, None)

    recs, seen = [], set()
    for t in fig.findobj(match=Text, include_self=False):
        if id(t) in seen or id(t) in hidden:
            continue
        seen.add(id(t))
        s = t.get_text()
        if not t.get_visible() or not s or not s.strip():
            continue
        # labelsize=0 (clamped to 1 pt) and fully transparent text are hiding tricks.
        if t.get_fontsize() <= 1.5 or to_rgba(t.get_color(), t.get_alpha())[3] == 0:
            continue
        kind, ax, axis = role.get(id(t), (None, t.axes, None))
        if kind == "hidden":
            continue
        if ax is not None and not ax.get_visible():
            continue
        if kind is None:
            kind = "annotation" if isinstance(t, Annotation) else ("figtext" if t.axes is None else "text")
        if isinstance(t, Annotation):
            try:
                if not t._check_xy(renderer):  # annotation_clip hides it
                    continue
            except Exception:
                pass
        try:
            bb = Text.get_window_extent(t, renderer=renderer)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0 or not np.all(np.isfinite(bb.extents)):
            continue
        angle = t.get_rotation() % 180
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        w, h = bb.width, bb.height
        if min(angle, abs(angle - 90), 180 - angle) >= 1:
            # Oriented box: the axis-aligned box of a rotated rectangle shares
            # its center, so measure the unrotated size and rotate about it.
            orig = t.get_rotation()
            t.set_rotation(0)
            b0 = Text.get_window_extent(t, renderer=renderer)
            t.set_rotation(orig)
            w, h = b0.width, b0.height
        else:
            if abs(angle - 90) < 1:
                w, h = h, w
            angle = round(angle / 90) * 90
        rec = TextRec(
            obj=t, kind=kind, ax=ax, axis=axis, label=s.strip(), size=float(t.get_fontsize()),
            zorder=t.get_zorder() if kind != "legend" else 5.0,
            cx=cx, cy=cy, w=w, h=h, angle=angle, aabb=(bb.x0, bb.y0, bb.x1, bb.y1),
            knockout=legend_knock.get(id(t), False) or text_has_knockout(t),
        )
        if rec.rotated:
            rec.poly = rect_poly(cx, cy, w, h, angle)
        else:
            rec.lines = line_boxes(t, bb, angle, renderer)
        recs.append(rec)

    # Drop exact duplicates (twin-axes ticks, white "halo" copies under text).
    out, keys = [], set()
    for r in recs:
        key = (r.label, *(round(v) for v in r.aabb))
        if key in keys:
            continue
        keys.add(key)
        out.append(r)
    return out


@dataclass
class SegOwner:
    kind: str          # line, collection, arrow
    name: str
    zorder: float
    ann_id: int | None = None


def is_reference_line(line: Line2D, ax) -> bool:
    """Non-data Line2D: markers only, axhline/axvline/axline, faint guides."""
    ls = line.get_linestyle()
    if ls in ("None", "none", " ", "") or line.get_linewidth() <= 0:
        return True
    tr = line.get_transform()
    if tr is ax.get_xaxis_transform(which="grid") or tr is ax.get_yaxis_transform(which="grid"):
        return True
    if type(line).__name__ == "_AxLine":
        return True
    alpha = to_rgba(line.get_color(), line.get_alpha())[3]
    if ls in (":", "--", "-.", "dotted", "dashed", "dashdot") and alpha < 0.6:
        return True
    return alpha < 0.2


def line_name(artist, color, kind="line") -> str:
    lab = artist.get_label() or ""
    if lab and not lab.startswith("_"):
        return snip(lab, 30)
    try:
        return f"{kind} {color_key(color)}"
    except Exception:
        return kind


def collect_segments(fig, renderer):
    """Return (segments array [N, 13], owners). Columns: x0 y0 x1 y1, clip box
    (4, NaN if unclipped), line start (2), line end (2), owner index."""
    rows, owners = [], []

    def add_polyline(pts, owner_idx, clip, endpoints=None):
        pts = pts[np.all(np.isfinite(pts), axis=1)]
        if len(pts) < 2:
            return
        s, e = endpoints if endpoints is not None else (pts[0], pts[-1])
        for i in range(len(pts) - 1):
            rows.append([*pts[i], *pts[i + 1], *clip, *s, *e, owner_idx])

    for ax in fig.axes:
        if not ax.get_visible():
            continue
        for line in ax.lines:
            if not line.get_visible() or is_reference_line(line, ax):
                continue
            xy = np.asarray(line.get_xydata(), dtype=float)
            if len(xy) < 2:
                continue
            ds = line.get_drawstyle()
            if ds and ds != "default" and ds in STEP_LOOKUP_MAP:
                xy = np.column_stack(STEP_LOOKUP_MAP[ds](xy[:, 0], xy[:, 1]))
            pts = line.get_transform().transform(xy)
            clip = line.get_clip_box().extents if line.get_clip_on() and line.get_clip_box() else [np.nan] * 4
            owners.append(SegOwner("line", line_name(line, line.get_color()), line.get_zorder()))
            add_polyline(pts, len(owners) - 1, clip)
        for coll in ax.collections:
            if not isinstance(coll, LineCollection) or not coll.get_visible():
                continue
            lws = np.atleast_1d(coll.get_linewidths())
            ecs = coll.get_edgecolor()
            if len(lws) and np.all(lws <= 0):
                continue
            alpha = float(ecs[:, 3].max()) if len(ecs) else 1.0
            dashed = any(d[1] is not None for d in coll.get_linestyles())
            if alpha < 0.2 or (dashed and alpha < 0.6):
                continue
            clip = coll.get_clip_box().extents if coll.get_clip_on() and coll.get_clip_box() else [np.nan] * 4
            owners.append(SegOwner("collection", line_name(coll, ecs[0] if len(ecs) else "k", "segments"),
                                  coll.get_zorder()))
            tr = coll.get_transform()
            for seg in coll.get_segments():
                if len(seg) >= 2:
                    add_polyline(tr.transform(np.asarray(seg, dtype=float)), len(owners) - 1, clip)

    # Annotation arrows and free-standing arrow patches.
    arrows = []
    for t in fig.findobj(match=Annotation):
        ap = getattr(t, "arrow_patch", None)
        if ap is not None and t.get_visible() and ap.get_visible():
            try:
                if not t._check_xy(renderer):
                    continue
            except Exception:
                pass
            arrows.append((ap, id(t)))
    known = {id(a) for a, _ in arrows}
    arrows += [(p, None) for p in fig.findobj(match=FancyArrowPatch) if id(p) not in known and p.get_visible()]
    for ap, ann_id in arrows:
        try:
            polys = ap.get_transform().transform_path(ap.get_path()).to_polygons(closed_only=False)
        except Exception:
            continue
        if not polys or len(polys[0]) < 2:
            continue
        # Exempt regions sit around the shaft's tail and tip (first subpath).
        ends = (polys[0][0], polys[0][-1])
        owners.append(SegOwner("arrow", "annotation arrow", ap.get_zorder(), ann_id))
        for poly in polys:
            add_polyline(np.asarray(poly, dtype=float), len(owners) - 1, [np.nan] * 4, ends)
    arr = np.array(rows, dtype=float) if rows else np.zeros((0, 13))
    return arr, owners


def clip_to_box(p0, p1, box):
    if not np.isfinite(box[0]):
        return p0, p1
    x0, y0, x1, y1 = box
    r = seg_clip_convex(p0, p1, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    if r is None:
        return None
    t0, t1 = r
    d = (p1[0] - p0[0], p1[1] - p0[1])
    return (p0[0] + t0 * d[0], p0[1] + t0 * d[1]), (p0[0] + t1 * d[0], p0[1] + t1 * d[1])


def data_axes(fig):
    """Axes worth style checks: visible, not colorbars."""
    out = []
    for i, ax in enumerate(fig.axes):
        if not ax.get_visible() or getattr(ax, "_colorbar", None) is not None or ax.get_label() == "<colorbar>":
            continue
        out.append((i, ax))
    return out


def has_data(ax) -> bool:
    return bool(ax.lines or ax.collections or ax.patches or ax.images)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, fig, fi, dest, save_kwargs):
        self.fig, self.fi, self.dest = fig, fi, dest
        self.save_kwargs = save_kwargs or {}
        self.renderer = fig.canvas.get_renderer()
        self.px_per_pt = fig.dpi / 72.0
        self.ax_index = {id(a): i for i, a in enumerate(fig.axes)}
        self.texts = collect_texts(fig, self.renderer)
        self.segs, self.owners = collect_segments(fig, self.renderer)
        self.findings: list[Finding] = []
        self.overlapping_ticks: set = set()
        self.legend_hits: set = set()  # texts already reported against a legend text
        self.on_area: set = set()      # texts text-on-area judged, so contrast skips them
        self.series: dict = {}         # id(ax) -> color_series(ax), shared by cvd and contrast

    def where(self, ax=None, extra: str = "") -> str:
        loc = f"fig{self.fi}/ax{self.ax_index[id(ax)]}" if ax is not None and id(ax) in self.ax_index else f"fig{self.fi}/figure"
        return f"{loc} {extra}".strip()

    def add(self, check, where, detail, fix, severity=None):
        self.findings.append(Finding(check, severity or CHECKS[check][0], where, detail, fix))


def text_collision(a: TextRec, b: TextRec, min_w: float):
    """Return a short description if two texts collide, else None.

    Unrotated text: per-line boxes collide when they overlap by more than
    `min_w` px horizontally and by more than 30% of the shorter line's height
    vertically. The height rule ignores stacked labels whose boxes only share
    descent/leading space; the width rule catches glyphs that truly touch.
    Rotated text: oriented boxes overlapping >= TEXT_OVERLAP_MIN_FRAC of the
    smaller box's area.
    """
    if a.rotated or b.rotated:
        pa, pb = a.shapes(), b.shapes()
        inter = sum(poly_area(clip_poly(p, q)) for p in pa for q in pb)
        frac = inter / max(min(sum(map(poly_area, pa)), sum(map(poly_area, pb))), 1e-9)
        return f"rotated boxes overlap {frac:.0%} of the smaller" if frac >= TEXT_OVERLAP_MIN_FRAC else None
    best = None
    for la in a.lines:
        for lb in b.lines:
            w_ov = min(la[2], lb[2]) - max(la[0], lb[0])
            h_ov = min(la[3], lb[3]) - max(la[1], lb[1])
            h_min = min(la[3] - la[1], lb[3] - lb[1])
            if w_ov > min_w and h_ov > 0.3 * h_min:
                if best is None or w_ov * h_ov > best[0] * best[1]:
                    best = (w_ov, h_ov)
    return best


def check_text_overlap(c: Ctx):
    recs = c.texts
    if len(recs) < 2:
        return
    boxes = np.array([r.aabb for r in recs])
    ix0 = np.maximum(boxes[:, None, 0], boxes[None, :, 0])
    ix1 = np.minimum(boxes[:, None, 2], boxes[None, :, 2])
    iy0 = np.maximum(boxes[:, None, 1], boxes[None, :, 1])
    iy1 = np.minimum(boxes[:, None, 3], boxes[None, :, 3])
    cand = np.argwhere(np.triu((ix1 > ix0) & (iy1 > iy0), k=1))
    min_w = TEXT_OVERLAP_MIN_PT * c.px_per_pt
    for i, j in cand:
        a, b = recs[i], recs[j]
        hit = text_collision(a, b, min_w)
        if hit is None:
            continue
        if isinstance(hit, tuple):
            hit = f"glyph boxes overlap {hit[0] / c.px_per_pt:.1f} x {hit[1] / c.px_per_pt:.1f} pt"
        if a.kind == "tick" and b.kind == "tick":
            c.overlapping_ticks.update((id(a.obj), id(b.obj)))
        if "legend" in (a.kind, b.kind):
            c.legend_hits.update((id(a.obj), id(b.obj)))
        ax = a.ax if a.ax is not None else b.ax
        c.add("text-overlap", c.where(ax, f"{a.kind} {snip(a.label, 30)} x {b.kind} {snip(b.label, 30)}"),
              hit, "Move, shorten, or resize one label so the two no longer intersect.")
    check_legend_boxes(c, min_w)
    check_text_on_markers(c)
    check_text_on_bars(c)


def check_legend_boxes(c: Ctx, min_w: float):
    """text-overlap for a legend's content box (handles and texts) covering text outside it."""
    legends = [(ax.get_legend(), ax) for ax in c.fig.axes if ax.get_legend()] + [(lg, None) for lg in c.fig.legends]
    for leg, ax in legends:
        if not leg.get_visible():
            continue
        try:
            box = leg._legend_box.get_window_extent(c.renderer)
        except Exception:
            box = leg.get_window_extent(c.renderer)
        own = {id(t) for t in leg.get_texts()} | {id(leg.get_title())}
        for r in c.texts:
            if id(r.obj) in own or id(r.obj) in c.legend_hits:
                continue
            for x0, y0, x1, y1 in r.lines or [r.aabb]:
                w_ov, h_ov = min(x1, box.x1) - max(x0, box.x0), min(y1, box.y1) - max(y0, box.y0)
                if w_ov > min_w and h_ov > 0.3 * (y1 - y0):
                    where = c.where(ax if ax is not None else r.ax, f"legend box x {r.kind} {snip(r.label, 30)}")
                    c.add("text-overlap", where,
                          f"legend covers the text by {w_ov / c.px_per_pt:.1f} x {h_ov / c.px_per_pt:.1f} pt",
                          "Move the legend into open space (or label series directly) so it clears the text.")
                    break


def marker_points(ax, renderer):
    """Drawn data markers in ax as (xy px [N, 2], radius px [N], zorder [N]): scatter dots and Line2D markers."""
    xys, rads, zs = [], [], []
    pts = scatter_points(ax, renderer)
    if pts is not None:
        xys.append(pts[0])
        rads.append(pts[1])
        zs.append(np.array([pts[3][k].get_zorder() for k in pts[2]], dtype=float))
    for ln in ax.lines:
        if not ln.get_visible() or ln.get_marker() in (None, "None", "none", "", " ") or ln.get_markersize() <= 0:
            continue
        xy = ln.get_transform().transform(np.asarray(ln.get_xydata(), dtype=float))
        xy = xy[np.all(np.isfinite(xy), axis=1)]
        xys.append(xy)
        rads.append(np.full(len(xy), ln.get_markersize() / 2 * ax.figure.dpi / 72))
        zs.append(np.full(len(xy), float(ln.get_zorder())))
    if not xys:
        return np.zeros((0, 2)), np.zeros(0), np.zeros(0)
    return np.concatenate(xys), np.concatenate(rads), np.concatenate(zs)


def inside_convex(pts, poly):
    """Mask of points inside a convex CCW polygon."""
    ok = np.ones(len(pts), bool)
    for (ax_, ay_), (bx_, by_) in zip(poly, poly[1:] + poly[:1]):
        ok &= (bx_ - ax_) * (pts[:, 1] - ay_) - (by_ - ay_) * (pts[:, 0] - ax_) >= 0
    return ok


def check_text_on_markers(c: Ctx):
    """text-overlap for text drawn over a data marker: the marker's center lies inside the text's glyph box.
    Skipped: ticks, legends, opaque-boxed text drawn above the marker, and text that fits inside its marker (bubble labels)."""
    cache = {}
    pad = TEXT_LINE_PAD_PT * c.px_per_pt
    for r in c.texts:
        if r.kind in ("tick", "legend"):
            continue
        axes = [r.ax] if r.ax is not None else [a for _, a in data_axes(c.fig)]
        for ax in axes:
            if id(ax) not in cache:
                cache[id(ax)] = marker_points(ax, c.renderer)
            xy, rad, z = cache[id(ax)]
            if not len(xy):
                continue
            hit = np.zeros(len(xy), bool)
            for poly in r.shapes(pad):
                hit |= inside_convex(xy, poly)
            hit &= 2 * rad < r.w  # text wider than its dot: not a label inside a bubble
            if r.knockout:
                hit &= z > r.zorder
            if hit.any():
                k = int(np.nonzero(hit)[0][0])
                c.add("text-overlap", c.where(ax, f"{r.kind} {snip(r.label, 30)} x marker"),
                      f"text covers {int(hit.sum())} data marker(s), e.g. at {data_coords(ax, xy[k])}",
                      "Move the label beside its marker (e.g. ev.label_points) or into open space.")
                break


def check_text_on_bars(c: Ctx):
    """text-overlap for text drawn across bars: its glyphs straddle a bar edge or touch two bars. A label wholly
    inside one bar (an inside value label) passes; so do ticks, legends, and opaque-boxed text drawn above the bars."""
    pad = TEXT_LINE_PAD_PT * c.px_per_pt
    bars = {id(ax): [(p.get_window_extent(c.renderer), p.get_zorder()) for cont in ax.containers
                     if isinstance(cont, BarContainer) for p in cont.patches
                     if p.get_visible() and p.get_width() and p.get_height()] for _, ax in data_axes(c.fig)}
    for r in c.texts:
        if r.kind in ("tick", "legend") or r.rotated:
            continue
        for ax in [r.ax] if r.ax is not None else [a for _, a in data_axes(c.fig)]:
            touched, straddled = 0, 0
            for b, z in bars.get(id(ax), []):
                if r.knockout and r.zorder >= z:
                    continue
                inside = []
                for (x0, y0), _, (x1, y1), _ in r.shapes(pad):
                    if min(x1, b.x1) - max(x0, b.x0) > pad and min(y1, b.y1) - max(y0, b.y0) > pad:
                        inside.append(b.x0 - pad <= x0 and x1 <= b.x1 + pad and b.y0 - pad <= y0 and y1 <= b.y1 + pad)
                touched += bool(inside)
                straddled += bool(inside) and not all(inside)
            if straddled or touched > 1:
                c.add("text-overlap", c.where(ax, f"{r.kind} {snip(r.label, 30)} x bar"),
                      f"text straddles {straddled} bar edge(s)" if straddled else f"text lies on {touched} bars",
                      "Move the label past the bar end or into open space, or fit it wholly inside one bar.")
                break


def check_text_on_line(c: Ctx):
    segs = c.segs
    if not len(segs):
        return
    pad = TEXT_LINE_PAD_PT * c.px_per_pt
    min_path = TEXT_LINE_MIN_PATH_PT * c.px_per_pt
    sx0, sx1 = np.minimum(segs[:, 0], segs[:, 2]), np.maximum(segs[:, 0], segs[:, 2])
    sy0, sy1 = np.minimum(segs[:, 1], segs[:, 3]), np.maximum(segs[:, 1], segs[:, 3])
    for r in c.texts:
        if r.kind == "tick":
            continue
        x0, y0, x1, y1 = r.aabb
        idx = np.nonzero((sx1 >= x0) & (sx0 <= x1) & (sy1 >= y0) & (sy0 <= y1))[0]
        if not len(idx):
            continue
        shapes = r.shapes(pad) + line_gaps(r, pad)
        if not shapes:
            continue
        # Endpoint exemption: a direct label placed at a line's end usually
        # has the last stub of the line run into its padding. Path inside the
        # text box within R of either end of the line (or arrow shaft) is
        # ignored, R = max(font size, ENDPOINT_MIN_RADIUS_PT). A label sitting
        # mid-line, or centered on the end so the line runs through its
        # glyphs, still accumulates path beyond R and fails.
        radius = max(r.size, ENDPOINT_MIN_RADIUS_PT) * c.px_per_pt
        per_owner: dict[int, float] = {}
        for k in idx:
            row = segs[k]
            owner = c.owners[int(row[12])]
            if owner.ann_id is not None and owner.ann_id == id(r.obj):
                continue  # an annotation's own arrow starts at its text
            if r.knockout and r.zorder >= owner.zorder:
                continue  # opaque box or halo drawn over the line keeps text legible
            clipped = clip_to_box((row[0], row[1]), (row[2], row[3]), row[4:8])
            if clipped is None:
                continue
            p0, p1 = clipped
            seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            for poly in shapes:
                inside = inside_length(p0, p1, seg_len, poly, (row[8], row[9]), (row[10], row[11]), radius)
                if inside > 0:
                    per_owner[int(row[12])] = per_owner.get(int(row[12]), 0.0) + inside
        hits = [(o, L) for o, L in per_owner.items() if L >= min_path]
        if not hits:
            continue
        names = ", ".join(sorted({c.owners[o].name for o, _ in hits}))[:80]
        longest = max(L for _, L in hits) / c.px_per_pt
        c.add("text-on-line", c.where(r.ax, f"{r.kind} {snip(r.label)} on {names}"),
              f"{longest:.0f} pt of path crosses the text",
              "Move the label into open space or to the line end, or give it an opaque background box.")


def line_gaps(r: TextRec, pad: float) -> list:
    """Polygons over the leading between consecutive lines of an unrotated multi-line text (where their widths
    overlap): a data line threading between a label's lines runs through the label."""
    out = []
    for (ax0, ay0, ax1, _), (bx0, _, bx1, by1) in zip(r.lines, r.lines[1:]):
        x0, x1 = max(ax0, bx0) + pad, min(ax1, bx1) - pad
        vpad = max(pad, 0.12 * (by1 - r.lines[1][1]))
        lo, hi = by1 - vpad, ay0 + vpad  # lower line's inked top to upper line's inked bottom
        if x1 > x0 and hi > lo:
            out.append([(x0, lo), (x1, lo), (x1, hi), (x0, hi)])
    return out


def inside_length(p0, p1, seg_len, poly, start, end, radius) -> float:
    """Length of segment p0->p1 inside `poly`, excluding the parts within
    `radius` of the owning line's start or end point."""
    tt = seg_clip_convex(p0, p1, poly)
    if tt is None or tt[1] <= tt[0]:
        return 0.0
    ta, tb = tt
    covered = []
    for pt in (start, end):
        iv = circle_interval(p0, p1, pt, radius)
        if iv and min(iv[1], tb) > max(iv[0], ta):
            covered.append((max(iv[0], ta), min(iv[1], tb)))
    if len(covered) == 2 and covered[1][0] < covered[0][1] and covered[0][0] < covered[1][1]:
        covered = [(min(covered[0][0], covered[1][0]), max(covered[0][1], covered[1][1]))]
    return max(0.0, (tb - ta - sum(hi - lo for lo, hi in covered)) * seg_len)


def check_text_clipped(c: Ctx):
    tight = c.save_kwargs.get("bbox_inches") == "tight"
    fw, fh = c.fig.bbox.width, c.fig.bbox.height
    tol = CANVAS_TOLERANCE_PX
    for r in c.texts:
        x0, y0, x1, y1 = r.aabb
        sides = []
        if not tight:
            sides = [s for s, bad in (("left", x0 < -tol), ("right", x1 > fw + tol),
                                      ("bottom", y0 < -tol), ("top", y1 > fh + tol)) if bad]
        if sides:
            c.add("text-clipped", c.where(r.ax, f"{r.kind} {snip(r.label)}"),
                  f"extends past the canvas {'/'.join(sides)} edge",
                  "Move the text inside the figure or widen that margin with subplots_adjust.")
            continue
        t = r.obj
        box = t.get_clip_box() if t.get_clip_on() else None
        if box is not None and (x0 < box.x0 - tol or x1 > box.x1 + tol or y0 < box.y0 - tol or y1 > box.y1 + tol):
            c.add("text-clipped", c.where(r.ax, f"{r.kind} {snip(r.label)}"),
                  "cut off by its clip box (clip_on=True)",
                  "Set clip_on=False or move the text inside the axes.")


def check_bar_baseline(c: Ctx):
    for i, ax in data_axes(c.fig):
        for cont in ax.containers:
            if not isinstance(cont, BarContainer) or not cont.patches:
                continue
            horizontal = getattr(cont, "orientation", "vertical") == "horizontal"
            rects = [p for p in cont.patches if isinstance(p, Rectangle)]
            bases = [p.get_x() if horizontal else p.get_y() for p in rects]
            if not any(abs(b) < 1e-9 for b in bases):
                continue  # floating bars (Gantt, waterfall): no zero baseline
            name = "x" if horizontal else "y"
            scale = ax.get_xscale() if horizontal else ax.get_yscale()
            lo, hi = sorted(ax.get_xlim() if horizontal else ax.get_ylim())
            span = max(hi - lo, 1e-12)
            if scale != "linear":
                c.add("bar-baseline", c.where(ax, f"{name}-axis"), f"bars on a {scale} value axis",
                      "Plot bars on a linear axis from zero, or use a dot plot for log data.")
                break
            if not (lo <= 1e-9 * span and hi >= -1e-9 * span):
                c.add("bar-baseline", c.where(ax, f"{name}-axis"),
                      f"value axis spans {lo:.4g} to {hi:.4g}, excluding 0",
                      "Start the bar value axis at zero, or switch to a dot plot.")
                break


def check_dual_axis(c: Ctx):
    axes = data_axes(c.fig)
    for n, (i, a) in enumerate(axes):
        for j, b in axes[n + 1:]:
            if not np.allclose(a.get_position().bounds, b.get_position().bounds, atol=1e-6):
                continue
            if not (has_data(a) and has_data(b)):
                continue
            if a.get_shared_x_axes().joined(a, b):
                kind = "twinx"
            elif a.get_shared_y_axes().joined(a, b):
                kind = "twiny"
            else:
                continue
            c.add("dual-axis", f"fig{c.fi}/ax{i}+ax{j}", f"{kind} axes both plot data on separate scales",
                  "Split into two aligned panels or index both series to a common baseline.")


def check_pie(c: Ctx):
    for i, ax in data_axes(c.fig):
        n = sum(isinstance(p, Wedge) for p in ax.patches)
        if not n:
            continue
        if n > MAX_PIE_WEDGES:
            c.add("pie-slices", c.where(ax), f"pie with {n} slices",
                  "Replace the pie with a sorted horizontal bar chart.")
        else:
            c.add("pie-slices", c.where(ax), f"pie with {n} slices (angles are hard to compare)",
                  "If comparing parts, use a sorted bar chart; keep pies for 2-3 parts of a whole.")


def check_rainbow(c: Ctx):
    seen = set()
    mappables = [(None, im) for im in c.fig.images]
    for _, ax in data_axes(c.fig):
        mappables += [(ax, m) for m in list(ax.images) + list(ax.collections)]
    for ax, m in mappables:
        if id(m) in seen or not hasattr(m, "get_cmap") or m.get_array() is None:
            continue
        seen.add(id(m))
        name = m.get_cmap().name
        base = name[:-2] if name.endswith("_r") else name
        if base in RAINBOW_CMAPS:
            c.add("rainbow-cmap", c.where(ax, f"cmap={name}"), f"rainbow colormap '{name}' distorts data order",
                  "Use a perceptually uniform colormap: viridis/cividis (sequential) or RdBu/PuOr (diverging).")
        elif base in SPECTRAL_CMAPS:
            norm = m.norm
            vmin, vmax = norm.vmin, norm.vmax
            diverging = isinstance(norm, (TwoSlopeNorm, CenteredNorm)) or (
                vmin is not None and vmax is not None and vmin < 0 < vmax)
            if diverging:
                c.add("rainbow-cmap", c.where(ax, f"cmap={name}"), "Spectral on diverging data is rainbow-like",
                      "Prefer RdBu or PuOr for diverging data.", severity="warn")
            else:
                c.add("rainbow-cmap", c.where(ax, f"cmap={name}"), "Spectral used for sequential data",
                      "Use a sequential colormap such as viridis or Blues.")


def check_3d(c: Ctx):
    for i, ax in enumerate(c.fig.axes):
        if getattr(ax, "name", "") == "3d":
            c.add("3d-axes", c.where(ax), "3D projection distorts values through perspective",
                  "Plot in 2D; encode the third variable with color, size, or small multiples.")


def data_lines(ax):
    return [ln for ln in ax.lines if ln.get_visible() and not is_reference_line(ln, ax) and len(ln.get_xydata()) >= 2]


def check_legend(c: Ctx):
    legends = [(ax.get_legend(), ax, data_lines(ax)) for ax in c.fig.axes if ax.get_legend()]
    all_lines = [ln for ax in c.fig.axes for ln in data_lines(ax)]
    legends += [(lg, None, all_lines) for lg in c.fig.legends]
    for leg, ax, lines in legends:
        if not leg.get_visible() or not lines:
            continue
        handles = getattr(leg, "legend_handles", None) or getattr(leg, "legendHandles", [])
        n = len(leg.get_texts())
        line_handles = [h for h in handles if isinstance(h, Line2D) and h.get_linestyle() not in ("None", "none", "")]
        if 1 <= n <= 4 and line_handles:
            c.add("legend-direct-label", c.where(ax, "legend"), f"legend with {n} entries on a line chart",
                  "Remove the legend and label each line directly at its end in the line's color.")


NUM_RE = re.compile(r"^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?[kKMBT]?$")
UNIT_SYMBOL_RE = re.compile(r"[%$€£¥°]|\b(kg|km|mi|mph|ppm|kwh|mwh|gwh|twh|usd|lbs?|hrs?|yrs?|min|sec)\b", re.I)
UNIT_CUE_RE = re.compile(
    r"\(.*[a-z%$].*\)|%|\$|€|£|°|\bper\b|\bin (thousands|millions|billions|trillions|percent|dollars|"
    r"hours|days|minutes|seconds|years|miles|kilometers|tons|tonnes)\b|\b(usd|kwh|mwh|gwh|twh|mph|ppm|kg|km|lbs?)\b",
    re.I)


def parse_tick(s: str):
    s = re.sub(r"\\mathdefault\{(.*?)\}", r"\1", s.strip())
    m = re.fullmatch(r"\$?\s*10\^\{?(-?\d+)\}?\s*\$?", s)
    if m:
        return 10.0 ** int(m.group(1))
    s = s.replace("\u2212", "-").replace(",", "").replace(" ", "")
    if not NUM_RE.match(s):
        return None
    return float(re.sub(r"[kKMBT]$", "", s))


VALUE_TICK_RE = re.compile(r"[-+]?[$\u20ac\u00a3\u00a5]?\d[\d,.:]*\s*[A-Za-z%\u00b0]{0,3}")


def value_tick(s: str) -> bool:
    """Tick label reads as a quantity: 5, 1.2k, 40%, $3, 2:03:59 (not a category name or a range)."""
    s = re.sub(r"\\mathdefault\{(.*?)\}", r"\1", s.strip()).replace("\u2212", "-")
    return parse_tick(s) is not None or bool(VALUE_TICK_RE.fullmatch(s.strip("$ ")))


def title_like_texts(c: Ctx):
    """Titles, suptitle, and any text above all axes or in the top quarter."""
    fh = c.fig.bbox.height
    tops = [ax.get_window_extent(c.renderer).y1 for _, ax in data_axes(c.fig)] or [fh]
    out = []
    for r in c.texts:
        if r.kind == "title":
            out.append(r)
        elif r.kind in ("figtext", "text", "annotation") and (r.cy > 0.75 * fh or r.aabb[1] >= max(tops)):
            out.append(r)
    return out


def check_mixed_tick_units(c: Ctx):
    """missing-axis-label for a unit on only some value ticks ("9%" above "6" and "3"): readers see two scales."""
    for i, ax in data_axes(c.fig):
        for name in ("x", "y"):
            ticks = [re.sub(r"\$\\mathdefault\{(.*?)\}\$", r"\1", r.label) for r in c.texts
                     if r.kind == "tick" and r.ax is ax and r.axis == name]
            if len(ticks) < 2 or not all(value_tick(t) for t in ticks):
                continue
            units = [bool(UNIT_SYMBOL_RE.search(t)) for t in ticks]
            if any(units) and not all(units):
                c.add("missing-axis-label", c.where(ax, f"{name}-axis"),
                      f"unit on {sum(units)} of {len(ticks)} ticks ({', '.join(ticks)})",
                      "Put the unit on every tick (PercentFormatter, StrMethodFormatter) or only in the axis label "
                      "or subtitle.")


def check_missing_axis_label(c: Ctx):
    check_mixed_tick_units(c)
    titles = " ".join(r.label for r in title_like_texts(c))
    if UNIT_CUE_RE.search(titles):
        return
    if getattr(c.fig, "_supxlabel", None) is not None or getattr(c.fig, "_supylabel", None) is not None:
        return
    for i, ax in data_axes(c.fig):
        if getattr(ax, "name", "") != "rectilinear" or not ax.axison or not has_data(ax):
            continue
        axbox = ax.get_window_extent(c.renderer)
        for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            if axis.label.get_visible() and axis.label.get_text().strip():
                continue
            ticks = [r.label for r in c.texts if r.kind == "tick" and r.ax is ax and r.axis == name
                     and r.obj is not axis.get_offset_text()]
            if not ticks:
                continue
            if any(UNIT_SYMBOL_RE.search(t) for t in ticks):
                continue
            vals = [parse_tick(t) for t in ticks]
            if any(v is None for v in vals):
                continue  # categorical or date labels
            if name == "x" and all(1000 <= v <= 2200 for v in vals):
                continue  # year axis explains itself
            if name == "y" and any(
                    r.kind in ("text", "figtext", "annotation") and r.aabb[1] >= axbox.y1 - 2
                    and r.aabb[0] <= axbox.x0 + 0.3 * axbox.width and r.aabb[2] >= axbox.x0 - 0.15 * axbox.width
                    for r in c.texts):
                continue  # unit label placed above the top of the y axis
            c.add("missing-axis-label", c.where(ax, f"{name}-axis"), "numeric ticks with no axis label or unit",
                  "Label the axis with quantity and unit, or state the unit in the subtitle.")


TAKEAWAY_CUE_RE = re.compile(
    r"\b(is|are|was|were|has|have|had|hit|hits|rose|rises|rise|fell|falls|fall|grew|grows|grow|beat|beats|won|"
    r"wins|lost|loses|lead|leads|led|tops?|surges?|soars?|drops?|climbs?|shrinks?|shrank|doubles?|triples?|"
    r"remains?|outpaces?|overtook|overtakes?|peaks?|lags?|dominates?|flips?|makes?|made|gets?|got|became|"
    r"becomes?|keeps?|kept|takes?|took|than|never|only|still|record|most|least|nearly|twice|half|now|"
    r"can|could|will|would|should|did|does|do|don't|isn't|aren't|wasn't)\b|\b\w{3,}ed\b",
    re.I)
DESCRIPTIVE_RE = re.compile(
    r"\b(by|vs\.?|versus|over time|over the (years|decades)|across|trends?|distribution|breakdown|comparison|overview)\b",
    re.I)


def main_title(c: Ctx):
    """The largest non-numeric title-like text (highest on ties), or None."""
    cands = [r for r in title_like_texts(c) if not value_tick(r.label)]  # big-number stats are not titles
    return max(cands, key=lambda r: (r.size, r.cy)) if cands else None


def check_default_title(c: Ctx):
    main = main_title(c)
    n_axes = len([a for _, a in data_axes(c.fig) if has_data(a)])
    fix_none = "Add a title that states the takeaway, e.g. 'Sales doubled after the 2020 launch'."
    if main is None:
        c.add("default-title", c.where(), "no title", fix_none)
        return
    if n_axes > 1 and main.kind == "title" and main.ax is not None:
        # ax.set_title on one panel can be the chart title; titles on several panels of similar size are panel titles.
        others = [r for r in c.texts if r.kind == "title" and r.ax is not None and r.ax is not main.ax]
        if any(r.size * 1.15 > main.size for r in others):
            c.add("default-title", c.where(), "only panel titles; no overall title", fix_none)
            return
    text = " ".join(main.label.split())
    words = re.findall(r"[A-Za-z']+", text)
    hero = any(value_tick(r.label) and r.size > main.size for r in title_like_texts(c))
    if text.endswith("?") or TAKEAWAY_CUE_RE.search(text) or hero:  # a hero number and its caption carry the claim
        return
    if DESCRIPTIVE_RE.search(text) or (len(words) <= 2 and not re.search(r"\d", text)):
        c.add("default-title", c.where(main.ax, snip(text, 50)), "title describes the chart instead of the takeaway",
              "Rewrite the title as the finding, e.g. 'Sales doubled after the 2020 launch'.")


def check_title_too_long(c: Ctx):
    main = main_title(c)
    if main is None:
        return
    t = main.obj
    raw = t._get_wrapped_text() if t.get_wrap() else t.get_text()
    n_lines = sum(1 for ln in raw.splitlines() if ln.strip())
    text = " ".join(main.label.split())
    fits, over = fits_title(text, c.dest)
    problems = []
    if n_lines > TITLE_MAX_LINES:
        problems.append(f"{n_lines} lines")
    if not fits:
        problems.append(f"past 2 lines at {c.dest} ({len(text)} chars, cut about {over})")
    if problems:
        c.add("title-too-long", c.where(main.ax, snip(text, 50)), "title runs " + ", ".join(problems),
              "Cut to one sentence that ev.fits_title accepts, on 1-2 lines; move detail to the subtitle.")


def check_process_note(c: Ctx):
    for r in c.texts:
        hits = [m.group(0) for m in PROCESS_RE.finditer(r.label)]
        hits += [f"file name {m.group(0)}" for m in DATA_FILE_RE.finditer(r.label)]
        if hits:
            c.add("process-note", c.where(r.ax, f"{r.kind} {snip(r.label)}"),
                  f"addressed to the user: {', '.join(hits)}",
                  "Move process notes and caveats to your reply; cite the publisher and dataset, never a file name.")


def check_missing_source(c: Ctx):
    if not any(SOURCE_RE.search(r.obj.get_text()) for r in c.texts if r.kind != "tick"):
        c.add("missing-source", c.where(), "no text contains 'Source:' and no line starts with 'Source' or 'Data:'",
              "Add a bottom-left line 'Source: <publisher>, <dataset>'.")


def number_matches(label: str, value: float) -> bool:
    """True if a number printed in `label` equals `value` to the label's precision, allowing
    k/M/B-style and percent scaling and a dropped sign."""
    value = abs(value)
    scales = (1, 1e3, 1e-3, 1e6, 1e-6, 1e9, 1e-9, 100, 0.01)
    for m in re.finditer(r"\d[\d,]*(\.\d+)?", label.replace("\u2212", "-")):
        num = float(m.group(0).replace(",", ""))
        tol = 0.5 * 10.0 ** -(len(m.group(1) or ".") - 1) * 1.001  # half a unit in the last printed digit
        if any(abs(value / k - num) <= tol + 1e-9 * num for k in scales):
            return True
    return False


def check_value_labels_and_axis(c: Ctx):
    for i, ax in data_axes(c.fig):
        conts = [ct for ct in ax.containers if isinstance(ct, BarContainer) and ct.patches]
        if not conts:
            continue
        horizontal = getattr(conts[0], "orientation", "vertical") == "horizontal"
        name = "x" if horizontal else "y"
        axis = getattr(ax, f"{name}axis")
        ticks = [r for r in c.texts if r.kind == "tick" and r.ax is ax and r.axis == name
                 and r.obj is not axis.get_offset_text() and value_tick(r.label)]
        if len(ticks) < 2:
            continue
        texts = [r for r in c.texts if r.kind in ("text", "annotation") and r.ax is ax and not r.rotated
                 and re.search(r"\d", r.label)]
        bars = labeled = 0
        for ct in conts:
            vals = getattr(ct, "datavalues", None)
            for k, p in enumerate(ct.patches):
                if not (isinstance(p, Rectangle) and p.get_visible()):
                    continue
                v = vals[k] if vals is not None else (p.get_width() if horizontal else p.get_height())
                if not np.isfinite(v) or v == 0:
                    continue
                bars += 1
                x0, y0, x1, y1 = p.get_window_extent(c.renderer).extents
                for r in texts:
                    lh = r.h / max(len(r.lines), 1)
                    reach = VALUE_LABEL_REACH_LINES * lh
                    if horizontal:
                        across = y0 <= r.cy <= y1
                        along = r.aabb[2] >= x0 - reach and r.aabb[0] <= x1 + reach
                    else:
                        across = x0 <= r.cx <= x1
                        along = r.aabb[3] >= y0 - reach and r.aabb[1] <= y1 + reach
                    if across and along and number_matches(r.label, v):
                        labeled += 1
                        break
        if labeled >= VALUE_LABEL_MIN_BARS and labeled >= VALUE_LABEL_MIN_FRAC * bars:
            c.add("value-labels-and-axis", c.where(ax, f"{name}-axis"),
                  f"{labeled} of {bars} bars carry value labels and the {name}-axis shows {len(ticks)} numeric ticks",
                  f"Keep one readout: hide the {name}-axis ticks, spine, and gridlines, or drop the value labels.")


def value_axes(ax) -> list:
    """Names of the axes that carry values: x for horizontal bars, both for a pure scatter, else y."""
    conts = [ct for ct in ax.containers if isinstance(ct, BarContainer)]
    if conts:
        return ["x" if getattr(conts[0], "orientation", "vertical") == "horizontal" else "y"]
    if not ax.lines and any(isinstance(cl, PathCollection) for cl in ax.collections):
        return ["x", "y"]
    return ["y"]


def check_inverted_axis(c: Ctx):
    for i, ax in data_axes(c.fig):
        if getattr(ax, "name", "") != "rectilinear" or not has_data(ax) or ax.images or \
                any(isinstance(cl, QuadMesh) for cl in ax.collections):
            continue  # images and heatmaps put row 0 on top by convention
        for name in value_axes(ax):
            axis = getattr(ax, f"{name}axis")
            if not (ax.xaxis_inverted() if name == "x" else ax.yaxis_inverted()):
                continue
            ticks = [r.label for r in c.texts if r.kind == "tick" and r.ax is ax and r.axis == name]
            if not ticks or not all(value_tick(t) for t in ticks):
                continue  # categorical axis: top-to-bottom order is not a value
            if RANK_RE.search(" ".join([axis.label.get_text(), *ticks])):
                continue
            c.add("inverted-axis", c.where(ax, f"{name}-axis"), "value axis inverted: higher values toward the origin",
                  f"Restore normal order (ax.invert_{name}axis() again), or label ranks 'Rank (1 = best)'.")


def check_log_unlabeled(c: Ctx):
    titles = " ".join(r.label for r in title_like_texts(c))
    for i, ax in data_axes(c.fig):
        if not has_data(ax) or not ax.axison:
            continue
        for name in ("x", "y"):
            axis = getattr(ax, f"{name}axis")
            scale = axis.get_scale()
            if scale not in ("log", "symlog") or not axis.get_visible():
                continue
            notes = " ".join(r.label for r in c.texts if r.ax is ax and r.kind in ("text", "annotation"))
            if LOG_WORD_RE.search(f"{axis.label.get_text()} {titles} {notes}"):
                continue
            c.add("log-unlabeled", c.where(ax, f"{name}-axis"),
                  f"{scale} scale not stated in axis label, title, or subtitle",
                  "Say 'log scale' in the axis label or subtitle, and keep real-value ticks (1, 10, 100).")


def texts_3d(fig) -> list:
    """Visible, non-empty texts inside 3D axes (tick and axis labels) that collect_texts leaves out."""
    return [t for ax in fig.axes if getattr(ax, "name", "") == "3d" and ax.get_visible()
            for t in ax.findobj(match=Text) if t.get_visible() and t.get_text().strip() and t.get_fontsize() > 1.5]


def check_small_text(c: Ctx):
    width_in = c.fig.get_figwidth()
    if c.save_kwargs.get("bbox_inches") == "tight":
        try:
            pad = c.save_kwargs.get("pad_inches", 0.1)
            pad = 0.1 if not isinstance(pad, (int, float)) else pad
            width_in = c.fig.get_tightbbox(c.renderer).width + 2 * pad
        except Exception:
            pass
    dest_px, min_px = DEST_WIDTH_PX[c.dest], DEST_MIN_TEXT_PX[c.dest]
    px_per_pt = dest_px / (width_in * 72.0)
    known = {id(r.obj) for r in c.texts}
    texts = [(r.label, r.size) for r in c.texts] + [(t.get_text().strip(), float(t.get_fontsize()))
                                                     for t in texts_3d(c.fig) if id(t) not in known]
    small = [(s, size) for s, size in texts if size * px_per_pt < min_px - 1e-6]
    if not small:
        return
    smallest = min(size for _, size in small)
    need_pt = math.ceil(min_px / px_per_pt * 2) / 2
    examples = ", ".join(snip(s, 20) for s, _ in sorted(small, key=lambda t: t[1])[:3])
    c.add("small-text", c.where(None, examples),
          f"{len(small)} text(s) below {min_px} px at {dest_px} px wide ({c.dest}); smallest {smallest:g} pt = "
          f"{smallest * px_per_pt:.1f} px",
          f"Use at least {need_pt:g} pt text at this {width_in:.1f} in figure width, or shrink figsize.")


def check_tick_crowding(c: Ctx):
    gap_min = TICK_MIN_GAP_PT * c.px_per_pt
    for i, ax in data_axes(c.fig):
        for name in ("x", "y"):
            ticks = [r for r in c.texts if r.kind == "tick" and r.ax is ax and r.axis == name
                     and r.obj is not getattr(ax, f"{name}axis").get_offset_text()]
            if len(ticks) < 2:
                continue
            rotated = [r for r in ticks if min(r.angle, 180 - r.angle) > TICK_ROTATION_MAX_DEG]
            if name == "x" and rotated:
                ang = max(min(r.angle, 180 - r.angle) for r in rotated)
                c.add("tick-crowding", c.where(ax, "x-axis"), f"{len(rotated)} tick labels rotated {ang:.0f} deg",
                      "Switch to a horizontal bar chart or shorten labels instead of rotating them.")
                continue
            if any(r.angle % 90 for r in ticks):
                continue
            k0, k1 = (0, 2) if name == "x" else (1, 3)
            # Group by side (label1 vs label2): which side of the axes center.
            axbox = ax.get_window_extent(c.renderer)
            mid = (axbox.y0 + axbox.y1) / 2 if name == "x" else (axbox.x0 + axbox.x1) / 2
            sides: dict[bool, list[TextRec]] = {}
            for r in ticks:
                sides.setdefault((r.cy if name == "x" else r.cx) > mid, []).append(r)
            tight = 0
            for group in sides.values():
                group.sort(key=lambda r: r.aabb[k0])
                for a, b in zip(group, group[1:]):
                    if id(a.obj) in c.overlapping_ticks and id(b.obj) in c.overlapping_ticks:
                        continue
                    if b.aabb[k0] - a.aabb[k1] < gap_min:
                        tight += 1
            if tight:
                rows = DEST_BAR_ROWS.get(c.dest)
                fix = ("Use fewer ticks (MaxNLocator) or shorter tick labels." if all(value_tick(r.label) for r in ticks)
                       else f"Every category needs its label, and {c.dest} has a fixed height: about {rows} bar rows fit, "
                       "so show fewer rows (the top ones, the rest grouped as Other) or split the set across panels."
                       if name == "y" and c.dest in DEST_FIXED_HEIGHT
                       else "Every category needs its label: use a taller canvas or fewer categories (group the rest)."
                       if name == "y" else "Every category needs its label: switch to horizontal bars, widen the "
                       "canvas, or use fewer categories.")
                c.add("tick-crowding", c.where(ax, f"{name}-axis"), f"{tight} adjacent tick label pair(s) nearly touch", fix)


def check_too_many_series(c: Ctx):
    for i, ax in data_axes(c.fig):
        line_colors = {color_key(ln.get_color()) for ln in data_lines(ax) if not is_neutral(ln.get_color())}
        if len(line_colors) > MAX_LINE_COLORS:
            c.add("too-many-series", c.where(ax), f"{len(line_colors)} distinct line colors",
                  "Highlight 1-3 key series in color and gray the rest, or use small multiples.")
        cat = set()
        for cont in ax.containers:
            if isinstance(cont, BarContainer):
                cat |= {color_key(p.get_facecolor()) for p in cont.patches if not is_neutral(p.get_facecolor())}
        for coll in ax.collections:
            if type(coll).__name__ == "Poly3DCollection":
                # bar3d shades each face by scaling RGB, which keeps hue and saturation.
                cat |= {"%.2f/%.2f" % colorsys.rgb_to_hsv(*to_rgba(fc)[:3])[:2] for fc in coll.get_facecolors()
                        if not is_neutral(fc)}
                continue
            # One scatter call with one color is one category. Per-point
            # color lists are usually a hand-rolled continuous scale: skip.
            if isinstance(coll, PathCollection) and coll.get_array() is None:
                fcs = {color_key(fc) for fc in coll.get_facecolors() if not is_neutral(fc)}
                if len(fcs) == 1:
                    cat |= fcs
        if len(cat) > MAX_CATEGORICAL_COLORS:
            c.add("too-many-series", c.where(ax), f"{len(cat)} distinct categorical colors",
                  "Group minor categories into 'Other' or highlight a few and gray the rest.")


def check_spines_gridlines(c: Ctx):
    for i, ax in data_axes(c.fig):
        if getattr(ax, "name", "") != "rectilinear" or not ax.axison or not has_data(ax):
            continue
        spines = [ax.spines[s] for s in ("top", "right", "bottom", "left") if s in ax.spines]
        if len(spines) < 4 or not all(sp.get_visible() and sp.get_linewidth() > 0
                                      and sp.get_edgecolor()[3] > 0 for sp in spines):
            continue

        def grid_on(axis):
            return any(t.gridline.get_visible() for t in drawn_ticks(axis) if t in axis.get_major_ticks())

        if grid_on(ax.xaxis) and grid_on(ax.yaxis):
            c.add("spines-gridlines", c.where(ax), "all four spines plus gridlines on both axes",
                  "Remove top/right spines and keep light gridlines on the value axis only.")


def scatter_points(ax, renderer):
    """Visible scatter dots in display px: (xy [N, 2], radius px [N], collection index [N], collections)."""
    xys, rads, owner, colls = [], [], [], []
    box = ax.get_window_extent(renderer)
    for coll in ax.collections:
        if not isinstance(coll, PathCollection) or not coll.get_visible():
            continue
        off = np.asarray(coll.get_offsets(), dtype=float)
        if not off.size:
            continue
        xy = coll.get_offset_transform().transform(off)
        sizes = np.atleast_1d(coll.get_sizes()).astype(float)
        sizes = sizes if len(sizes) else np.array([plt.rcParams["lines.markersize"] ** 2])
        r = np.sqrt(np.resize(sizes, len(xy))) / 2 * ax.figure.dpi / 72
        ok = np.all(np.isfinite(xy), axis=1) & (xy[:, 0] >= box.x0 - r) & (xy[:, 0] <= box.x1 + r) \
            & (xy[:, 1] >= box.y0 - r) & (xy[:, 1] <= box.y1 + r)
        colls.append(coll)
        xys.append(xy[ok])
        rads.append(r[ok])
        owner.append(np.full(int(ok.sum()), len(colls) - 1))
    if not colls:
        return None
    return np.concatenate(xys), np.concatenate(rads), np.concatenate(owner), colls


def leader_ends(c: Ctx) -> list:
    """(start, end, is_arrow) px of annotation arrows and 2-point lines: candidate leader lines."""
    if not len(c.segs):
        return []
    owner = c.segs[:, 12].astype(int)
    counts = np.bincount(owner)
    _, first = np.unique(owner, return_index=True)
    return [(c.segs[i, 8:10], c.segs[i, 10:12], c.owners[owner[i]].kind == "arrow") for i in first
            if c.owners[owner[i]].kind == "arrow" or counts[owner[i]] == 1]


def has_leader(r: TextRec, leaders, xy, rad, lh, tol) -> bool:
    """True if a leader starts at the text (within one line height) and ends on a dot. A plain
    2-point line must not start on a dot too, or dumbbell and slope segments would count."""
    def on_dot(q):
        return bool(np.any(np.hypot(xy[:, 0] - q[0], xy[:, 1] - q[1]) <= rad + tol))
    for a, b, arrow in leaders:
        for near, far in ((a, b), (b, a)):
            if box_gaps(r, np.array([near]), np.zeros(1))[0] <= lh and (arrow or not on_dot(near)) and on_dot(far):
                return True
    return False


def box_gaps(r: TextRec, xy, rad):
    """Gap (px) from each dot's edge to the nearest glyph line box of text r (0 if they touch)."""
    best = np.full(len(xy), np.inf)
    for x0, y0, x1, y1 in (r.lines or [r.aabb]):
        dx = np.maximum.reduce([x0 - xy[:, 0], np.zeros(len(xy)), xy[:, 0] - x1])
        dy = np.maximum.reduce([y0 - xy[:, 1], np.zeros(len(xy)), xy[:, 1] - y1])
        best = np.minimum(best, np.hypot(dx, dy))
    return np.maximum(best - rad, 0.0)


def data_coords(ax, p) -> str:
    try:
        dx, dy = ax.transData.inverted().transform(p)
        return f"({dx:.4g}, {dy:.4g})"
    except Exception:
        return "(?)"


def aligned(r: TextRec, xy, rad):
    """Per dot: 2 if its center is within the text's height (label beside it), 1 if under or over the
    middle half of its width (label above or below it), else 0."""
    x0, y0, x1, y1 = r.aabb
    row = (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
    col = np.abs(xy[:, 0] - (x0 + x1) / 2) <= (x1 - x0) / 4 + rad
    return np.where(row, 2, np.where(col, 1, 0))


def line_paths(ax):
    """Display-px segments [N, 4] of every drawn line in ax: data lines, reference rules, line collections."""
    out = []
    for ln in ax.lines:
        if ln.get_visible() and ln.get_linestyle() not in ("None", "none", " ", "") and ln.get_linewidth() > 0:
            out.append(ln.get_transform().transform(np.asarray(ln.get_xydata(), dtype=float)))
    for coll in ax.collections:
        if isinstance(coll, LineCollection) and coll.get_visible():
            out += [coll.get_transform().transform(np.asarray(seg, dtype=float)) for seg in coll.get_segments()]
    segs = [np.hstack([p[:-1], p[1:]]) for p in out if len(p) >= 2]
    segs = np.vstack(segs) if segs else np.zeros((0, 4))
    return segs[np.all(np.isfinite(segs), axis=1)]


def line_label(r: TextRec, segs, anchor, reach) -> bool:
    """True if text r is anchored on a line vertex, or a line passes within `reach` px (its nearest dot's gap) of its box."""
    if not len(segs):
        return False
    if anchor is not None and np.hypot(*(segs.reshape(-1, 2) - anchor).T).min() <= 2:
        return True
    x0, y0, x1, y1 = r.aabb[0] - reach, r.aabb[1] - reach, r.aabb[2] + reach, r.aabb[3] + reach
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    near = (np.maximum(segs[:, 0], segs[:, 2]) >= x0) & (np.minimum(segs[:, 0], segs[:, 2]) <= x1) & \
        (np.maximum(segs[:, 1], segs[:, 3]) >= y0) & (np.minimum(segs[:, 1], segs[:, 3]) <= y1)
    return any(seg_clip_convex(s[:2], s[2:], box) is not None for s in segs[near])


def check_label_ambiguous(c: Ctx):
    """Heuristic: a reader pairs a point label with the dot nearest its glyphs.

    Point labels are axes texts and arrowless annotations of at most
    LABEL_MAX_WORDS words within LABEL_GATE_RADII marker radii plus one line
    height of a scatter (PathCollection) dot. Skipped: titles, ticks, axis
    labels, legends, far-off notes, sentences (callouts), labels whose leader
    line (annotation arrow or 2-point line) lands on a dot, free text with
    no known own dot lying on LABEL_DENSE_DOTS or more dots (lettering over a
    point field), and labels not anchored on a dot that are anchored on a
    line vertex or lie nearer a drawn line than any dot (line end labels,
    reference rules, median ticks).
    Gaps run from dot edge to glyph box, padded by LABEL_PAD_FRAC line height.
    The own dot is the annotation's xy when it lands on a dot, else the dot of
    the scatter whose legend label equals the text, else the nearest dot
    (preferring one aligned with the label within LABEL_AMBIG_RATIO). Warn
    when a known own dot is farther than a rival, or a rival is within
    LABEL_AMBIG_RATIO of the own gap. A rival less aligned with the label
    than the own dot (see aligned) must instead be nearer by more than
    LABEL_PAD_FRAC line height. Dots within LABEL_SAME_POINT_FRAC of the own
    radius read as one blob (or one point drawn twice) and are not rivals.
    """
    cache, lines, leaders = {}, {}, None
    for r in c.texts:
        if r.kind not in ("text", "annotation") or r.ax is None:
            continue
        if id(r.ax) not in cache:
            cache[id(r.ax)] = scatter_points(r.ax, c.renderer)
        pts = cache[id(r.ax)]
        if pts is None or len(pts[0]) < 2:
            continue
        xy, rad, owner, colls = pts
        t = r.obj
        if isinstance(t, Annotation) and getattr(t, "arrow_patch", None) is not None and t.arrow_patch.get_visible():
            continue
        if len(r.label.split()) > LABEL_MAX_WORDS:
            continue
        lh = r.h / max(len(r.lines), 1) if not r.rotated else r.h
        gaps = box_gaps(r, xy, rad)
        if np.all(gaps + rad > LABEL_GATE_RADII * rad + lh):
            continue  # a note, not a point label
        if leaders is None:
            leaders = leader_ends(c)
        if has_leader(r, leaders, xy, rad, lh, LEADER_TOL_PT * c.px_per_pt):
            continue  # a leader line from the label lands on a dot and names it
        own, known, axy = None, False, None
        if isinstance(t, Annotation):
            try:
                axy = t._get_xy(c.renderer, t.xy, t.xycoords)
                d = np.hypot(xy[:, 0] - axy[0], xy[:, 1] - axy[1])
                k = int(np.argmin(d))
                if d[k] <= rad[k] + 2:
                    own, known = k, True
            except Exception:
                pass
        if not known:
            if id(r.ax) not in lines:
                lines[id(r.ax)] = line_paths(r.ax)
            if line_label(r, lines[id(r.ax)], axy, gaps.min()):
                continue  # labels a line, reference rule, or median tick, not a dot
        if own is None:
            named = [i for i, coll in enumerate(colls) if (coll.get_label() or "").strip() == r.label]
            if len(named) == 1:
                idx = np.nonzero(owner == named[0])[0]
                if len(idx):
                    own, known = int(idx[np.argmin(gaps[idx])]), True
        pad = LABEL_PAD_FRAC * lh
        eff = gaps + pad
        al = aligned(r, xy, rad)
        if own is None:
            if len(np.unique(np.round(xy[gaps <= 0]), axis=0)) >= LABEL_DENSE_DOTS:
                continue  # free lettering over a dense point field (e.g. axis years on a radial chart)
            own = int(np.argmin(eff))
            ok = np.nonzero((al > al[own]) & (eff <= LABEL_AMBIG_RATIO * eff[own]))[0]
            if len(ok):
                own = int(ok[np.lexsort((eff[ok], -al[ok]))[0]])
        rivals = np.hypot(xy[:, 0] - xy[own, 0], xy[:, 1] - xy[own, 1]) > LABEL_SAME_POINT_FRAC * max(rad[own], 1.0)
        if not rivals.any():
            continue
        # A dot on the label's row (label beside it) or under its middle
        # (label above/below it) is the reader's first pick. A less aligned
        # rival, such as one grazing the label's top or bottom edge, must be
        # nearer by more than LABEL_PAD_FRAC line height before it misleads.
        closer = eff < eff[own]
        near = eff <= LABEL_AMBIG_RATIO * eff[own]
        loose = al < al[own]
        clear = gaps + pad < gaps[own]
        closer, near = np.where(loose, clear, closer), np.where(loose, clear, near)
        fire = rivals & ((closer & known) | near)
        if not fire.any():
            continue
        cand = np.nonzero(fire)[0]
        k = int(cand[np.argmin(eff[cand])])
        closer = bool(known and eff[k] * LABEL_AMBIG_RATIO < eff[own])  # else "about equally"
        at = lambda i: data_coords(r.ax, xy[i])  # noqa: E731
        go, gk = gaps[own] / c.px_per_pt, gaps[k] / c.px_per_pt
        detail = (f"nearer the dot at {at(k)} ({gk:.0f} pt) than its own at {at(own)} ({go:.0f} pt)" if closer else
                  f"about equally near the dots at {at(own)} ({go:.0f} pt) and {at(k)} ({gk:.0f} pt)")
        c.add("label-ambiguous", c.where(r.ax, f"{r.kind} {snip(r.label)}"), detail,
              "Put the label on the side of its dot away from neighbors, tight to the dot, or add a short leader line.")


def layer_edges(coll):
    """(xs, lo, hi) of a filled area's lower and upper edge per x in data units, or None if not an x-filled area."""
    paths = coll.get_paths()
    if len(paths) != 1:
        return None
    v = np.asarray(paths[0].vertices, dtype=float)
    v = v[np.all(np.isfinite(v), axis=1)]
    if len(v) < 4:
        return None
    xs, inv = np.unique(np.round(v[:, 0], 9), return_inverse=True)
    lo, hi = np.full(len(xs), np.inf), np.full(len(xs), -np.inf)
    np.minimum.at(lo, inv, v[:, 1])
    np.maximum.at(hi, inv, v[:, 1])
    return xs, lo, hi


def area_layers(ax):
    """Filled areas (fill_between / stackplot) in ax as (xs, lo, hi) edges."""
    out = []
    for coll in ax.collections:
        if isinstance(coll, PolyCollection) and coll.get_visible() and type(coll).__name__ != "Poly3DCollection":
            e = layer_edges(coll)
            if e is not None and len(e[0]) >= 3:
                out.append(e)
    return out


def sits_on(b, a, tol):
    """True if area b's lower edge is area a's upper edge over (nearly) all shared x."""
    common, ia, ib = np.intersect1d(a[0], b[0], return_indices=True)
    if len(common) < 3 or not np.any(b[2][ib] - b[1][ib] > tol):
        return False
    return np.mean(np.abs(b[1][ib] - a[2][ia]) <= tol) >= 0.9


def stack_depth(layers, tol):
    """Longest chain of areas each sitting on the one below."""
    on = {j: [i for i in range(len(layers)) if i != j and sits_on(layers[j], layers[i], tol)] for j in range(len(layers))}
    memo = {}

    def depth(j, seen=()):
        if j not in memo:
            memo[j] = 1 + max([depth(i, seen + (j,)) for i in on[j] if i not in seen], default=0)
        return memo[j]
    return max((depth(j) for j in range(len(layers))), default=0)


def check_stacked_area(c: Ctx):
    for i, ax in data_axes(c.fig):
        layers = area_layers(ax)
        if len(layers) <= STACK_MAX_LAYERS:
            continue
        lo, hi = ax.get_ylim()
        n = stack_depth(layers, 1e-6 * max(abs(hi - lo), 1e-12))
        if n > STACK_MAX_LAYERS:
            c.add("stacked-area", c.where(ax), f"stacked area with {n} layers",
                  "Use small multiples or lines for each series; keep a stack for 2 layers or a total that matters.")


def only_rises(y) -> bool:
    """A running total: enough points, never falls, rises on most steps, and starts near 1/n of its end."""
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if len(y) < CUMULATIVE_MIN_POINTS:
        return False
    d = np.diff(y)
    span = max(np.abs(y).max(), 1e-12)
    return bool(np.all(d >= -1e-9 * span) and np.mean(d > 1e-9 * span) >= CUMULATIVE_STEP_FRAC
                and 0 <= y[0] <= CUMULATIVE_START_MULT / len(y) * y[-1])


def check_cumulative_as_rate(c: Ctx):
    titles = " ".join(r.label for r in title_like_texts(c))
    for i, ax in data_axes(c.fig):
        words = " ".join([ax.yaxis.label.get_text(), ax.get_title(), ax.get_title("left"), titles])
        if not RATE_RE.search(words) or CUMULATIVE_RE.search(words):
            continue
        series = []
        for ln in data_lines(ax):
            xy = np.asarray(ln.get_xydata(), dtype=float)
            xy = xy[np.all(np.isfinite(xy), axis=1)]
            if len(xy) and np.all(np.diff(xy[:, 0]) > 0):
                series.append((line_name(ln, ln.get_color()), xy[:, 1]))
        layers = area_layers(ax)
        lo_, hi_ = ax.get_ylim()
        tol = 1e-6 * max(abs(hi_ - lo_), 1e-12)
        for k, (xs, lo, hi) in enumerate(layers):  # areas to zero or stacked on another area: their own values
            if np.all(np.abs(lo) <= tol) or any(sits_on((xs, lo, hi), a, tol) for j, a in enumerate(layers) if j != k):
                series.append((f"area layer {k + 1}", hi - lo))
        hits = [name for name, y in series if only_rises(y)]
        if hits:
            c.add("cumulative-as-rate", c.where(ax, ", ".join(hits)[:80]),
                  f"{len(hits)} series only ever rise, like a running total, under a rate/share/% label",
                  "Plot per-period values (np.diff of the running total) for a rate, or say 'Cumulative' in the label.")


def check_plot_area_tiny(c: Ctx):
    fw, fh = c.fig.bbox.width, c.fig.bbox.height
    for i, ax in data_axes(c.fig):
        spec = ax.get_subplotspec() if hasattr(ax, "get_subplotspec") else None
        if spec is None or not has_data(ax):
            continue  # insets and hand-placed axes are small on purpose
        nrows, ncols = spec.get_gridspec().get_geometry()
        box = ax.get_position(original=True)
        min_w, min_h = PLOT_TINY_FRAC * min(1, 3 / ncols), PLOT_TINY_FRAC * min(1, 3 / nrows)
        small = [f"{name} {v:.0%} < {m:.0%}" for name, v, m in (("width", box.width, min_w), ("height", box.height, min_h))
                 if v < m]
        if small:
            c.add("plot-area-tiny", c.where(ax), f"plot area {' and '.join(small)} of the figure "
                  f"({box.width * fw / c.px_per_pt:.0f} x {box.height * fh / c.px_per_pt:.0f} pt)",
                  "Shorten or wrap long tick labels, cut the title block, or give panels more room (fewer columns).")


def check_plot_area_underused(c: Ctx):
    if c.dest not in NARROW_DESTS:
        return
    axes = [ax for _, ax in data_axes(c.fig) if has_data(ax) and getattr(ax, "get_subplotspec", lambda: None)()]
    if len(axes) != 1:
        return
    ax, fw = axes[0], c.fig.bbox.width
    ml, mr = DEST_MARGINS.get(c.dest, (0.05, 0.05))
    usable = fw * (1 - ml - mr)
    box, tight = ax.get_window_extent(c.renderer), ax.get_tightbbox(c.renderer)
    empty = max(0.0, tight.x0 - ml * fw) + max(0.0, fw * (1 - mr) - tight.x1)
    if box.width < PLOT_UNDERUSED_FRAC * usable and empty >= PLOT_EMPTY_FRAC * usable:
        c.add("plot-area-underused", c.where(ax), f"plot box {box.width / usable:.0%} of the usable width; "
              f"{empty / usable:.0%} left empty beside the axes",
              "Let the plot take the full width: drop set_box_aspect/set_aspect('equal') on narrow canvases and let "
              "ev.save refit the margins.")


def check_plot_aspect(c: Ctx):
    main = main_title(c)
    if main is not None and any(value_tick(r.label) and r.size > main.size for r in title_like_texts(c)):
        return  # big-number card: its visual is small by design (LY-6)
    got = plot_aspect(c.fig)
    if not got or not got[2]:
        return
    ax, ratio, verdict = got
    shape = f"{ratio:.1f}:1" if verdict == "wide" else f"1:{1 / ratio:.1f}"
    if verdict == "tall":
        fix = "Use a shorter canvas (ev.figure(dest, height=...)) or turn it into horizontal bars."
    elif c.dest in DEST_FIXED_HEIGHT:
        fix = (f"{c.dest} has a fixed height: cut the title and subtitle to one line each (ev.fits_title(text, dest, "
               "lines=1), ev.fits_subtitle), or export the chart without them (ev.titles(fig, None, source=...)) and "
               "put the title in the slide's title placeholder or the post text.")
    else:
        fix = "Cut the title block or give the canvas more height (ev.figure(dest, height=...))."
    c.add("plot-aspect", c.where(ax), f"plot area {shape} (width:height), outside the "
          f"{ASPECT['widest']:g}:1 to 1:{1 / ASPECT['tallest']:g} band", fix)


# ---------------------------------------------------------------------------
# Color: cvd, contrast, text-on-area
# ---------------------------------------------------------------------------

def over(color, under) -> str:
    """Hex of an RGBA color painted over an opaque backdrop."""
    r, g, b, a = to_rgba(color)
    u = to_rgba(under)
    return to_hex((r * a + u[0] * (1 - a), g * a + u[1] * (1 - a), b * a + u[2] * (1 - a)))


def figure_bg(c) -> str:
    fc = c.save_kwargs.get("facecolor", "auto")
    if c.save_kwargs.get("transparent"):
        return "#ffffff"  # judged on the usual white page
    return over(c.fig.get_facecolor() if fc in (None, "auto") else fc, "#ffffff")


def axes_bg(c, ax) -> str:
    base = figure_bg(c)
    if ax is None or not (ax.axison and ax.get_frame_on() and ax.patch.get_visible()):
        return base
    return over(ax.patch.get_facecolor(), base)


def dense(pts, step=1.5):
    """Points every `step` px along a polyline [N, 2], skipping non-finite vertices."""
    pts = np.asarray(pts, dtype=float).reshape(-1, 2)
    seg = np.hstack([pts[:-1], pts[1:]]) if len(pts) > 1 else np.zeros((0, 4))
    seg = seg[np.all(np.isfinite(seg), axis=1)]
    if not len(seg):
        return pts[np.all(np.isfinite(pts), axis=1)]
    n = np.maximum((np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]) / step).astype(int), 1)
    n = np.minimum(n, 2000)
    counts = n + 1
    idx = np.repeat(np.arange(len(seg)), counts)
    t = (np.arange(counts.sum()) - np.repeat(np.cumsum(counts) - counts, counts)) / np.repeat(n, counts)
    return seg[idx, :2] + (seg[idx, 2:] - seg[idx, :2]) * t[:, None]


def dash_key(pattern):
    """Comparable dash pattern from an (offset, seq) pair; None is solid."""
    seq = pattern[1] if isinstance(pattern, tuple) and len(pattern) == 2 else None
    return tuple(np.round(seq, 1)) if seq is not None else None


def marker_key(path):
    return tuple(np.round(path.vertices, 2).ravel()) if path is not None else None


def hue(color) -> float:
    return colorsys.rgb_to_hsv(*to_rgba(color)[:3])[0] * 360


def hue_gap(a, b) -> float:
    d = abs(hue(a) - hue(b)) % 360
    return min(d, 360 - d)


@dataclass
class Series:
    """One data color in an axes: every artist drawn in the same opaque hex is one series (a line and its band)."""
    hex: str
    alpha: float = 0.0
    marks: set = field(default_factory=set)     # line, point, bar, area
    names: set = field(default_factory=set)     # artist labels
    styles: set = field(default_factory=set)    # (mark, dash, marker, hatch) per artist
    bars: set = field(default_factory=set)      # ids of the bar containers holding it
    pts: list = field(default_factory=list)     # display px along its marks, then one array
    rads: list = field(default_factory=list)
    paths: list = field(default_factory=list)   # display-px filled outlines
    edge_cr: float = 0.0                        # best outline contrast against the background

    def name(self) -> str:
        return snip(sorted(self.names)[0], 30) if self.names else f"{'/'.join(sorted(self.marks))} {self.hex}"


def color_series(c, ax) -> list:
    """Data colors in ax that tell series apart. Grays and near-black (is_neutral), colormapped artists (scales, not
    categories), per-point color lists of more than MAX_CATEGORICAL_COLORS, and reference lines are left out."""
    if id(ax) in c.series:
        return c.series[id(ax)]
    bg, px, out = axes_bg(c, ax), c.px_per_pt, {}

    def add(color, mark, label, style, pts, rads=0.0, paths=(), bar=None, edge=None):
        rgba = to_rgba(color)
        if rgba[3] == 0 or is_neutral(rgba):
            return
        s = out.setdefault(color_key(rgba), Series(color_key(rgba)))
        s.alpha = max(s.alpha, rgba[3])
        s.marks.add(mark)
        s.styles.add((mark, *style))
        if label and not label.startswith("_"):
            s.names.add(" ".join(label.split()))
        pts = np.asarray(pts, dtype=float).reshape(-1, 2)
        s.pts.append(pts)
        s.rads.append(np.resize(np.asarray(rads, dtype=float), len(pts)))
        s.paths += list(paths)
        if bar is not None:
            s.bars.add(bar)
        if edge is not None:
            s.edge_cr = max(s.edge_cr, contrast(over(edge, bg), bg))

    grid = (ax.get_xaxis_transform(which="grid"), ax.get_yaxis_transform(which="grid"))
    for ln in ax.lines:
        if not ln.get_visible() or ln.get_transform() in grid or type(ln).__name__ == "_AxLine":
            continue
        xy = np.asarray(ln.get_xydata(), dtype=float)
        mk = ln.get_marker() if ln.get_marker() not in (None, "None", "none", "", " ") and ln.get_markersize() > 0 \
            else None
        mpath = None
        if mk is not None:
            ms = MarkerStyle(mk)
            mpath = ms.get_path().transformed(ms.get_transform())
        pts = ln.get_transform().transform(xy)
        if ln.get_linestyle() not in ("None", "none", " ", "") and ln.get_linewidth() > 0:
            if len(xy) < 2 or is_reference_line(ln, ax):
                continue
            ds = ln.get_drawstyle()
            if ds and ds != "default" and ds in STEP_LOOKUP_MAP:
                pts = ln.get_transform().transform(np.column_stack(STEP_LOOKUP_MAP[ds](xy[:, 0], xy[:, 1])))
            add(to_rgba(ln.get_color(), ln.get_alpha()), "line", ln.get_label(),
                (dash_key(getattr(ln, "_unscaled_dash_pattern", None)), marker_key(mpath), None), dense(pts))
        elif mk is not None and to_rgba(ln.get_color(), ln.get_alpha())[3] >= 0.2:
            fc = ln.get_markerfacecolor()
            fc = fc if to_rgba(fc)[3] > 0 else ln.get_markeredgecolor()
            add(to_rgba(fc, ln.get_alpha()), "point", ln.get_label(), (None, marker_key(mpath), None), pts,
                ln.get_markersize() / 2 * px)
    for coll in ax.collections:
        if not coll.get_visible() or type(coll).__name__ == "Poly3DCollection" or coll.get_array() is not None:
            continue
        if isinstance(coll, PathCollection):
            off = np.asarray(coll.get_offsets(), dtype=float)
            if not off.size:
                continue
            xy = coll.get_offset_transform().transform(off)
            fcs = coll.get_facecolors()
            if not len(fcs) or np.all(fcs[:, 3] == 0):
                fcs = coll.get_edgecolors()
            if not len(fcs):
                continue
            keys = np.array([color_key(f) for f in fcs])
            keys, fcs = np.resize(keys, len(xy)), np.resize(fcs, (len(xy), 4))
            uniq = [k for k in dict.fromkeys(keys) if not is_neutral(k)]
            if len(uniq) > MAX_CATEGORICAL_COLORS:
                continue
            sizes = np.atleast_1d(coll.get_sizes()).astype(float)
            sizes = sizes if len(sizes) else np.array([plt.rcParams["lines.markersize"] ** 2])
            r = np.sqrt(np.resize(sizes, len(xy))) / 2 * px
            mpath = coll.get_paths()[0] if coll.get_paths() else None
            for k in uniq:
                m = keys == k
                add(fcs[np.argmax(m)], "point", coll.get_label() if len(uniq) == 1 else None,
                    (None, marker_key(mpath), None), xy[m], r[m])
        elif isinstance(coll, LineCollection):
            ecs, segs = coll.get_edgecolors(), coll.get_segments()
            if not len(ecs) or not segs:
                continue
            dashed = dash_key(coll.get_linestyles()[0])
            tr = coll.get_transform()
            for k, seg in enumerate(segs):
                ec = ecs[k % len(ecs)]
                if len(seg) >= 2 and ec[3] >= (0.6 if dashed else 0.2):
                    add(ec, "line", coll.get_label(), (dashed, None, None), dense(tr.transform(np.asarray(seg))))
        elif isinstance(coll, PolyCollection) and len(coll.get_offsets()) <= 1:
            fcs, ecs, tr = coll.get_facecolors(), coll.get_edgecolors(), coll.get_transform()
            lw = np.atleast_1d(coll.get_linewidths())
            for k, path in enumerate(coll.get_paths()):
                if not len(fcs):
                    break
                dp = tr.transform_path(path)
                edge = ecs[k % len(ecs)] if len(ecs) and lw[k % len(lw)] > 0 else None
                add(fcs[k % len(fcs)], "area", coll.get_label(), (None, None, coll.get_hatch()),
                    np.vstack([dense(q) for q in dp.to_polygons()] or [np.zeros((0, 2))]), paths=[dp], edge=edge)
    for cont in ax.containers:
        if not isinstance(cont, BarContainer):
            continue
        for p in cont.patches:
            if not p.get_visible() or not p.get_width() or not p.get_height():
                continue
            b = p.get_window_extent(c.renderer)
            ring = [(b.x0, b.y0), (b.x1, b.y0), (b.x1, b.y1), (b.x0, b.y1), (b.x0, b.y0)]
            fc = p.get_facecolor() if p.get_facecolor()[3] > 0 else p.get_edgecolor()
            add(fc, "bar", cont.get_label(), (None, None, p.get_hatch()), dense(ring), paths=[MplPath(ring)],
                bar=id(cont), edge=p.get_edgecolor() if p.get_linewidth() > 0 else None)
    for p in data_patches(ax):
        dp = p.get_transform().transform_path(p.get_path())
        add(p.get_facecolor(), "area", p.get_label(), (None, None, p.get_hatch()),
            np.vstack([dense(q) for q in dp.to_polygons()] or [np.zeros((0, 2))]), paths=[dp],
            edge=p.get_edgecolor() if p.get_linewidth() > 0 else None)
    for s in out.values():
        s.pts, s.rads = np.concatenate(s.pts), np.concatenate(s.rads)
    c.series[id(ax)] = list(out.values())
    return c.series[id(ax)]


def data_patches(ax) -> list:
    """Filled data shapes other than bars: pie wedges and data-space polygons (ax.fill), not spans or arrows."""
    return [p for p in ax.patches if p.get_visible() and p.get_fill() and isinstance(p, (Wedge, Polygon, PathPatch))
            and p.get_data_transform() is ax.transData]


def series_gap(r: TextRec, s: Series) -> float:
    """Gap (px) from text r's glyph boxes to the nearest mark of series s (0 inside one of its fills)."""
    if any(p.contains_point((r.cx, r.cy)) for p in s.paths):
        return 0.0
    if not len(s.pts):
        return math.inf
    best = math.inf
    for x0, y0, x1, y1 in r.lines or [r.aabb]:
        dx = np.maximum(np.maximum(x0 - s.pts[:, 0], s.pts[:, 0] - x1), 0)
        dy = np.maximum(np.maximum(y0 - s.pts[:, 1], s.pts[:, 1] - y1), 0)
        best = min(best, float((np.hypot(dx, dy) - s.rads).min()))
    return max(best, 0.0)


def names_series(r: TextRec, s: Series, rival: Series | None) -> bool:
    """Text r names s: it contains s's label as a word, or (any series) shares s's hue and not the rival's."""
    text = " ".join(r.label.lower().split())
    if any(re.search(rf"(?<!\w){re.escape(n.lower())}(?!\w)", text) for n in s.names):
        return True
    tc = r.obj.get_color()
    return not is_neutral(tc) and hue_gap(tc, s.hex) <= HUE_MATCH_DEG and (
        rival is None or hue_gap(tc, rival.hex) > HUE_MATCH_DEG)


def direct_labeled(c, ax, s: Series, rival: Series | None = None) -> bool:
    """A text names s next to its mark (within DIRECT_LABEL_REACH_LINES line heights and nearer s than the rival),
    or an annotation naming s points at it."""
    for r in c.texts:
        near = r.kind in ("text", "annotation") and r.ax is ax or r.kind == "figtext"
        if not near or not names_series(r, s, rival):
            continue
        if isinstance(r.obj, Annotation) and len(s.pts):
            try:
                a = r.obj._get_xy(c.renderer, r.obj.xy, r.obj.xycoords)
                if (np.hypot(s.pts[:, 0] - a[0], s.pts[:, 1] - a[1]) - s.rads).min() <= LEADER_TOL_PT * c.px_per_pt:
                    return True
            except Exception:
                pass
        g = series_gap(r, s)
        if g <= DIRECT_LABEL_REACH_LINES * r.h / max(len(r.lines), 1) and (rival is None or g <= series_gap(r, rival)):
            return True
    return False


def redundant_cue(c, ax, a: Series, b: Series) -> str | None:
    """What besides color tells a from b, or None."""
    if a.bars & b.bars:
        return "bar position in one bar series"
    shared = a.marks & b.marks
    if not shared or any({st for st in a.styles if st[0] == m}.isdisjoint({st for st in b.styles if st[0] == m})
                         for m in shared):
        return "dash, marker, hatch, or mark type"
    if direct_labeled(c, ax, a, b) and direct_labeled(c, ax, b, a):
        return "direct labels"
    return None


def check_cvd(c: Ctx):
    for i, ax in data_axes(c.fig):
        bg = axes_bg(c, ax)
        series = color_series(c, ax)
        cols = {id(s): Color(over((*to_rgba(s.hex)[:3], s.alpha), bg)) for s in series}
        for n, a in enumerate(series):
            for b in series[n + 1:]:
                ca, cb = cols[id(a)], cols[id(b)]
                floor = max(DE_FLOOR[m] for m in a.marks | b.marks) * CVD_FACTOR
                d = {v: de(ca, cb, v) for v in ("protan", "deutan", "tritan")}
                red_green = [v for v in ("protan", "deutan") if d[v] < floor]
                if not red_green and d["tritan"] >= floor:
                    continue
                cue = redundant_cue(c, ax, a, b)
                if cue and not red_green:
                    continue  # tritan-only and redundantly encoded
                v = min(red_green or ["tritan"], key=d.get)
                detail = (f"{ca.hex}~{cb.hex} dE00 {d[v]:.1f} under {v} (floor {floor:.1f}; normal {de(ca, cb):.1f})"
                          + (f"; told apart only by {cue}" if cue else "; color is the only cue"))
                fix = ("Direct-label each series at its mark (ev.label_lines), or vary dash or marker; better, use "
                       "palettes.json slots that stay distinct (blue #0072B2 vs vermillion #D55E00).")
                c.add("cvd", c.where(ax, f"{a.name()} x {b.name()}"), detail, fix,
                      severity="fail" if red_green and not cue else "warn")


def is_large(r: TextRec) -> bool:
    w = r.obj.get_fontweight()
    w = w if isinstance(w, (int, float)) else {"semibold": 600, "demibold": 600, "demi": 600, "bold": 700,
                                               "heavy": 800, "extra bold": 800, "black": 900}.get(str(w), 400)
    return r.size >= LARGE_TEXT_PT or (w >= 700 and r.size >= LARGE_BOLD_PT)


def text_backdrop(c, r: TextRec, frames: dict) -> str:
    """Color behind text r: its box, halo, or legend frame; else a bar under its center; else axes or figure."""
    t = r.obj
    ax = next((a for _, a in data_axes(c.fig) if a.get_window_extent(c.renderer).contains(r.cx, r.cy)), None)
    base = axes_bg(c, ax) if ax is not None else figure_bg(c)
    if id(t) in frames:
        return over(frames[id(t)], base)
    patch = t.get_bbox_patch()
    if patch is not None and patch.get_visible() and patch.get_fill() and patch.get_facecolor()[3] > 0:
        return over(patch.get_facecolor(), base)
    for pe in t.get_path_effects() or []:
        if isinstance(pe, patheffects.Stroke) and pe._gc.get("foreground") is not None:
            return over(pe._gc["foreground"], base)
    if ax is None:
        return base
    under = None
    for cont in ax.containers:
        if isinstance(cont, BarContainer):
            for p in cont.patches:
                if p.get_visible() and p.get_zorder() <= r.zorder and \
                        p.get_window_extent(c.renderer).contains(r.cx, r.cy) and p.get_facecolor()[3] > 0:
                    under = p.get_facecolor()
    for coll in ax.collections:  # a number inside a bubble
        if not (isinstance(coll, PathCollection) and coll.get_visible() and coll.get_zorder() <= r.zorder):
            continue
        off, fcs = np.asarray(coll.get_offsets(), dtype=float), coll.get_facecolors()
        if not off.size or not len(fcs):
            continue
        xy = coll.get_offset_transform().transform(off)
        sizes = np.atleast_1d(coll.get_sizes()).astype(float)
        rad = np.sqrt(np.resize(sizes if len(sizes) else [plt.rcParams["lines.markersize"] ** 2], len(xy))) / 2 \
            * c.px_per_pt
        hit = np.nonzero((np.hypot(xy[:, 0] - r.cx, xy[:, 1] - r.cy) <= rad) & (2 * rad >= r.w))[0]
        if len(hit) and fcs[hit[-1] % len(fcs)][3] > 0:
            under = fcs[hit[-1] % len(fcs)]
    return over(under, base) if under is not None else base


def check_contrast(c: Ctx):
    frames = {}
    for leg in [ax.get_legend() for ax in c.fig.axes if ax.get_legend()] + list(c.fig.legends):
        if legend_has_frame(leg):
            frames.update({id(t): leg.get_frame().get_facecolor() for t in leg.get_texts() + [leg.get_title()]})
    low = {}  # one finding per text, or per axis for tick labels
    for r in c.texts:
        if id(r.obj) in c.on_area:
            continue
        back = text_backdrop(c, r, frames)
        cr = contrast(over(to_rgba(r.obj.get_color(), r.obj.get_alpha()), back), back)
        glyph = not any(ch.isalnum() for ch in r.obj.get_text())  # a symbol used as a color key is a mark
        floor = MARK_MIN if glyph else TEXT_MIN_LARGE if is_large(r) else TEXT_MIN
        if cr < floor:
            key = (id(r.ax), r.axis) if r.kind == "tick" else id(r.obj)
            low.setdefault(key, []).append((cr, floor, back, r))
    for rows in low.values():
        cr, floor, back, r = min(rows, key=lambda t: t[0])
        what = f"{len(rows)} {r.axis}-axis tick labels" if r.kind == "tick" else f"{r.kind} {snip(r.label, 30)}"
        c.add("contrast", c.where(r.ax, what),
              f"text {color_key(r.obj.get_color())} on {back} is {cr:.2f}:1; floor {floor:g}:1",
              "Darken the text (ev.text_color gives a 4.5:1 variant of a mark color) or lighten what is behind it.")
    for i, ax in data_axes(c.fig):
        bg = axes_bg(c, ax)
        for s in color_series(c, ax):
            cr = contrast(over((*to_rgba(s.hex)[:3], s.alpha), bg), bg)
            where = c.where(ax, s.name())
            if s.marks & {"line", "point"}:
                if cr < INVISIBLE:
                    c.add("contrast", where, f"{s.hex} lines/points {cr:.2f}:1 on {bg}; below {INVISIBLE}:1 they "
                          "vanish", "Use a darker slot (palettes.json use notes) for thin marks.")
                elif cr < MARK_MIN and not direct_labeled(c, ax, s):
                    c.add("contrast", where, f"{s.hex} lines/points {cr:.2f}:1 on {bg}; floor {MARK_MIN}:1",
                          "Direct-label the series or use a darker slot.", severity="warn")
            elif cr < INVISIBLE and s.edge_cr < MARK_MIN:
                c.add("contrast", where, f"{s.hex} fill {cr:.2f}:1 on {bg} with no outline",
                      "Outline the fill in a darker color or use a darker slot.", severity="warn")


def fill_surfaces(c, ax, bg) -> list:
    """Data fills in ax at least FILL_MIN_ALPHA opaque, bottom to top, as (zorder, lookup): lookup(pts px [N, 2])
    returns the fill's color over bg per point, or None. Bars are left to check_text_on_bars."""
    def poly(path, color):
        def look(pts):
            out = np.full(len(pts), None, dtype=object)
            out[path.contains_points(pts)] = color
            return out
        return look

    def cells(inv, color_at):
        def look(pts):
            out = np.full(len(pts), None, dtype=object)
            for k, fc in color_at(inv.transform(pts)):
                if fc is not None and fc[3] >= FILL_MIN_ALPHA:
                    out[k] = over(fc, bg)
            return out
        return look

    def edges_index(edges, v):
        asc = edges[-1] > edges[0]
        e = edges if asc else edges[::-1]
        i = np.searchsorted(e, v, side="right") - 1
        ok = (i >= 0) & (i < len(e) - 1)
        return np.where(ok, i if asc else len(e) - 2 - i, -1)

    found = []
    kids = ax._children if hasattr(ax, "_children") else ax.get_children()
    patches = {id(p) for p in data_patches(ax)}
    for order, art in enumerate(kids):
        if not art.get_visible():
            continue
        z = art.get_zorder()
        if isinstance(art, QuadMesh):
            xy = np.asarray(art.get_coordinates(), dtype=float)
            xe, ye = xy[0, :, 0], xy[:, 0, 1]
            fcs = art.get_facecolors()
            nx, ny = len(xe) - 1, len(ye) - 1
            if not (np.allclose(xy[..., 0], xe[None, :]) and np.allclose(xy[..., 1], ye[:, None])) or \
                    len(fcs) not in (1, nx * ny):
                continue

            def at(d, xe=xe, ye=ye, fcs=fcs, nx=nx):
                ix, iy = edges_index(xe, d[:, 0]), edges_index(ye, d[:, 1])
                return [(k, fcs[(iy[k] * nx + ix[k]) % len(fcs)] if ix[k] >= 0 and iy[k] >= 0 else None)
                        for k in range(len(d))]
            found.append((z, order, cells(art.get_transform().inverted(), at)))
        elif isinstance(art, AxesImage):
            arr = art.get_array()
            if arr is None:
                continue
            rgba = np.asarray(art.to_rgba(arr), dtype=float)
            if rgba.ndim != 3:
                continue
            rgba = rgba / 255.0 if rgba.max() > 1 else rgba
            if rgba.shape[2] == 3:
                rgba = np.dstack([rgba, np.ones(rgba.shape[:2])])
            a = art.get_alpha()
            if isinstance(a, (int, float)):
                rgba[..., 3] *= a
            left, right, bottom, top = art.get_extent()
            upper = art.origin == "upper"

            def at(d, rgba=rgba, ext=(left, right, bottom, top), upper=upper):
                ny, nx = rgba.shape[:2]
                fx = (d[:, 0] - ext[0]) / (ext[1] - ext[0])
                fy = (d[:, 1] - ext[2]) / (ext[3] - ext[2])
                col = np.floor(fx * nx).astype(int)
                row = np.floor(((1 - fy) if upper else fy) * ny).astype(int)
                return [(k, rgba[row[k], col[k]] if 0 <= col[k] < nx and 0 <= row[k] < ny else None)
                        for k in range(len(d))]
            found.append((z, order, cells(art.get_transform().inverted(), at)))
        elif isinstance(art, PolyCollection) and type(art).__name__ != "Poly3DCollection" \
                and len(art.get_offsets()) <= 1 or isinstance(art, ContourSet) and art.filled:
            fcs, tr = art.get_facecolors(), art.get_transform()
            for k, path in enumerate(art.get_paths()):
                if len(fcs) and fcs[k % len(fcs)][3] >= FILL_MIN_ALPHA:
                    found.append((z, order, poly(tr.transform_path(path), over(fcs[k % len(fcs)], bg))))
        elif id(art) in patches and art.get_facecolor()[3] >= FILL_MIN_ALPHA:
            found.append((z, order, poly(art.get_transform().transform_path(art.get_path()),
                                         over(art.get_facecolor(), bg))))
    return [(z, look) for z, _, look in sorted(found, key=lambda f: (f[0], f[1]))]


def text_samples(r: TextRec, pad: float):
    """An 8 x 3 grid of points over each glyph line box (or the rotated box)."""
    u, v = np.meshgrid(np.linspace(0.05, 0.95, 8), np.linspace(0.2, 0.8, 3))
    u, v = u.ravel()[:, None], v.ravel()[:, None]
    out = []
    for p0, p1, p2, p3 in (np.asarray(s, dtype=float) for s in r.shapes(pad)):
        lo, hi = p0 + (p1 - p0) * u, p3 + (p2 - p3) * u
        out.append(lo + (hi - lo) * v)
    return np.vstack(out) if out else np.zeros((0, 2))


def check_text_on_area(c: Ctx):
    """Text over data fills must sit wholly inside one fill with text contrast, or carry an opaque box or halo."""
    pad = TEXT_LINE_PAD_PT * c.px_per_pt
    cache = {}
    clabels = {id(t) for ax in c.fig.axes for cs in ax.collections if isinstance(cs, ContourSet)
               for t in getattr(cs, "labelTexts", [])}
    for r in c.texts:
        if r.kind not in ("text", "annotation", "figtext") or id(r.obj) in clabels:
            continue
        pts = text_samples(r, pad)
        if not len(pts):
            continue
        for ax in [r.ax] if r.ax is not None else [a for _, a in data_axes(c.fig)]:
            if id(ax) not in cache:
                bg = axes_bg(c, ax)
                cache[id(ax)] = bg, fill_surfaces(c, ax, bg), ax.get_window_extent(c.renderer)
            bg, surfaces, box = cache[id(ax)]
            if not surfaces:
                continue
            inside = (pts[:, 0] >= box.x0) & (pts[:, 0] <= box.x1) & (pts[:, 1] >= box.y0) & (pts[:, 1] <= box.y1)
            backs = np.where(inside, bg, figure_bg(c)).astype(object)
            on = np.zeros(len(pts), bool)
            for z, look in surfaces:
                if z > r.zorder:
                    break
                got = look(pts)
                hit = np.array([g is not None for g in got]) & inside
                backs[hit], on[hit] = got[hit], True
            if on.mean() < AREA_OVERLAP_FRAC:
                continue
            if r.knockout:
                break
            c.on_area.add(id(r.obj))
            uniq = sorted(set(backs))
            spread = max((de(Color(a), Color(b)) for n, a in enumerate(uniq) for b in uniq[n + 1:]), default=0.0)
            where = c.where(ax, f"{r.kind} {snip(r.label, 30)}")
            if spread >= DE_FLOOR["area"]:
                c.add("text-on-area", where, f"text straddles an edge between fills ({len(uniq)} backdrops, "
                      f"dE00 up to {spread:.0f})",
                      "Put the label wholly inside one fill (a stack label inside its own layer) or in open space, "
                      "or give it an opaque bbox or a halo.")
            else:
                tc = to_rgba(r.obj.get_color(), r.obj.get_alpha())
                cr, back = min((contrast(over(tc, b), b), b) for b in uniq)
                floor = TEXT_MIN_LARGE if is_large(r) else TEXT_MIN
                if cr < floor:
                    c.add("text-on-area", where, f"text inside a {back} fill at {cr:.2f}:1; floor {floor:g}:1",
                          "Use dark text on light fills and white on dark ones (4.5:1), or move the label out.")
            break


CHECK_FUNCS = [
    check_text_overlap, check_text_on_line, check_text_on_area, check_text_clipped, check_bar_baseline, check_dual_axis,
    check_pie, check_rainbow, check_3d, check_legend, check_missing_axis_label, check_default_title,
    check_small_text, check_tick_crowding, check_too_many_series, check_spines_gridlines, check_label_ambiguous,
    check_process_note, check_missing_source, check_value_labels_and_axis, check_title_too_long, check_inverted_axis,
    check_log_unlabeled, check_cumulative_as_rate, check_stacked_area, check_plot_area_tiny,
    check_plot_area_underused, check_plot_aspect, check_cvd, check_contrast,
]


def lint_figure(fig, fi, dest="blog", save_kwargs=None):
    if not hasattr(fig.canvas, "get_renderer"):
        FigureCanvasAgg(fig)
    fig.canvas.draw()
    c = Ctx(fig, fi, dest, save_kwargs)
    for fn in CHECK_FUNCS:
        fn(c)
    inventory = {"figure": fi, "axes": len(fig.axes), "texts": len(c.texts),
                 "segments": int(len(c.segs)), "size_in": [round(v, 2) for v in fig.get_size_inches()]}
    return c.findings, inventory


def run_checks(chart, cwd=None, dest="blog", verbose=False) -> dict:
    """Run a chart script and lint every figure. Raises ScriptError."""
    findings, inventory = [], []
    with matplotlib.rc_context():  # scripts' rcParams must not leak between runs
        figs, save_kwargs = run_script(Path(chart), Path(cwd) if cwd else None, verbose)
        if not figs:
            raise ScriptError("script produced no matplotlib figures")
        try:
            for fi, fig in enumerate(figs):
                f, inv = lint_figure(fig, fi, dest, save_kwargs.get(id(fig)))
                findings += f
                inventory.append(inv)
        finally:
            plt.close("all")
    fails = sum(f.severity == "fail" for f in findings)
    warns = len(findings) - fails
    return {
        "result": "fail" if fails else "pass",
        "dest": dest,
        "figures": len(figs),
        "fails": fails,
        "warns": warns,
        "findings": [f.__dict__ for f in findings],
        "inventory": inventory,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint a matplotlib chart script for explanatory-chart problems. Executes "
                                 "the script: savefig is blocked, but any file it writes another way (data exports, "
                                 "PIL images, even its own PNG) is really written, so lint a scratch copy.")
    ap.add_argument("chart", nargs="?", type=Path, help="Path to the chart .py script.")
    ap.add_argument("--cwd", type=Path, default=None, help="Directory to run the script in (default: its folder).")
    ap.add_argument("--json", action="store_true", help="Print JSON only.")
    ap.add_argument("--dest", choices=sorted(DEST_WIDTH_PX), default="blog",
                    help="Display target for small-text and title-too-long.")
    ap.add_argument("--verbose", action="store_true", help="Show script stdout and per-figure inventory.")
    ap.add_argument("--list-checks", action="store_true", help="List checks and exit.")
    args = ap.parse_args(argv)

    if args.list_checks:
        for name, (sev, desc) in CHECKS.items():
            print(f"{name}\t{sev}\t{desc}")
        return 0
    if args.chart is None:
        ap.error("chart path required")

    def error(msg):
        if args.json:
            print(json.dumps({"result": "error", "error": msg}))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 2

    if not args.chart.is_file():
        return error(f"chart file not found: {args.chart}")
    if args.cwd is not None and not args.cwd.is_dir():
        return error(f"cwd not found: {args.cwd}")
    try:
        res = run_checks(args.chart, args.cwd, args.dest, args.verbose)
    except ScriptError as e:
        return error(e.tail.rstrip())

    if not args.verbose:
        res.pop("inventory")
    if args.json:
        print(json.dumps(res, indent=1))
    else:
        if args.verbose:
            for inv in res["inventory"]:
                print(f"INFO fig{inv['figure']}: {inv['axes']} axes, {inv['texts']} texts, "
                      f"{inv['segments']} line segments, {inv['size_in'][0]}x{inv['size_in'][1]} in")
        for f in res["findings"]:
            print(f"{f['severity'].upper()} {f['check']} | {f['where']} | {f['detail']} | fix: {f['fix']}")
        print(f"RESULT {res['result'].upper()}: {res['fails']} fail, {res['warns']} warn, "
              f"{res['figures']} figure(s), dest={res['dest']}")
    return 1 if res["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
