"""Tests for skills/evident-charts/scripts/evident.py helpers."""
import sys
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "evident-charts" / "scripts"))

import check_chart  # noqa: E402
import evident as ev  # noqa: E402


@pytest.fixture
def blog():
    with matplotlib.rc_context():
        fig, ax = ev.figure("blog")
        yield fig, ax
        plt.close(fig)


def test_label_lines_leaders_values_and_reference(blog):
    fig, ax = blog
    x = np.arange(10)
    for name, end in {"All items": 3.1, "Food": 3.16, "Core": 3.04, "Energy": -2.4}.items():
        ax.plot(x, np.linspace(1, end, 10), color=ev.ACCENT if name == "Energy" else ev.GRAY, label=name)
    texts = {t.get_text().split()[0]: t for t in
             ev.label_lines(ax, highlight="Energy", reference="All items", values="{:.1f}%")}
    fig.canvas.draw()
    assert texts["Energy"].get_text() == "Energy −2.4%" and texts["Food"].get_text() == "Food 3.2%"
    assert texts["All"].get_color() == ev.DARK and texts["All"].get_weight() == "bold"
    assert texts["Energy"].get_color() == ev.ACCENT_TEXT and texts["Food"].get_weight() == "normal"
    leaders = {k: t.arrow_patch.get_visible() for k, t in texts.items()}
    assert leaders == {"All": False, "Food": True, "Core": True, "Energy": False}
    assert texts["Food"].xyann[1] > 0 > texts["Core"].xyann[1] and texts["Energy"].xyann[0] > ev.size("label", fig)


def test_label_lines_no_leaders_when_labels_stay_put(blog):
    fig, ax = blog
    ax.plot([0, 1], [0, 1], label="A")
    ax.plot([0, 1], [0, 10], label="B")
    texts = ev.label_lines(ax, values=True)
    assert [t.get_text() for t in texts] == ["A 1.0", "B 10.0"]
    assert not any(t.arrow_patch.get_visible() for t in texts)


def test_strip_stacks_equal_values_symmetrically_within_the_row(blog):
    fig, ax = blog
    groups = ["a"] * 25 + ["b"] * 3
    values = [5.0] * 20 + [1, 2, 3, 4, 6] + [2, 2, 9]
    scs = ev.strip(ax, groups, values, colors={"a": ev.ACCENT, "b": ev.GRAY})
    ev.titles(fig, "Group a clusters at five")
    off_a, off_b = (np.asarray(sc.get_offsets()) for sc in scs)
    stack = off_a[off_a[:, 0] == 5, 1]
    assert np.isclose(stack.mean(), 1) and stack.max() - stack.min() <= .85  # row a sits at y=1 (on top)
    pair = np.sort(off_b[off_b[:, 0] == 2, 1])
    assert pair[0] == pytest.approx(-pair[1]) and pair[1] > 0 and off_b[off_b[:, 0] == 9, 1] == pytest.approx(0)
    assert [t.get_text() for t in ax.get_yticklabels()] == ["b", "a"]
    assert matplotlib.colors.to_hex(scs[0].get_facecolor()[0]) == ev.ACCENT.lower()
    assert [ln.get_xdata()[0] for ln in ax.lines if ln.get_label() == "_median"] == [5.0, 2.0]


def test_provisional_marks_open_point_with_dashed_connector(blog):
    fig, ax = blog
    ax.plot([2020, 2021, 2022], [1, 2, 3], color=ev.ALT)
    t = ev.provisional(ax, 2023, 3.4, 2022, 3, label="Preliminary")
    conn, dot = ax.lines[-2:]
    assert conn.get_linestyle() == "--" and list(conn.get_xdata()) == [2022, 2023]
    assert dot.get_markerfacecolor() == "white" and dot.get_markeredgecolor() == ev.ALT
    assert t.get_text() == "Preliminary" and t.get_ha() == "left"
    assert ev.provisional(ax, 2024, 3.6) is None


def test_value_labels_warn_threshold_and_opt_out(blog):
    fig, ax = blog
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ev.value_labels(ax, ax.bar(range(12), range(1, 13)))
        ev.value_labels(ax, ax.bar(range(13), range(1, 14)), warn=False)
    with pytest.warns(UserWarning, match="more than 12 bars"):
        ev.value_labels(ax, ax.bar(range(13), range(1, 14)))


@pytest.mark.parametrize("title,frac,first", [
    ("Pay rose fastest in the U.S. South and slowest in New England", .65, "Pay rose fastest in the U.S. South"),
    ("Coal use fell in rich countries, e.g. Germany and Britain, but kept rising in Asia", .62,
     "Coal use fell in rich countries, e.g. Germany"),
])
def test_title_wrap_ignores_abbreviation_periods(blog, title, frac, first):
    fig, _ = blog
    t, r = fig.text(0, 0, "", fontsize=ev.size("title", fig)), fig.canvas.get_renderer()
    assert ev._wrap2(t, title, ev._width(t, title, r) * frac, r).split("\n")[0] == first


def test_titles_stats_row_sits_under_subtitle_and_is_not_the_title():
    with matplotlib.rc_context():
        fig, ax = ev.figure("social")
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_ylabel("Sales ($M)")
        texts = ev.titles(fig, "Sales grew ninefold in two years", subtitle="Sales, $M",
                          stats=[("17.1%", "Q2 2026"), ("27x", "growth", ev.ACCENT)])
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        title, sub, v1, c1, v2, c2 = texts
        assert v1.get_fontsize() == pytest.approx(1.5 * title.get_fontsize())
        assert v1.get_window_extent(r).y1 < sub.get_window_extent(r).y0
        assert c1.get_window_extent(r).y1 < v1.get_window_extent(r).y0
        assert v2.get_window_extent(r).x0 > c1.get_window_extent(r).x1 and v2.get_color() == ev.ACCENT_TEXT
        assert ax.get_window_extent(r).y1 < c1.get_window_extent(r).y0
        ctx = check_chart.Ctx(fig, 0, "social", None)
        assert check_chart.main_title(ctx).label == "Sales grew ninefold in two years"
        plt.close(fig)


def test_style_uses_true_minus_sign():
    with matplotlib.rc_context({"axes.unicode_minus": False}):
        fig, ax = ev.figure("blog")
        ax.plot([0, 1], [-5, 5])
        fig.canvas.draw()
        assert "\u22124" in [t.get_text() for t in ax.get_yticklabels()]
        plt.close(fig)


# --- v0.3: type scale, font, layout, escaping, new helpers --------------------------------------

import json  # noqa: E402
import re  # noqa: E402
import logging  # noqa: E402

from matplotlib import font_manager  # noqa: E402

PRESETS = json.loads((ev.ASSETS / "presets.json").read_text())
SAMPLE = ("Rents rose faster than wages in every region except the Midwest, where both grew at roughly the same pace "
          "through the whole of the last decade, while prices for groceries, energy and insurance climbed even faster "
          "than rents did in the largest coastal metros")


@pytest.mark.parametrize("dest", sorted(ev.PRESETS))
def test_every_type_role_meets_the_minimum_pixel_size(dest):
    p = ev.PRESETS[dest]
    for role, pct in p["type"].items():
        pt = pct / 100 * p["width_in"] * 72
        assert pt * p["display_px"] / (p["width_in"] * 72) >= p["min_text_px"] - 1e-9, role


def test_type_scales_are_the_approved_ones():
    approved = {"title": 4.6, "subtitle": 3.0, "label": 2.8, "annotation": 2.9, "source": 2.2}
    assert ev.PRESETS["social"]["type"] == approved == ev.PRESETS["social_portrait"]["type"]
    assert ev.PRESETS["blog"]["type"] == {"title": 3.2, "subtitle": 2.2, "label": 1.9, "annotation": 2.0, "source": 1.6}
    assert ev.PRESETS["slide"]["type"] == {"title": 3.75, "subtitle": 2.5, "label": 2.1, "annotation": 2.3, "source": 1.6}
    assert ev.PRESETS["report"]["type"] == {"title": 2.9, "subtitle": 2.35, "label": 2.0, "annotation": 2.1, "source": 2.0}
    assert ev.PRESETS["mobile"]["type"] == {"title": 5.6, "subtitle": 3.9, "label": 3.6, "annotation": 3.6, "source": 3.4}
    assert all("subtitle_chars_2_lines" in p and "title_chars_2_lines" in p for p in ev.PRESETS.values())


def test_font_stack_prefers_helvetica_neue_and_resolves_quietly(caplog):
    with matplotlib.rc_context(), caplog.at_level(logging.WARNING, logger="matplotlib.font_manager"):
        fig, ax = ev.figure("blog")
        stack = ["Helvetica Neue", "Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"]
        assert plt.rcParams["font.sans-serif"][:5] == stack
        installed = {f.name for f in font_manager.fontManager.ttflist}
        assert plt.rcParams["font.family"] == [f for f in stack if f in installed or f == "DejaVu Sans"]
        font_manager.findfont(font_manager.FontProperties(family="sans-serif", weight="bold"))
        ev.titles(fig, "Sales doubled after the launch", source="Source: X")
        fig.canvas.draw()
        plt.close(fig)
    assert not [r for r in caplog.records if "findfont" in r.getMessage()]


def test_fits_title_matches_titles_warning():
    ok, over = ev.fits_title("Sales doubled after the launch", "blog")
    assert (ok, over) == (True, 0)
    ok, over = ev.fits_title(SAMPLE, "blog")
    assert not ok and over > 0
    assert ev.fits_title(SAMPLE[:len(SAMPLE) - over].rsplit(" ", 1)[0], "blog")[0]
    with matplotlib.rc_context():
        fig, ax = ev.figure("blog")
        with pytest.warns(UserWarning, match=f"cut about {over} characters"):
            ev.titles(fig, SAMPLE)
        assert ev.fits_title(SAMPLE, fig=fig) == (False, over)
        plt.close(fig)
    assert ev.fits_subtitle(SAMPLE[:150], "blog") == (True, 0) and not ev.fits_subtitle(SAMPLE[:150], "mobile")[0]


@pytest.mark.parametrize("dest", sorted(ev.PRESETS))
def test_char_budgets_agree_with_the_measured_title_block(dest):
    with plt.style.context(ev.STYLE):
        resolved = font_manager.findfont(font_manager.FontProperties(family=["sans-serif"]))
    if "DejaVu" in resolved:
        pytest.skip("budgets are calibrated on Helvetica/Arial metrics")
    p = ev.PRESETS[dest]
    for role, fits in (("title", ev.fits_title), ("subtitle", ev.fits_subtitle)):
        budget = p[f"{role}_chars_2_lines"]
        text = (SAMPLE + " " + SAMPLE)[:budget].rsplit(" ", 1)[0]
        assert fits(text, dest)[0], (role, budget)
        assert not fits((SAMPLE + " " + SAMPLE)[:int(budget * 1.25)], dest)[0], (role, budget)


def test_dollar_signs_stay_literal_everywhere(blog):
    fig, ax = blog
    bars = ax.bar(["a", "b"], [5, 10])
    texts = ev.value_labels(ax, bars, fmt="${:,.0f}")
    ax.plot([0, 1], [1, 2], label="Rent $")
    lines = ev.label_lines(ax)
    head = ev.titles(fig, "Rent costs $5 more, food $10 more", subtitle="In $", source="Source: $ data")
    fig.canvas.draw()
    for t in texts + lines + head:
        assert "\\$" in t.get_text() and not t._preprocess_math(t.get_text())[1], t.get_text()
    assert head[0]._preprocess_math(head[0].get_text())[0] == "Rent costs $5 more, food $10 more"


def test_value_labels_leave_category_ticks_plain_unless_emphasized(blog):
    fig, ax = blog
    names = ["a", "b", "c"]
    col = ev.colors(names, highlight="b")
    bars = ax.barh(names, [1, 2, 3], color=[col[n] for n in names])
    texts = ev.value_labels(ax, bars)
    fig.canvas.draw()
    ticks = {t.get_text(): t for t in ax.get_yticklabels()}
    assert ticks["b"].get_weight() == "normal" and ticks["b"].get_color() == ev.DARK
    assert texts[1].get_weight() == "bold" and texts[1].get_color() == ev.ACCENT_TEXT
    fig2, ax2 = ev.figure("blog")
    ev.value_labels(ax2, ax2.barh(names, [1, 2, 3], color=[col[n] for n in names]), emphasize=True)
    ticks = {t.get_text(): t for t in ax2.get_yticklabels()}
    assert ticks["b"].get_weight() == "bold" and ticks["b"].get_color() == ev.ACCENT_TEXT
    assert ticks["a"].get_weight() == "normal"
    plt.close(fig2)


def test_shared_y_panels_keep_room_own_styles_and_user_limits():
    names = ["A very long category name number one", "Another rather long category", "Short", "United States"]
    with matplotlib.rc_context():
        fig, (a1, a2) = ev.figure("blog", 1, 2, sharey=True)
        c1, c2 = ev.colors(names, highlight="Short"), ev.colors(names, highlight="United States")
        ev.value_labels(a1, a1.barh(names, [3, 5, 2, 4], color=[c1[n] for n in names]), emphasize=True)
        ev.value_labels(a2, a2.barh(names, [30, 50, 20, 40], color=[c2[n] for n in names]), emphasize=True)
        a2.set_xlim(0, 100)
        ev.titles(fig, "Short trails on one measure and leads on another", source="Source: X")
        ev.save(fig, fig_path := Path(__file__).parent / "_tmp_shared.png")
        fig_path.unlink()
        w1, w2 = a1.get_position().width, a2.get_position().width
        assert min(w1, w2) > .2 and abs(w1 - w2) < 1e-6
        assert a2.get_xlim() == (0, 100)
        bold = [t.get_text() for t in a1.get_yticklabels() if t.get_weight() == "bold"]
        assert bold == ["Short"]
        findings, _ = check_chart.lint_figure(fig, 0)
        assert "plot-area-tiny" not in {f.check for f in findings}
        plt.close(fig)


def test_shared_value_axis_fits_both_panels_labels():
    with matplotlib.rc_context():
        fig, (a1, a2) = ev.figure("blog", 2, 1, sharex=True)
        ev.value_labels(a1, a1.barh(["a", "b"], [10, 20]))
        ev.value_labels(a2, a2.barh(["c", "d"], [100, 5]))
        ev.titles(fig, "Panel two holds the largest value")
        r = fig.canvas.get_renderer()
        assert a1.get_xlim() == a2.get_xlim() and a1.get_xlim()[1] > 100
        for ax in (a1, a2):
            assert all(t.get_window_extent(r).x1 <= ax.get_window_extent(r).x1 + 1 for t in ax.texts)
        plt.close(fig)


def test_columns_sit_right_of_the_axes_and_follow_relayout(blog):
    fig, ax = blog
    names = ["Denmark", "Canada", "United States"]
    bars = ax.barh(names, [8.1, 6.2, 4.3], color=ev.GRAY)
    ev.value_labels(ax, bars, fmt="{:.1f}")
    texts = ev.columns(ax, names, [("Past year", [1.25, -0.5, 2.0], "{:+.1f}%"), ("vs 2019", [12, -3, 40], "{:+.0f}%")])
    ev.titles(fig, "The US trails its peers", source="Source: X")
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    box = ax.get_window_extent(r)
    assert [t.get_text() for t in texts[:4]] == ["Past year", "+1.2%", "−0.5%", "+2.0%"]
    assert texts[6].get_text() == "−3%"
    ext = [t.get_window_extent(r) for t in texts]
    assert all(e.x0 > box.x1 for e in ext) and ext[4].x0 > max(e.x1 for e in ext[:4])
    assert len({round(e.x1, 3) for e in ext[:4]}) == 1  # right-aligned column
    assert ext[0].y0 >= box.y1 and max(e.x1 for e in ext) <= fig.bbox.width
    row = ax.transData.transform((0, 2))[1]  # "United States" is the third category
    assert abs((ext[3].y0 + ext[3].y1) / 2 - row) < 2


def test_provisional_marks_every_series_and_label_lines_uses_full_data(blog):
    fig, ax = blog
    x = np.arange(2019, 2026)
    ax.plot(x, np.linspace(1, 4, 7), color=ev.ACCENT, label="US")
    ax.plot(x, np.linspace(2, 3, 7), color=ev.GRAY, label="Peers")
    assert ev.provisional(ax) is None
    us, peers = ax.lines[:2]
    assert us.get_xdata()[-1] == 2024 and peers.get_xdata()[-1] == 2024
    dashed = [ln for ln in ax.lines if ln.get_label() == "_provisional" and ln.get_linestyle() == "--"]
    dots = [ln for ln in ax.lines if ln.get_label() == "_provisional" and ln.get_marker() == "o"]
    assert len(dashed) == len(dots) == 2 and dots[0].get_markeredgecolor() == ev.ACCENT
    texts = ev.label_lines(ax, values="{:.1f}")
    assert [t.get_text() for t in texts] == ["US 4.0", "Peers 3.0"] and texts[0].xy[0] == 2025
    ev.provisional(ax)  # idempotent
    assert len([ln for ln in ax.lines if ln.get_label() == "_provisional"]) == 4


def test_provisional_single_point_extends_its_line_for_label_lines(blog):
    fig, ax = blog
    ax.plot([2020, 2021, 2022], [1, 2, 3], color=ev.ALT, label="Sales", lw=3)
    ev.provisional(ax, 2023, 3.4, 2022, 3)
    conn = [ln for ln in ax.lines if ln.get_label() == "_provisional"][0]
    assert conn.get_linewidth() == 3
    t = ev.label_lines(ax, values="{:.1f}")[0]
    assert t.get_text() == "Sales 3.4" and t.xy[0] == 2023


def test_side_by_side_top_aligns_images_of_different_aspect(tmp_path):
    import side_by_side
    wide, tall = tmp_path / "wide.png", tmp_path / "tall.png"
    plt.imsave(wide, np.zeros((10, 40, 3)))
    plt.imsave(tall, np.zeros((40, 20, 3)))
    fig = side_by_side.compose([wide, tall], ["Wide", "Tall"], width=3)
    tops = [ax.get_position().y1 for ax in fig.axes]
    assert abs(tops[0] - tops[1]) < 1e-9
    assert len({t.get_position()[1] for t in fig.texts}) == 1
    assert [round(ax.get_position().x0 - t.get_position()[0], 9) for ax, t in zip(fig.axes, fig.texts)] == [0, 0]
    plt.close(fig)


def test_theme_files_mirror_the_preset_type_scale():
    themes = ev.ASSETS / "themes"
    js, r = (themes / "evident_d3_tokens.js").read_text(), (themes / "theme_evident.R").read_text()
    roles = ("title", "subtitle", "label", "annotation", "source")
    for dest, p in ev.PRESETS.items():
        t = p["type"]
        want_js = "type: { " + ", ".join(f"{k}: {t[k]}" for k in roles) + " }"
        assert re.search(rf"\b{dest}: {{[^\n]*{re.escape(want_js)}", js), dest
        for key, names in (("strokes", ("line", "accent_line", "marker", "grid")), ("margins", ("left", "right", "top", "bottom"))):
            want = f"{key}: {{ " + ", ".join(f"{k}: {p[key][k]}" for k in names) + " }"
            assert re.search(rf"\b{dest}: {{[^\n]*\n\s*[^\n]*{re.escape(want)}", js), (dest, key)
        vec = re.search(rf"^\s*{dest}\s*= list\([^\n]*type = c\(([^)]*)\)", r, re.M).group(1)
        assert [float(v) for v in vec.split(",")] == [t[k] for k in roles], dest
    # blog-sized files: CSS, Plotly and Vega-Lite in px at 800 wide, the mplstyle in pt at 8 in wide
    b = ev.PRESETS["blog"]
    px = {k: round(v / 100 * 800, 2) for k, v in b["type"].items()}
    pt = {k: round(v / 100 * b["width_in"] * 72, 1) for k, v in b["type"].items()}
    css = (themes / "evident_d3.css").read_text()
    for cls, role in (("text", "label"), (".ev-title", "title"), (".ev-subtitle", "subtitle"),
                      (".ev-source", "source"), (".ev-annotation", "annotation")):
        assert re.search(rf"{re.escape(cls)}[^{{\n]*{{[^}}]*var\(--ev-{role}, {px[role]:g}px\)", css), role
    plotly = json.loads((themes / "evident_plotly.json").read_text())["layout"]
    assert (plotly["font"]["size"], plotly["title"]["font"]["size"], plotly["annotationdefaults"]["font"]["size"]) == (
        px["label"], px["title"], px["annotation"])
    vl = json.loads((themes / "evident_vegalite.json").read_text())["config"]
    assert (vl["axis"]["labelFontSize"], vl["title"]["fontSize"], vl["title"]["subtitleFontSize"], vl["text"]["fontSize"]) == (
        px["label"], px["title"], px["subtitle"], px["annotation"])
    style = matplotlib.rc_params_from_file(ev.STYLE, use_default_template=False)
    assert (style["figure.titlesize"], style["xtick.labelsize"], style["font.size"]) == (
        pt["title"], pt["label"], pt["annotation"])


# --- v0.4: shared accents, callout boxes, group labels, reference lines, stack caps, category rows ----------

def test_colors_returns_a_dict_and_can_share_one_accent():
    assert ev.colors(["a", "b", "c"], highlight=["a", "b"]) == {"a": ev.ACCENT, "b": ev.ALT, "c": ev.GRAY}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c = ev.colors(["a", "b", "c", "d"], highlight=["a", "b", "c"], one_accent=True)
    assert c == {"a": ev.ACCENT, "b": ev.ACCENT, "c": ev.ACCENT, "d": ev.GRAY}
    assert "dict name -> color" in ev.colors.__doc__


def test_callout_box_and_no_marker(blog):
    fig, ax = blog
    ax.plot([0, 1], [0, 1])
    n = len(ax.lines)
    t = ev.callout(ax, 1, 1, "Latest", marker=False, box=True)
    assert len(ax.lines) == n and check_chart.text_has_knockout(t)
    assert ev.callout(ax, 0, 0, "Start").get_bbox_patch() is None and len(ax.lines) == n + 1


def test_label_lines_group_gets_one_label_at_the_median_end(blog):
    fig, ax = blog
    for name, end in {"A": 1.0, "B": 2.0, "C": 6.0, "Story": 9.0}.items():
        ax.plot([0, 5], [0, end], color=ev.ACCENT if name == "Story" else ev.GRAY, label=name)
    texts = ev.label_lines(ax, highlight="Story", values=True, group={"Other groups": ["A", "B", "C"]})
    assert [t.get_text() for t in texts] == ["Story 9.0", "Other groups"]
    assert tuple(texts[1].xy) == (5, 2.0) and texts[1].get_color() == ev.MUTED


def test_reference_line_labels_its_end_and_gaps_crossed_value_labels(blog):
    fig, ax = blog
    bars = ax.bar(["a", "b", "c"], [3.0, 5.0, 8.0], color=ev.GRAY)
    labels = ev.value_labels(ax, bars, fmt="{:.1f}")
    t = ev.reference(ax, 5.3, "Average 5.3")
    ev.titles(fig, "c leads", source="Source: X")
    fig.canvas.draw()
    r, box = fig.canvas.get_renderer(), ax.get_window_extent()
    assert t.get_window_extent(r).x0 > box.x1  # label past the right end of the line
    ref = [ln for ln in ax.lines if ln.get_label() == "_reference"]
    assert len(ref) == 1 and ref[0].get_ydata()[0] == 5.3
    assert check_chart.text_has_knockout(labels[1]) and labels[0].get_bbox_patch() is None  # "5.0" sits on the line
    v = ev.reference(ax, 1, "Target", axis="x")
    fig.canvas.draw()
    assert v.get_window_extent(r).y0 > box.y1 - 1 and v.get_ha() == "center"


def test_strip_max_stack_keeps_dots_full_size_and_rows_inside(blog):
    fig, ax = blog
    groups, values = ["a"] * 40 + ["b"] * 4, [5.0] * 40 + [1, 2, 3, 4]
    capped = ev.strip(ax, groups, values, max_stack=4)
    plt.close(fig)
    with matplotlib.rc_context():
        fig2, ax2 = ev.figure("blog")
        free = ev.strip(ax2, groups, values)
        assert capped[0].get_sizes()[0] > 5 * free[0].get_sizes()[0]
        plt.close(fig2)
    ys = np.asarray(capped[0].get_offsets())[:, 1]
    assert np.isclose(ys.mean(), 1) and ys.max() - ys.min() <= .85


def test_columns_accept_category_names_on_tick_label_axes_and_callable_formats(blog):
    fig, ax = blog
    ev.strip(ax, ["x", "x", "y", "z"], [1, 2, 3, 4])  # numeric rows with category tick labels
    texts = ev.columns(ax, ["z", "y", "x"], [("n", [1, 1, 2], lambda v: f"{v} obs")])
    assert [t.get_text() for t in texts] == ["n", "1 obs", "1 obs", "2 obs"]
    assert [t.xy[1] for t in texts[1:]] == [0, 1, 2]
    ax2 = fig.add_axes([0, 0, .1, .1])
    ax2.barh(range(2), [1, 2])
    ax2.set_yticks(range(2), ["p", "q"])
    assert [t.xy[1] for t in ev.columns(ax2, ["q", "p"], [("v", [2, 1])])[1:]] == [1, 0]
    with pytest.raises(ValueError, match="not on the y axis"):
        ev.columns(ax2, ["missing"], [("v", [1])])


@pytest.mark.parametrize("dest", sorted(ev.PRESETS))
def test_preset_bar_rows_fit_without_tick_crowding(dest):
    with matplotlib.rc_context():
        fig, ax = ev.figure(dest)
        n = ev.PRESETS[dest]["bar_rows"]
        ax.barh([f"Category {i}" for i in range(n)], np.arange(n) + 1.0, color=ev.GRAY)
        ev.titles(fig, "A one-line takeaway title", subtitle="Measure, units, period", source="Source: X")
        fig.canvas.draw()
        c = check_chart.Ctx(fig, 0, dest, None)
        check_chart.check_tick_crowding(c)
        plt.close(fig)
    assert not c.findings
    assert ev.PRESETS[dest].get("fixed_height", False) == (dest in {"slide", "social", "social_portrait"})


def test_missing_glyphs_fall_back_to_dejavu_without_warnings(blog):
    fig, ax = blog
    ax.text(.5, .5, "Imports \u2192 exports \u2191 \u2713")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fig.canvas.draw()


def test_figure_height_and_rows_grow_the_canvas_except_fixed_height_presets():
    with matplotlib.rc_context():
        base = ev.PRESETS["blog"]["height_in"]
        fig, _ = ev.figure("blog", rows=ev.PRESETS["blog"]["bar_rows"] + 10)
        assert fig.get_figwidth() == ev.PRESETS["blog"]["width_in"] and fig.get_figheight() > base + 1
        fig2, _ = ev.figure("blog", height=9)
        assert fig2.get_figheight() == 9
        with pytest.warns(UserWarning, match="fixed height"):
            fig3, _ = ev.figure("social", rows=30)
        assert fig3.get_figheight() == ev.PRESETS["social"]["height_in"]
        plt.close("all")


def test_save_replaces_the_title_block_after_a_resize(tmp_path):
    with matplotlib.rc_context():
        fig, ax = ev.figure("blog")
        ax.plot([1, 2, 3], [1, 4, 9])
        title = ev.titles(fig, "Sales grew ninefold in two years", source="Source: X")[0]
        fig.set_size_inches(8, 9)
        ev.save(fig, tmp_path / "tall.png")
        r = fig.canvas.get_renderer()
        head = [t for t in fig.texts if t.get_text() == title.get_text()]
        top_gap = fig.bbox.height - head[0].get_window_extent(r).y1
        assert len(head) == 1 and top_gap < .08 * fig.bbox.width
        plt.close(fig)


def test_hero_stat_outranks_the_title_and_fits_the_width():
    with matplotlib.rc_context():
        fig, ax = ev.figure("social")
        ax.plot([1, 2, 3], [1, 4, 9])
        title, v, c = ev.titles(fig, "Spending on new plants keeps climbing", stats=[("+57%", "vs a year earlier")],
                                stats_size="hero")[:3]
        assert v.get_fontsize() >= 3 * title.get_fontsize()
        _, v2, _ = ev.titles(fig, "Spending keeps climbing", stats=[("+1,234,567,890%", "vs a year earlier")],
                             stats_size="hero")[:3]
        r = fig.canvas.get_renderer()
        assert v2.get_fontsize() < v.get_fontsize() and v2.get_window_extent(r).x1 <= fig.bbox.width
        plt.close(fig)


def test_provisional_warns_about_unlabeled_lines(blog):
    fig, ax = blog
    ax.plot([2020, 2021, 2022], [1, 2, 3])
    with pytest.warns(UserWarning, match="skipped 1 unlabeled line"):
        ev.provisional(ax)


@pytest.mark.parametrize("dest", ["blog", "mobile", "report"])
def test_rows_fit_under_a_two_line_title_block_without_tick_crowding(dest):
    with matplotlib.rc_context(), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        n = ev.PRESETS[dest]["bar_rows"] + 2
        fig, ax = ev.figure(dest, rows=n)
        ax.barh([f"Category {i}" for i in range(n)], np.arange(n) + 1.0, color=ev.GRAY)
        ev.value_labels(ax, ax.containers[0], warn=False)
        ev.titles(fig, "A takeaway title long enough that it has to wrap onto a second line here",
                  subtitle="Measure, units, geography, and period, long enough to wrap onto a second subtitle line",
                  source="Source: X", note="Note: Y")
        fig.canvas.draw()
        c = check_chart.Ctx(fig, 0, dest, None)
        check_chart.check_tick_crowding(c)
        plt.close(fig)
    assert not c.findings


def test_num_rounds_half_up_and_compacts():
    assert [ev.num(1)(v) for v in (28.45, 28.44, -0.04)] == ["28.5", "28.4", "0.0"]
    assert ev.num(1, compact=True)(12831) == "12.8k" and ev.num(compact=True, prefix="$")(2.5e9) == "$3bn"
    assert ev.num(1, suffix="%", sign=True)(3.25) == "+3.3%" and ev.num()(1234567) == "1,234,567"
    assert ev._num(ev.num(prefix="$"), -5) == "−$5"


def test_columns_color_cells_by_list_or_callable(blog):
    fig, ax = blog
    ax.barh(["a", "b"], [1, 2])
    t = ev.columns(ax, ["a", "b"], [("chg", [-1.25, 2.0], ev.num(1, sign=True), lambda v: ev.ACCENT if v < 0 else None),
                                   ("n", [10, 20], "{}", [ev.ALT, None])])
    assert [x.get_text() for x in t[1:3]] == ["−1.3", "+2.0"]
    assert matplotlib.colors.to_hex(t[1].get_color()) == ev.ACCENT_TEXT.lower()
    assert matplotlib.colors.to_hex(t[2].get_color()) == ev.DARK.lower()
    assert matplotlib.colors.to_hex(t[4].get_color()) == ev.text_color(ev.ALT)


def test_label_lines_two_line_puts_the_value_under_the_name(blog):
    fig, ax = blog
    ax.plot([0, 1], [1, 2], label="North")
    ax.plot([0, 1], [1, 8], label="South")
    texts = ev.label_lines(ax, values="{:.0f}", two_line=True)
    assert [t.get_text() for t in texts] == ["North\n2", "South\n8"]


def test_reference_label_can_sit_inside_the_plot_at_a_row(blog):
    fig, ax = blog
    ax.barh(["a", "b", "c"], [3, 5, 4], color=ev.GRAY)
    t = ev.reference(ax, 4.2, "Average 4.2", axis="x", at="c")
    assert t.xy == (4.2, 2) and t.get_ha() == "left" and t.get_bbox_patch() is not None
    t2 = ev.reference(ax, 1, "Target", at=0.5)
    assert t2.xy == (0.5, 1) and t2.get_va() == "bottom"


def test_hero_caption_wraps_to_the_canvas_width():
    with matplotlib.rc_context():
        fig, ax = ev.figure("social")
        ax.plot([1, 2, 3], [1, 4, 9])
        cap = ("A long one-line takeaway caption that would run far past the right edge of the square canvas if it "
               "were never wrapped")
        _, v, c = ev.titles(fig, "Solar power", stats=[("+57%", cap)], stats_size="hero")[:3]
        r = fig.canvas.get_renderer()
        assert "\n" in c.get_text() and c.get_window_extent(r).x1 <= fig.bbox.width * (1 - ev.PRESETS["social"]["margins"]["right"]) + 1
        plt.close(fig)


def test_titles_warn_when_the_title_block_squeezes_a_fixed_height_plot():
    long_title = "Texas and Arizona added a third of new US utility-scale solar capacity so far in 2026"
    long_sub = ("Solar capacity online January to August 2026, MW (share of the US total). The other 28 states "
                "added the remaining third")
    with matplotlib.rc_context():
        fig, ax = ev.figure("slide")
        ax.barh([f"State {i}" for i in range(8)], np.arange(8, 0, -1.0))
        ev.value_labels(ax, ax.containers[0])
        with pytest.warns(UserWarning, match=r"plot area is [\d.]+:1, wider than 3.5:1 on the fixed-height slide"):
            ev.titles(fig, long_title, subtitle=long_sub, source="Source: X")
        assert ev.plot_aspect(fig)[2] == "wide"
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ev.titles(fig, "Texas and Arizona led US solar in 2026", subtitle="Capacity online, MW", source="Source: X")
            assert ev.plot_aspect(fig)[2] is None
            ev.titles(fig, None, source="Source: X")  # title set in the slide's placeholder instead
            ev.titles(fig, "Texas and Arizona led US solar in 2026", subtitle="Capacity online, MW",
                      stats=[("33%", "Texas and Arizona")], source="Source: X")  # a number card's visual stays small
        assert ev.plot_aspect(fig)[2] == "wide"
        plt.close(fig)


def test_tall_plots_warn_except_row_charts():
    with matplotlib.rc_context():
        fig, ax = ev.figure("blog", height=20)
        ax.plot([1, 2, 3], [1, 4, 9])
        with pytest.warns(UserWarning, match=r"plot area is 1:[\d.]+, taller than 1:2"):
            ev.titles(fig, "Sales grew ninefold in two years", source="Source: X")
        fig2, ax2 = ev.figure("blog", rows=60)
        ax2.barh([f"Category {i}" for i in range(60)], np.arange(60) + 1.0)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ev.titles(fig2, "Category 59 leads all sixty", source="Source: X")
        assert ev.plot_aspect(fig2)[1] < .5 and ev.plot_aspect(fig2)[2] is None
        plt.close("all")


def test_fits_title_one_line_budget():
    long_title = "Texas and Arizona added a third of new US solar in 2026"
    assert ev.fits_title(long_title, "slide") == (True, 0)
    ok, over = ev.fits_title(long_title, "slide", lines=1)
    assert not ok and 0 < over < len(long_title)
    assert ev.fits_title(long_title[:len(long_title) - over].rsplit(" ", 1)[0], "slide", lines=1)[0]
    assert ev.fits_subtitle("Capacity online, MW", "slide", lines=1) == (True, 0)
