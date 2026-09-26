"""Demo of scripts/evident.py: highlighted line chart, sorted bar with value labels, dumbbell; blog and social.

Data are illustrative (seeded), not real statistics.
Run: python examples/demo_evident.py  -> PNGs in examples/output/
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SKILL = next(p for p in (HERE.parent / "skills").iterdir() if (p / "scripts" / "evident.py").exists())
sys.path.insert(0, str(SKILL / "scripts"))
import evident as ev  # noqa: E402

OUT = HERE / "output"
SOURCE = "Source: illustrative data generated for this demo"

# --- data (all numbers used in text are computed below, never typed in) ---
rng = np.random.default_rng(7)
years = np.arange(2000, 2026)
peers = ["Japan", "France", "Canada", "UK", "Germany"]
life = {c: 77.5 + i * .7 + .18 * (years - 2000) + rng.normal(0, .15, len(years)) for i, c in enumerate(peers)}
life["US"] = (76.6 + .12 * (years - 2000) - np.where(years >= 2020, 1.6, 0) + np.where(years >= 2023, .9, 0)
              + rng.normal(0, .08, len(years)))
gap = np.mean([life[c][-1] for c in peers]) - life["US"][-1]

leave = {"Denmark": 8.1, "Norway": 7.8, "Sweden": 7.6, "Finland": 7.4, "Netherlands": 7.0,
         "Germany": 6.5, "Canada": 6.2, "United States": 4.3}

metros = ["San Jose", "Los Angeles", "Miami", "Boston", "Denver", "Chicago", "Houston"]
ratio_2000 = np.array([6.1, 5.2, 3.9, 4.6, 3.8, 3.7, 2.9])
ratio_2024 = np.array([11.8, 10.9, 8.4, 7.6, 6.9, 4.8, 4.1])


def line_chart(dest):
    fig, ax = ev.figure(dest)
    col = ev.colors(life, highlight="US")
    for name, y in life.items():
        ax.plot(years, y, color=col[name], label=name,
                lw=ev.size("accent_line") if name == "US" else ev.size("line"))
    ev.label_lines(ax, highlight="US")
    ax.set_xlim(2000, 2025)
    ax.set_xticks([2000, 2010, 2020])
    ax.set_ylim(75.6, None)
    i20 = int(np.argmax(years == 2020))
    drop = life["US"][i20 - 1] - life["US"][i20]
    ax.annotate(f"Covid: -{drop:.1f} years in 2020", xy=(2020, life["US"][i20]),
                xytext=(2012, 76.3), ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=ev.DARK, lw=ev.size("grid"), shrinkB=4))
    ev.titles(fig, "Americans now die years sooner than people in peer countries",
              subtitle=f"Life expectancy at birth, years. 2025 gap to peer average: {gap:.1f} years",
              source=SOURCE)
    return ev.save(fig, OUT / f"line_{dest}.png")


def bar_chart(dest):
    fig, ax = ev.figure(dest)
    names = sorted(leave, key=leave.get)
    col = ev.colors(names, highlight="United States")
    bars = ax.barh(names, [leave[n] for n in names], color=[col[n] for n in names], height=.68)
    ev.value_labels(ax, bars, fmt="{:.1f}")
    ev.titles(fig, "The US trails every peer country on paid family leave",
              subtitle="Paid leave generosity index, 0-10", source=SOURCE)
    return ev.save(fig, OUT / f"bar_{dest}.png")


def dumbbell(dest):
    fig, ax = ev.figure(dest)
    y = np.arange(len(metros))[::-1]
    ax.hlines(y, ratio_2000, ratio_2024, color=ev.GRAY, lw=ev.size("line") * 1.4, capstyle="butt", zorder=1)
    ax.plot(ratio_2000, y, "o", color=ev.GRAY, ms=ev.size("marker"), mec="white", mew=0, zorder=2)
    ax.plot(ratio_2024, y, "o", color=ev.ACCENT, ms=ev.size("marker"), mec="white", mew=0, zorder=3)
    ax.set_yticks(y, metros)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlim(0, 12.6)
    ax.set_xlabel("Years of income to buy the median home")
    ax.set_ylim(-.6, len(metros) - .2)
    top = y[0]
    for x, lab, c in ((ratio_2000[0], "2000", ev.MUTED), (ratio_2024[0], "2024", ev.ACCENT_TEXT)):
        ax.annotate(lab, xy=(x, top), xytext=(0, ev.size("marker") * .9), textcoords="offset points",
                    ha="center", va="bottom", fontsize=ev.size("label"), color=c, weight="bold")
    mult = np.median(ratio_2024 / ratio_2000)
    ev.titles(fig, f"Homes now cost {mult:.1f}x as many years of income as in 2000",
              subtitle=f"Median home price / median household income, by metro. {mult:.1f}x is the median metro",
              source=SOURCE)
    return ev.save(fig, OUT / f"dumbbell_{dest}.png")


if __name__ == "__main__":
    for dest in ("blog", "social"):
        for make in (line_chart, bar_chart, dumbbell):
            make(dest)
