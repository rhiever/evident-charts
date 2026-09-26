import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# Three series end within a label height of each other: their labels spread apart with leaders.
fig, ax = ev.figure("blog")
years = np.arange(2015, 2026)
ends = {"All items": 3.1, "Food": 3.16, "Core": 3.04, "Energy": -2.4}
col = {"All items": ev.DARK, "Food": ev.GRAY, "Core": ev.GRAY, "Energy": ev.ACCENT}
for name, end in ends.items():
    ax.plot(years, np.linspace(1, end, len(years)), color=col[name], label=name)
ev.label_lines(ax, highlight="Energy", reference="All items", values="{:.1f}%")
ax.set_ylabel("Price change (%)")
ev.titles(fig, "Energy prices fell while other prices kept rising", subtitle="Annual change, percent",
          source="Source: illustrative data")
ev.save(fig, "out.png")
