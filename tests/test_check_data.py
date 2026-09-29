"""Tests for skills/evident-charts/scripts/check_data.py.

Each fixture in tests/fixtures_data is a small synthetic table with a known defect (or none).
Most tests call main() in-process with --json; CLI behavior is tested via subprocess.
"""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "evident-charts" / "scripts" / "check_data.py"
FIX = Path(__file__).resolve().parent / "fixtures_data"
ASOF = "2026-09-28"
sys.path.insert(0, str(SCRIPT.parent))

import check_data  # noqa: E402


def check(name, *flags, capsys):
    code = check_data.main([str(FIX / name), "--json", "--asof", ASOF, *flags])
    res = json.loads(capsys.readouterr().out)
    res["exit"] = code
    return res


def found(res, name=None, severity=None):
    return [f for f in res["findings"] if (name is None or f["check"] == name)
            and (severity is None or f["severity"] == severity)]


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=60)


# --- clean tables and role inference ---------------------------------------------------

@pytest.mark.parametrize("name", ["clean.csv", "clean.tsv", "clean_wide_series.csv", "preamble.csv",
                                  "policy_rate_ok.csv", "status_key_ok.csv", "rates_high_ok.csv", "low_counts.csv",
                                  "likert_ok.csv", "poll_shares_ok.csv"])
@pytest.mark.parametrize("plotted", [False, True])
def test_clean_tables_have_no_findings(name, plotted, capsys):
    res = check(name, *(["--plotted"] if plotted else []), capsys=capsys)
    assert res["exit"] == 0 and res["findings"] == [], res["findings"]


def test_roles_long_table(capsys):
    r = check("clean.csv", capsys=capsys)["roles"]
    assert (r["date"], r["freq"], r["values"], r["keys"]) == ("month", "monthly", ["sales"], ["region"])
    assert r["coverage"] == "2023-01..2024-12, 24 periods"


def test_roles_skip_title_and_footnote_lines(capsys):
    r = check("preamble.csv", capsys=capsys)["roles"]
    assert r["rows"] == 72 and r["notes"] == ["skipped 3 title line(s)", "skipped 2 footnote line(s)"]


def test_roles_wide_year_columns_are_melted(capsys):
    r = check("wide_years.csv", capsys=capsys)["roles"]
    assert r["date"] == "period" and r["freq"] == "annual" and r["values"] == ["value"]
    assert r["keys"] == ["Country Name"]  # Country Code is its 1:1 code, Series Name is constant
    assert "melted 6 period columns" in r["notes"]


def test_roles_year_plus_period_columns_are_joined(capsys):
    r = check("bls.csv", capsys=capsys)["roles"]
    assert r["date"] == "year+period" and r["freq"] == "monthly" and r["coverage"].startswith("2022-01..2023-12")


def test_roles_status_named_key_is_not_a_flag(capsys):
    r = check("status_key_ok.csv", capsys=capsys)["roles"]
    assert r["keys"] == ["employment status"] and r["flags"] == []


def test_to_num_parses_signs_codes_and_suffixes():
    v, flag, tok = check_data.to_num(pd.Series(["-9", "(1,234)", "1.2K", "12.3 p", "$5", "5%", "(D)", "", "1e3"]))
    assert v.tolist()[:6] == [-9, -1234, 1200, 12.3, 5, 5] and v.tolist()[8] == 1000
    assert flag[3] == "p" and tok.tolist() == ["(D)"]


@pytest.mark.parametrize("raw,freq,first", [
    (["2019", "2020", "2021"], "A", "2019-01-01"), (["2019Q1", "2019Q2", "2019Q3"], "Q", "2019-01-01"),
    (["Q3 2019", "Q4 2019", "Q1 2020"], "Q", "2019-07-01"), (["2019-01", "2019-02", "2019-03"], "M", "2019-01-01"),
    (["2019M11", "2019M12", "2020M01"], "M", "2019-11-01"), (["Jun-26", "Jul-26p", "Aug-26p"], "M", "2026-06-01"),
    (["2019 [YR2019]", "2020 [YR2020]", "2021 [YR2021]"], "A", "2019-01-01"),
    (["FY2020", "FY2021", "FY2022"], "A", "2020-01-01"), (["03/05/2024", "03/12/2024", "03/19/2024"], "W", "2024-03-05"),
])
def test_parse_period_formats(raw, freq, first):
    t, f = check_data.parse_period(pd.Series(raw))
    assert f == freq and t.notna().all() and str(t.iloc[0].date()) == first


def test_parse_period_rejects_seasons_and_plain_numbers():
    assert check_data.parse_period(pd.Series(["2023-24", "2024-25", "2025-26"]))[1] is None
    assert check_data.parse_period(pd.Series(["1", "2", "3"]))[1] is None


# --- aggregate-rows ---------------------------------------------------------------------

@pytest.mark.parametrize("name,label", [("total_row.csv", "All regions"), ("agg_unlabeled.csv", "Pacific Rim"),
                                        ("wide_series.csv", "Total")])
def test_aggregate_rows_warn_on_input_fail_when_plotted(name, label, capsys):
    raw = found(check(name, capsys=capsys), "aggregate-rows")
    assert [f["severity"] for f in raw] == ["warn"] and f"'{label}' equals the sum" in raw[0]["detail"]
    plotted = check(name, "--plotted", capsys=capsys)
    assert plotted["exit"] == 1 and [f["severity"] for f in found(plotted, "aggregate-rows")] == ["fail"]


def test_aggregate_rows_nested_needs_largest_member(capsys):
    # Neutral is a third of Agree + Disagree, but a total is never below its parts (likert_ok.csv is in the clean list)
    assert found(check("likert_ok.csv", "--plotted", capsys=capsys), "aggregate-rows") == []


def test_aggregate_rows_nested_levels(capsys):
    f = found(check("nested.csv", capsys=capsys), "aggregate-rows")
    assert len(f) == 1 and "'Nation'" in f[0]["detail"] and "3 nested levels" in f[0]["detail"]


def test_aggregate_rows_measure_columns_only_warn(capsys):
    f = found(check("measures.csv", "--plotted", capsys=capsys), "aggregate-rows")
    assert [x["severity"] for x in f] == ["warn"] and "'revenue'" in f[0]["detail"]


def test_aggregate_rows_total_label_only_warns(capsys):
    f = found(check("label_total.csv", "--plotted", capsys=capsys), "aggregate-rows")
    assert [x["severity"] for x in f] == ["warn"] and "'World'" in f[0]["detail"]


def test_aggregate_rows_declared_total(capsys):
    over = found(check("parts_total.csv", "--total", "Total", "--plotted", capsys=capsys), "aggregate-rows")
    assert [x["severity"] for x in over] == ["fail"] and "parts exceed 'Total' by up to 16.2%" in over[0]["detail"]
    short = found(check("parts_short.csv", "--total", "Total", capsys=capsys), "aggregate-rows")
    assert [x["severity"] for x in short] == ["info"] and "remainder 420" in short[0]["detail"]
    # a declared total that matches its parts is not reported again as an aggregate row
    assert found(check("total_row.csv", "--total", "All regions", "--plotted", capsys=capsys)) == []


def test_aggregate_rows_annual_average_periods(capsys):
    f = found(check("bls.csv", capsys=capsys), "aggregate-rows")
    assert len(f) == 1 and f[0]["severity"] == "warn" and "M13" in f[0]["detail"]


def test_unknown_total_label_exits_2(capsys):
    assert check_data.main([str(FIX / "clean.csv"), "--total", "Nope"]) == 2
    assert "--total Nope" in capsys.readouterr().err


# --- duplicate-keys ---------------------------------------------------------------------

def test_duplicate_keys_conflicting_fail(capsys):
    res = check("duplicates.csv", capsys=capsys)
    f = found(res, "duplicate-keys")
    assert res["exit"] == 1 and f[0]["severity"] == "fail" and "2 key(s) with different values" in f[0]["detail"]


def test_duplicate_keys_identical_warn(capsys):
    assert [f["severity"] for f in found(check("dup_identical.csv", capsys=capsys), "duplicate-keys")] == ["warn"]


def test_record_level_tables_skip_series_checks(capsys):
    res = check("records.csv", capsys=capsys)
    assert [(f["check"], f["severity"]) for f in res["findings"]] == [("record-level", "info")]


# --- trailing-empty ---------------------------------------------------------------------

def test_trailing_zeros_fail_and_future_periods_warn(capsys):
    res = check("trailing_zero.csv", capsys=capsys)
    sev = sorted(f["severity"] for f in found(res, "trailing-empty"))
    assert res["exit"] == 1 and sev == ["fail", "warn"]
    assert "5 from 2026-08" in found(res, "trailing-empty", "fail")[0]["detail"]


def test_single_trailing_zero_warns(capsys):
    assert [f["severity"] for f in found(check("trailing_one_zero.csv", capsys=capsys), "trailing-empty")] == ["warn"]


@pytest.mark.parametrize("name,who", [("blank_latest.csv", "West"), ("wide_years.csv", "Bravia")])
def test_series_missing_latest_period_warns(name, who, capsys):
    f = found(check(name, capsys=capsys), "trailing-empty")
    assert [x["severity"] for x in f] == ["warn"] and who in f[0]["detail"]


# --- status-flags -----------------------------------------------------------------------

@pytest.mark.parametrize("name,where,text", [
    ("flags.csv", "OBS_FLAG", "'p' x2, 'b' x1"), ("cell_flags.csv", "rate", "'p' x1"),
    ("period_suffix.csv", "year", "'2023p'"), ("vintages.csv", "estimate", "'Advance'"),
])
def test_status_flags(name, where, text, capsys):
    f = found(check(name, capsys=capsys), "status-flags")
    assert len(f) == 1 and f[0]["where"] == where and text in f[0]["detail"] and f[0]["severity"] == "warn"


def test_status_flags_name_the_latest_period(capsys):
    assert "incl. the latest" in found(check("flags.csv", capsys=capsys), "status-flags")[0]["detail"]


# --- sentinel-values --------------------------------------------------------------------

def test_sentinel_codes(capsys):
    details = " ".join(f["detail"] for f in found(check("sentinels.csv", capsys=capsys), "sentinel-values"))
    assert "'999'" in details and "'-9'" in details


def test_missing_tokens(capsys):
    f = found(check("tokens.csv", capsys=capsys), "sentinel-values")
    assert len(f) == 1 and "':' x2" in f[0]["detail"]


def test_zero_and_blank(capsys):
    f = found(check("zero_blank.csv", capsys=capsys), "sentinel-values")
    assert len(f) == 1 and "4 zeros, 2 blanks" in f[0]["detail"]


# --- mixed-units ------------------------------------------------------------------------

def test_mixed_units_warn_on_input_fail_when_plotted(capsys):
    assert [f["severity"] for f in found(check("mixed_units.csv", capsys=capsys), "mixed-units")] == ["warn"]
    res = check("mixed_units.csv", "--plotted", capsys=capsys)
    assert res["exit"] == 1 and [f["severity"] for f in found(res, "mixed-units")] == ["fail"]


def test_mixed_indicators_only_warn(capsys):
    f = found(check("indicators.csv", "--plotted", capsys=capsys), "mixed-units")
    assert [x["severity"] for x in f] == ["warn"] and f[0]["where"] == "indicator"


# --- gaps, frozen-values ----------------------------------------------------------------

def test_gaps(capsys):
    f = found(check("gaps.csv", capsys=capsys), "gaps")
    assert len(f) == 1 and "South: 2 missing, first 2023-06" in f[0]["detail"]


def test_missing_cells_are_not_gaps(capsys):
    assert found(check("tokens.csv", capsys=capsys), "gaps") == []


def test_frozen_values(capsys):
    f = found(check("frozen.csv", capsys=capsys), "frozen-values")
    assert len(f) == 1 and "5 identical to 2025-12, at the end" in f[0]["detail"]


def test_frozen_values_narrow_integer_band_is_not_frozen(capsys):
    # integer shares moving 44-47 repeat by chance: a run of 4 is expected in a series this coarse
    assert found(check("poll_shares_ok.csv", capsys=capsys), "frozen-values") == []


def test_frozen_values_long_run_in_noisy_series_warns(capsys):
    f = found(check("frozen_noisy.csv", capsys=capsys), "frozen-values")
    assert len(f) == 1 and "10 identical to 2024-10" in f[0]["detail"] and "step series" in f[0]["fix"]


def test_old_pandas_exits_2(monkeypatch, capsys):
    monkeypatch.setattr(check_data.pd, "__version__", "1.5.3")
    res = check("clean.csv", capsys=capsys)
    assert res["exit"] == 2 and "pandas >= 2" in res["error"]


# --- partial-last-period, small-n -------------------------------------------------------

def test_partial_last_period(capsys):
    f = found(check("partial.csv", capsys=capsys), "partial-last-period")
    assert [x["severity"] for x in f] == ["info"] and "2026 is partial (8/12 months)" in f[0]["detail"]


def test_partial_annual_year_not_over(capsys):
    code = check_data.main([str(FIX / "flags.csv"), "--json", "--asof", "2023-06-30"])
    res = json.loads(capsys.readouterr().out)
    assert code == 0 and "not over" in found(res, "partial-last-period")[0]["detail"]


def test_small_n(capsys):
    f = found(check("small_n.csv", capsys=capsys), "small-n")
    assert [x["severity"] for x in f] == ["info"] and "2 rows have n < 30 (min 7)" in f[0]["detail"]
    assert found(check("small_n.csv", "--min-n", "5", capsys=capsys), "small-n") == []


# --- untidy layouts ---------------------------------------------------------------------

@pytest.mark.parametrize("name,text", [
    ("untidy_two_headers.csv", "second header"), ("untidy_sections.csv", "section header rows"),
    ("untidy_repeated_header.csv", "header repeats"), ("untidy_merged_header.csv", "multi-row header"),
    ("no_numbers.csv", "no numeric value column"),
])
def test_untidy_layouts_exit_2(name, text):
    res = cli(FIX / name)
    assert res.returncode == 2 and res.stdout == "" and text in res.stderr


# --- CLI --------------------------------------------------------------------------------

def test_cli_exit_codes_and_text_output():
    ok = cli(FIX / "clean.csv", "--asof", ASOF)
    lines = ok.stdout.strip().splitlines()
    assert ok.returncode == 0 and lines[0].startswith("INFO roles | date=month (monthly) | values=sales")
    assert lines[-1] == "RESULT PASS: 0 fail, 0 warn, 72 rows"
    bad = cli(FIX / "total_row.csv", "--plotted", "--asof", ASOF)
    lines = bad.stdout.strip().splitlines()
    assert bad.returncode == 1 and lines[1].startswith("FAIL aggregate-rows | sales by region | ")
    assert " | fix: " in lines[1] and lines[-1] == "RESULT FAIL: 1 fail, 0 warn, 96 rows, plotted"


def test_cli_json():
    res = cli(FIX / "duplicates.csv", "--json", "--asof", ASOF)
    data = json.loads(res.stdout)
    assert res.returncode == 1 and data["result"] == "fail" and data["plotted"] is False
    assert set(data["findings"][0]) == {"check", "severity", "where", "detail", "fix"}
    err = cli(FIX / "untidy_sections.csv", "--json")
    assert err.returncode == 2 and json.loads(err.stdout)["result"] == "error"


def test_cli_missing_file_and_column_exit_2():
    assert cli(FIX / "nope.csv").returncode == 2
    res = cli(FIX / "clean.csv", "--date", "nope")
    assert res.returncode == 2 and "--date column not found" in res.stderr


def test_cli_list_checks():
    res = cli("--list-checks")
    rows = [ln.split("\t") for ln in res.stdout.strip().splitlines()]
    assert res.returncode == 0 and [r[0] for r in rows] == list(check_data.CHECKS)
    assert dict((r[0], r[1]) for r in rows)["mixed-units"] == "warn (--plotted: fail)"


def test_missing_pandas_exits_2_with_install_hint():
    code = ("import runpy, sys; sys.modules['pandas'] = None; sys.argv = ['check_data.py', 'x.csv']; "
            f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')")
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert res.returncode == 2 and "pip install pandas" in res.stderr
