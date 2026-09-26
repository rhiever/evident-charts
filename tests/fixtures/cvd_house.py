import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# House palette charts: no cvd or contrast findings.
years = np.arange(2016, 2024)
fig, ax = ev.figure("blog")  # four default slots, legend only
for k, col in enumerate(ev.OKABE_ITO[:4]):
    ax.plot(years, np.linspace(1 + k, 4 + 2 * k, len(years)), color=col, label=f"Region {k + 1}")
ax.legend(frameon=False)
ax.set_ylabel("Output (TWh)")
ev.titles(fig, "Every region grew", subtitle="Output, TWh", source="Source: illustrative data")

fig1, ax1 = ev.figure("blog")  # grouped bars in the first three slots
x = np.arange(4)
for k, col in enumerate(ev.OKABE_ITO[:3]):
    ax1.bar(x + (k - 1) * 0.25, [3 + k, 4, 5 - k, 6], width=0.25, color=col, label=f"Plan {k + 1}")
ax1.legend(frameon=False)
ax1.set_xticks(x, ["North", "South", "East", "West"])
ax1.set_ylabel("Sites")
ev.titles(fig1, "West has the most sites under every plan", subtitle="Sites", source="Source: illustrative data")

fig2, ax2 = ev.figure("blog")  # scatter groups, and accent over gray
rng = np.random.default_rng(3)
for k, col in enumerate(ev.OKABE_ITO[:3]):
    ax2.scatter(rng.normal(k, 0.3, 20), rng.normal(k, 0.3, 20), color=col, s=30, label=f"Group {k + 1}")
ax2.plot([0, 2], [0, 2], color=ev.GRAY)
ax2.legend(frameon=False)
ax2.set_xlabel("Score A")
ax2.set_ylabel("Score B")
ev.titles(fig2, "Scores rise together", subtitle="Scores", source="Source: illustrative data")
for f in (fig, fig1, fig2):
    ev.save(f, "out.png")
