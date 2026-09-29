#!/usr/bin/env python3
"""Deterministic sanity checks on a data table before charting it.

Run it on each input file while analyzing, and again with --plotted on the table the chart plots.
Roles are inferred unless given: date (by name, or year + M01/Q1/month columns joined), values (numeric
after stripping commas, %, currency, K/M/B, flag letters), keys (text columns with repeats; code + label
pairs count once), flags (flag, status, footnote columns). Title lines above the header and footnote lines
below the data are skipped; wide tables with period headers (2019, 2019 [YR2019], 2019-Q1) are melted.

Usage:
  python check_data.py data.csv|tsv [--date COL] [--value COL]... [--key COL]... [--total LABEL]...
                       [--n COL] [--min-n 30] [--asof YYYY-MM-DD] [--plotted] [--json]
  python check_data.py --list-checks

Output: an INFO roles line (roles, frequency, date coverage), one line per finding,
`SEVERITY check | where | detail | fix: ...`, then a RESULT line. Findings that are normal in raw
multi-series files (aggregate rows, mixed units) warn, and fail only with --plotted.

Exit codes: 0 no fails (warns allowed), 1 at least one fail, 2 pandas missing or older than 2.0, unreadable file, or a
layout that is not one header row over data rows (reshape it, or pass --date/--value/--key).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError:
    _msg = "check_data.py needs pandas: pip install pandas (or run it with uv run --with pandas python ...)"
    print(json.dumps({"result": "error", "error": _msg}) if "--json" in sys.argv else f"ERROR: {_msg}",
          file=sys.stdout if "--json" in sys.argv else sys.stderr)
    sys.exit(2)

CHECKS = {  # name: (severity on raw inputs, severity with --plotted, description)
    "aggregate-rows": ("warn", "fail", "A member equals the sum of the others along a key (or 2x/3x: nested "
                                       "levels), or parts exceed the --total row; warn only: a value column equal "
                                       "to the sum of the others unless named like a total, a total-like label "
                                       "(Total, All, World, EU27) among members; info: remainder below --total."),
    "duplicate-keys": ("fail", "fail", "Rows share keys and period but differ in value (identical rows warn)."),
    "trailing-empty": ("fail", "fail", "A series ends in 2+ zeros after nonzero values, or zeros dated after "
                                       "--asof (one zero warns); warn: series blank in the latest period others "
                                       "have, periods dated after --asof."),
    "status-flags": ("warn", "warn", "Flag or status cells, value suffixes ('12.3 p'), p/r period labels, or keys "
                                     "naming vintages mark provisional, estimated, forecast, revised, or break "
                                     "values."),
    "sentinel-values": ("warn", "warn", "Values standing for missing: 99/888/-9-style codes far outside the rest, "
                                        "non-numeric cells (':', '..', '(D)'), or 0 and blank in one column."),
    "mixed-units": ("warn", "fail", "A unit, adjustment, or price-base key holds 2+ values; an indicator or "
                                    "measure key always warns."),
    "gaps": ("warn", "warn", "A monthly, quarterly, or annual series skips periods between its first and last "
                             "value."),
    "frozen-values": ("warn", "warn", "A series repeats one nonzero value 3+ periods in a row, unlikely given how "
                                      "rarely it repeats otherwise."),
    "partial-last-period": ("info", "info", "The last calendar year is incomplete (sub-annual data) or not over "
                                            "(annual data)."),
    "small-n": ("info", "info", "Rows whose sample size (--n, or an n/sample/respondents column) is below --min-n."),
    "record-level": ("info", "info", "Several rows share each key: records, not one row per series and period; "
                                     "series checks skipped."),
}

REL_TOL = 0.005          # aggregate-rows: a member within 0.5% of the sum of the others (or of 1/2, 1/3 of it)...
AGG_MIN_SHARE = 0.6      # ...in at least this share of the groups (periods) it appears in
ZERO_SHARE_MAX = 0.05    # trailing-empty: zeros elsewhere in the series must be rarer than this
FROZEN_RUN = 3           # frozen-values: identical consecutive readings
FROZEN_P = 0.05          # ...and a run this unlikely: n * p^(run-1), p = the series' chance of a repeat outside the run
SENTINEL_IQR = 3         # sentinel-values: code-like numbers this many IQRs outside the other values
MIN_N_DEFAULT = 30       # small-n (NCHS uses 20 events for rates)

TOTAL_RE = re.compile(r"^\s*(total\b|.*\btotal\s*$|.*\btotal,|all\b|world\b|overall\b|both sexes|grand total|"
                      r"subtotal|euro area|european union|eu\s?\d*\b|eu\d+_\d+|ea\d*\b|oecd\b|"
                      r".*\bincome\b.*countries|.*\(aggregate\)|.+\bregion$)", re.I)
PERIOD_TOTAL_RE = re.compile(r"M13$|Q5$|annual|average|avg|total|ytd|\ball\b", re.I)
MISSING_TOKENS = {":", "..", "...", "-", "--", "—", "–", "(d)", "(na)", "(x)", "(s)", "(z)", "(nr)", "na",
                  "n/a", "nan", "x", "*", "**", "s", "n", "c", "d", "w", "suppressed", "unreliable", "not available"}
SENTINEL_RE = re.compile(r"^-?(9{2,}|8{3,}|7{3,}|6{6,}|2{9})(\.0+)?$")
NEG_CODES = {-1, -7, -8, -9, -77, -88, -99, -777, -888, -999, -9999}
STATUS_RE = re.compile(r"\b(?:prelim\w*|provisional|advance|estimat\w*|forecast|project\w*|revised|break|"
                       r"unreliable|suppress\w*|incomplete|partial)\b", re.I)
VINTAGE_RE = re.compile(r"\b(?:prelim\w*|provisional|advance|forecast|projected|projection|revised|flash|nowcast)\b",
                        re.I)
FLAG_CODES = {"b": "break", "c": "confidential", "d": "definition differs", "e": "estimated", "f": "forecast",
              "n": "not significant", "p": "provisional", "r": "revised", "s": "estimate", "u": "low reliability",
              "z": "not applicable"}
DATE_NAME_RE = re.compile(r"^(date|time|year|yr|month|period|quarter|week|day|ref_date|time_period|timestamp|"
                          r"fiscal_year|fy)$|date$|_date|^date_|_(month|year|period)$", re.I)
NOT_DATE_RE = re.compile(r"update|release|created|modified|birth|founded|vintage", re.I)
FLAG_NAME_RE = re.compile(r"flag|status|footnote|^notes?$|_notes?$|qualifier|^estimate_type$", re.I)
ID_NAME_RE = re.compile(r"(^|[_ ])(id|code|fips|geoid|dguid|vector|coordinate|index|rank|zip|zipcode|sumlev|decimals|"
                        r"uom_id|scalar_id|lat|lon|latitude|longitude|age)$|^(state|region|division|district)$", re.I)
UNIT_RE = re.compile(r"^(units?|uom|unit[ _]of[ _]measure|unit_measure|unit_mult|scalar(_factor)?|multiplier|"
                     r"adjustment|seasonal( adjustment)?|seasonally adjusted|s_?adj|price_?base|prices|currency|"
                     r"base( year| period)?|valuation)$", re.I)
INDICATOR_RE = re.compile(r"^(measure|metric|indicator|indicator[ _]name|series[ _]name|series[ _]title|na_item|"
                          r"concept)$", re.I)
N_NAME_RE = re.compile(r"^(n|obs|sample|sample[ _]size|unweighted.*|respondents|num_respondents|.+_n|n_.+)$", re.I)
WIDE_RE = re.compile(r"^((1[89]|20)\d{2}(\.0)?( \[YR\d{4}\])?[pPrR]?|(1[89]|20)\d{2}[-_ ]?(Q[1-4]|M\d{2})|"
                     r"(1[89]|20)\d{2}-(0[1-9]|1[0-2])|Q[1-4][ -](1[89]|20)\d{2})$")
FOOTER_RE = re.compile(r"^\s*(sources?\b|notes?\b|footnotes?\b|\*|\d{1,2}\s*[.)]\s|\([a-z0-9]\)\s|©|copyright|"
                       r"last updated|data extracted|symbol legend)", re.I)
NUM_RE = (r"^(?P<neg>\()?±?(?P<sign>-)?\+?[$£€¥]?\s*(?P<num>[-+]?(?:\d[\d,]*\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
          r"(?P<mult>[KMB](?![A-Za-z]))?\s*%?\s*\)?\s*(?P<flag>\(?[bcdefnprsuzBCDEFNPRSUZ]{1,2}\)?|\*{1,3})?$")
NUM_LIKE_RE = re.compile(r"^[(\-+$£€]*[\d.,]+\s*[%)A-Za-z*]{0,3}$")
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"], 1)}
FREQ_NAME = {"H": "sub-daily", "D": "daily", "W": "weekly", "M": "monthly", "Q": "quarterly", "A": "annual"}
PERIOD_FREQ = {"M": "M", "Q": "Q", "A": "Y"}


class Untidy(ValueError):
    """The file is not one header row over data rows, or a named column is unusable."""


@dataclass
class Finding:
    check: str
    severity: str
    where: str
    detail: str
    fix: str


def fmt_t(ts, freq):
    if freq == "A":
        return f"{ts.year}"
    if freq == "Q":
        return f"{ts.year}Q{ts.quarter}"
    return f"{ts:%Y-%m}" if freq == "M" else f"{ts:%Y-%m-%d}"


def ex(items, n=3):
    """Short example list: 'a', 'b', 'c' (+2 more)."""
    items = list(items)
    s = ", ".join(f"'{x}'" for x in items[:n])
    return s + (f" (+{len(items) - n} more)" if len(items) > n else "")


# ---------------------------------------------------------------------------- reading

def sniff_delimiter(text, suffix):
    if suffix == ".tsv":
        return "\t"
    lines = [ln for ln in text.splitlines()[:60] if ln.strip()]
    best, choice = (0.0, 1), ","
    for d in (",", "\t", ";", "|"):
        counts = [len(r) for r in csv.reader(lines, delimiter=d)]
        modal = max(set(counts), key=counts.count) if counts else 1
        score = (counts.count(modal) / len(counts), modal) if modal > 1 else (0.0, 1)
        if score > best:
            best, choice = score, d
    return choice


def read_table(path):
    """Return (DataFrame of stripped strings, notes). Raises Untidy."""
    path = Path(path)
    raw = path.read_bytes()
    if raw[:4] == b"PK\x03\x04" or b"\x00" in raw[:4096]:
        raise Untidy("binary file (a spreadsheet?): export the sheet to CSV first")
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text), delimiter=sniff_delimiter(text, path.suffix.lower())))
    nb = [sum(bool(x.strip()) for x in r) for r in rows]
    if not rows or max(nb) < 2:
        raise Untidy("fewer than two columns: not a delimited table")
    top = max(nb[:50])
    head = next(i for i, n in enumerate(nb) if n >= max(2, top / 2))
    end = len(rows)
    while end > head + 1 and (nb[end - 1] == 0 or (nb[end - 1] < top / 2 and rows[end - 1][0].strip() and (
            FOOTER_RE.match(rows[end - 1][0]) or len(rows[end - 1][0].strip()) > 40))):
        end -= 1
    notes = [f"skipped {head} title line(s)"] if head else []
    above = rows[head - 1] if head else []
    if sum(bool(x.strip()) for x in above[1:]) >= 2:
        raise Untidy(f"lines {head} and {head + 1} both look like headers: merged or multi-row header; "
                     "flatten it to one header row")
    if any(nb[end:]):
        notes.append(f"skipped {sum(map(bool, nb[end:]))} footnote line(s)")
    header = [x.strip() for x in rows[head]]
    width = len(header)
    body = [r for r in rows[head + 1:end] if any(x.strip() for x in r)]
    for i, r in enumerate(body):
        if len(r) > width:
            if any(x.strip() for x in r[width:]):
                raise Untidy(f"data line {head + i + 2} has more fields than the header: ragged rows")
            body[i] = r[:width]
        elif len(r) < width:
            body[i] = r + [""] * (width - len(r))
    # section rows ("Northeast:" or a label over indented members) mean a hierarchy laid out for print
    for i, r in enumerate(body):
        lone = r[0].strip() and not any(x.strip() for x in r[1:])
        nxt = body[i + 1][0] if i + 1 < len(body) else ""
        if lone and (r[0].strip().endswith(":") or re.match(r"^(\s{2,}|\t)\S", nxt)):
            raise Untidy(f"section header rows ('{r[0].strip()}'): one column holds a hierarchy; reshape to one "
                         "row per member with the section as its own column")
    keep = [j for j in range(width) if header[j] or any(r[j].strip() for r in body)]
    blank = [j for j in keep if not header[j] and j > 0]
    if len(blank) > max(1, len(keep) / 3):
        raise Untidy(f"{len(blank)} of {len(keep)} header cells are blank: merged or multi-row header; flatten "
                     "it to one header row")
    names = []
    for j in keep:
        name = header[j] or ("label" if j == 0 else f"col{j}")
        names.append(name if name not in names else f"{name}.{j}")
    df = pd.DataFrame([[r[j].strip() for j in keep] for r in body], columns=names, dtype=str)
    if not len(df):
        raise Untidy("no data rows under the header")
    hdr = df.eq(pd.Series(names, index=names)).mean(axis=1)
    if (hdr >= 0.8).any():
        raise Untidy(f"the header repeats at data line {int(np.argmax(hdr.values >= 0.8)) + head + 2}: stacked "
                     "tables; split them")
    if len(df) >= 5:
        first = df.iloc[0]
        rest = df.iloc[1:]
        numeric = [c for c in names if (rest[c] != "").sum() >= 4 and
                   rest[c][rest[c] != ""].str.match(NUM_LIKE_RE).mean() >= 0.9]
        texty = [c for c in numeric if first[c] and not NUM_LIKE_RE.match(first[c])
                 and first[c].lower() not in MISSING_TOKENS and first[c][0] not in "<>"]
        if len(texty) >= 2 and len(texty) >= len(numeric) / 2:
            raise Untidy(f"the first data row is a second header ({ex(first[texty].tolist())}); fold it into "
                         "the header")
    return df, notes


# ---------------------------------------------------------------------------- roles

def to_num(s):
    """Parse numbers: returns (values, flag suffixes, non-numeric tokens)."""
    m = s.str.extract(NUM_RE)
    v = pd.to_numeric(m["num"].str.replace(",", "", regex=False), errors="coerce")
    v = v * m["mult"].map({"K": 1e3, "M": 1e6, "B": 1e9}).fillna(1.0)
    v = v.where(m["neg"].isna() & m["sign"].isna(), -v)
    tokens = s[v.isna() & (s != "")]
    return v, m["flag"].str.strip("()").where(v.notna()), tokens


def parse_period(s):
    """Return (timestamps, freq) where freq is A/Q/M/W/D/H, or (all-NaT, None)."""
    t = (s.str.replace(r"\s*\[YR\d{4}\]$", "", regex=True).str.replace(r"(?<=\d)\s*\(?[pPrReE]\)?$", "", regex=True)
         .str.replace(r"(?i)^FY\s?", "", regex=True).str.replace(r"^(\d{4})\.0$", r"\1", regex=True))
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    nb = t != ""
    if not nb.any():
        return out, None

    def quarter(x):
        x = x.str.replace(r"^Q([1-4])[ -]?(\d{4})$", r"\2Q\1", regex=True).str.replace(r"[- ]", "", regex=True)
        return pd.PeriodIndex(x.tolist(), freq="Q").to_timestamp()

    pats = [(r"(1[89]|20)\d{2}", "A", lambda x: pd.to_datetime(x, format="%Y")),
            (r"(1[89]|20)\d{2}[- ]?Q[1-4]|Q[1-4][ -]?(1[89]|20)\d{2}", "Q", quarter),
            (r"(1[89]|20)\d{2}-(0[1-9]|1[0-2])", "M", lambda x: pd.to_datetime(x, format="%Y-%m")),
            (r"(1[89]|20)\d{2}M(0[1-9]|1[0-2])", "M", lambda x: pd.to_datetime(x, format="%YM%m")),
            (r"[A-Za-z]{3}-\d{2}", "M", lambda x: pd.to_datetime(x, format="%b-%y")),
            (r"(1[89]|20)\d{2}(0[1-9]|1[0-2])", "M", lambda x: pd.to_datetime(x, format="%Y%m"))]
    for pat, freq, conv in pats:
        m = t.str.fullmatch(pat) & nb
        if m.sum() / nb.sum() > 0.9:
            out[m] = np.asarray(conv(t[m]), dtype="datetime64[ns]")
            return out, freq
    if t[nb].str.fullmatch(r"\d{4}-\d{2}").mean() > 0.9 or t[nb].str.fullmatch(r"\d{1,3}|\d{5,}").mean() > 0.5:
        return out, None  # seasons like 2024-25, or plain numbers
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = pd.to_datetime(t.where(nb), errors="coerce", format="mixed", utc=True).dt.tz_localize(None)
    if d[nb].notna().mean() <= 0.9:
        return out, None
    u = pd.Series(d.dropna().unique()).sort_values()
    step = u.diff().dt.total_seconds().median() / 86400 if len(u) > 2 else None
    freq = None if step is None or step > 370 else "H" if step < 0.9 else "D" if step <= 1.5 else "W" \
        if step <= 8 else "M" if step <= 32 else "Q" if step <= 93 else "A"
    return d.astype("datetime64[ns]"), freq


def join_year_period(df):
    """BLS/Census style year + period (M01, Q1) or year + month (1-12, Jan) columns -> one 'year+period' column."""
    cols = {c.lower(): c for c in df.columns}
    y, p = cols.get("year"), next((cols[k] for k in ("period", "month", "quarter") if k in cols), None)
    if not y or not p or not df[y].str.fullmatch(r"(1[89]|20)\d{2}").all():
        return df, None
    per = df[p]
    num = pd.to_numeric(per, errors="coerce")
    mon = per.str[:3].str.lower().map(MONTHS)
    if per.str.fullmatch(r"M\d{2}").mean() > 0.9:
        lab = df[y] + per
    elif per.str.fullmatch(r"Q0?\d").mean() > 0.9:
        lab = df[y] + "Q" + per.str[-1]
    elif p.lower() != "quarter" and num.between(1, 12).mean() > 0.9:
        lab = df[y] + "M" + num.fillna(13).astype(int).astype(str).str.zfill(2)
    elif mon.notna().mean() > 0.9:
        lab = df[y] + "M" + mon.fillna(13).astype(int).astype(str).str.zfill(2)
    else:
        return df, None
    name = f"{y}+{p}"
    return df.drop(columns=[y, p]).assign(**{name: lab}), name


@dataclass
class Table:
    df: object
    date: str | None
    freq: str | None
    values: list
    parsed: dict
    keys: list
    flags: list
    ncol: str | None
    unparsed: object
    notes: list


def infer_roles(df, args):
    notes = []
    for opt in ("date", "n"):
        if getattr(args, opt) and getattr(args, opt) not in df.columns:
            raise Untidy(f"--{opt} column not found: {getattr(args, opt)}")
    for c in (args.value or []) + (args.key or []):
        if c not in df.columns:
            raise Untidy(f"column not found: {c}")
    date = args.date
    wide = [c for c in df.columns if WIDE_RE.match(c)]
    if not date and len(wide) >= 3:
        ids = [c for c in df.columns if c not in wide]
        pcol, vcol = ("period", "value") if not {"period", "value"} & set(ids) else ("_period", "_value")
        df = df.melt(id_vars=ids, value_vars=wide, var_name=pcol, value_name=vcol)
        date = pcol
        notes.append(f"melted {len(wide)} period columns")
    if not date:
        df, date = join_year_period(df)
    per, freq = pd.Series(pd.NaT, index=df.index), None
    if date:
        per, freq = parse_period(df[date])
        if args.date and per.notna().sum() <= 0.5 * (df[date] != "").sum():
            raise Untidy(f"--date {date}: periods do not parse (e.g. {ex(df[date].unique(), 2)})")
    else:
        cands = [c for c in df.columns if DATE_NAME_RE.search(c) and not NOT_DATE_RE.search(c)]
        cands.sort(key=lambda c: not re.fullmatch(r"time_period|ref_date|period|date|month|quarter|year", c, re.I))
        for c in cands or df.columns[:1]:
            p, f = parse_period(df[c])
            if p.notna().sum() > 0.9 * (df[c] != "").sum() > 0:
                date, per, freq = c, p, f
                break
    df = df.assign(_t=per)
    unparsed = df.loc[per.isna() & (df[date] != ""), date] if date else pd.Series(dtype=str)
    used = {date, "_t"} | set(args.key or [])
    parsed = {}
    for c in df.columns:
        if c in used:
            continue
        v, fl, tok = to_num(df[c])
        known = tok.str.lower().isin(MISSING_TOKENS).sum()
        real = (df[c] != "").sum() - known
        if c in (args.value or []) or (v.notna().sum() and v.notna().sum() >= 0.8 * real
                                       and not ID_NAME_RE.search(c) and not df[c].str.match(r"^0\d").any()):
            parsed[c] = (v, fl, tok)
    values = args.value or list(parsed)
    if not values:
        raise Untidy("no numeric value column found; pass --value COL")
    rest = [c for c in df.columns if c not in used and c not in values]
    flags = [c for c in rest if FLAG_NAME_RE.search(c) and ((df[c] == "").mean() >= 0.5 or df[c].str.len().median()
                                                            <= 3 or df[c].str.contains(STATUS_RE).any())]
    keys = args.key
    if keys is None:
        keys = [c for c in rest if c not in flags and 1 < df.loc[df[c] != "", c].nunique() <= max(200, len(df) // 2)]
        kept = []
        for c in keys:  # code + label pairs: keep the first
            if not any(df.groupby(k)[c].nunique().max() == 1 and df.groupby(c)[k].nunique().max() == 1 for k in kept):
                kept.append(c)
        keys = kept
        if not keys and not date:  # a bar table: its unique row labels are the members
            keys = [c for c in rest if c not in flags and df[c].ne("").all() and df[c].is_unique][:1]
    ncol = args.n or next((c for c in values if N_NAME_RE.match(c)), None)
    return Table(df, date, freq, values, parsed, keys, flags, ncol, unparsed, notes)


# ---------------------------------------------------------------------------- checks

class Ctx:
    def __init__(self, tab: Table, args):
        self.t, self.args, self.findings = tab, args, []
        self.df, self.keys, self.values, self.parsed = tab.df, tab.keys, tab.values, tab.parsed
        self.members = [v for v in tab.values if v != tab.ncol]
        self.asof = pd.Timestamp(args.asof) if args.asof else pd.Timestamp.today().normalize()
        self.record_level = False
        self._series = {}

    def add(self, check, where, detail, fix, severity=None):
        sev = severity or CHECKS[check][1 if self.args.plotted else 0]
        self.findings.append(Finding(check, sev, where, detail, fix))

    def series(self, col):
        """[(label, float Series indexed by period)] per key combination; skips groups with repeated periods."""
        if col not in self._series:
            out = []
            if self.t.date and not self.record_level:
                d = self.df[self.keys + ["_t"]].assign(_v=self.parsed[col][0]).dropna(subset=["_t"])
                for name, g in (d.groupby(self.keys, sort=False) if self.keys else [((), d)]):
                    g = g.sort_values("_t")
                    if not g["_t"].duplicated().any():
                        name = name if isinstance(name, tuple) else (name,)
                        out.append((" / ".join(map(str, name)) or col, g.set_index("_t")["_v"]))
            self._series[col] = out
        return self._series[col]


def check_mixed_units(c: Ctx):
    for k in c.keys:
        vals = [x for x in c.df[k].unique() if x]
        if len(vals) > 1 and (UNIT_RE.match(k) or INDICATOR_RE.match(k)):
            c.add("mixed-units", k, f"{len(vals)} values in one table: {ex(vals)}",
                  f"Filter {k} to one value before summing or plotting series on one axis; different units go in "
                  "separate panels (H12).", None if UNIT_RE.match(k) else "warn")


def check_duplicates(c: Ctx):
    cols = c.keys + (["_t"] if c.t.date else [])
    if not cols:
        return
    d = c.df[cols].assign(**{f"_v{i}": c.parsed[v][0] for i, v in enumerate(c.values)})
    if c.t.date:
        d = d.dropna(subset=["_t"])
    if c.keys:
        d = d[(d[c.keys] != "").any(axis=1)]
    dup = d[d.duplicated(cols, keep=False)]
    if not len(dup):
        return
    where = ", ".join(c.t.date if x == "_t" else x for x in cols)
    if dup.groupby(cols).size().max() >= 3 or len(dup) > 0.5 * len(d):
        c.record_level = True
        c.add("record-level", where,
              f"{len(dup)} of {len(d)} rows share a key: records or a missing key column",
              "Aggregate to one row per series and period first, or pass --key/--date to name the series.")
        return
    vcols = [x for x in d.columns if x.startswith("_v")]
    conflict = int((dup.groupby(cols)[vcols].nunique() > 1).any(axis=1).sum()) if vcols else 0
    first = [fmt_t(x, c.t.freq) if isinstance(x, pd.Timestamp) else x for x in dup.iloc[0][cols]]
    c.add("duplicate-keys", where,
          f"{len(dup)} rows share a key, {conflict} key(s) with different values; e.g. {first}",
          "Find the column that tells them apart (method, estimate, revision, vintage) and keep one; drop exact "
          "duplicates (H11, H16).", None if conflict else "warn")


def agg_scan(d, k, by):
    """d holds k, by..., _v. Return {label: multiple} for members equal to the sum of the others (x1),
    or to half/a third of it (nested levels; then also the largest member), in AGG_MIN_SHARE of the groups they appear in."""
    d = d.dropna(subset=["_v"])
    if d.duplicated([k] + by).any():
        return {}
    grp = d.groupby(by, sort=False)["_v"] if by else None
    x = d["_v"]
    tot = grp.transform("sum") if by else pd.Series(x.sum(), index=d.index)
    size = grp.transform("size") if by else pd.Series(len(d), index=d.index)
    nz = (x != 0).astype(int)
    nz_others = (d.assign(_nz=nz).groupby(by, sort=False)["_nz"].transform("sum") if by else nz.sum()) - nz
    ok = (size >= 3) & (nz_others >= 2) & (x != 0)
    biggest = (grp.transform("max") if by else pd.Series(x.max(), index=d.index)) <= x  # a total is not below its parts
    ngroups = d.loc[size >= 3, by].drop_duplicates().shape[0] if by else int(len(d) >= 3)
    found = {}
    for m in (1, 2, 3):
        if m > 1 and ngroups < 3:
            break
        hit = ok & (((tot - x) / m - x).abs() <= REL_TOL * x.abs()) & (biggest if m > 1 else True)
        share = hit.groupby(d[k]).sum() / ok.groupby(d[k]).sum().clip(lower=1)
        for lab in share[(share >= AGG_MIN_SHARE) & (hit.groupby(d[k]).sum() > 0)].index:
            found.setdefault(lab, m)
    return found


def check_aggregates(c: Ctx):
    if c.record_level or not c.members:
        return
    declared = set(c.args.total or [])
    by_t = ["_t"] if c.t.date else []
    fix = ("Drop it from sums, shares, rankings, and stacks, or keep it as the denominator; with nested levels keep "
           "one level (H11).")
    col = c.members[0] if c.members else None
    scans = [(k, [x for x in c.keys if x != k] + by_t, c.df[[k] + [x for x in c.keys if x != k] + by_t]
              .assign(_v=c.parsed[col][0]), f"{col} by {k}") for k in c.keys] if col else []
    if len(c.members) >= 3 or declared & set(c.members):  # value columns as members (date, Total, North, South)
        long = c.df[c.keys + by_t].assign(_row=range(len(c.df)))
        long = pd.concat([long.assign(_col=m, _v=c.parsed[m][0]) for m in c.members])
        scans.append(("_col", ["_row"], long, "value columns"))
    for k, by, d, where in scans:
        found = {lab: m for lab, m in agg_scan(d, k, by).items() if lab not in declared}
        if found:
            lab, m = next(iter(found.items()))
            nest = "" if m == 1 else f"; the rows sum to {m + 1}x it, so {m + 1} nested levels are mixed"
            more = f" (also {ex(list(found)[1:])})" if len(found) > 1 else ""
            # value columns are often measures (revenue = cost + profit): fail only a total-like column name
            sev = "warn" if k == "_col" and not TOTAL_RE.match(str(lab)) else None
            c.add("aggregate-rows", where, f"'{lab}' equals the sum of the others{nest}{more}", fix, sev)
            continue
        labs = [x for x in d[k].unique() if TOTAL_RE.match(str(x)) and x not in declared]
        if labs and len(labs) < d[k].nunique() - 1:
            c.add("aggregate-rows", where, f"total-like label(s) among members: {ex(labs)}",
                  "Drop it from rankings, sums, and stacks, or use it as the published total; remainder = total "
                  "minus listed members (H11).", "warn")
    unp = c.t.unparsed[c.t.unparsed.str.contains(PERIOD_TOTAL_RE)]
    if len(unp):
        c.add("aggregate-rows", c.t.date, f"{len(unp)} rows with period {ex(unp.unique())} sit among "
              f"{FREQ_NAME.get(c.t.freq, 'dated')} periods: annual averages or totals",
              "Drop them from the series; use them only as the published annual figure (H11).", "warn")
    for lab in declared:  # parts against the published total
        k = next((k for k in c.keys if lab in set(c.df[k])), None)
        if k:
            by = [x for x in c.keys if x != k] + by_t
            d, where = c.df[[k] + by].assign(_v=c.parsed[col][0]), f"{col} by {k}"
        elif lab in c.members:
            k, by, d, where = next(s for s in scans if s[0] == "_col")
        else:
            raise Untidy(f"--total {lab}: not found in any key column or value column")
        d = d.dropna(subset=["_v"])
        is_tot = d[k] == lab
        d = d.assign(_tot=d["_v"].where(is_tot, 0), _parts=d["_v"].where(~is_tot, 0))
        sums = d.groupby(by, sort=False)[["_tot", "_parts"]].sum() if by else d[["_tot", "_parts"]].sum().to_frame().T
        sums = sums[sums["_tot"] != 0]
        if not len(sums):
            continue
        gap = (sums["_tot"] - sums["_parts"]) / sums["_tot"]
        worst = gap.abs().idxmax()
        rest = sums.loc[worst, "_tot"] - sums.loc[worst, "_parts"]
        at = f" at {fmt_t(worst, c.t.freq)}" if by == ["_t"] else ""
        if gap[worst] < -REL_TOL:
            c.add("aggregate-rows", where, f"parts exceed '{lab}' by up to {-gap[worst]:.1%}{at}",
                  "Parts above the total: double counting or nested levels; keep one level (H11).")
        elif gap[worst] > REL_TOL:
            c.add("aggregate-rows", where, f"parts fall short of '{lab}' by up to {gap[worst]:.1%}{at} "
                  f"(remainder {rest:,.4g})",
                  "Plot the remainder (total minus parts) as 'Other' in part-to-whole charts; keep the total as "
                  "the denominator (H11).", "info")


def check_sentinels(c: Ctx):
    tokens, zero_blank = {}, []
    for col in c.values:
        v, _, tok = c.parsed[col]
        x = v.dropna()
        if len(x) >= 5:
            is_code = x.map(lambda y: bool(SENTINEL_RE.match(f"{y:.0f}" if y == int(y) else "")))
            rest = x[~is_code]
            if is_code.any() and len(rest) >= 3:
                q1, q3 = rest.quantile([0.25, 0.75])
                iqr = max(q3 - q1, 1e-9)
                codes = x[is_code]
                odd = codes[(codes > q3 + SENTINEL_IQR * iqr) | (codes < q1 - SENTINEL_IQR * iqr)]
                if len(odd):
                    c.add("sentinel-values", col, f"{len(odd)} value(s) look like codes: "
                          f"{ex(f'{x:g}' for x in sorted(set(odd)))}",
                          "Check the codebook: 99/888/999-style values usually mean missing or not asked; set them "
                          "to missing or name them (H24).")
            neg = x[x < 0]
            if len(neg) and neg.isin(NEG_CODES).all() and neg.nunique() <= 2 and len(neg) <= 0.2 * len(x):
                codes = ex(f"{x:g}" for x in sorted(set(neg)))
                c.add("sentinel-values", col, f"{len(neg)} value(s) of {codes} in an otherwise non-negative column",
                      "A lone repeated negative is usually a missing code; set it to missing (H24).")
        for t, n in tok.value_counts().items():
            tokens.setdefault(t, [0, []])
            tokens[t][0] += n
            tokens[t][1].append(col)
        blanks = int((c.df[col] == "").sum())
        if len(x) > 10 and (x == 0).any() and blanks:
            zero_blank.append(f"{col} ({int((x == 0).sum())} zeros, {blanks} blanks)")
    if tokens:
        top = sorted(tokens.items(), key=lambda kv: -kv[1][0])
        cols = sorted({col for _, (_, cs) in top for col in cs})
        c.add("sentinel-values", ", ".join(cols[:3]) + (" ..." if len(cols) > 3 else ""),
              f"{sum(n for n, _ in tokens.values())} non-numeric cells read as missing: "
              + ", ".join(f"'{t}' x{n}" for t, (n, _) in top[:4]),
              "Look up each code (suppressed, not available, zero, below threshold) and name it in the note; "
              "never treat it as zero (H24).")
    if zero_blank:
        c.add("sentinel-values", ", ".join(z.split(" (")[0] for z in zero_blank[:3]),
              f"0 and blank both occur: {'; '.join(zero_blank[:3])}",
              "0 and blank can differ (none vs not estimated); keep them apart in averages and counts (H24).")


def check_status(c: Ctx):
    t = c.df["_t"]
    latest = t.max()

    def when(idx):
        tt = t.loc[idx].dropna()
        if not len(tt):
            return ""
        lo, hi = fmt_t(tt.min(), c.t.freq), fmt_t(tt.max(), c.t.freq)
        s = f", period {lo}" if lo == hi else f", periods {lo}..{hi}"
        return s + (", incl. the latest" if tt.max() == latest else "")

    fix = "Draw provisional, estimated, or forecast points distinct and label them; note breaks (H16, H17)."
    for f in c.t.flags:
        s = c.df[f]
        codes = s.str.lower().str.strip("() ").map(FLAG_CODES)
        hit = s[(s != "") & (s.str.contains(STATUS_RE) | (codes.notna() & (s.str.len() <= 4)))]
        if len(hit):
            kinds = ", ".join(f"'{k}' x{n}" for k, n in hit.value_counts().head(4).items())
            c.add("status-flags", f, f"{len(hit)} rows flagged ({kinds}){when(hit.index)}", fix)
    for col in c.values:
        fl = c.parsed[col][1].dropna()
        if len(fl):
            kinds = ", ".join(f"'{k}' x{n}" for k, n in fl.value_counts().head(4).items())
            c.add("status-flags", col, f"{len(fl)} values carry flag suffixes ({kinds}){when(fl.index)}",
                  "Look up the publisher's codes (p provisional, e estimated, b break, * low reliability), then "
                  "draw flagged points distinct and label them (H16, H17).")
    for k in c.keys:
        vint = [x for x in c.df[k].unique() if VINTAGE_RE.search(x)]
        if vint:
            c.add("status-flags", k, f"key values name vintages: {ex(vint)}",
                  "One period may appear once per vintage: keep the latest estimate per period, and mark "
                  "provisional ones (H16, H17).")
    if c.t.date:
        raw = c.df[c.t.date]
        pr = raw[raw.str.match(r".*\d\s*\(?[pPrReE]\)?$")]
        if len(pr):
            c.add("status-flags", c.t.date, f"{len(pr)} period labels carry p/r/e suffixes: {ex(pr.unique())}", fix)


def check_time(c: Ctx):
    if not c.t.date or c.record_level:
        return
    t = c.df["_t"].dropna()
    fut = t[t > c.asof]
    if len(fut):
        c.add("trailing-empty", c.t.date, f"{fut.nunique()} periods dated after {c.asof:%Y-%m-%d} (latest "
              f"{fmt_t(fut.max(), c.t.freq)})", "Future periods are forecasts or placeholders: drop or mark them "
              "(H17, H24).", "warn")
    zeros, blanks, frozen, gaps, latest = [], [], [], [], {}
    fam = {col: (col if c.keys else "all") for col in c.members}
    for col in c.members:
        for name, s in c.series(col):
            valid = s.dropna()
            if len(valid):
                latest[fam[col]] = max(latest.get(fam[col], valid.index[-1]), valid.index[-1])
            nzpos = np.flatnonzero(s.notna().values & (s.values != 0))
            if len(nzpos) >= 3:
                tail = s.iloc[nzpos[-1] + 1:].dropna()
                head = s.iloc[:nzpos[-1] + 1].dropna()
                if len(tail) and (tail == 0).all() and (head == 0).mean() < ZERO_SHARE_MAX:
                    zeros.append((col, name, len(tail), tail.index[0], tail.index[-1] > c.asof))
            # low counts (0-20) repeat by chance; a series constant throughout is not carried forward
            if len(valid) >= 8 and not (valid.max() <= 20 and (valid % 1 == 0).all()) and valid.nunique() > 1:
                same = ((valid.diff() == 0) & (valid != 0)).values[1:]
                run = best = 0
                for i, flag in enumerate(same):
                    run = run + 1 if flag else 0
                    if run > best:
                        best, pos = run, i + 1
                if best + 1 >= FROZEN_RUN:
                    # chance of a repeat, the run under test left out: the larger of how often the series repeats
                    # (step series hold flat) and how often two draws of its own values match (coarse integers)
                    rest = np.delete(valid.values, np.arange(pos - best + 1, pos + 1))
                    p = max((same.sum() - best) / max(len(same) - best, 1),
                            float((pd.Series(rest).value_counts(normalize=True) ** 2).sum()), 1 / len(valid))
                    if len(valid) * p ** best < FROZEN_P:
                        end = valid.index[pos]
                        frozen.append((col, name, best + 1, end, end == valid.index[-1]))
            if c.t.freq in PERIOD_FREQ and len(valid) >= 3:
                per = s.index.to_period(PERIOD_FREQ[c.t.freq])
                if not per.duplicated().any():
                    vper = valid.index.to_period(PERIOD_FREQ[c.t.freq])  # absent rows only: NaN rows break a line
                    full = pd.period_range(vper.min(), vper.max(), freq=PERIOD_FREQ[c.t.freq])
                    miss = full.difference(per)
                    if len(miss):
                        gaps.append((col, name, len(miss), miss[0]))
    for col in c.members:
        if len(c.series(col)) > 1 or fam[col] == "all":
            for name, s in c.series(col):
                valid = s.dropna()
                if len(valid) and valid.index[-1] < latest[fam[col]]:
                    blanks.append((col, name, valid.index[-1]))

    def cols(rows):
        return ", ".join(dict.fromkeys(r[0] for r in rows))

    for sev in ("fail", "warn"):
        z = [r for r in zeros if (r[2] >= 2 or r[4]) == (sev == "fail")]
        if z:
            _, name, n, start, _ = z[0]
            c.add("trailing-empty", cols(z), f"{len(z)} series end in zeros after real values (e.g. {name}: "
                  f"{n} from {fmt_t(start, c.t.freq)})", "Trailing zeros are usually unreleased periods: drop them; "
                  "never plot a fall to zero unless the source confirms it (H24).", None if sev == "fail" else "warn")
    if blanks:
        _, name, last = blanks[0]
        c.add("trailing-empty", cols(blanks), f"{len(blanks)} series lack the latest period others have (e.g. "
              f"{name}: last value {fmt_t(last, c.t.freq)})", "A latest-period ranking or total silently drops "
              "them: use each one's latest value and say so, or the last common period (H24).", "warn")
    if frozen:
        _, name, n, end, at_end = frozen[0]
        c.add("frozen-values", cols(frozen), f"{len(frozen)} series repeat one value {FROZEN_RUN}+ periods in a row "
              f"(e.g. {name}: {n} identical to {fmt_t(end, c.t.freq)}{', at the end' if at_end else ''})",
              "Check whether they are carried-forward values rather than new readings (then treat them as "
              "missing or say so); step series (policy rates, prices, legal limits) legitimately hold flat "
              "(H24).")
    if gaps:
        _, name, n, first = gaps[0]
        c.add("gaps", cols(gaps), f"{len(gaps)} series skip periods (e.g. {name}: {n} missing, first "
              f"{first})", "Keep missing periods missing: a line breaks there (NaN), never interpolated or "
              "connected across; bars leave the slot empty (H15, H16).")
    last = t.max()
    years = t.dt.year.nunique()
    if c.t.freq in ("M", "Q", "W", "D") and years >= 2:
        have = {"M": last.month, "Q": last.quarter}.get(c.t.freq)
        full = {"M": 12, "Q": 4}.get(c.t.freq)
        short = have < full if have else (pd.Timestamp(year=last.year, month=12, day=31) - last).days > \
            (7 if c.t.freq == "W" else 1)
        if short:
            unit = {"M": "months", "Q": "quarters"}.get(c.t.freq)
            part = f"{have}/{full} {unit}" if have else f"through {last:%b %d}"
            c.add("partial-last-period", c.t.date, f"{last.year} is partial ({part})", "Compare year to date or "
                  "trailing 12 months, never a partial year against full years (H15).")
    elif c.t.freq == "A" and last.year >= c.asof.year:
        c.add("partial-last-period", c.t.date, f"annual data includes {last.year}, not over as of "
              f"{c.asof:%Y-%m-%d}", "Label it year to date, provisional, or forecast (H15, H17).")


def check_small_n(c: Ctx):
    if not c.t.ncol or c.t.ncol not in c.parsed:
        return
    n = c.parsed[c.t.ncol][0]
    small = n[n < c.args.min_n]
    if len(small):
        c.add("small-n", c.t.ncol, f"{len(small)} rows have n < {c.args.min_n:g} (min {small.min():g})",
              "State the minimum n; show n on small groups, pool or drop those under it, never rank them (H23).")


CHECK_FUNCS = [check_mixed_units, check_duplicates, check_aggregates, check_sentinels, check_status, check_time,
               check_small_n]


def coverage(tab: Table):
    t = tab.df["_t"].dropna()
    if not len(t):
        return None
    return f"{fmt_t(t.min(), tab.freq)}..{fmt_t(t.max(), tab.freq)}, {t.nunique()} periods"


def run_checks(path, args) -> dict:
    """Read, infer roles, and check one table. Raises Untidy or OSError."""
    df, notes = read_table(path)
    tab = infer_roles(df, args)
    tab.notes = notes + tab.notes
    other = tab.unparsed[~tab.unparsed.str.contains(PERIOD_TOTAL_RE)]
    if len(other):
        tab.notes.append(f"{len(other)} rows with unparsed period skipped ({ex(other.unique(), 2)})")
    c = Ctx(tab, args)
    for fn in CHECK_FUNCS:
        fn(c)
    fails = sum(f.severity == "fail" for f in c.findings)
    return {
        "result": "fail" if fails else "pass",
        "plotted": bool(args.plotted),
        "roles": {"rows": len(tab.df), "date": tab.date, "freq": FREQ_NAME.get(tab.freq), "coverage": coverage(tab),
                  "values": tab.values, "keys": tab.keys, "flags": tab.flags, "n": tab.ncol, "notes": tab.notes},
        "fails": fails,
        "warns": sum(f.severity == "warn" for f in c.findings),
        "findings": [f.__dict__ for f in c.findings],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sanity-check a data table (CSV/TSV) before charting it: aggregate "
                                 "rows, duplicates, trailing zeros, status flags, missing codes, mixed units, gaps, "
                                 "frozen values.")
    ap.add_argument("data", nargs="?", type=Path, help="Path to a .csv or .tsv file.")
    ap.add_argument("--date", help="Period column (default: inferred).")
    ap.add_argument("--value", action="append", help="Value column; repeat for several (default: numeric columns).")
    ap.add_argument("--key", action="append", help="Series key column; repeat for several (default: inferred).")
    ap.add_argument("--total", action="append", help="Label (key value or column) of the published total.")
    ap.add_argument("--n", help="Sample-size column for small-n (default: n/sample/respondents by name).")
    ap.add_argument("--min-n", type=float, default=MIN_N_DEFAULT, help="Minimum n (default 30).")
    ap.add_argument("--asof", help="Today's date for future and partial-period checks (default: today).")
    ap.add_argument("--plotted", action="store_true", help="This is the table the chart plots: aggregate rows "
                    "and mixed units fail instead of warn.")
    ap.add_argument("--json", action="store_true", help="Print JSON only.")
    ap.add_argument("--list-checks", action="store_true", help="List checks and exit.")
    args = ap.parse_args(argv)

    if args.list_checks:
        for name, (raw, plotted, desc) in CHECKS.items():
            print(f"{name}\t{raw if raw == plotted else f'{raw} (--plotted: {plotted})'}\t{desc}")
        return 0
    if args.data is None:
        ap.error("data path required")

    def error(msg):
        print(json.dumps({"result": "error", "error": msg}) if args.json else f"ERROR: {msg}",
              file=sys.stdout if args.json else sys.stderr)
        return 2

    if int(pd.__version__.split(".")[0]) < 2:  # date parsing needs format="mixed"; older pandas would parse nothing
        return error(f"check_data.py needs pandas >= 2 (found {pd.__version__}): pip install -U pandas "
                     "(or run it with uv run --with pandas python ...)")
    if not args.data.is_file():
        return error(f"data file not found: {args.data}")
    try:
        res = run_checks(args.data, args)
    except Untidy as e:
        return error(f"{args.data.name}: {e}")
    except (OSError, ValueError) as e:
        return error(f"{args.data.name}: unreadable: {e}")

    if args.json:
        print(json.dumps(res, indent=1, default=str))
    else:
        r = res["roles"]
        date = f"{r['date']} ({r['freq']})" if r["date"] else "none"
        parts = [f"date={date}", f"values={','.join(r['values'][:6])}" + (" ..." if len(r["values"]) > 6 else ""),
                 f"keys={','.join(r['keys']) or '-'}"]
        parts += [f"flags={','.join(r['flags'])}"] if r["flags"] else []
        parts += [f"coverage {r['coverage']}"] if r["coverage"] else []
        print("INFO roles | " + " | ".join(parts + r["notes"]))
        for f in res["findings"]:
            print(f"{f['severity'].upper()} {f['check']} | {f['where']} | {f['detail']} | fix: {f['fix']}")
        print(f"RESULT {res['result'].upper()}: {res['fails']} fail, {res['warns']} warn, {r['rows']} rows"
              + (", plotted" if res["plotted"] else ""))
    return 1 if res["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())
