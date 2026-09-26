import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# A labeled average line crosses the value-labeled bars without running through any value label.
fig, ax = ev.figure("blog")
shops = ["North", "East", "South", "West", "Central"]
sales = [5.1, 4.6, 4.1, 3.9, 2.7]
bars = ax.barh(shops[::-1], sales[::-1], color=[ev.GRAY] * 4 + [ev.ACCENT])
ev.value_labels(ax, bars, fmt="{:.1f}")
ev.reference(ax, 4.1, "Average 4.1", axis="x")
ev.titles(fig, "North sells a quarter more than the average shop", subtitle="Weekly sales, thousand units, 2025",
          source="Source: illustrative data")
ev.save(fig, "out.png")
