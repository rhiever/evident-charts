"""Tests for scripts/check_palette.py (pure stdlib; runs under pytest or `python test_check_palette.py`)."""

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = next(ROOT.glob("skills/*/scripts/check_palette.py"))
_spec = importlib.util.spec_from_file_location("check_palette", _SCRIPT)
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)

OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
JET = ["#00007F", "#0000FF", "#007FFF", "#00FFFF", "#7FFF7F", "#FFFF00", "#FF7F00", "#FF0000", "#7F0000"]
RDBU = ["#B2182B", "#EF8A62", "#FDDBC7", "#F7F7F7", "#D1E5F0", "#67A9CF", "#2166AC"]
PUOR = ["#B35806", "#F1A340", "#FEE0B6", "#F7F7F7", "#D8DAEB", "#998EC3", "#542788"]


def status(run, cid):
    return next(c["status"] for c in run["checks"] if c["id"] == cid)


def cli(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cp.main(list(args) + ["--json"])
    return code, json.loads(buf.getvalue())


def test_ciede2000_sharma_pairs():
    assert len(cp.SHARMA_PAIRS) == 34
    for row in cp.SHARMA_PAIRS:
        assert abs(cp.ciede2000(row[0:3], row[3:6]) - row[6]) < 1e-4, row
        assert abs(cp.ciede2000(row[3:6], row[0:3]) - row[6]) < 1e-4, row
    ok, err = cp.self_test()
    assert ok and err < 1e-4


def test_contrast_reference_values():
    assert abs(cp.contrast("#000000", "#FFFFFF") - 21.0) < 1e-9
    assert abs(cp.contrast("#767676", "#FFFFFF") - 4.54) < 0.01
    assert cp.parse_hex("abc") == "#AABBCC"


def test_okabe_ito_first_four_pass_for_lines():
    run = cp.validate(OKABE[:4], role="categorical", mark="line")
    assert run["pairs"] == "all"
    for cid in ("V3", "V5", "V6", "V7", "V9"):
        assert status(run, cid) == "PASS", cid
    assert all(c["status"] != "FAIL" for c in run["checks"])


def test_jet_fails_sequential_monotonic_lightness():
    run = cp.validate(JET, role="sequential", mark="area")
    assert status(run, "V10") == "FAIL"


def test_red_green_pair_fails_reliance():
    run = cp.validate(["#CC0000", "#009900"], role="categorical", mark="line")
    assert status(run, "V7") == "FAIL"
    code, out = cli("#CC0000,#009900", "--mark", "line")
    assert code == 1 and out["result"] == "fail"


def test_rdbu_passes_diverging_symmetry():
    run = cp.validate(RDBU, role="diverging", mark="area")
    for cid in ("V10", "V13", "V14", "V15"):
        assert status(run, cid) == "PASS", cid


def test_puor_warns_on_symmetry():
    run = cp.validate(PUOR, role="diverging", mark="area")
    assert status(run, "V14") == "WARN"
    assert all(c["status"] != "FAIL" for c in run["checks"])


def test_highlight_preset_passes():
    code, out = cli("--preset", "highlight")
    assert code == 0
    assert all(c["status"] == "PASS" for r in out["runs"] for c in r["checks"])


def test_all_presets_have_no_fail_on_white():
    code, out = cli("--preset", "all")
    assert code == 0 and out["fails"] == 0


def test_yellow_line_fails_contrast():
    run = cp.validate(["#0072B2", "#F0E442"], role="categorical", mark="line")
    assert status(run, "V3") == "FAIL"


def test_highlight_needs_lightness_gap():
    run = cp.validate(["#D55E00"], role="highlight", mark="line", context=["#8E8E8E"])
    assert status(run, "V8") == "FAIL"


def test_bad_hex_exits_2():
    code, out = cli("#12345G")
    assert code == 2 and out["result"] == "error"


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {e!r}")
    print(f"{len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
