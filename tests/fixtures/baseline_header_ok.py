import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# The same grouped bars with each header beside the zero baseline, plus a reference line labeled beside it.
fig, ax = ev.figure("blog")
rows = [0, 1, 2, 4, 5, 6]
vals = [-9, -6, -3, 5, 8, 12]
bars = ax.barh(rows, vals, color=ev.GRAY)
ev.value_labels(ax, bars)
ax.set_yticks(rows, ["Item F", "Item E", "Item D", "Item C", "Item B", "Item A"])
for y, text in ((7, "Group 1: 60% of total"), (3, "Group 2: 40% of total")):
    ax.annotate(text, xy=(0, y), xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                fontsize=ev.size("label", fig), weight="bold", color=ev.DARK)
ax.set_ylim(-1.6, 7.6)
ev.reference(ax, 10, "Target 10", axis="x", at=-1)
ev.titles(fig, "Group 1 items gained while Group 2 items lost", subtitle="Change in units, 2020", source="Source: illustrative data")
ev.save(fig, "out.png")
