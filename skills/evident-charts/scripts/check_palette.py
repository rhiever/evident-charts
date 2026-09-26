#!/usr/bin/env python3
"""Palette and contrast validator for explanatory charts (checks V2-V16).

Pure standard library. MIT License. Our own implementation from the primary
formulas: IEC 61966-2-1 sRGB, CIE 1976 L*a*b* (D65), CIEDE2000 (Sharma, Wu &
Dalal 2005), OKLab (Ottosson 2020), Machado, Oliveira & Fernandes 2009 CVD
matrices (severity 1.0, applied in linear sRGB), WCAG 2.x luminance/contrast.

Usage:
  check_palette.py "#D55E00,#0072B2,#009E73" --role categorical --mark line
  check_palette.py "#D55E00" --role highlight --context "#BDBDBD" --text "#C15500"
  check_palette.py --preset highlight          (see --list-presets)
  check_palette.py ... --background "#FFFFFF,#121212"   (V16: rerun per surface)
  check_palette.py --list-checks | --self-test

Output: one line per check, `ID STATUS [tag] detail`, then a RESULT line.
Tags: E replicated evidence, P practitioner standard, T convention.
Exit: 0 no FAIL (WARN allowed), 1 any FAIL, 2 bad input.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
from pathlib import Path

PALETTES_JSON = Path(__file__).resolve().parent.parent / "assets" / "palettes.json"

# ---------------------------------------------------------------------------
# Thresholds. Tag says how firmly each is held.
# ---------------------------------------------------------------------------
TEXT_MIN, TEXT_MIN_LARGE = 4.5, 3.0          # V2  [P] WCAG 1.4.3
MARK_MIN = 3.0                               # V3  [P] WCAG 1.4.11
INVISIBLE = 1.5                              # V3/V4/V12 [T] practically invisible
DE_FLOOR = {"bar": 10.0, "area": 10.0, "line": 15.0, "point": 20.0, "text": 20.0}  # V5 [T]
CVD_FACTOR = 0.6                             # V6/V7/V15 floor = 0.6 x V5 floor [T]
RG_RATIO = 2.0                               # V7 normal dE >= 2x CVD dE [T]
DL_HIGHLIGHT = 0.15                          # V8 accent vs context OKLab dL [T]
DL_CATEGORICAL = 0.05                        # V8 categorical grayscale merge [T]
CAT_WARN, CAT_MAX, MAX_ACCENTS = 4, 7, 2     # V9  [P]
UNIFORM_CV = 0.35                            # V11 [T]
MID_CHROMA = 0.03                            # V13 [P] OKLCH C
ARM_ASYM = 0.05                              # V14 [T] OKLab L
DARK_DEFAULT = "#121212"

CHECKS = {
    "V2": ("P", "text contrast >= 4.5:1 (3:1 with --large-text)"),
    "V3": ("P", "mark contrast vs background >= 3:1, else WARN; line/point/text < 1.5:1 FAIL"),
    "V4": ("T", "context grays < 3:1 allowed only in highlight role with an accent"),
    "V5": ("T", "CIEDE2000 >= mark floor (bar/area 10, line 15, point/text 20); direction is [E]"),
    "V6": ("T", "CIEDE2000 under protan/deutan >= 0.6x V5 floor; tritan WARN only"),
    "V7": ("T", "red-green reliance: normal dE >= 2x protan/deutan dE and CVD dE < V6 floor"),
    "V8": ("T", "OKLab lightness: accent vs context dL >= 0.15; categorical min dL < 0.05 WARN"),
    "V9": ("P", "categorical count WARN > 4, FAIL > 7; highlight accents <= 2"),
    "V10": ("E", "sequential lightness strictly monotone (diverging: each arm)"),
    "V11": ("T", "sequential step uniformity: CV of adjacent dE00 <= 0.35"),
    "V12": ("T", "faintest step (seq) or midpoint (div) >= 1.5:1 for bar/line/point/text marks"),
    "V13": ("P", "diverging midpoint: odd count, OKLCH C <= 0.03, closest to background lightness"),
    "V14": ("T", "diverging arm symmetry: |L_i - L_mirror| <= 0.05"),
    "V15": ("T", "diverging endpoints distinct under protan/deutan (>= V6 floor)"),
    "V16": ("P", "rerun all checks per background: --background A,B or --dark"),
}

# ---------------------------------------------------------------------------
# Color math
# ---------------------------------------------------------------------------
SRGB_TO_XYZ = ((0.4124564, 0.3575761, 0.1804375),
               (0.2126729, 0.7151522, 0.0721750),
               (0.0193339, 0.1191920, 0.9503041))
WHITE_D65 = (0.95047, 1.0, 1.08883)
# Machado, Oliveira & Fernandes 2009, severity 1.0 (authors' published table).
CVD = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}
VISIONS = ("normal", "protan", "deutan", "tritan")


def _mul(m, v):
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))


def parse_hex(s: str) -> str:
    """Normalize '#abc', 'abc', '#aabbcc' to '#AABBCC'. Raises ValueError."""
    h = s.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"not a hex color: {s!r}")
    return "#" + h.upper()


def srgb_to_linear(c8: int) -> float:
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h: str):
    h = parse_hex(h)
    return tuple(srgb_to_linear(int(h[i:i + 2], 16)) for i in (1, 3, 5))


def linear_to_lab(rgb):
    x, y, z = _mul(SRGB_TO_XYZ, rgb)
    d = 6.0 / 29.0

    def f(t):
        return t ** (1.0 / 3.0) if t > d ** 3 else t / (3 * d * d) + 4.0 / 29.0

    fx, fy, fz = f(x / WHITE_D65[0]), f(y / WHITE_D65[1]), f(z / WHITE_D65[2])
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def linear_to_oklab(rgb):
    r, g, b = rgb
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1.0 / 3.0), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def simulate(rgb, vision: str):
    if vision == "normal":
        return rgb
    return tuple(min(1.0, max(0.0, v)) for v in _mul(CVD[vision], rgb))


def ciede2000(lab1, lab2, kl=1.0, kc=1.0, kh=1.0) -> float:
    """CIEDE2000 color difference (Sharma, Wu & Dalal 2005, eqs. 1-22)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    cbar = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2.0
    g = 0.5 * (1.0 - math.sqrt(cbar ** 7 / (cbar ** 7 + 25.0 ** 7)))
    a1p, a2p = (1.0 + g) * a1, (1.0 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360.0 if c1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360.0 if c2p else 0.0
    dlp, dcp = L2 - L1, c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180.0:
            dhp -= 360.0
        elif dhp < -180.0:
            dhp += 360.0
    dhp_big = 2.0 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp / 2.0))
    lbar, cbarp = (L1 + L2) / 2.0, (c1p + c2p) / 2.0
    if c1p * c2p == 0:
        hbar = h1p + h2p
    elif abs(h1p - h2p) <= 180.0:
        hbar = (h1p + h2p) / 2.0
    elif h1p + h2p < 360.0:
        hbar = (h1p + h2p + 360.0) / 2.0
    else:
        hbar = (h1p + h2p - 360.0) / 2.0
    t = (1.0 - 0.17 * math.cos(math.radians(hbar - 30.0)) + 0.24 * math.cos(math.radians(2.0 * hbar))
         + 0.32 * math.cos(math.radians(3.0 * hbar + 6.0)) - 0.20 * math.cos(math.radians(4.0 * hbar - 63.0)))
    dtheta = 30.0 * math.exp(-(((hbar - 275.0) / 25.0) ** 2))
    rc = 2.0 * math.sqrt(cbarp ** 7 / (cbarp ** 7 + 25.0 ** 7))
    sl = 1.0 + 0.015 * (lbar - 50.0) ** 2 / math.sqrt(20.0 + (lbar - 50.0) ** 2)
    sc = 1.0 + 0.045 * cbarp
    sh = 1.0 + 0.015 * cbarp * t
    rt = -math.sin(math.radians(2.0 * dtheta)) * rc
    dl, dc, dh = dlp / (kl * sl), dcp / (kc * sc), dhp_big / (kh * sh)
    return math.sqrt(dl * dl + dc * dc + dh * dh + rt * dc * dh)


def luminance(h: str) -> float:
    r, g, b = hex_to_linear(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1: str, h2: str) -> float:
    a, b = sorted((luminance(h1), luminance(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


class Color:
    __slots__ = ("hex", "lin", "ok", "_lab")

    def __init__(self, h: str):
        self.hex = parse_hex(h)
        self.lin = hex_to_linear(self.hex)
        self.ok = linear_to_oklab(self.lin)
        self._lab = {}

    @property
    def L(self):
        return self.ok[0]

    @property
    def C(self):
        return math.hypot(self.ok[1], self.ok[2])

    def lab(self, vision="normal"):
        if vision not in self._lab:
            self._lab[vision] = linear_to_lab(simulate(self.lin, vision))
        return self._lab[vision]


def de(c1: Color, c2: Color, vision="normal") -> float:
    return ciede2000(c1.lab(vision), c2.lab(vision))


# Sharma, Wu & Dalal 2005 test data: L1 a1 b1 L2 a2 b2 dE00 (34 pairs).
SHARMA_PAIRS = (
    (50.0000, 2.6772, -79.7751, 50.0000, 0.0000, -82.7485, 2.0425),
    (50.0000, 3.1571, -77.2803, 50.0000, 0.0000, -82.7485, 2.8615),
    (50.0000, 2.8361, -74.0200, 50.0000, 0.0000, -82.7485, 3.4412),
    (50.0000, -1.3802, -84.2814, 50.0000, 0.0000, -82.7485, 1.0000),
    (50.0000, -1.1848, -84.8006, 50.0000, 0.0000, -82.7485, 1.0000),
    (50.0000, -0.9009, -85.5211, 50.0000, 0.0000, -82.7485, 1.0000),
    (50.0000, 0.0000, 0.0000, 50.0000, -1.0000, 2.0000, 2.3669),
    (50.0000, -1.0000, 2.0000, 50.0000, 0.0000, 0.0000, 2.3669),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0009, 7.1792),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0010, 7.1792),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0011, 7.2195),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0012, 7.2195),
    (50.0000, -0.0010, 2.4900, 50.0000, 0.0009, -2.4900, 4.8045),
    (50.0000, -0.0010, 2.4900, 50.0000, 0.0010, -2.4900, 4.8045),
    (50.0000, -0.0010, 2.4900, 50.0000, 0.0011, -2.4900, 4.7461),
    (50.0000, 2.5000, 0.0000, 50.0000, 0.0000, -2.5000, 4.3065),
    (50.0000, 2.5000, 0.0000, 73.0000, 25.0000, -18.0000, 27.1492),
    (50.0000, 2.5000, 0.0000, 61.0000, -5.0000, 29.0000, 22.8977),
    (50.0000, 2.5000, 0.0000, 56.0000, -27.0000, -3.0000, 31.9030),
    (50.0000, 2.5000, 0.0000, 58.0000, 24.0000, 15.0000, 19.4535),
    (50.0000, 2.5000, 0.0000, 50.0000, 3.1736, 0.5854, 1.0000),
    (50.0000, 2.5000, 0.0000, 50.0000, 3.2972, 0.0000, 1.0000),
    (50.0000, 2.5000, 0.0000, 50.0000, 1.8634, 0.5757, 1.0000),
    (50.0000, 2.5000, 0.0000, 50.0000, 3.2592, 0.3350, 1.0000),
    (60.2574, -34.0099, 36.2677, 60.4626, -34.1751, 39.4387, 1.2644),
    (63.0109, -31.0961, -5.8663, 62.8187, -29.7946, -4.0864, 1.2630),
    (61.2901, 3.7196, -5.3901, 61.4292, 2.2480, -4.9620, 1.8731),
    (35.0831, -44.1164, 3.7933, 35.0232, -40.0716, 1.5901, 1.8645),
    (22.7233, 20.0904, -46.6940, 23.0331, 14.9730, -42.5619, 2.0373),
    (36.4612, 47.8580, 18.3852, 36.2715, 50.5065, 21.2231, 1.4146),
    (90.8027, -2.0831, 1.4410, 91.1528, -1.6435, 0.0447, 1.4441),
    (90.9257, -0.5406, -0.9208, 88.6381, -0.8985, -0.7239, 1.5381),
    (6.7747, -0.2908, -2.4247, 5.8714, -0.0985, -2.2286, 0.6377),
    (2.0776, 0.0795, -1.1350, 0.9033, -0.0636, -0.5514, 0.9082),
)


def self_test(tol=1e-4):
    """Return (ok, max_abs_error) over Sharma pairs, both argument orders."""
    err = 0.0
    for row in SHARMA_PAIRS:
        for p, q in ((row[0:3], row[3:6]), (row[3:6], row[0:3])):
            err = max(err, abs(ciede2000(p, q) - row[6]))
    return err <= tol, err


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def _r(cid, status, detail, offenders=()):
    return {"id": cid, "status": status, "tag": CHECKS[cid][0], "detail": detail,
            "offenders": list(offenders)}


def _pairs(colors, context, pairs):
    idx = range(len(colors))
    base = zip(idx, idx[1:]) if pairs == "adjacent" else itertools.combinations(idx, 2)
    out = [(colors[i], colors[j]) for i, j in base]
    out += [(c, g) for c in colors for g in context]
    return out


def _min_pair(pairs, vision):
    best = None
    for a, b in pairs:
        d = de(a, b, vision)
        if best is None or d < best[0]:
            best = (d, a, b)
    return best


def _fmt(p):
    return f"{p[0]:.1f} {p[1].hex}~{p[2].hex}"


def check_text(texts, bg, large):
    floor = TEXT_MIN_LARGE if large else TEXT_MIN
    rows = sorted((contrast(c.hex, bg.hex), c.hex) for c in texts)
    bad = [h for cr, h in rows if cr < floor]
    worst = rows[0]
    status = "FAIL" if bad else "PASS"
    return _r("V2", status, f"min {worst[0]:.2f}:1 {worst[1]}; floor {floor}:1"
              + (f"; below: {','.join(bad)}" if bad else ""), bad)


def check_marks(colors, bg, mark, label="marks"):
    rows = sorted((contrast(c.hex, bg.hex), c.hex) for c in colors)
    low = [h for cr, h in rows if cr < MARK_MIN]
    invisible = [h for cr, h in rows if cr < INVISIBLE]
    worst = rows[0]
    detail = f"{label} {'min ' if len(rows) > 1 else ''}{worst[0]:.2f}:1 {worst[1]}"
    dim = [h for h in low if h not in invisible]
    if invisible and mark in ("line", "point", "text"):
        return _r("V3", "FAIL", detail + f"; < {INVISIBLE}:1 invisible as {mark}: {','.join(invisible)}", invisible)
    if low:
        parts = [f"< {INVISIBLE}:1 fills need dark outline: {','.join(invisible)}"] if invisible else []
        parts += [f"< 3:1 needs direct labels or table: {','.join(dim)}"] if dim else []
        return _r("V3", "WARN", detail + "; " + "; ".join(parts), low)
    return _r("V3", "PASS", detail + "; floor 3:1")


def check_context(context, bg, role, has_accent):
    rows = sorted((contrast(c.hex, bg.hex), c.hex) for c in context)
    worst = rows[0]
    detail = f"context min {worst[0]:.2f}:1 {worst[1]}"
    if worst[0] >= MARK_MIN:
        return _r("V4", "PASS", detail)
    if worst[0] < INVISIBLE:
        return _r("V4", "WARN", detail + f"; < {INVISIBLE}:1 barely visible", [worst[1]])
    if role == "highlight" and has_accent:
        return _r("V4", "PASS", detail + "; exempt < 3:1: direct-label the accent series")
    return _r("V4", "WARN", detail + "; < 3:1 exempt only in highlight role", [worst[1]])


def check_distinct(pairs, floor, label):
    if not pairs:
        return []
    out = []
    n = _min_pair(pairs, "normal")
    status = "PASS" if n[0] >= floor else "FAIL"
    out.append(_r("V5", status, f"min dE00 {_fmt(n)} ({label}); floor {floor:g}",
                  [n[1].hex, n[2].hex] if status == "FAIL" else ()))
    cfloor = floor * CVD_FACTOR
    mins = {v: _min_pair(pairs, v) for v in ("protan", "deutan", "tritan")}
    red_green_bad = [v for v in ("protan", "deutan") if mins[v][0] < cfloor]
    status = "FAIL" if red_green_bad else ("WARN" if mins["tritan"][0] < cfloor else "PASS")
    offs = []
    for v in red_green_bad or (["tritan"] if status == "WARN" else []):
        offs += [mins[v][1].hex, mins[v][2].hex]
    out.append(_r("V6", status, "; ".join(f"{v} {_fmt(mins[v])}" for v in mins)
                  + f"; floor {cfloor:.1f} (tritan WARN only)", offs))
    out.append(check_red_green(pairs, cfloor))
    return out


def check_red_green(pairs, cfloor):
    worst = None
    for a, b in pairs:
        dn = de(a, b)
        for v in ("protan", "deutan"):
            dv = de(a, b, v)
            if dn >= RG_RATIO * dv and dv < cfloor and (worst is None or dv < worst[0]):
                worst = (dv, a, b, v, dn)
    if worst:
        dv, a, b, v, dn = worst
        return _r("V7", "FAIL", f"{a.hex}~{b.hex} dE00 {dn:.1f} normal -> {dv:.1f} {v}; "
                  "add labels/position/lightness or swap to blue/orange", [a.hex, b.hex])
    return _r("V7", "PASS", "no pair relies on red-green alone")


def check_lightness(pairs, role, context, colors):
    if role == "highlight":
        rows = sorted((abs(a.L - g.L), a.hex, g.hex) for a in colors for g in context)
        if not rows:
            return None
        d, a, g = rows[0]
        status = "PASS" if d >= DL_HIGHLIGHT else "FAIL"
        return _r("V8", status, f"accent~context min dL {d:.3f} {a}~{g}; floor {DL_HIGHLIGHT}",
                  [a, g] if status == "FAIL" else ())
    if not pairs:
        return None
    d, a, b = min((abs(a.L - b.L), a, b) for a, b in pairs)
    if d < DL_CATEGORICAL:
        return _r("V8", "WARN", f"min dL {d:.3f} {a.hex}~{b.hex} merge in grayscale; direct-label", [a.hex, b.hex])
    return _r("V8", "PASS", f"min dL {d:.3f} {a.hex}~{b.hex}")


def check_monotone(colors, role):
    Ls = [c.L for c in colors]
    if role == "sequential":
        steps = [Ls[i + 1] - Ls[i] for i in range(len(Ls) - 1)]
        sign = 1 if Ls[-1] >= Ls[0] else -1
        bad = [(-s * sign, i) for i, s in enumerate(steps) if s * sign <= 0]
        if bad:
            _, i = max(bad)
            return _r("V10", "FAIL", f"L reverses {colors[i].hex}->{colors[i + 1].hex} "
                      f"({Ls[i]:.3f}->{Ls[i + 1]:.3f}), {len(bad)} reversal(s); use a monotone ramp (viridis)",
                      [colors[i].hex, colors[i + 1].hex])
        return _r("V10", "PASS", f"L {Ls[0]:.3f}->{Ls[-1]:.3f} monotone, min step {min(abs(s) for s in steps):.3f}")
    n = len(colors)
    left = list(range((n - 1) // 2, -1, -1))         # middle outward
    right = list(range(n // 2, n))
    signs = set()
    for arm in (left, right):
        for i, j in zip(arm, arm[1:]):
            d = Ls[j] - Ls[i]
            if d == 0:
                return _r("V10", "FAIL", f"arm flat {colors[i].hex}->{colors[j].hex}",
                          [colors[i].hex, colors[j].hex])
            signs.add(d > 0)
    if len(signs) > 1:
        return _r("V10", "FAIL", "arm lightness not monotone away from midpoint", [c.hex for c in colors])
    return _r("V10", "PASS", "each arm monotone in L away from midpoint")


def check_uniform(colors):
    steps = [de(colors[i], colors[i + 1]) for i in range(len(colors) - 1)]
    cv = statistics.pstdev(steps) / statistics.mean(steps) if statistics.mean(steps) else float("inf")
    status = "PASS" if cv <= UNIFORM_CV else "WARN"
    return _r("V11", status, f"step dE00 {min(steps):.1f}-{max(steps):.1f}, CV {cv:.2f}; max {UNIFORM_CV}")


def check_visible_end(colors, bg, role):
    if role == "diverging":
        n = len(colors)
        mids = colors[(n - 1) // 2:n // 2 + 1]
        cr, h = min((contrast(c.hex, bg.hex), c.hex) for c in mids)
        what, fix = "midpoint", "outline marks or use a darker neutral"
    else:
        cr, h = min((contrast(c.hex, bg.hex), c.hex) for c in colors)
        what, fix = "faintest step", "trim the light end or outline marks"
    if cr < INVISIBLE:
        return _r("V12", "WARN", f"{what} {h} {cr:.2f}:1 < {INVISIBLE}; {fix}", [h])
    return _r("V12", "PASS", f"{what} {h} {cr:.2f}:1")


def check_midpoint(colors, bg):
    n = len(colors)
    bgL = bg.L
    lo, hi = (n - 1) // 2, n // 2 + 1
    mids, rest = colors[lo:hi], colors[:lo] + colors[hi:]
    if max(abs(m.L - bgL) for m in mids) > min(abs(c.L - bgL) for c in rest):
        far = [m.hex for m in mids]
        return _r("V13", "FAIL", f"midpoint {','.join(far)} is not the step closest to background lightness", far)
    if n % 2 == 0:
        return _r("V13", "WARN", f"even count {n}: no neutral class; OK only if 0 is a class boundary")
    m = mids[0]
    if m.C > MID_CHROMA:
        return _r("V13", "WARN", f"midpoint {m.hex} OKLCH C {m.C:.3f} > {MID_CHROMA}; use a neutral", [m.hex])
    return _r("V13", "PASS", f"midpoint {m.hex} C {m.C:.3f}, closest to background")


def check_symmetry(colors):
    n = len(colors)
    rows = [(abs(colors[i].L - colors[n - 1 - i].L), colors[i].hex, colors[n - 1 - i].hex) for i in range(n // 2)]
    d, a, b = max(rows)
    status = "PASS" if d <= ARM_ASYM else "WARN"
    return _r("V14", status, f"max arm dL {d:.3f} {a}~{b}; max {ARM_ASYM}", [a, b] if status == "WARN" else ())


def check_div_cvd(colors, cfloor):
    a, b = colors[0], colors[-1]
    d = {v: de(a, b, v) for v in ("protan", "deutan", "tritan")}
    detail = f"ends {a.hex}~{b.hex} " + ", ".join(f"{v} {x:.1f}" for v, x in d.items()) + f"; floor {cfloor:.1f}"
    if min(d["protan"], d["deutan"]) < cfloor:
        return _r("V15", "FAIL", detail, [a.hex, b.hex])
    if d["tritan"] < cfloor:
        return _r("V15", "WARN", detail + " (tritan)", [a.hex, b.hex])
    return _r("V15", "PASS", detail)


def validate(colors, role="categorical", background="#FFFFFF", mark="bar", pairs=None,
             context=(), text=(), large_text=False):
    """Run checks for one background. Returns a run dict."""
    cols = [Color(c) for c in colors]
    ctx = [Color(c) for c in context]
    txt = [Color(c) for c in text]
    bg = Color(background)
    if role not in ("categorical", "sequential", "diverging", "highlight"):
        raise ValueError(f"unknown role {role!r}")
    if mark not in DE_FLOOR:
        raise ValueError(f"unknown mark {mark!r}")
    if not cols:
        raise ValueError("no colors")
    if role in ("sequential", "diverging") and len(cols) < 3:
        raise ValueError(f"{role} needs at least 3 colors")
    pairs = pairs or ("all" if mark in ("line", "point", "text") else "adjacent")
    floor = DE_FLOOR[mark]
    res = []
    text_cols = txt + (cols if mark == "text" else [])
    if text_cols:
        res.append(check_text(text_cols, bg, large_text))
    if role in ("categorical", "highlight"):
        if mark != "text":
            res.append(check_marks(cols, bg, mark, "accents" if role == "highlight" else "marks"))
    elif role == "sequential":
        ends = [cols[0], cols[-1]]
        best = max(ends, key=lambda c: contrast(c.hex, bg.hex))
        res.append(check_marks([best], bg, "area", "strongest end"))
    if ctx:
        res.append(check_context(ctx, bg, role, bool(cols)))
    if role == "categorical":
        pl = _pairs(cols, ctx, pairs)
        res += check_distinct(pl, floor, f"{pairs} pairs, {mark}")
        v8 = check_lightness(pl, role, ctx, cols)
        if v8:
            res.append(v8)
        n = len(cols)
        st = "FAIL" if n > CAT_MAX else ("WARN" if n > CAT_WARN else "PASS")
        res.append(_r("V9", st, f"{n} hues; default cap {CAT_WARN}, hard cap {CAT_MAX}"))
    elif role == "highlight":
        pl = _pairs(cols, ctx, "all")
        res += check_distinct(pl, floor, f"accents+context, {mark}")
        v8 = check_lightness(pl, role, ctx, cols)
        if v8:
            res.append(v8)
        n = len(cols)
        res.append(_r("V9", "FAIL" if n > MAX_ACCENTS else "PASS", f"{n} accent(s); max {MAX_ACCENTS}"))
    else:
        res.append(check_monotone(cols, role))
        if role == "sequential":
            res.append(check_uniform(cols))
        if mark != "area":
            res.append(check_visible_end(cols, bg, role))
        if role == "diverging":
            res.append(check_midpoint(cols, bg))
            res.append(check_symmetry(cols))
            res.append(check_red_green([(cols[0], cols[-1])], floor * CVD_FACTOR))
            res.append(check_div_cvd(cols, floor * CVD_FACTOR))
    res.sort(key=lambda r: int(r["id"][1:]))
    return {"role": role, "mark": mark, "pairs": pairs, "background": bg.hex,
            "colors": [c.hex for c in cols], "context": [c.hex for c in ctx], "text": [c.hex for c in txt],
            "checks": res}


# ---------------------------------------------------------------------------
# Presets from assets/palettes.json
# ---------------------------------------------------------------------------
def load_palettes(path=PALETTES_JSON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def presets(p, n_cat=None):
    t = p["tokens"]
    cat = [s["hex"] for s in p["categorical"]["slots"]]
    seq, div = p["sequential"], p["diverging"]
    n = n_cat or p["categorical"]["default_cap"]
    return {
        "categorical": dict(colors=cat[:n], role="categorical", mark="line"),
        "categorical_all": dict(colors=cat, role="categorical", mark="bar"),
        "highlight": dict(colors=[t["accent"], t["accent_alt"]], role="highlight", mark="line",
                          context=[t["context_gray"]],
                          text=[t["accent_text"], t["accent_alt"]] + list(t["text"].values())),
        "viridis": dict(colors=seq["viridis"]["hex"], role="sequential", mark="area"),
        "viridis_marks": dict(colors=seq["viridis"]["hex_marks"], role="sequential", mark="point"),
        "cividis": dict(colors=seq["cividis"]["hex"], role="sequential", mark="area"),
        "blues": dict(colors=seq["blues"]["hex"], role="sequential", mark="area"),
        "rdbu": dict(colors=div["rdbu"]["hex"], role="diverging", mark="area"),
        "puor": dict(colors=div["puor"]["hex"], role="diverging", mark="area"),
    }


PRESET_ALIASES = {"sequential": "viridis", "diverging": "rdbu"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _split(values):
    out = []
    for v in values or ():
        out += [x for x in v.replace(",", " ").split() if x]
    return out


def summarize(runs):
    fails = sum(c["status"] == "FAIL" for r in runs for c in r["checks"])
    warns = sum(c["status"] == "WARN" for r in runs for c in r["checks"])
    return {"result": "fail" if fails else ("warn" if warns else "pass"), "fails": fails, "warns": warns,
            "runs": runs}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate chart palette contrast, distinctness, CVD safety.")
    ap.add_argument("colors", nargs="*", help="hex colors, comma or space separated, in order")
    ap.add_argument("--role", choices=["categorical", "sequential", "diverging", "highlight"], default=None)
    ap.add_argument("--mark", choices=sorted(DE_FLOOR), default=None, help="default bar (presets set their own)")
    ap.add_argument("--pairs", choices=["adjacent", "all"], default=None,
                    help="default: all for line/point/text, adjacent for bar/area")
    ap.add_argument("--background", default="#FFFFFF", help="hex; comma list reruns per background (V16)")
    ap.add_argument("--dark", action="store_true", help=f"also rerun on {DARK_DEFAULT}")
    ap.add_argument("--context", action="append", help="context grays (highlight role)")
    ap.add_argument("--text", action="append", help="colors used for text (V2)")
    ap.add_argument("--large-text", action="store_true", help="V2 floor 3:1 (18pt, or 14pt bold, and up)")
    ap.add_argument("--preset", help="house palette from palettes.json; 'all' runs every preset")
    ap.add_argument("--n", type=int, default=None, help="categorical preset: first N Okabe-Ito slots")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-checks", action="store_true")
    ap.add_argument("--list-presets", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="CIEDE2000 vs Sharma et al. 2005 pairs")
    a = ap.parse_args(argv)

    def err(msg):
        print(json.dumps({"result": "error", "error": msg}) if a.json else f"ERROR {msg}")
        return 2

    if a.list_checks:
        for k, (tag, desc) in CHECKS.items():
            print(f"{k} [{tag}] {desc}")
        return 0
    if a.self_test:
        ok, e = self_test()
        print(f"SELFTEST {'PASS' if ok else 'FAIL'} ciede2000 {len(SHARMA_PAIRS)} Sharma pairs x2 orders, max err {e:.1e}")
        return 0 if ok else 1
    try:
        bgs = [parse_hex(b) for b in _split([a.background])]
        if a.dark and parse_hex(DARK_DEFAULT) not in bgs:
            bgs.append(parse_hex(DARK_DEFAULT))
        jobs = []
        if a.preset or a.list_presets:
            try:
                table = presets(load_palettes(), a.n)
            except (OSError, KeyError, ValueError) as e:
                return err(f"cannot load presets from {PALETTES_JSON}: {e}")
            if a.list_presets:
                for k, v in table.items():
                    print(f"{k} role={v['role']} mark={v['mark']} {','.join(v['colors'])}")
                return 0
            name = PRESET_ALIASES.get(a.preset, a.preset)
            names = list(table) if name == "all" else [name]
            for nm in names:
                if nm not in table:
                    return err(f"unknown preset {a.preset!r}; one of: all, {', '.join(table)}")
                spec = dict(table[nm])
                if a.mark:
                    spec["mark"] = a.mark
                jobs.append((nm, spec))
        else:
            cols = _split(a.colors)
            if not cols:
                return err("no colors given (or use --preset)")
            jobs.append(("cli", dict(colors=cols, role=a.role or "categorical", mark=a.mark or "bar",
                                     context=_split(a.context), text=_split(a.text))))
        runs = []
        for nm, spec in jobs:
            for bg in bgs:
                run = validate(spec["colors"], spec["role"], bg, spec["mark"], a.pairs,
                               spec.get("context", ()), spec.get("text", ()), a.large_text)
                run["name"] = nm
                runs.append(run)
    except ValueError as e:
        return err(str(e))

    out = summarize(runs)
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        for r in runs:
            extra = f" context={','.join(r['context'])}" if r["context"] else ""
            print(f"RUN {r['name']} role={r['role']} mark={r['mark']} pairs={r['pairs']} bg={r['background']} "
                  f"colors={','.join(r['colors'])}{extra}")
            for c in r["checks"]:
                print(f"{c['id']} {c['status']} [{c['tag']}] {c['detail']}")
        print(f"RESULT {out['result'].upper()}: {out['fails']} fail, {out['warns']} warn, {len(runs)} run(s)")
    return 1 if out["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
