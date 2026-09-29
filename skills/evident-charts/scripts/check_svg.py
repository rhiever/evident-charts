#!/usr/bin/env python3
"""Deterministic chart checks for any stack that exports SVG with live text: Plotly, Vega-Lite/Altair, D3,
ggplot2 (svglite), and others.

Headless Chrome lays out the SVG and measures it (scripts/measure_svg.js), so text boxes, fonts, transforms,
and clip paths are resolved exactly as a browser draws them. Check names, output, and exit codes match
check_chart.py, so rule `check:` names apply. Chart-level facts the SVG cannot show (bar baselines, twin axes,
reversed or log scales, color schemes) come from the optional spec: Plotly's figure JSON or Vega.

Usage:
  python check_svg.py chart.svg [--dest blog|social|social_portrait|slide|report|mobile] [--json]
                      [--spec fig.json | chart.vg.json | chart.vl.json]
  python check_svg.py --list-checks

Export:
  Plotly      fig.write_image("c.svg"); open("c.json", "w").write(fig.full_figure_for_development().to_json())
  Altair      chart.save("c.svg"); json.dump(chart.to_dict(format="vega"), open("c.vg.json", "w"))
  Vega-Lite   vl_convert.vegalite_to_svg(spec) and vl_convert.vegalite_to_vega(spec)
  ggplot2     ggsave("c.svg", p, device = svglite::svglite)  (base svg() and cairo outline their text)
  D3          serialize the <svg> node (new XMLSerializer().serializeToString(node)) with its CSS inlined
  matplotlib  use check_chart.py; for an SVG, set rcParams["svg.fonttype"] = "none" first

Chrome: $CHROME_PATH or $BROWSER_PATH, else chrome-headless-shell (Puppeteer or Playwright cache), kaleido's
Chrome, then Google Chrome, Chromium, or Edge.

Without Chrome, --spec still runs its checks (the SVG checks are reported as skipped); with no --spec and no
Chrome there is nothing to run.

Exit codes: 0 no fails (warns allowed), 1 at least one fail, 2 missing file, unreadable SVG or spec,
outlined text, or no Chrome and no --spec.
"""

from __future__ import annotations

import argparse
import colorsys
import glob
import html
import json
import math
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Color math and floors come from check_palette, as in check_chart: CVD pairs must differ by CVD_FACTOR x the
# mark's DE_FLOOR (V6), text meets TEXT_MIN (V2), marks MARK_MIN / INVISIBLE (V3).
from check_palette import (CVD_FACTOR, DE_FLOOR, INVISIBLE, MARK_MIN, TEXT_MIN, TEXT_MIN_LARGE,  # noqa: E402
                           Color, contrast, de, hex_to_linear, linear_to_oklab)

PRESETS = {k: v for k, v in json.loads((HERE.parent / "assets" / "presets.json").read_text()).items()
           if not k.startswith("_")}

# ---------------------------------------------------------------------------
# Tunable constants, in canvas px (SVG user px; 1 pt = 4/3 px). Mirrors check_chart where a twin exists.
# ---------------------------------------------------------------------------
PT = 4 / 3
TEXT_OVERLAP_MIN_PX = 1.0 * PT   # unrotated texts: min horizontal overlap to fail
TEXT_OVERLAP_MIN_FRAC = 0.15     # rotated texts: overlap area / smaller box area to fail
TEXT_LINE_PAD_PX = 1.0 * PT      # shrink text boxes by this before line and marker tests
TEXT_LINE_MIN_PATH_PX = 4.0 * PT  # min length of data line inside a text box to fail
ENDPOINT_MIN_RADIUS_PX = 6.0 * PT  # a line's last stub may run into a direct label within this radius
CANVAS_TOLERANCE_PX = 1.0
LARGE_TEXT_PX, LARGE_BOLD_PX = 18.0 * PT, 14.0 * PT  # WCAG large text gets TEXT_MIN_LARGE
NEUTRAL_SATURATION = 0.15        # colors below this saturation (or value) count as gray
MAX_CATEGORICAL_COLORS = 8       # more distinct data colors of one kind is a color scale, not categories
HUE_MATCH_DEG = 15.0             # a direct label shares its series' hue within this
DIRECT_LABEL_REACH_LINES = 2.0   # and sits within this many line heights of its marks
AREA_OVERLAP_FRAC = TEXT_OVERLAP_MIN_FRAC  # text-on-area: share of text samples on data fills to count
UNKNOWN_FILL_MIN_CR = 1.25       # unclassed fills lighter than this vs white are backgrounds, not data
UNKNOWN_FILL_MAX_FRAC = 0.4      # unclassed fills covering more of the canvas are panels
LOG_WORD_RE = re.compile(r"\blog(arithmic)?(?![a-z])", re.I)
RANK_RE = re.compile(r"\b(rank|depth)|\b\d+(st|nd|rd|th)\b", re.I)
VEGA_RAINBOW = {"rainbow", "sinebow", "turbo"}

CHECKS = {
    "text-overlap": ("fail", "Two visible text boxes intersect, a legend covers text, text covers a data marker, "
                             "or text straddles a bar edge or lies on two bars."),
    "text-on-line": ("fail", "Text sits on a data line (4 pt of path or more inside it, the line's ends excepted)."),
    "text-on-area": ("fail", "Text over filled data (areas, stacks, cells, wedges) straddles an edge between fills, "
                             "or sits inside one fill below text contrast (4.5:1, large 3:1)."),
    "text-clipped": ("fail", "Text extends beyond the canvas or its clip box."),
    "small-text": ("warn", "Text renders below the destination's minimum pixel size."),
    "contrast": ("fail", "Text below 4.5:1 (large text 3:1) against what is drawn behind it, or a colored "
                         "line/point below 1.5:1; warn: colored line/point below 3:1 and not direct-labeled, or a "
                         "fill below 1.5:1 without an outline."),
    "cvd": ("fail", "Two data colors collapse under protan/deutan simulation (check_palette V6 floor) with nothing "
                    "else telling them apart (direct labels in the series hue, dash, mark type, one Plotly bar "
                    "trace); warn when redundantly encoded or tritan-only."),
    "bar-baseline": ("fail", "--spec: bar value axis excludes zero or is log-scaled; warn: Vega scale.zero false."),
    "dual-axis": ("warn", "--spec: two value axes on different scales share one plot."),
    "inverted-axis": ("fail", "--spec: value axis reversed, and its title does not say 'rank'."),
    "log-unlabeled": ("fail", "--spec: log-scaled axis, and no text on the chart says 'log'."),
    "rainbow-cmap": ("fail", "--spec: rainbow color scale (jet, rainbow, hsv, turbo, sinebow)."),
}

OUTLINED_HINT = ("export text as <text> elements: matplotlib rcParams['svg.fonttype'] = 'none' (or lint the "
                 "script with check_chart.py); ggplot2 ggsave(..., device = svglite::svglite), not svg() or cairo")
CHROME_HINT = ("no Chrome found. Install one: python -c \"import kaleido; kaleido.get_chrome_sync()\" (kaleido "
               ">= 1), or npx @puppeteer/browsers install chrome-headless-shell@stable, or set CHROME_PATH to a "
               "Chrome/Chromium binary. Meanwhile check colors with check_palette.py.")


class CheckError(Exception):
    """Bad input or environment; exit code 2."""


# ---------------------------------------------------------------------------
# Chrome
# ---------------------------------------------------------------------------

def _version_key(path: str):
    return [int(n) for n in re.findall(r"\d+", path)]


def find_chrome() -> str | None:
    """Path to a Chrome binary, fastest kind first (chrome-headless-shell starts in about 0.4 s, Chrome 1.5 s+)."""
    home = Path.home()
    cands = [os.environ.get("CHROME_PATH"), os.environ.get("BROWSER_PATH"), shutil.which("chrome-headless-shell")]
    shells = []
    for pat in ("chrome-headless-shell/*/chrome-headless-shell*/chrome-headless-shell*",    # npx @puppeteer/browsers
                str(home / ".cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell*"),
                str(home / "Library/Caches/ms-playwright/chromium_headless_shell-*/*/*headless_shell*"),
                str(home / ".cache/ms-playwright/chromium_headless_shell-*/*/*headless_shell*"),
                str(home / "AppData/Local/ms-playwright/chromium_headless_shell-*/*/*headless_shell.exe")):
        shells += [p for p in glob.glob(pat) if os.path.isfile(p) and not p.endswith((".zip", ".json"))]
    cands += sorted(shells, key=_version_key, reverse=True)
    # kaleido v1 (choreographer) downloads Chrome for Testing here via kaleido.get_chrome_sync().
    for root in (home / "Library/Application Support/choreographer", home / ".local/share/choreographer",
                 home / "AppData/Local/plotly/choreographer"):
        cands += glob.glob(str(root / "deps/chrome-*/Google Chrome for Testing.app/Contents/MacOS/*"))
        cands += glob.glob(str(root / "deps/chrome-*/chrome")) + glob.glob(str(root / "deps/chrome-*/chrome.exe"))
    cands += [shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                                        "chrome", "microsoft-edge")]
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              str(home / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
    return next((c for c in cands if c and os.path.isfile(c) and os.access(c, os.X_OK)), None)


def outlined_text(svg: str) -> bool:
    """True when the SVG draws its text as glyph outlines (no <text>, but glyph <use>/<symbol> or font paths)."""
    if re.search(r"<(\w+:)?text[\s>]", svg):
        return False
    return bool(re.search(r"""id=["'](glyph|DejaVu|Liberation|Arial|Helvetica)""", svg)
                or len(re.findall(r"<(\w+:)?use[\s>]", svg)) >= 3)


def stack_of(svg: str) -> str:
    head = svg[:4000]
    for name, pat in (("plotly", r"class=\"main-svg\""), ("vega", r"<svg[^>]*class=\"marks\""),
                      ("svglite", r"class=['\"]svglite['\"]"), ("matplotlib", r"matplotlib"),
                      ("d3-evident", r"ev-chart")):
        if re.search(pat, head):
            return name
    return "svg"


def measure(svg_text: str, chrome: str, timeout: float = 90.0) -> dict:
    """Lay out the SVG in headless Chrome and return measure_svg.js's JSON."""
    js = (HERE / "measure_svg.js").read_text(encoding="utf-8")
    src = json.dumps(svg_text).replace("<", "\\u003c")
    page = ("<!doctype html><html><head><meta charset=\"utf-8\"></head><body style=\"margin:0\">"
            f"<script>const EVIDENT_SVG = {src};</script><script>{js}</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="check_svg_") as tmp:
        path = Path(tmp) / "page.html"
        path.write_text(page, encoding="utf-8")
        # No --user-data-dir: Google Chrome on macOS can hang on exit with a fresh profile.
        cmd = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--no-first-run",
               "--disable-extensions", "--dump-dom", path.as_uri()]
        if platform.system() == "Linux":
            cmd.insert(1, "--disable-dev-shm-usage")
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                cmd.insert(1, "--no-sandbox")  # Chrome refuses to run as root with its sandbox
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                start_new_session=os.name == "posix")
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(proc)
            raise CheckError(f"Chrome did not finish within {timeout:.0f} s ({chrome})")
        _kill(proc)  # helpers can outlive the main process
    m = re.search(r'<pre id="evident-measure">(.*?)</pre>', out.decode("utf-8", "replace"), re.S)
    if not m:
        raise CheckError(f"Chrome returned no measurement ({chrome}); try another binary via CHROME_PATH")
    res = json.loads(html.unescape(m.group(1)))
    if res.get("error"):
        raise CheckError(res["error"])
    return res


def _kill(proc):
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

def rgba(css) -> tuple | None:
    """A computed CSS color ('rgb(1, 2, 3)', 'rgba(1, 2, 3, 0.5)') as (r, g, b, a); None for none/url()."""
    if not css:
        return None
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+)(%?))?\s*\)", css.strip())
    if not m:
        return None
    a = 1.0 if m.group(4) is None else float(m.group(4)) / (100 if m.group(5) else 1)
    return float(m.group(1)), float(m.group(2)), float(m.group(3)), a


def over(css, alpha: float, under: str = "#FFFFFF") -> str | None:
    """Hex of CSS color `css` at extra opacity `alpha` painted over opaque hex `under`."""
    c = rgba(css)
    if c is None:
        return None
    a = max(0.0, min(1.0, c[3] * alpha))
    u = [int(under[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a * v + (1 - a) * w):02X}" for v, w in zip(c[:3], u))


def is_neutral(h: str) -> bool:
    _, s, v = colorsys.rgb_to_hsv(*(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)))
    return s < NEUTRAL_SATURATION or v < 0.15


def hue(h: str) -> float:
    return colorsys.rgb_to_hsv(*(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)))[0] * 360


def hue_gap(a: str, b: str) -> float:
    d = abs(hue(a) - hue(b)) % 360
    return min(d, 360 - d)


def rainbow_like(hexes: list) -> bool:
    """A rainbow scale: saturated stops in 4+ of six hue sectors, lightness not monotone, and a saturated middle
    (diverging scales pass through a pale neutral). Flags jet, rainbow, hsv, and turbo among Plotly's scales."""
    if len(hexes) < 5:
        return False
    lab = [linear_to_oklab(hex_to_linear(h)) for h in hexes]
    chroma = [math.hypot(a, b) for _, a, b in lab]
    sectors = {int(math.degrees(math.atan2(b, a)) % 360 // 60) for (_, a, b), c in zip(lab, chroma) if c > 0.08}
    steps = [q[0] - p[0] for p, q in zip(lab, lab[1:])]
    monotone = all(d >= -0.02 for d in steps) or all(d <= 0.02 for d in steps)
    n = len(hexes)
    return len(sectors) >= 4 and not monotone and min(chroma[int(n * 0.3):int(n * 0.7) + 1]) > 0.1


# ---------------------------------------------------------------------------
# Geometry (canvas px; polygons are lists of (x, y), either winding)
# ---------------------------------------------------------------------------

def aabb(pts) -> list:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def poly_area(poly) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2


def ccw(poly) -> list:
    s = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
    return poly if s >= 0 else poly[::-1]


def clip_poly(subject, clip) -> list:
    """Sutherland-Hodgman: subject polygon clipped to a convex polygon (both CCW)."""
    out = subject
    for (ax, ay), (bx, by) in zip(clip, clip[1:] + clip[:1]):
        if not out:
            break
        inp, out = out, []
        side = [(bx - ax) * (py - ay) - (by - ay) * (px - ax) for px, py in inp]
        for k, (p, sp) in enumerate(zip(inp, side)):
            q, sq = inp[k - 1], side[k - 1]
            if sp >= 0:
                if sq < 0:
                    out.append(_cross(q, p, sq, sp))
                out.append(p)
            elif sq >= 0:
                out.append(_cross(q, p, sq, sp))
    return out


def _cross(p, q, sp, sq):
    t = sp / (sp - sq)
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def inside(poly, x, y) -> bool:
    """Point in a convex polygon of either winding."""
    signs = [(bx - ax) * (y - ay) - (by - ay) * (x - ax) for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1])]
    return all(s >= 0 for s in signs) or all(s <= 0 for s in signs)


def snip(s: str, n: int = 40) -> str:
    s = " ".join(s.split())
    return f"'{s[:n - 3]}...'" if len(s) > n else f"'{s}'"


# ---------------------------------------------------------------------------
# Measured texts and shapes
# ---------------------------------------------------------------------------

class Text:
    def __init__(self, d: dict):
        self.__dict__.update(d)
        self.rotated = abs(self.angle) % 90 > 0.5
        self.lines = [aabb(q) for q in self.quads]
        self.box = aabb([p for q in self.quads for p in q])
        self.width = max(math.dist(q[0], q[1]) for q in self.quads)
        self.line_h = sum(math.dist(q[0], q[3]) for q in self.quads) / len(self.quads)
        self.knock = -1  # paint order below which an opaque label box or halo hides marks
        self.backs, self.on_area = [], False  # sampled backdrop colors; judged by text-on-area

    def polys(self, pad: float = 0.0) -> list:
        """Each line's quad shrunk by pad at the sides and by max(pad, 12% of the line height) at top and bottom
        (descent and leading rarely hold ink)."""
        out = []
        for q in self.quads:
            (x0, y0), (x1, y1), _, (x3, y3) = q
            w, h = math.hypot(x1 - x0, y1 - y0), math.hypot(x3 - x0, y3 - y0)
            vpad = max(pad, 0.12 * h) if pad else 0.0
            if w <= 2 * pad or h <= 2 * vpad or w == 0 or h == 0:
                continue
            ux, uy, vx, vy = (x1 - x0) / w, (y1 - y0) / w, (x3 - x0) / h, (y3 - y0) / h
            corners = [(pad, vpad), (w - pad, vpad), (w - pad, h - vpad), (pad, h - vpad)]
            out.append([(x0 + a * ux + b * vx, y0 + a * uy + b * vy) for a, b in corners])
        return out

    def gaps(self, pad: float) -> list:
        """Boxes over the leading between consecutive lines of unrotated multi-line text: a data line threading
        between a label's lines runs through the label."""
        out = []
        if self.rotated:
            return out
        for (ax0, _, ax1, ay1), (bx0, by0, bx1, by1) in zip(self.lines, self.lines[1:]):
            x0, x1 = max(ax0, bx0) + pad, min(ax1, bx1) - pad
            lo, hi = ay1 - 0.12 * (by1 - by0), by0 + 0.12 * (by1 - by0)
            if x1 > x0 and hi > lo:
                out.append([(x0, lo), (x1, lo), (x1, hi), (x0, hi)])
        return out

    def large(self) -> bool:
        return self.font_px >= LARGE_TEXT_PX or (self.weight >= 700 and self.font_px >= LARGE_BOLD_PX)


class Chart:
    """Measured SVG plus the derived facts every check shares."""

    def __init__(self, m: dict, dest: str):
        self.dest, self.w, self.h = dest, m["width"], m["height"]
        self.shapes, self.legends = m["shapes"], m.get("legends", [])
        self.findings = []
        self.scale_marks = set()  # class names of marks whose colors are a continuous scale (from a Vega spec)
        self.series = None        # color_series, computed once
        seen = {}
        for d in m["texts"]:  # the same text drawn twice at one spot (duplicate axes, a halo copy) reads as one:
            t = Text(d)       # keep the top copy, and a halo stroke from the one beneath
            key = (t.text, tuple(round(v) for v in t.box))
            if key in seen:
                t.halo = t.halo or seen[key].halo
            seen[key] = t
        self.texts = sorted(seen.values(), key=lambda t: t.order)
        canvas = self.w * self.h
        for s in self.shapes:
            b = s["box"]
            s["area_frac"] = max(b[2] - b[0], 0) * max(b[3] - b[1], 0) / max(canvas, 1e-9)
            s["fill_hex"] = over(s["fill"], s["fill_opacity"] * s["opacity"]) if s["fill"] else None
            s["data_fill"] = self._data_fill(s)
        for s in self.shapes:
            # A mark is judged against the page or panel behind it, not against other data (a line over its own
            # area fill), and its colors are composited over that.
            s["back"] = self.backdrop([k for k in s["under"] if not self.shapes[k]["data_fill"]])
            s["fill_hex"] = over(s["fill"], s["fill_opacity"] * s["opacity"], s["back"]) if s["fill"] else None
            s["stroke_hex"] = over(s["stroke"], s["stroke_opacity"] * s["opacity"], s["back"]) if s["stroke"] else None
            s["data_stroke"] = self._data_stroke(s)
        for t in self.texts:
            tops = [u[-1] if u else None for u in t.under]
            boxes = [k for k in tops if k is not None and self._label_box(self.shapes[k])]
            if tops and len(boxes) == len(tops):
                t.knock = min(self.shapes[k]["order"] for k in boxes)
            if t.halo:
                t.knock = max(t.knock, t.order)

    def _data_fill(self, s) -> bool:
        if not s["fill_hex"] or s["role"] == "chrome":
            return False
        if s["role"] == "data":
            return True
        # Unclassed (svglite, hand SVG): a fill darker than a page or panel background, smaller than a panel.
        return contrast(s["fill_hex"], "#FFFFFF") >= UNKNOWN_FILL_MIN_CR and s["area_frac"] < UNKNOWN_FILL_MAX_FRAC

    def _data_stroke(self, s) -> bool:
        if not s["stroke_hex"] or s["role"] == "chrome" or s["stroke_width"] < 0.5:
            return False
        if s["role"] == "data":
            return True
        # Unclassed: a colored stroke, or a dark one with 3+ vertices (gridlines, ticks, and axes are straight).
        h = s["stroke_hex"]
        return not is_neutral(h) or (contrast(h, "#FFFFFF") >= MARK_MIN and s["verts"] >= 3)

    def _label_box(self, s) -> bool:
        """An opaque fill that is not data: an annotation box or legend background under text."""
        return not s["data_fill"] and s["fill"] and (rgba(s["fill"]) or (0, 0, 0, 0))[3] * s["fill_opacity"] \
            * s["opacity"] >= 0.9 and s["area_frac"] < UNKNOWN_FILL_MAX_FRAC

    def backdrop(self, stack) -> str:
        """Composite color of the fills in `stack` (paint order) over a white page."""
        back = "#FFFFFF"
        for k in stack:
            s = self.shapes[k]
            back = over(s["fill"], s["fill_opacity"] * s["opacity"], back) or back
        return back

    def text_color(self, t: Text, back: str) -> str | None:
        return over(t.fill, t.fill_opacity * t.opacity, back)

    def add(self, check, where, detail, fix, severity=None):
        self.findings.append({"check": check, "severity": severity or CHECKS[check][0], "where": where,
                              "detail": detail, "fix": fix})


# ---------------------------------------------------------------------------
# Checks on the measured SVG
# ---------------------------------------------------------------------------

def check_text_overlap(c: Chart):
    for a, b in combinations(c.texts, 2):
        if a.box[2] <= b.box[0] or b.box[2] <= a.box[0] or a.box[3] <= b.box[1] or b.box[3] <= a.box[1]:
            continue
        hit = None
        if a.rotated or b.rotated:
            pa, pb = [ccw(p) for p in a.polys()], [ccw(p) for p in b.polys()]
            inter = sum(poly_area(clip_poly(p, q)) for p in pa for q in pb)
            frac = inter / max(min(sum(map(poly_area, pa)), sum(map(poly_area, pb))), 1e-9)
            if frac >= TEXT_OVERLAP_MIN_FRAC:
                hit = f"rotated boxes overlap {frac:.0%} of the smaller"
        else:
            best = None
            for la in a.lines:
                for lb in b.lines:
                    w = min(la[2], lb[2]) - max(la[0], lb[0])
                    h = min(la[3], lb[3]) - max(la[1], lb[1])
                    if w > TEXT_OVERLAP_MIN_PX and h > 0.3 * min(la[3] - la[1], lb[3] - lb[1]):
                        if best is None or w * h > best[0] * best[1]:
                            best = (w, h)
            if best:
                hit = f"glyph boxes overlap {best[0]:.1f} x {best[1]:.1f} px"
        if hit:
            c.add("text-overlap", f"{a.kind} {snip(a.text, 30)} x {b.kind} {snip(b.text, 30)}", hit,
                  "Move, shorten, or resize one label so the two no longer intersect.")
    for box in c.legends:  # a legend's box covering text outside it
        for t in c.texts:
            if t.kind == "legend" or (box[0] <= t.box[0] and t.box[2] <= box[2] and box[1] <= t.box[1]
                                      and t.box[3] <= box[3]):
                continue
            for x0, y0, x1, y1 in t.lines:
                w, h = min(x1, box[2]) - max(x0, box[0]), min(y1, box[3]) - max(y0, box[1])
                if w > TEXT_OVERLAP_MIN_PX and h > 0.3 * (y1 - y0):
                    c.add("text-overlap", f"legend box x {t.kind} {snip(t.text, 30)}",
                          f"legend covers the text by {w:.1f} x {h:.1f} px",
                          "Move the legend into open space, or drop it and label series directly.")
                    break
    check_text_on_markers(c)


def check_text_on_markers(c: Chart):
    """Text drawn over a data marker: the marker's center lies inside the text's glyph box. Text that fits
    inside its marker (a bubble label) passes."""
    marks = [s for s in c.shapes if s["kind"] == "point" and (s["data_fill"] or s["data_stroke"])]
    for t in c.texts:
        if t.kind in ("tick", "legend") or not marks:
            continue
        polys = t.polys(TEXT_LINE_PAD_PX)
        hits = []
        for s in marks:
            b = s["box"]
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            if marker_size(s) < t.width and s["order"] > t.knock and any(inside(p, cx, cy) for p in polys):
                hits.append((cx, cy))
        if hits:
            c.add("text-overlap", f"{t.kind} {snip(t.text, 30)} x marker",
                  f"text covers {len(hits)} data marker(s), e.g. at ({hits[0][0]:.0f}, {hits[0][1]:.0f}) px",
                  "Move the label beside its marker or into open space.")


def check_text_on_line(c: Chart):
    lines = []
    for s in c.shapes:
        if s["data_stroke"] and s["pieces"]:
            pieces = [list(zip(p[0::2], p[1::2])) for p in s["pieces"]]
            lines.append((s, [(p, aabb(p)) for p in pieces if len(p) > 1]))
    for t in c.texts:
        if t.kind == "tick" or not lines:
            continue
        polys = t.polys(TEXT_LINE_PAD_PX) + t.gaps(TEXT_LINE_PAD_PX)
        if not polys:
            continue
        radius = max(t.font_px, ENDPOINT_MIN_RADIUS_PX)
        hits = []
        for s, pieces in lines:
            if s["order"] < t.knock:
                continue  # an opaque label box or halo drawn over the line keeps the text legible
            length = 0.0
            for pts, pb in pieces:
                if pb[2] < t.box[0] or pb[0] > t.box[2] or pb[3] < t.box[1] or pb[1] > t.box[3]:
                    continue
                start, end = pts[0], pts[-1]
                for p, q in zip(pts, pts[1:]):
                    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                    if math.dist((mx, my), start) > radius and math.dist((mx, my), end) > radius and \
                            any(inside(poly, mx, my) for poly in polys):
                        length += math.dist(p, q)
            if length >= TEXT_LINE_MIN_PATH_PX:
                hits.append((s, length))
        if hits:
            names = ", ".join(sorted({f"line {s['stroke_hex']}" for s, _ in hits}))[:80]
            c.add("text-on-line", f"{t.kind} {snip(t.text)} on {names}",
                  f"{max(L for _, L in hits):.0f} px of path crosses the text",
                  "Move the label into open space or past the line's end, or give it an opaque background box.")


def marker_size(s) -> float:
    b = s["box"]
    return max(b[2] - b[0], b[3] - b[1])


def check_text_on_fills(c: Chart):
    """Text over data fills (sampled in the browser): straddling a bar edge or lying on two bars is text-overlap;
    straddling an area edge, or sitting in an area fill below text contrast, is text-on-area. Everything else,
    including text wholly inside one bar, is left to check_contrast against the backdrops recorded here (so this
    check runs first)."""
    for t in c.texts:
        tops = []  # per sample: the topmost fill if it is a data bar or area, else None
        for stack in t.under:
            # A marker smaller than the text is text-overlap's finding, not part of the text's backdrop.
            stack = [k for k in stack if not (c.shapes[k]["kind"] == "point" and marker_size(c.shapes[k]) < t.width)]
            top = c.shapes[stack[-1]] if stack else None
            tops.append(top["i"] if top and top["data_fill"] and top["kind"] != "point" else None)
            t.backs.append(c.backdrop(stack))
        if t.kind in ("tick", "legend") or not any(k is not None for k in tops):
            continue
        touched = {k for k in tops if k is not None}
        bars = {k for k in touched if c.shapes[k]["kind"] == "bar"}
        uniq = sorted(set(t.backs))
        spread = max((de(Color(a), Color(b)) for a, b in combinations(uniq, 2)), default=0.0)
        whole = len(touched) == 1 and all(k is not None for k in tops)
        where = f"{t.kind} {snip(t.text, 30)}"
        if bars and not whole and (spread >= DE_FLOOR["area"] or len(bars) > 1):
            off = any(k is None for k in tops)
            c.add("text-overlap", f"{where} x bar", f"text straddles the edge of {len(bars)} bar(s)" if off
                  else f"text lies on {len(bars)} bars",
                  "Move the label past the bar end or into open space, or fit it wholly inside one bar.")
            t.on_area = True
        elif not bars and not whole and spread >= DE_FLOOR["area"] and \
                sum(k is not None for k in tops) / len(tops) >= AREA_OVERLAP_FRAC:
            c.add("text-on-area", where, f"text straddles an edge between fills ({len(uniq)} backdrops, dE00 up to "
                  f"{spread:.0f})", "Put the label wholly inside one fill or in open space, or give it an opaque "
                  "box or a halo.")
            t.on_area = True
        elif whole and c.shapes[next(iter(touched))]["kind"] == "area":
            back = t.backs[0]
            fg = c.text_color(t, back)
            floor = TEXT_MIN_LARGE if t.large() else TEXT_MIN
            if fg and contrast(fg, back) < floor:
                c.add("text-on-area", where, f"text inside a {back} fill at {contrast(fg, back):.2f}:1; floor "
                      f"{floor:g}:1", "Use dark text on light fills and white on dark ones (4.5:1), or move the "
                      "label out.")
            t.on_area = True


def check_text_clipped(c: Chart):
    tol = CANVAS_TOLERANCE_PX
    for t in c.texts:
        x0, y0, x1, y1 = t.box
        sides = [s for s, bad in (("left", x0 < -tol), ("right", x1 > c.w + tol), ("top", y0 < -tol),
                                  ("bottom", y1 > c.h + tol)) if bad]
        if sides:
            c.add("text-clipped", f"{t.kind} {snip(t.text)}", f"extends past the canvas {'/'.join(sides)} edge",
                  "Move the text inside the canvas or widen that margin.")
            continue
        b = t.clip
        if b and (x0 < b[0] - tol or x1 > b[2] + tol or y0 < b[1] - tol or y1 > b[3] + tol):
            c.add("text-clipped", f"{t.kind} {snip(t.text)}", "cut off by its clip box",
                  "Move the text inside the plot, or turn off clipping (Plotly cliponaxis=False, Vega-Lite "
                  "mark clip false, ggplot2 coord_cartesian(clip = 'off')) and widen that margin.")


def check_small_text(c: Chart):
    p = PRESETS[c.dest]
    scale = p["display_px"] / max(c.w, 1e-9)
    small = [t for t in c.texts if t.font_px * scale < p["min_text_px"] - 1e-6]
    if not small:
        return
    smallest = min(t.font_px for t in small)
    need = math.ceil(p["min_text_px"] / scale * 2) / 2
    examples = ", ".join(snip(t.text, 20) for t in sorted(small, key=lambda t: t.font_px)[:3])
    c.add("small-text", examples, f"{len(small)} text(s) below {p['min_text_px']} px at {p['display_px']} px wide "
          f"({c.dest}); smallest {smallest:.1f} px = {smallest * scale:.1f} px displayed",
          f"Use at least {need:g} px text on this {c.w:.0f} px wide canvas, or make the canvas narrower.")


def check_contrast(c: Chart):
    low = {}  # one finding per group of like texts (a whole axis of tick labels)
    for t in c.texts:
        if t.on_area or not t.backs:
            continue
        if t.halo and rgba(t.halo):
            backs = [over(t.halo, 1.0)]
        else:  # backdrops under at least AREA_OVERLAP_FRAC of the text (straddles are judged above)
            n = Counter(t.backs)
            backs = [b for b, k in n.items() if k >= AREA_OVERLAP_FRAC * len(t.backs)] or [n.most_common(1)[0][0]]
        glyph = not any(ch.isalnum() for ch in t.text)  # a symbol used as a color key is a mark
        floor = MARK_MIN if glyph else TEXT_MIN_LARGE if t.large() else TEXT_MIN
        worst = None
        for back in backs:
            fg = c.text_color(t, back)
            if fg and (worst is None or contrast(fg, back) < worst[0]):
                worst = (contrast(fg, back), fg, back)
        if worst and worst[0] < floor:
            key = (t.kind, worst[1], worst[2]) if t.kind == "tick" else id(t)
            low.setdefault(key, []).append((*worst, floor, t))
    for rows in low.values():
        cr, fg, back, floor, t = min(rows, key=lambda r: r[0])
        what = f"{len(rows)} tick labels, e.g. {snip(t.text, 20)}" if len(rows) > 1 else f"{t.kind} {snip(t.text, 30)}"
        c.add("contrast", what, f"text {fg} on {back} is {cr:.2f}:1; floor {floor:g}:1",
              "Darken the text (ev.text_color gives a 4.5:1 variant of a mark color) or lighten what is behind it.")
    for s in color_series(c):
        where = f"{'/'.join(sorted(s['marks']))} {s['hex']}"
        cr = contrast(s["hex"], s["back"])
        if s["marks"] & {"line", "point"}:
            if cr < INVISIBLE:
                c.add("contrast", where, f"lines/points {cr:.2f}:1 on {s['back']}; below {INVISIBLE}:1 they vanish",
                      "Use a darker slot (palettes.json use notes) for thin marks.")
            elif cr < MARK_MIN and not direct_labeled(c, s):
                c.add("contrast", where, f"lines/points {cr:.2f}:1 on {s['back']}; floor {MARK_MIN}:1",
                      "Direct-label the series or use a darker slot.", severity="warn")
        elif cr < INVISIBLE and s["edge_cr"] < MARK_MIN:
            c.add("contrast", where, f"fill {cr:.2f}:1 on {s['back']} with no outline",
                  "Outline the fill in a darker color or use a darker slot.", severity="warn")


def color_series(c: Chart) -> list:
    """Data colors that tell series apart: one per composited hex. Grays are left out, and so is any mark kind
    drawn in more than MAX_CATEGORICAL_COLORS colors (a color scale, not categories)."""
    if c.series is not None:
        return c.series
    out = {}
    for s in c.shapes:
        if c.scale_marks & set(s["cls"].split()):
            continue  # Vega marks colored by a continuous scale (heatmaps, choropleths)
        for paint in ("fill", "stroke"):
            h = s[f"{paint}_hex"]
            if not (s[f"data_{paint}"] and h) or is_neutral(h) or (paint == "stroke" and s["data_fill"]):
                continue
            mark = s["kind"] if paint == "fill" else ("point" if s["kind"] == "point" else "line")
            r = out.setdefault(h, {"hex": h, "back": s["back"], "marks": set(), "styles": set(), "traces": set(),
                                   "pts": [], "edge_cr": 0.0})
            r["marks"].add(mark)
            r["styles"].add((mark, s["dashed"] if paint == "stroke" else None))
            if s["trace"] is not None and mark == "bar":
                r["traces"].add(s["trace"])
            if paint == "fill" and s["stroke_hex"]:
                r["edge_cr"] = max(r["edge_cr"], contrast(s["stroke_hex"], s["back"]))
            if s["pieces"]:
                flat = [pt for p in s["pieces"] for pt in zip(p[0::2], p[1::2])]
                r["pts"] += [(x, y, 0.0) for x, y in flat[::max(1, len(flat) // 200)]]
            else:
                b = s["box"]
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                r["pts"] += [(cx, cy, max(b[2] - b[0], b[3] - b[1]) / 2)] if mark == "point" else \
                    [(b[0], b[1], 0.0), (b[2], b[1], 0.0), (b[0], b[3], 0.0), (b[2], b[3], 0.0), (cx, cy, 0.0)]
    series = list(out.values())
    for kinds in ({"line"}, {"point"}, {"bar", "area"}):
        group = [r for r in series if r["marks"] <= kinds]
        if len(group) > MAX_CATEGORICAL_COLORS:
            series = [r for r in series if r not in group]
    c.series = series
    return series


def series_gap(t: Text, s: dict) -> float:
    best = math.inf
    for x0, y0, x1, y1 in t.lines:
        for x, y, r in s["pts"]:
            best = min(best, math.hypot(max(x0 - x, x - x1, 0), max(y0 - y, y - y1, 0)) - r)
    return max(best, 0.0)


def direct_labeled(c: Chart, s: dict, rival: dict | None = None) -> bool:
    """A text in the series' hue (and not the rival's) sits within DIRECT_LABEL_REACH_LINES line heights of the
    series' marks and no farther from them than from the rival's."""
    for t in c.texts:
        if t.kind not in ("text",):
            continue
        fg = c.text_color(t, "#FFFFFF")
        if not fg or is_neutral(fg) or hue_gap(fg, s["hex"]) > HUE_MATCH_DEG or \
                (rival is not None and hue_gap(fg, rival["hex"]) <= HUE_MATCH_DEG):
            continue
        g = series_gap(t, s)
        if g <= DIRECT_LABEL_REACH_LINES * t.line_h and (rival is None or g <= series_gap(t, rival)):
            return True
    return False


def redundant_cue(c: Chart, a: dict, b: dict) -> str | None:
    """What besides color tells a from b, or None."""
    if a["traces"] & b["traces"]:
        return "bar position in one bar trace"
    shared = a["marks"] & b["marks"]
    if not shared or any({st for st in a["styles"] if st[0] == m}.isdisjoint({st for st in b["styles"] if st[0] == m})
                         for m in shared):
        return "dash or mark type"
    if direct_labeled(c, a, b) and direct_labeled(c, b, a):
        return "direct labels"
    return None


def check_cvd(c: Chart):
    series = color_series(c)
    for a, b in combinations(series, 2):
        ca, cb = Color(a["hex"]), Color(b["hex"])
        floor = max(DE_FLOOR[m] for m in a["marks"] | b["marks"]) * CVD_FACTOR
        d = {v: de(ca, cb, v) for v in ("protan", "deutan", "tritan")}
        red_green = [v for v in ("protan", "deutan") if d[v] < floor]
        if not red_green and d["tritan"] >= floor:
            continue
        cue = redundant_cue(c, a, b)
        if cue and not red_green:
            continue  # tritan-only and redundantly encoded
        v = min(red_green or ["tritan"], key=d.get)
        c.add("cvd", f"{a['hex']} x {b['hex']}",
              f"dE00 {d[v]:.1f} under {v} (floor {floor:.1f}; normal {de(ca, cb):.1f})"
              + (f"; told apart only by {cue}" if cue else "; color is the only cue"),
              "Direct-label each series in its own color at its mark, or vary dash or marker; better, use "
              "palettes.json slots that stay distinct (blue #0072B2 vs vermillion #D55E00).",
              severity="fail" if red_green and not cue else "warn")


SVG_CHECKS = [check_text_overlap, check_text_on_line, check_text_on_fills, check_text_clipped, check_small_text,
              check_contrast, check_cvd]


# ---------------------------------------------------------------------------
# Spec checks: Plotly figure JSON (full_figure_for_development() resolves ranges) and Vega
# ---------------------------------------------------------------------------

def load_spec(path: Path) -> tuple:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CheckError(f"cannot read spec {path}: {e}")
    if not isinstance(spec, dict):
        raise CheckError(f"spec {path} is not a JSON object")
    if isinstance(spec.get("data"), list) and isinstance(spec.get("layout"), dict):
        return "plotly", spec
    schema = str(spec.get("$schema", ""))
    if "vega-lite" in schema or ("marks" not in spec and any(k in spec for k in ("mark", "layer", "concat", "hconcat",
                                                                                "vconcat", "facet", "repeat"))):
        try:
            import vl_convert
        except ImportError:
            raise CheckError("a Vega-Lite spec needs vl-convert-python to compile; pass the compiled Vega instead "
                             "(vl_convert.vegalite_to_vega(spec), or Altair chart.to_dict(format='vega'))")
        return "vega", vl_convert.vegalite_to_vega(spec)
    if "marks" in spec or "/vega/" in schema:
        return "vega", spec
    raise CheckError(f"spec {path} is neither Plotly figure JSON (data + layout) nor Vega/Vega-Lite")


PLOTLY_CARTESIAN = {"scatter", "scattergl", "bar", "histogram", "box", "violin", "heatmap", "heatmapgl", "contour",
                    "histogram2d", "histogram2dcontour", "funnel", "waterfall", "ohlc", "candlestick", "image"}


def _title(obj) -> str:
    t = obj.get("title") if isinstance(obj, dict) else None
    return (t.get("text") or "") if isinstance(t, dict) else (t or "") if isinstance(t, str) else ""


def plotly_checks(fig: dict, texts: list, add):
    lay = fig.get("layout", {})
    axis = lambda ref: lay.get(ref[0] + "axis" + ref[1:], {})  # noqa: E731
    traces = [t for t in fig.get("data", []) if t.get("visible", True) is True]
    used, value_axes = set(), {}
    for tr in traces:
        typ = tr.get("type", "scatter")
        if typ not in PLOTLY_CARTESIAN:
            continue
        xr, yr = tr.get("xaxis", "x"), tr.get("yaxis", "y")
        used |= {xr, yr}
        horiz = tr.get("orientation") == "h" or (typ == "histogram" and "y" in tr and "x" not in tr)
        if typ not in ("heatmap", "heatmapgl", "contour", "histogram2d", "histogram2dcontour", "image"):
            value_axes.setdefault(xr if horiz else yr, set()).add(typ)
        if typ in ("bar", "histogram") and tr.get("base") is None:
            ref = xr if horiz else yr
            ax = axis(ref)
            rng = ax.get("range")
            if ax.get("type") == "log":
                add("bar-baseline", f"{ref}axis", "bars on a log value axis",
                    "Plot bars on a linear axis from zero, or use a dot plot for log data.")
            elif ax.get("type") in (None, "linear", "-") and isinstance(rng, list) and len(rng) == 2 and \
                    all(isinstance(v, (int, float)) for v in rng) and not min(rng) <= 0 <= max(rng):
                add("bar-baseline", f"{ref}axis", f"value axis spans {min(rng):.4g} to {max(rng):.4g}, excluding 0",
                    "Drop the explicit range on the bar axis (autorange includes 0) or start it at 0; or use a "
                    "dot plot.")
    for key, ax in lay.items():
        if re.fullmatch(r"[xy]axis\d*", key) and ax.get("overlaying"):
            ref = key[0] + key[5:]
            if ref in used and ax["overlaying"] in used:
                add("dual-axis", f"{key} over {ax['overlaying']}axis", "two value axes on separate scales share a plot",
                    "Split into two aligned panels (make_subplots(shared_xaxes=True)) or index both series to a "
                    "common baseline.")
    words = " ".join(t.text for t in texts)
    for ref in sorted(used):
        ax = axis(ref)
        if ax.get("type") == "log" and not LOG_WORD_RE.search(words):
            add("log-unlabeled", f"{ref}axis", "log scale not stated in any axis title, title, or note",
                "Say 'log scale' in the axis title or subtitle, and keep real-value ticks (1, 10, 100).")
        rng = ax.get("range")
        reversed_ = ax.get("autorange") == "reversed" or (isinstance(rng, list) and len(rng) == 2 and all(
            isinstance(v, (int, float)) for v in rng) and rng[0] > rng[1])
        if reversed_ and ref in value_axes and ax.get("type") in (None, "linear", "log", "-") and \
                not RANK_RE.search(f"{_title(ax)} {_title(lay)}"):
            add("inverted-axis", f"{ref}axis", "value axis reversed: higher values toward the origin",
                "Restore normal order (drop autorange='reversed'), or title the axis 'Rank (1 = best)'.")
    scales = []
    for tr in traces:
        if tr.get("colorscale") and tr.get("type") in ("heatmap", "heatmapgl", "contour", "histogram2d",
                                                       "histogram2dcontour", "surface", "choropleth",
                                                       "choroplethmapbox", "choroplethmap", "densitymapbox",
                                                       "densitymap"):
            scales.append((tr.get("type"), tr["colorscale"]))
        for part in ("marker", "line"):
            sub = tr.get(part) or {}
            if isinstance(sub, dict) and sub.get("colorscale") and isinstance(sub.get("color"), list) and \
                    any(isinstance(v, (int, float)) for v in sub["color"]):
                scales.append((f"{tr.get('type', 'scatter')} {part}", sub["colorscale"]))
    for key, ca in lay.items():
        if re.fullmatch(r"coloraxis\d*", key) and isinstance(ca, dict) and ca.get("colorscale"):
            if any(isinstance(tr.get(p), dict) and tr[p].get("coloraxis") == key for tr in traces
                   for p in ("marker", "line")) or any(tr.get("coloraxis") == key for tr in traces):
                scales.append((key, ca["colorscale"]))
    for where, cs in scales:
        hexes = _plotly_scale_hexes(cs)
        if hexes and rainbow_like(hexes):
            add("rainbow-cmap", where, "rainbow color scale distorts data order",
                "Use a perceptually uniform scale: viridis or cividis (sequential), RdBu or PuOr (diverging).")


def _plotly_scale_hexes(cs, n: int = 11) -> list:
    """Sample a Plotly colorscale ([[0, color], ..., [1, color]]) at n even steps as hex."""
    if not isinstance(cs, list) or len(cs) < 2:
        return []
    stops = []
    for pos, col in cs:
        c = rgba(col) if str(col).startswith("rgb") else None
        if c is None and re.fullmatch(r"#[0-9a-fA-F]{6}", str(col)):
            c = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5)) + (1.0,)
        if c is None:
            return []
        stops.append((float(pos), c))
    out = []
    for k in range(n):
        x = k / (n - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= x <= p1:
                f = 0.0 if p1 == p0 else (x - p0) / (p1 - p0)
                out.append("#" + "".join(f"{round(a + (b - a) * f):02X}" for a, b in zip(c0[:3], c1[:3])))
                break
    return out if len(out) == n else []


def vega_groups(node, path="root"):
    yield path, node
    for mk in node.get("marks", []):
        if mk.get("type") == "group":
            yield from vega_groups(mk, f"{path}/{mk.get('name', 'group')}")


def vega_scale_marks(spec: dict) -> set:
    """Names of Vega marks whose fill or stroke comes from a continuous scale; the SVG carries the name as a
    class on the mark's group."""
    scales = {s.get("name"): s for _, g in vega_groups(spec) for s in g.get("scales", [])}
    out = set()
    for _, g in vega_groups(spec):
        for mk in g.get("marks", []):
            enc = mk.get("encode", {})
            for rule in [(enc.get(k) or {}).get(ch) for k in ("enter", "update") for ch in ("fill", "stroke")]:
                for r in rule if isinstance(rule, list) else [rule]:
                    typ = scales.get(r.get("scale"), {}).get("type") if isinstance(r, dict) else None
                    if typ and typ not in ("ordinal", "band", "point") and mk.get("name"):
                        out.add(mk["name"])
    return out


def vega_checks(spec: dict, texts: list, add):
    groups = vega_groups
    words = " ".join(t.text for t in texts)
    scales, axis_scales = {}, set()
    for path, g in groups(spec):
        scales.update({s["name"]: s for s in g.get("scales", []) if "name" in s})
    for path, g in groups(spec):
        axes = [a for a in g.get("axes", []) if a.get("scale") and a.get("labels", True) is not False]
        axis_scales |= {a["scale"] for a in axes}
        for o1, o2 in (("left", "right"), ("top", "bottom")):
            s1 = {a["scale"] for a in axes if a.get("orient") == o1}
            s2 = {a["scale"] for a in axes if a.get("orient") == o2}
            if s1 and s2 and s1 != s2 and all(scales.get(s, {}).get("type") not in ("band", "point", "ordinal")
                                               for s in s1 | s2):
                add("dual-axis", path, f"{o1} axis {sorted(s1)} and {o2} axis {sorted(s2)} use different scales",
                    "Split into two aligned views (vconcat) or index both series to a common baseline; drop "
                    "resolve.scale independent.")
        for a in axes:
            s = scales.get(a["scale"], {})
            title = a.get("title") if isinstance(a.get("title"), str) else " ".join(a.get("title") or []) \
                if isinstance(a.get("title"), list) else ""
            if s.get("reverse") is True and s.get("type", "linear") in ("linear", "log", "pow", "sqrt", "symlog") \
                    and not RANK_RE.search(title):
                add("inverted-axis", f"{path}/{a['scale']}", "value axis reversed: higher values toward the origin",
                    "Drop scale.reverse, or title the axis 'Rank (1 = best)'.")
        for mk in g.get("marks", []):
            if mk.get("type") != "rect" or "bar" not in (mk.get("style") or []):
                continue
            enc = {**mk.get("encode", {}).get("enter", {}), **mk.get("encode", {}).get("update", {})}
            names = {(enc.get(ch) or {}).get("scale") for ch in ("x", "y", "x2", "y2") if isinstance(enc.get(ch), dict)}
            for name in sorted(n for n in names if n):
                s = scales.get(name, {})
                typ = s.get("type", "linear")
                if typ in ("band", "point", "ordinal", "time", "utc"):
                    continue
                where = f"{path}/{mk.get('name', 'bar')}"
                dom = s.get("domain")
                if typ in ("log", "symlog", "pow", "sqrt"):
                    add("bar-baseline", where, f"bars on a {typ} scale",
                        "Plot bars on a linear scale from zero, or use a point mark for log data.")
                elif isinstance(dom, list) and len(dom) == 2 and all(isinstance(v, (int, float)) for v in dom) and \
                        not min(dom) <= 0 <= max(dom):
                    add("bar-baseline", where, f"scale domain {dom} excludes 0",
                        "Drop scale.domain on the bar axis (or include 0), or use a point mark.")
                elif (isinstance(s.get("domainMin"), (int, float)) and s["domainMin"] > 0) or \
                        (isinstance(s.get("domainMax"), (int, float)) and s["domainMax"] < 0):
                    add("bar-baseline", where, "scale domainMin/domainMax excludes 0",
                        "Drop domainMin/domainMax on the bar axis, or use a point mark.")
                elif s.get("zero") is False and not isinstance(dom, list):
                    add("bar-baseline", where, "scale.zero is false: the axis may not reach 0",
                        "Remove scale: {zero: false} from the bar axis.", severity="warn")
    for name, s in scales.items():
        if s.get("type") in ("log", "symlog") and name in axis_scales and not LOG_WORD_RE.search(words):
            add("log-unlabeled", name, f"{s['type']} scale not stated in any axis title, title, or note",
                "Say 'log scale' in the axis title or subtitle, and keep real-value ticks (1, 10, 100).")
        rng = s.get("range")
        scheme = rng.get("scheme") if isinstance(rng, dict) else s.get("scheme")
        if isinstance(scheme, str) and scheme.lower() in VEGA_RAINBOW and s.get("type") not in ("ordinal", "band",
                                                                                                "point"):
            add("rainbow-cmap", name, f"rainbow scheme '{scheme}' distorts data order",
                "Use a perceptually uniform scheme: viridis or cividis (sequential), redblue or purpleorange "
                "(diverging).")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run_checks(svg_path, dest: str = "blog", spec_path=None, chrome: str | None = None) -> dict:
    """Measure and check one SVG (plus an optional spec). Raises CheckError."""
    svg_path = Path(svg_path)
    try:
        svg_text = svg_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise CheckError(f"cannot read {svg_path}: {e}")
    if outlined_text(svg_text):
        raise CheckError(f"{svg_path.name} draws its text as outlines, which cannot be measured; {OUTLINED_HINT}")
    spec = load_spec(Path(spec_path)) if spec_path else None
    chrome = chrome or find_chrome()
    if not chrome and not spec:
        raise CheckError(CHROME_HINT)
    stack = stack_of(svg_text)
    if chrome:
        c = Chart(measure(svg_text, chrome), dest)
        if spec and spec[0] == "vega":
            c.scale_marks = vega_scale_marks(spec[1])
        for fn in SVG_CHECKS:
            fn(c)
        findings, texts = c.findings, c.texts
    else:  # spec checks read the spec, and the chart's words from the SVG source; nothing needs a browser
        findings = []
        texts = [SimpleNamespace(text=html.unescape(re.sub(r"<[^>]+>", "", t)))
                 for t in re.findall(r"<text\b[^>]*>(.*?)</text>", svg_text, re.S)]

        def add(check, where, detail, fix, severity=None):
            findings.append({"check": check, "severity": severity or CHECKS[check][0], "where": where,
                             "detail": detail, "fix": fix})
    if spec:
        (plotly_checks if spec[0] == "plotly" else vega_checks)(spec[1], texts, c.add if chrome else add)
    fails = sum(f["severity"] == "fail" for f in findings)
    res = {"result": "fail" if fails else "pass", "dest": dest, "stack": stack, "spec": spec[0] if spec else None,
           "fails": fails, "warns": len(findings) - fails, "findings": findings}
    if not chrome:
        res["note"] = f"SVG checks skipped, only the --spec checks ran: {CHROME_HINT}"
    elif stack == "matplotlib":
        res["note"] = "matplotlib chart: check_chart.py on the script runs more checks"
    elif not spec:
        res["note"] = "no --spec: bar-baseline, dual-axis, inverted-axis, log-unlabeled, rainbow-cmap not checked"
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an exported chart SVG (Plotly, Vega-Lite/Altair, D3, ggplot2 "
                                 "via svglite) in headless Chrome, with check_chart.py's check names.")
    ap.add_argument("svg", nargs="?", type=Path, help="Path to the chart .svg (text exported as text).")
    ap.add_argument("--dest", choices=sorted(PRESETS), default="blog", help="Display target for small-text.")
    ap.add_argument("--spec", type=Path, help="Plotly figure JSON (full_figure_for_development().to_json()), "
                    "compiled Vega, or Vega-Lite (needs vl-convert-python).")
    ap.add_argument("--json", action="store_true", help="Print JSON only.")
    ap.add_argument("--list-checks", action="store_true", help="List checks and exit.")
    args = ap.parse_args(argv)

    if args.list_checks:
        for name, (sev, desc) in CHECKS.items():
            print(f"{name}\t{sev}\t{desc}")
        return 0
    if args.svg is None:
        ap.error("svg path required")

    def error(msg):
        if args.json:
            print(json.dumps({"result": "error", "error": msg}))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 2

    if not args.svg.is_file():
        return error(f"svg file not found: {args.svg}")
    if args.spec is not None and not args.spec.is_file():
        return error(f"spec file not found: {args.spec}")
    try:
        res = run_checks(args.svg, args.dest, args.spec)
    except CheckError as e:
        return error(str(e))
    if args.json:
        print(json.dumps(res, indent=1))
    else:
        for f in res["findings"]:
            print(f"{f['severity'].upper()} {f['check']} | {f['where']} | {f['detail']} | fix: {f['fix']}")
        if res.get("note"):
            print(f"NOTE {res['note']}")
        print(f"RESULT {res['result'].upper()}: {res['fails']} fail, {res['warns']} warn, stack={res['stack']}, "
              f"dest={res['dest']}")
    return 1 if res["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
