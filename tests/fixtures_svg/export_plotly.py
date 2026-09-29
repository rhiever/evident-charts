"""Regenerate the Plotly fixtures: python tests/fixtures_svg/export_plotly.py (needs plotly and kaleido >= 1).

Writes <name>.svg and <name>.json (full_figure_for_development, which resolves axis ranges) next to this file.
"""
from pathlib import Path

import plotly.graph_objects as go

HERE = Path(__file__).resolve().parent
FONT = "Arial, Helvetica, sans-serif"


def clean():
    """Two direct-labeled lines in text-safe colors, a takeaway title, and a source line."""
    q = ["Q1", "Q2", "Q3", "Q4"]
    fig = go.Figure()
    for name, ys, col, text in [("West", [12, 14, 15, 17], "#0072B2", "#0072B2"),
                                ("East", [9, 10, 10, 11], "#D55E00", "#C15500")]:
        fig.add_scatter(x=q, y=ys, mode="lines", line=dict(color=col, width=3), name=name)
        fig.add_annotation(x="Q4", y=ys[-1], text=name, xanchor="left", xshift=8, showarrow=False,
                           font=dict(color=text, size=16))
    fig.add_annotation(text="Source: Company filings", xref="paper", yref="paper", x=0, y=0, yshift=-60,
                       xanchor="left", yanchor="top", showarrow=False, font=dict(size=13, color="#767676"))
    fig.update_layout(width=800, height=600, showlegend=False, template="simple_white", font=dict(family=FONT, size=15),
                      title=dict(text="West leads every quarter<br><sup>Sales, $ millions, 2025</sup>", font_size=24),
                      margin=dict(l=80, r=100, t=110, b=100),
                      yaxis=dict(title="$ millions", showgrid=True, range=[0, 20]))
    return fig


def bad():
    """Truncated bars, a twin axis, labels across bars and the line, red/green bars, a legend over tick labels."""
    regions = ["North", "South", "East", "West"]
    fig = go.Figure()
    fig.add_bar(x=regions, y=[92, 95, 97, 99], marker_color=["#D62728", "#2CA02C", "#D62728", "#2CA02C"], name="Sales")
    fig.add_scatter(x=regions, y=[0.12, 0.18, 0.15, 0.21], yaxis="y2", line_color="#999999", name="Margin")
    for r, y in zip(regions, [92, 95, 97, 99]):
        fig.add_annotation(x=r, y=y, text="Margin rising fast in region", showarrow=False, font_size=14, yshift=10)
    fig.update_layout(width=500, height=350, title=dict(text="Sales by region", font_size=9),
                      font=dict(family=FONT, size=9),
                      yaxis=dict(range=[90, 100]), yaxis2=dict(overlaying="y", side="right"))
    return fig


def lines_bad():
    """Red/green lines told apart by a legend alone, an unlabeled log axis, faint and clipped notes."""
    x = list(range(2015, 2025))
    fig = go.Figure()
    fig.add_scatter(x=x, y=[10 * 1.5 ** i for i in range(10)], mode="lines", line=dict(color="#D62728", width=3),
                    name="Solar")
    fig.add_scatter(x=x, y=[30 * 1.2 ** i for i in range(10)], mode="lines", line=dict(color="#2CA02C", width=3),
                    name="Wind")
    fig.add_annotation(text="Source: Energy agency", xref="paper", yref="paper", x=0, y=-0.15, xanchor="left",
                       showarrow=False, font=dict(size=13, color="#BBBBBB"))
    fig.add_annotation(text="Solar overtakes wind in 2021 and keeps going", xref="paper", yref="paper", x=0.97, y=0.1,
                       xanchor="left", showarrow=False, font=dict(size=15, color="#333333"))
    fig.update_layout(width=800, height=600, template="simple_white", font=dict(family=FONT, size=15),
                      title=dict(text="Solar grew faster than wind", font_size=24), margin=dict(r=60),
                      yaxis=dict(type="log", title="Capacity (GW)"))
    return fig


for name, fig in [("plotly_clean", clean()), ("plotly_bad", bad()), ("plotly_lines_bad", lines_bad())]:
    fig.write_image(HERE / f"{name}.svg")
    (HERE / f"{name}.json").write_text(fig.full_figure_for_development(warn=False).to_json())
