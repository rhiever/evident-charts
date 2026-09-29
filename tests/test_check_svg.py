"""Tests for skills/evident-charts/scripts/check_svg.py.

Fixtures in tests/fixtures_svg are pre-exported SVGs (plus Plotly figure JSON and compiled Vega) with a clean
and a bad variant per stack; export_plotly.py and export_vegalite.py regenerate theirs, and the d3_* and
svglite_* files are hand-written in those stacks' output formats. Measuring needs Chrome: those tests skip when
none is found. Spec checks run on inline dicts and need no browser.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "evident-charts" / "scripts"
SCRIPT = SCRIPTS / "check_svg.py"
FIX = Path(__file__).resolve().parent / "fixtures_svg"
sys.path.insert(0, str(SCRIPTS))

import check_svg  # noqa: E402

CHROME = check_svg.find_chrome()
needs_chrome = pytest.mark.skipif(CHROME is None, reason="no Chrome or chrome-headless-shell found")
SPECS = {"plotly_clean": "plotly_clean.json", "plotly_bad": "plotly_bad.json",
         "plotly_lines_bad": "plotly_lines_bad.json", "vegalite_clean": "vegalite_clean.vg.json",
         "vegalite_bad": "vegalite_bad.vg.json"}
_cache = {}


def lint(name, dest="blog"):
    if (name, dest) not in _cache:
        spec = FIX / SPECS[name] if name in SPECS else None
        _cache[name, dest] = check_svg.run_checks(FIX / f"{name}.svg", dest, spec, chrome=CHROME)
    return _cache[name, dest]


def checks(res, severity=None):
    return {f["check"] for f in res["findings"] if severity is None or f["severity"] == severity}


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=120)


# --- measured SVGs ------------------------------------------------------------

@needs_chrome
@pytest.mark.parametrize("name", ["plotly_clean", "vegalite_clean", "d3_clean", "svglite_clean"])
def test_clean_charts_have_no_findings(name):
    res = lint(name)
    assert res["result"] == "pass"
    assert res["findings"] == [], res["findings"]


@needs_chrome
@pytest.mark.parametrize("name,stack", [("plotly_clean", "plotly"), ("vegalite_clean", "vega"),
                                        ("d3_clean", "d3-evident"), ("svglite_clean", "svglite")])
def test_stack_detected(name, stack):
    assert lint(name)["stack"] == stack


@needs_chrome
def test_plotly_bad():
    res = lint("plotly_bad")
    assert checks(res, "fail") == {"text-overlap", "text-on-line", "bar-baseline"}
    assert checks(res, "warn") == {"cvd", "dual-axis"}
    overlap = [f for f in res["findings"] if f["check"] == "text-overlap"]
    assert any("x bar" in f["where"] for f in overlap)       # annotation straddles a bar
    assert any("x marker" in f["where"] for f in overlap)    # and covers the line's marker
    assert any("legend box" in f["where"] for f in overlap)  # legend over the right-axis ticks
    cvd = next(f for f in res["findings"] if f["check"] == "cvd")
    assert "one bar trace" in cvd["detail"]                  # red/green bars in one trace: position tells them apart


@needs_chrome
def test_plotly_lines_bad():
    res = lint("plotly_lines_bad")
    assert checks(res, "fail") == {"text-clipped", "contrast", "cvd", "log-unlabeled"}
    cvd = next(f for f in res["findings"] if f["check"] == "cvd")
    assert "#D62728" in cvd["where"] and "color is the only cue" in cvd["detail"]
    assert "Source" in next(f for f in res["findings"] if f["check"] == "contrast")["where"]


@needs_chrome
def test_vegalite_bad():
    res = lint("vegalite_bad")
    assert checks(res, "fail") == {"text-overlap", "text-on-line", "bar-baseline"}
    assert checks(res, "warn") == {"dual-axis"}
    assert any("tick '0.22'" in f["where"] for f in res["findings"] if f["check"] == "text-overlap")


@needs_chrome
def test_d3_bad():
    res = lint("d3_bad")
    assert checks(res) == {"text-overlap", "text-on-line", "text-on-area", "text-clipped", "contrast"}
    assert next(f for f in res["findings"] if f["check"] == "text-on-area")["where"] == "text 'Recession'"
    # the marker under a label is text-overlap's finding, not the label's backdrop
    assert [f["where"] for f in res["findings"] if f["check"] == "contrast"] == ["text 'Source: Trade office'"]


@needs_chrome
def test_svglite_bad_unclassed_marks():
    res = lint("svglite_bad")
    assert checks(res, "fail") == {"text-overlap", "text-on-line", "contrast", "cvd"}
    assert checks(res, "warn") == {"small-text", "contrast"}
    # the gray panel and white gridlines are background, the yellow trend line is data
    assert any(f["where"] == "line #F0E442" for f in res["findings"] if f["check"] == "contrast")
    assert next(f for f in res["findings"] if f["check"] == "cvd")["where"] == "#F8766D x #00BA38"


@needs_chrome
def test_small_text_scales_with_destination():
    res = lint("plotly_clean", "mobile")
    assert checks(res) == {"small-text"}
    assert "at 360 px wide" in res["findings"][0]["detail"]


# --- CLI ------------------------------------------------------------------------

def test_list_checks_names_match_check_chart():
    out = cli("--list-checks").stdout
    names = [line.split("\t")[0] for line in out.strip().splitlines()]
    assert names == list(check_svg.CHECKS)
    chart_names = set((SCRIPTS / "check_chart.py").read_text().split("CHECKS = {", 1)[1].split("\n}", 1)[0]
                      .replace('"', " ").split())
    assert set(names) <= chart_names


def test_outlined_text_exits_2():
    r = cli(FIX / "outlined_text.svg")
    assert r.returncode == 2
    assert "outlines" in r.stderr and "svg.fonttype" in r.stderr and "svglite" in r.stderr


def test_missing_file_exits_2():
    r = cli(FIX / "nope.svg", "--json")
    assert r.returncode == 2
    assert json.loads(r.stdout)["result"] == "error"


def test_no_chrome_gives_install_hints(monkeypatch):
    monkeypatch.setattr(check_svg, "find_chrome", lambda: None)
    with pytest.raises(check_svg.CheckError, match="chrome-headless-shell"):
        check_svg.run_checks(FIX / "d3_clean.svg")


def test_no_chrome_still_runs_spec_checks(monkeypatch):
    monkeypatch.setattr(check_svg, "find_chrome", lambda: None)
    res = check_svg.run_checks(FIX / "plotly_bad.svg", spec_path=FIX / "plotly_bad.json")
    assert res["result"] == "fail" and "bar-baseline" in checks(res, "fail")
    assert res["note"].startswith("SVG checks skipped") and "chrome-headless-shell" in res["note"]


def test_no_chrome_spec_reads_log_label_from_svg_source(monkeypatch):
    monkeypatch.setattr(check_svg, "find_chrome", lambda: None)
    assert "log-unlabeled" in checks(check_svg.run_checks(FIX / "plotly_lines_bad.svg",
                                                          spec_path=FIX / "plotly_lines_bad.json"))
    assert "log-unlabeled" not in checks(check_svg.run_checks(FIX / "plotly_clean.svg",
                                                              spec_path=FIX / "plotly_clean.json"))


def test_no_chrome_exit_follows_spec(monkeypatch, capsys):
    monkeypatch.setattr(check_svg, "find_chrome", lambda: None)
    assert check_svg.main([str(FIX / "plotly_bad.svg"), "--spec", str(FIX / "plotly_bad.json")]) == 1
    out = capsys.readouterr().out
    assert "FAIL bar-baseline" in out and "SVG checks skipped" in out
    assert check_svg.main([str(FIX / "plotly_clean.svg"), "--spec", str(FIX / "plotly_clean.json")]) == 0
    capsys.readouterr()
    assert check_svg.main([str(FIX / "plotly_bad.svg")]) == 2
    assert "no Chrome found" in capsys.readouterr().err


def test_unknown_spec_exits_2(tmp_path):
    spec = tmp_path / "spec.json"
    spec.write_text('{"hello": 1}')
    r = cli(FIX / "d3_clean.svg", "--spec", spec)
    assert r.returncode == 2 and "neither Plotly" in r.stderr


@needs_chrome
def test_cli_json_and_exit_codes():
    r = cli(FIX / "svglite_bad.svg", "--json")
    assert r.returncode == 1
    res = json.loads(r.stdout)
    assert res["result"] == "fail" and res["fails"] >= 1
    assert {"check", "severity", "where", "detail", "fix"} <= set(res["findings"][0])
    r = cli(FIX / "d3_clean.svg")
    assert r.returncode == 0 and r.stdout.strip().endswith("dest=blog")


# --- spec checks (no browser) ---------------------------------------------------

class T:
    def __init__(self, text):
        self.text = text


def plotly(fig, texts=()):
    found = []
    check_svg.plotly_checks(fig, [T(t) for t in texts], lambda check, where, detail, fix, severity=None:
                            found.append((check, severity or check_svg.CHECKS[check][0], where)))
    return found


def vega(spec, texts=()):
    found = []
    check_svg.vega_checks(spec, [T(t) for t in texts], lambda check, where, detail, fix, severity=None:
                          found.append((check, severity or check_svg.CHECKS[check][0], where)))
    return found


def test_plotly_bar_baseline():
    bars = {"type": "bar", "x": ["a", "b"], "y": [5, 6]}
    assert plotly({"data": [bars], "layout": {"yaxis": {"type": "linear", "range": [4, 7]}}}) == \
        [("bar-baseline", "fail", "yaxis")]
    assert plotly({"data": [bars], "layout": {"yaxis": {"type": "linear", "range": [0, 7]}}}) == []
    assert plotly({"data": [{**bars, "base": [1, 2]}], "layout": {"yaxis": {"range": [4, 7]}}}) == []  # floating
    hbar = {"type": "bar", "orientation": "h", "yaxis": "y", "xaxis": "x"}
    assert plotly({"data": [hbar], "layout": {"xaxis": {"type": "log", "range": [0, 2]}}}, ["log scale"])[0][0] == \
        "bar-baseline"


def test_plotly_dual_inverted_log():
    data = [{"type": "scatter", "y": [1, 2]}, {"type": "scatter", "y": [1, 2], "yaxis": "y2"}]
    lay = {"yaxis": {"type": "log", "autorange": "reversed"}, "yaxis2": {"overlaying": "y", "side": "right"}}
    got = {c for c, _, _ in plotly({"data": data, "layout": lay})}
    assert got == {"dual-axis", "inverted-axis", "log-unlabeled"}
    lay["yaxis"]["title"] = {"text": "Rank"}
    got = {c for c, _, _ in plotly({"data": data, "layout": lay}, ["GDP, log scale"])}
    assert got == {"dual-axis"}


def test_plotly_rainbow():
    jet = [[0, "rgb(0,0,131)"], [0.125, "rgb(0,60,170)"], [0.375, "rgb(5,255,255)"], [0.625, "rgb(255,255,0)"],
           [0.875, "rgb(250,0,0)"], [1, "rgb(128,0,0)"]]
    viridis = [[0, "#440154"], [0.25, "#3b528b"], [0.5, "#21918c"], [0.75, "#5ec962"], [1, "#fde725"]]
    rdbu = [[0, "rgb(5,10,172)"], [0.5, "rgb(247,247,247)"], [1, "rgb(178,10,28)"]]
    heat = lambda cs: {"data": [{"type": "heatmap", "z": [[1, 2]], "colorscale": cs}], "layout": {}}  # noqa: E731
    assert [c for c, _, _ in plotly(heat(jet))] == ["rainbow-cmap"]
    assert plotly(heat(viridis)) == [] and plotly(heat(rdbu)) == []


def vega_bar(scale):
    return {"scales": [{"name": "x", "type": "band"}, {"name": "y", **scale}],
            "axes": [{"scale": "y", "orient": "left"}],
            "marks": [{"type": "rect", "name": "bars", "style": ["bar"],
                       "encode": {"update": {"x": {"scale": "x", "field": "c"}, "y": {"scale": "y", "field": "v"},
                                             "y2": {"scale": "y", "value": 0}}}}]}


def test_vega_bar_baseline():
    assert vega(vega_bar({"type": "linear", "domain": [90, 100], "zero": False})) == \
        [("bar-baseline", "fail", "root/bars")]
    assert vega(vega_bar({"type": "linear", "domain": {"data": "d", "field": "v"}, "zero": True})) == []
    assert vega(vega_bar({"type": "linear", "domain": {"data": "d", "field": "v"}, "zero": False})) == \
        [("bar-baseline", "warn", "root/bars")]
    assert vega(vega_bar({"type": "log", "domain": {"data": "d", "field": "v"}}), ["log"])[0][:2] == \
        ("bar-baseline", "fail")


def test_vega_dual_inverted_log_rainbow():
    spec = {"scales": [{"name": "y", "type": "log", "reverse": True}, {"name": "y2", "type": "linear"},
                       {"name": "color", "type": "linear", "range": {"scheme": "turbo"}},
                       {"name": "cat", "type": "ordinal", "range": {"scheme": "rainbow"}}],
            "axes": [{"scale": "y", "orient": "left"}, {"scale": "y2", "orient": "right"},
                     {"scale": "y2", "orient": "left", "grid": True, "labels": False}]}
    got = {c for c, _, _ in vega(spec)}
    assert got == {"dual-axis", "inverted-axis", "log-unlabeled", "rainbow-cmap"}
    assert [w for c, _, w in vega(spec) if c == "rainbow-cmap"] == ["color"]  # categorical schemes are not colormaps


def test_vega_scale_marks():
    spec = {"scales": [{"name": "color", "type": "linear"}, {"name": "cat", "type": "ordinal"}],
            "marks": [{"type": "rect", "name": "cells",
                       "encode": {"update": {"fill": {"scale": "color", "field": "z"}}}},
                      {"type": "rect", "name": "bars", "encode": {"update": {"fill": {"scale": "cat", "field": "g"}}}}]}
    assert check_svg.vega_scale_marks(spec) == {"cells"}


def test_outlined_text_detection():
    assert check_svg.outlined_text((FIX / "outlined_text.svg").read_text())
    assert not check_svg.outlined_text((FIX / "svglite_clean.svg").read_text())
