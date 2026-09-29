"""Tests for skills/evident-charts/scripts/check_chart.py.

Each fixture in tests/fixtures is a small chart script with a known defect
(or none). Most tests lint in-process; CLI behavior is tested via subprocess.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "evident-charts" / "scripts" / "check_chart.py"
FIX = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPT.parent))

import check_chart  # noqa: E402


def lint(name, dest="blog"):
    return check_chart.run_checks(FIX / name, dest=dest)


def checks(res, severity=None):
    return {f["check"] for f in res["findings"] if severity is None or f["severity"] == severity}


def cli(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd, timeout=120)


# --- clean charts -----------------------------------------------------------

@pytest.mark.parametrize("name", ["good_line.py", "slope_good.py", "lollipop.py", "bar_good.py", "label_clear.py",
                                  "label_points_ev.py", "source_ok.py", "value_labels_ok.py", "inverted_ok.py",
                                  "log_labeled.py", "label_lines_ev.py", "strip_ev.py",
                                  "reference_ev.py", "group_label_ev.py"])
def test_clean_charts_have_no_findings(name):
    res = lint(name)
    assert res["result"] == "pass"
    # Minimal fixtures omit source lines; missing-source has its own test.
    assert [f for f in res["findings"] if f["check"] != "missing-source"] == [], res["findings"]


# --- text-overlap -------------------------------------------------------------

def test_text_overlap_fails():
    res = lint("text_overlap.py")
    assert checks(res, "fail") == {"text-overlap"}
    assert "Peak demand" in res["findings"][0]["where"]


def test_overlapping_tick_labels_fail():
    res = lint("tick_overlap.py")
    assert "text-overlap" in checks(res, "fail")
    assert all("tick" in f["where"] for f in res["findings"] if f["check"] == "text-overlap")


def test_legend_box_covering_axis_label_fails():
    hits = [f for f in lint("legend_overlap.py")["findings"] if f["check"] == "text-overlap"]
    assert [(h["severity"], h["where"]) for h in hits] == [("fail", "fig0/ax0 legend box x axis_label 'Quarter'")]


def test_text_straddling_a_bar_edge_or_two_bars_fails_inside_labels_pass():
    hits = [f["where"] for f in lint("text_on_bar.py")["findings"] if f["check"] == "text-overlap"]
    assert sorted(hits) == ["fig0/ax0 text 'Both years' x bar", "fig0/ax0 text 'Peak' x bar"]


def test_short_kicker_over_a_hero_number_is_not_a_default_title():
    assert "default-title" not in checks(lint("hero_kicker.py"))


def test_figure_created_without_pyplot_or_savefig_is_checked():
    res = lint("no_savefig_figure.py")
    assert "text-overlap" in checks(res, "fail")


# --- text-on-line -------------------------------------------------------------

def test_label_on_two_point_slope_line_fails():
    res = lint("slope_bad.py")
    hits = [f for f in res["findings"] if f["check"] == "text-on-line"]
    assert len(hits) == 1 and "'Rural'" in hits[0]["where"]


def test_endpoint_direct_labels_pass():
    assert "text-on-line" not in checks(lint("slope_good.py"))


def test_annotation_arrow_through_other_text_fails():
    res = lint("arrow_through_text.py")
    hits = [f for f in res["findings"] if f["check"] == "text-on-line"]
    assert len(hits) == 1
    assert "Unrelated note" in hits[0]["where"] and "arrow" in hits[0]["where"]


def test_line_threading_between_lines_of_a_label_fails():
    hits = [f for f in lint("multiline_on_line.py")["findings"] if f["check"] == "text-on-line"]
    assert len(hits) == 1 and "'Target / set in 2012' on 'Target'" in hits[0]["where"]


# --- text-clipped ---------------------------------------------------------------

def test_text_clipped_at_right_edge_fails():
    res = lint("clipped_right.py")
    hits = [f for f in res["findings"] if f["check"] == "text-clipped"]
    assert len(hits) == 1 and "right" in hits[0]["detail"]


def test_bbox_tight_savefig_is_not_clipped():
    assert "text-clipped" not in checks(lint("clipped_tight_ok.py"))


# --- bar-baseline -----------------------------------------------------------------

def test_truncated_bar_axis_fails():
    res = lint("bar_truncated.py")
    assert checks(res, "fail") == {"bar-baseline"}


def test_log_bar_axis_fails():
    res = lint("bar_log.py")
    assert checks(res, "fail") == {"bar-baseline", "log-unlabeled"}
    assert "log" in res["findings"][0]["detail"]


# --- sources, process notes, readouts, titles, scales ---------------------------------

def test_process_notes_and_file_sources_fail():
    hits = [f for f in lint("process_note.py")["findings"] if f["check"] == "process-note"]
    assert [h["severity"] for h in hits] == ["fail", "fail"]
    assert "inferred, confirm" in hits[0]["detail"]
    assert "file name sales_2022.csv" in hits[1]["detail"]


def test_missing_source_warns_once_per_figure():
    hits = [f for f in lint("good_line.py")["findings"] if f["check"] == "missing-source"]
    assert [(h["severity"], h["where"]) for h in hits] == [("warn", "fig0/figure")]
    for name in ("source_ok.py", "process_note.py", "value_labels_ok.py", "inverted_ok.py", "log_labeled.py"):
        assert "missing-source" not in checks(lint(name)), name


def test_value_labels_with_value_axis_warn():
    res = lint("value_labels_axis.py")
    hits = [f for f in res["findings"] if f["check"] == "value-labels-and-axis"]
    assert len(hits) == 1 and hits[0]["where"] == "fig0/ax0 y-axis" and hits[0]["detail"].startswith("4 of 4 bars")
    assert res["result"] == "pass"


def test_value_label_number_matching():
    assert check_chart.number_matches("80k", 80)
    assert check_chart.number_matches("$1.2M", 1_234_567)
    assert check_chart.number_matches("45%", 0.448)
    assert check_chart.number_matches("\u22123.5", -3.46)
    assert not check_chart.number_matches("12 stores", 80)
    assert not check_chart.number_matches("1.2", 1.3)


def test_number_format_fails_offsets_scientific_and_year_ticks_and_warns_mixed_decimals():
    hits = [(f["severity"], f["where"], f["detail"].split(" (")[0].split(" print")[0])
            for f in lint("number_format.py")["findings"] if f["check"] == "number-format"]
    assert hits == [
        ("fail", "fig0/ax0 y-axis", "offset text '1e6' changes every tick's value"),
        ("fail", "fig1/ax0 x-axis", "offset text '+2.019e3' changes every tick's value"),
        ("fail", "fig2/ax0 y-axis", "scientific-notation ticks"),
        ("fail", "fig3/ax0 x-axis", "year ticks"),
        ("fail", "fig4/ax0 x-axis", "year ticks"),
        ("warn", "fig5/ax0 y-axis", "ticks mix [0, 1, 2] decimals"),
        ("warn", "fig6/ax0 value labels", "value labels mix [0, 1, 2, 4] decimals")]


def test_number_format_passes_abbreviations_counts_bare_zero_separate_label_sets_log_ticks_and_value_axes():
    assert "number-format" not in checks(lint("number_format_ok.py"))
    assert check_chart.decimals("$1,234.50M") == 2 and check_chart.decimals("−0.5") == 1
    assert check_chart.decimals("n/a") is None


def test_category_order_warns_unsorted_bars_nominal_lines_and_evenly_spaced_uneven_years():
    res = lint("category_order.py")
    hits = [(f["severity"], f["where"], f["detail"]) for f in res["findings"] if f["check"] == "category-order"]
    assert hits == [
        ("warn", "fig0/ax0 y-axis", "6 nominal bars unsorted (3 of 15 pairs out of order)"),
        ("warn", "fig1/ax0 x-axis", "5 nominal bars unsorted (4 of 10 pairs out of order)"),
        ("warn", "fig2/ax0 x-axis", "line drawn across nominal categories (North, South, East, ...)"),
        ("warn", "fig3/ax0 x-axis", "years 2010-2020 evenly spaced as categories, hiding gaps of [1, 2, 3, 4] years")]


def test_category_order_skips_tails_sections_ties_ordinal_labels_numeric_years_waterfalls_and_shared_rows():
    assert "category-order" not in checks(lint("category_order_ok.py"))


def test_title_too_long_by_lines_and_the_same_measured_fit_as_fits_title():
    import evident as ev
    ns = {}
    exec((FIX / "title_long.py").read_text().split("for i, title")[0].replace("from _clean import new", ""), ns)
    for dest in ("blog", "mobile"):
        hits = {f["where"].split("/")[0]: f["detail"] for f in lint("title_long.py", dest)["findings"]
                if f["check"] == "title-too-long"}
        assert hits["fig0"].startswith("title runs 3 lines")
        for i, title in enumerate(ns["titles"][1:], 1):  # flagged exactly when fits_title says it does not fit
            text = " ".join(title.split())
            assert (f"fig{i}" in hits) == (not ev.fits_title(text, dest)[0]), (dest, i)
            if f"fig{i}" in hits:
                assert hits[f"fig{i}"].startswith(f"title runs past 2 lines at {dest} ({len(text)} chars, cut about")
    assert "fig2" not in [f["where"].split("/")[0] for f in lint("title_long.py")["findings"]
                          if f["check"] == "title-too-long"]
    assert {"fig2", "fig3"} <= {f["where"].split("/")[0] for f in lint("title_long.py", "mobile")["findings"]
                                if f["check"] == "title-too-long"}


def test_inverted_value_axis_fails():
    hits = [f for f in lint("inverted_axis.py")["findings"] if f["check"] == "inverted-axis"]
    assert [(h["severity"], h["where"]) for h in hits] == [("fail", "fig0/ax0 y-axis")]


def test_log_axis_without_log_label_fails():
    hits = [f for f in lint("log_unlabeled.py")["findings"] if f["check"] == "log-unlabeled"]
    assert [(h["severity"], h["where"]) for h in hits] == [("fail", "fig0/ax0 y-axis")]


# --- warn-level checks ---------------------------------------------------------------

@pytest.mark.parametrize("name,check", [
    ("dual_axis.py", "dual-axis"),
    ("pie_many.py", "pie-slices"),
    ("legend_lines.py", "legend-direct-label"),
    ("missing_label.py", "missing-axis-label"),
    ("tick_rotation.py", "tick-crowding"),
    ("many_lines.py", "too-many-series"),
    ("default_style.py", "spines-gridlines"),
    ("small_text.py", "small-text"),
])
def test_warn_checks_fire(name, check):
    res = lint(name)
    assert check in checks(res, "warn")
    assert res["result"] == "pass"  # warns alone do not fail


def test_3d_axes_fail():
    res = lint("surface_3d.py")
    assert checks(res, "fail") == {"3d-axes"} and res["result"] == "fail"


def test_bar3d_colors_and_tick_labels_are_checked():
    res = lint("bar3d_many.py")
    assert {"too-many-series", "small-text"} <= checks(res, "warn")
    assert [f["detail"] for f in res["findings"] if f["check"] == "too-many-series"] == ["9 distinct categorical colors"]


def test_crowded_category_ticks_suggest_taller_canvas():
    hits = [f for f in lint("tick_crowd_categories.py")["findings"] if f["check"] == "tick-crowding"]
    assert [h["where"] for h in hits] == ["fig0/ax0 y-axis"]
    assert "taller canvas or fewer categories" in hits[0]["fix"] and "fewer ticks" not in hits[0]["fix"]


@pytest.mark.parametrize("dest", ["slide", "social", "social_portrait"])
def test_crowded_categories_on_fixed_height_presets_suggest_fewer_rows(dest):
    hits = [f for f in lint("tick_crowd_categories.py", dest)["findings"] if f["check"] == "tick-crowding"]
    rows = check_chart.DEST_BAR_ROWS[dest]
    assert f"about {rows} bar rows fit" in hits[0]["fix"] and "taller" not in hits[0]["fix"]


def test_pie_detail_counts_slices():
    f = [f for f in lint("pie_many.py")["findings"] if f["check"] == "pie-slices"][0]
    assert "7 slices" in f["detail"]


def test_missing_axis_label_skips_year_axis():
    hits = [f for f in lint("missing_label.py")["findings"] if f["check"] == "missing-axis-label"]
    assert [h["where"] for h in hits] == ["fig0/ax0 y-axis"]


def test_gray_context_lines_do_not_count_as_series():
    hits = [f for f in lint("many_lines.py")["findings"] if f["check"] == "too-many-series"]
    assert [h["where"] for h in hits] == ["fig0/ax0"]


def test_default_title_variants():
    hits = [f for f in lint("titles.py")["findings"] if f["check"] == "default-title"]
    assert len(hits) == 3
    assert "Revenue by region" in hits[0]["where"]
    assert "over time" in hits[1]["where"]
    assert hits[2]["detail"] == "no title"


def test_axes_title_on_one_panel_is_the_chart_title():
    hits = [f for f in lint("title_on_axes.py")["findings"] if f["check"] == "default-title"]
    assert [(h["where"], h["detail"]) for h in hits] == [("fig1/figure", "only panel titles; no overall title")]


def test_unit_on_some_ticks_only_warns():
    hits = [f for f in lint("tick_units_mixed.py")["findings"] if f["check"] == "missing-axis-label"]
    assert [h["where"] for h in hits] == ["fig0/ax0 y-axis"] and "1 of 4" in hits[0]["detail"]


@pytest.mark.parametrize("dest,expected", [("mobile", ["fig0/ax0"]), ("social_portrait", ["fig0/ax0"]), ("blog", [])])
def test_square_scatter_on_narrow_canvas_underuses_width(dest, expected):
    res = lint("scatter_square_narrow.py", dest=dest)
    assert [f["where"] for f in res["findings"] if f["check"] == "plot-area-underused"] == expected


def test_takeaway_title_passes():
    assert "default-title" not in checks(lint("good_line.py"))


def test_small_text_depends_on_destination():
    assert "small-text" not in checks(lint("good_line.py", dest="blog"))
    res = lint("good_line.py", dest="mobile")
    f = [f for f in res["findings"] if f["check"] == "small-text"][0]
    assert "mobile" in f["detail"] and "pt" in f["fix"]


# --- label-ambiguous -----------------------------------------------------------------

def test_label_next_to_wrong_dot_warns():
    res = lint("label_ambiguous.py")
    hits = {f["where"]: f for f in res["findings"] if f["check"] == "label-ambiguous"}
    assert set(hits) == {"fig0/ax0 annotation 'Norway'", "fig0/ax0 text 'Chile'"}
    assert hits["fig0/ax0 annotation 'Norway'"]["detail"].startswith("nearer the dot at (1470, 120)")
    assert hits["fig0/ax0 text 'Chile'"]["detail"].startswith("about equally near")
    assert res["result"] == "pass"


def test_label_ambiguous_skips_labels_of_lines_rules_and_median_ticks():
    assert "label-ambiguous" not in checks(lint("label_line_dots.py"))


def test_label_points_places_labels_beside_their_dots():
    import matplotlib
    import matplotlib.pyplot as plt
    import evident as ev
    with matplotlib.rc_context():
        fig, ax = ev.figure("blog")
        x, y, names = [1, 2, 3, 3], [5, 4, 3, 2.2], ["Norway", "Denmark", "Chile", "Mexico"]
        ax.scatter(x, y, s=ev.size("marker", fig) ** 2, color=ev.GRAY)
        texts = ev.label_points(ax, x, y, names, offsets={"Chile": "above", "Mexico": (0, -8)}, highlight="Norway")
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 6)
        findings, _ = check_chart.lint_figure(fig, 0)
        plt.close(fig)
    assert [t.get_text() for t in texts] == names
    assert texts[0].get_weight() == "bold" and texts[1].get_weight() == "normal"
    assert texts[0].get_color() == ev.ACCENT_TEXT
    assert (texts[1].get_ha(), texts[1].get_va()) == ("left", "center")
    assert (texts[2].get_va(), texts[3].get_va()) == ("bottom", "top")
    assert not [f for f in findings if f.check == "label-ambiguous"], findings


# --- rainbow-cmap ------------------------------------------------------------------

def test_jet_fails_once_not_on_colorbar():
    hits = [f for f in lint("rainbow_jet.py")["findings"] if f["check"] == "rainbow-cmap"]
    assert len(hits) == 1 and hits[0]["severity"] == "fail"


def test_spectral_diverging_warns_sequential_fails_viridis_ok():
    hits = {f["where"].split()[0]: f["severity"] for f in lint("spectral.py")["findings"]
            if f["check"] == "rainbow-cmap"}
    assert hits == {"fig0/ax0": "warn", "fig0/ax1": "fail"}


# --- CLI ------------------------------------------------------------------------------

def test_cli_exit_codes_and_text_output():
    ok = cli(FIX / "source_ok.py")
    assert ok.returncode == 0 and ok.stdout.strip().startswith("RESULT PASS")
    bad = cli(FIX / "slope_bad.py")
    assert bad.returncode == 1
    lines = bad.stdout.strip().splitlines()
    assert lines[0].startswith("FAIL text-on-line | ") and " | fix: " in lines[0]
    assert lines[-1].startswith("RESULT FAIL: 1 fail")


def test_cli_json_is_pure_json_even_if_script_prints(tmp_path):
    res = cli(FIX / "writes_file.py", "--json", "--cwd", tmp_path)
    data = json.loads(res.stdout)
    assert res.returncode == 0 and data["result"] == "pass"
    assert set(data["findings"][0]) == {"check", "severity", "where", "detail", "fix"}
    assert not list(tmp_path.iterdir()), "savefig must not write files"
    assert not (FIX / "SHOULD_NOT_EXIST.png").exists()


def test_cli_script_error_exits_2_with_traceback_tail():
    res = cli(FIX / "script_error.py")
    assert res.returncode == 2
    assert "boom in chart script" in res.stderr
    res = cli(FIX / "script_error.py", "--json")
    assert res.returncode == 2 and json.loads(res.stdout)["result"] == "error"


def test_cli_missing_file_exits_2():
    assert cli(FIX / "nope.py").returncode == 2


def test_cli_help_says_it_executes_the_script():
    res = cli("--help")
    out = " ".join(res.stdout.split())
    assert res.returncode == 0 and "Executes the script" in out and "scratch copy" in out


def test_cli_list_checks():
    res = cli("--list-checks")
    names = [ln.split("\t")[0] for ln in res.stdout.strip().splitlines()]
    assert res.returncode == 0 and names == list(check_chart.CHECKS)


def test_cli_verbose_prints_inventory():
    res = cli(FIX / "good_line.py", "--verbose")
    assert res.stdout.startswith("INFO fig0: 1 axes")


# --- v0.3 checks -----------------------------------------------------------------------

def test_source_anywhere_in_a_footer_line_counts():
    hits = [f for f in lint("source_ok.py")["findings"] if f["check"] == "missing-source"]
    assert hits == []
    assert check_chart.SOURCE_RE.search("Note: 2024 is provisional | Source: CDC")
    assert check_chart.SOURCE_RE.search("Note: 2024 is provisional. Source: CDC")
    assert not check_chart.SOURCE_RE.search("Open-source software grew")


def test_cumulative_series_under_rate_label_fails():
    hits = [(f["severity"], f["where"].split()[0]) for f in lint("cumulative_rate.py")["findings"]
            if f["check"] == "cumulative-as-rate"]
    assert hits == [("fail", "fig0/ax0"), ("fail", "fig3/ax0")]


def test_stacked_area_with_three_or_more_layers_warns():
    res = lint("stacked_area.py")
    hits = [(f["severity"], f["where"], f["detail"]) for f in res["findings"] if f["check"] == "stacked-area"]
    assert hits == [("warn", "fig0/ax0", "stacked area with 4 layers"), ("warn", "fig1/ax0", "stacked area with 3 layers")]
    assert "stacked-area" not in checks(lint("cumulative_rate.py"))  # 2 layers


def test_segment_edges_warns_touching_fills_without_background_edges():
    hits = [(f["severity"], f["where"], f["detail"], f["fix"]) for f in lint("segment_edges.py")["findings"]
            if f["check"] == "segment-edges"]
    assert [h[:3] for h in hits] == [
        ("warn", "fig0/ax0", "4 boundaries between differently colored bar segments have no background-colored edge"),
        ("warn", "fig1/ax0", "3 boundaries between differently colored pie wedges have no background-colored edge"),
        ("warn", "fig2/ax0", "1 boundary between differently colored stacked area layers has no background-colored "
                             "edge"),
        ("warn", "fig3/ax0", "4 boundaries between differently colored bar segments have no background-colored edge")]
    assert 'ax.bar(..., edgecolor="white", linewidth=ev.size("grid"))' in hits[0][3]
    assert 'wedgeprops=dict(edgecolor="white", linewidth=ev.size("grid"))' in hits[1][3]
    assert 'ax.stackplot(..., edgecolor="white", linewidth=ev.size("grid"))' in hits[2][3]


def test_segment_edges_passes_white_edges_same_color_gaps_narrow_bars_bands_heatmaps_and_violins():
    assert "segment-edges" not in checks(lint("segment_edges_ok.py"))
    assert [f["where"] for f in lint("stacked_area.py")["findings"] if f["check"] == "segment-edges"] == \
        ["fig0/ax0", "fig1/ax0"]  # the nested uncertainty bands in fig2 do not sit on one another


def test_text_covering_a_data_marker_fails():
    hits = [f["where"] for f in lint("text_on_marker.py")["findings"] if f["check"] == "text-overlap"]
    assert hits == ["fig0/ax0 annotation 'Chile' x marker", "fig0/ax0 text 'Dip here' x marker"]


def test_collapsed_panels_fail_but_small_multiples_and_insets_pass():
    hits = [(f["severity"], f["where"]) for f in lint("plot_tiny.py")["findings"] if f["check"] == "plot-area-tiny"]
    assert hits == [("fail", "fig0/ax0"), ("fail", "fig0/ax1")]


def test_plot_aspect_flags_squeezed_and_tall_plots_but_not_rows_multiples_or_cards():
    for dest, fixed in (("blog", False), ("slide", True)):
        hits = [f for f in lint("plot_aspect.py", dest)["findings"] if f["check"] == "plot-aspect"]
        assert [(f["severity"], f["where"]) for f in hits] == [("warn", "fig0/ax0"), ("warn", "fig1/ax0")]
        assert "5.3:1" in hits[0]["detail"] and "1:2.5" in hits[1]["detail"]
        assert ("fixed height" in hits[0]["fix"] and "ev.titles(fig, None" in hits[0]["fix"]) == fixed


# --- color: cvd, contrast, text-on-area ---------------------------------------------------

def color_hits(name, check):
    return [(f["severity"], f["where"]) for f in lint(name)["findings"] if f["check"] == check]


def test_cvd_fails_red_green_told_apart_by_legend_only():
    hits = [f for f in lint("cvd_legend.py")["findings"] if f["check"] == "cvd"]
    assert [(h["severity"], h["where"]) for h in hits] == [("fail", "fig0/ax0 'Online' x 'Stores'")]
    assert "deutan" in hits[0]["detail"] and "only cue" in hits[0]["detail"]


def test_cvd_warns_when_labels_hue_matched_labels_dashes_or_markers_also_separate_series():
    hits = [f for f in lint("cvd_redundant.py")["findings"] if f["check"] == "cvd"]
    assert [(h["severity"], h["where"].split()[0]) for h in hits] == [
        ("warn", "fig0/ax0"), ("warn", "fig1/ax0"), ("warn", "fig2/ax0"), ("warn", "fig3/ax0")]
    assert ["direct labels" in h["detail"] for h in hits] == [True, True, False, False]


def test_house_palette_charts_have_no_color_findings():
    res = lint("cvd_house.py")
    assert not checks(res) & {"cvd", "contrast", "text-on-area"}, res["findings"]
    assert res["result"] == "pass"


def test_contrast_flags_faint_text_and_marks_and_groups_ticks_per_axis():
    assert color_hits("contrast_low.py", "contrast") == [
        ("fail", "fig0/ax0 text 'Faint note'"), ("fail", "fig0/ax0 line #f0e442"), ("warn", "fig0/ax0 line #e69f00"),
        ("fail", "fig1/ax0 9 x-axis tick labels"), ("fail", "fig1/ax0 9 y-axis tick labels")]


def test_symbol_glyph_key_is_judged_as_a_mark_not_text():
    assert "contrast" not in checks(lint("contrast_glyph.py"))


def test_text_inside_a_bubble_is_judged_against_the_bubble():
    assert "contrast" not in checks(lint("text_on_marker.py"), "fail")


def test_text_on_area_fails_straddles_and_faint_inside_but_allows_own_layer_cells_and_boxes():
    res = lint("text_on_area.py")
    hits = [(f["where"], f["detail"].split(" (")[0].split(" at ")[0]) for f in res["findings"]
            if f["check"] == "text-on-area"]
    assert hits == [("fig0/ax0 text 'Straddles'", "text straddles an edge between fills"),
                    ("fig0/ax0 text 'Faint'", "text inside a #e69f00 fill"),
                    ("fig1/ax0 text 'Across many cells'", "text straddles an edge between fills")]
    assert "contrast" not in checks(res)  # texts on fills are judged once, by text-on-area


def test_invisible_arrow_fails_unstyled_zero_width_and_background_colored_arrows():
    hits = [(f["severity"], f["where"]) for f in lint("arrow_invisible.py")["findings"] if f["check"] == "invisible-arrow"]
    assert hits == [("fail", "fig0/ax0 annotation 'Default'"), ("fail", "fig0/ax0 annotation 'Colored, no width'"),
                    ("fail", "fig0/ax0 annotation 'Width, white'")]


def test_invisible_arrow_passes_stroked_filled_and_arrowless_annotations():
    for name in ("arrow_visible.py", "arrow_through_text.py"):
        assert "invisible-arrow" not in checks(lint(name))
