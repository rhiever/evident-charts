import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# Four context lines share one group label; the provisional last point gets a boxed callout without a second dot.
fig, ax = ev.figure("blog")
years = np.arange(2015, 2026)
for i, name in enumerate(["Lakes", "Hills", "Coast", "Plains"]):
    ax.plot(years, np.linspace(40, 44 + i, len(years)), color=ev.GRAY, label=name)
ax.plot(years, np.linspace(40, 62, len(years)), color=ev.ACCENT, label="Valley")
ev.provisional(ax)
ev.label_lines(ax, highlight="Valley", group={"Other regions": ["Lakes", "Hills", "Coast", "Plains"]})
ev.callout(ax, 2025, 62, "2025 provisional", where="above_left", marker=False, box=True)
ax.set_ylabel("Library visits per 100 residents")
ev.titles(fig, "Valley library visits pulled away from every other region", subtitle="Visits per 100 residents, 2015-2025",
          source="Source: illustrative data")
ev.save(fig, "out.png")
