import datetime as dt

import numpy as np

from _clean import new

regions = ["North", "South", "East", "West"]
edge = dict(edgecolor="white", linewidth=0.8)
# Stacked bars, pie, and stackplot with a thin white edge at the call site.
fig, ax = new()
ax.bar(regions, [3, 4, 2, 5], color="#1f77b4", **edge)
ax.bar(regions, [2, 3, 4, 1], bottom=[3, 4, 2, 5], color="#aec7e8", **edge)
ax.set_ylabel("Sales ($M)")
fig1, ax1 = new()
ax1.pie([45, 30, 25], colors=["#1f77b4", "#6baed6", "#c6dbef"], labels=["Rent", "Food", "Other"], wedgeprops=edge)
fig2, ax2 = new()
x = np.arange(10)
ax2.stackplot(x, 1 + 0.1 * x, 2 + 0.05 * x, colors=["#1f77b4", "#aec7e8"], **edge)
ax2.set_ylabel("Users (M)")
# Histogram: touching bins of one color.
fig3, ax3 = new()
ax3.hist(np.random.default_rng(0).normal(size=500), bins=20, color="#1f77b4")
ax3.set_ylabel("Count")
# Grouped bars with gaps between them.
fig4, ax4 = new()
pos = np.arange(4)
ax4.bar(pos - 0.2, [3, 4, 2, 5], width=0.35, color="#1f77b4")
ax4.bar(pos + 0.2, [2, 3, 4, 1], width=0.35, color="#aec7e8")
ax4.set_xticks(pos, regions)
ax4.set_ylabel("Sales ($M)")
# 365 touching daily bars in two colors: too narrow for an edge, which would erase them.
fig5, ax5 = new()
days = [dt.date(2023, 1, 1) + dt.timedelta(days=k) for k in range(365)]
vals = np.sin(np.arange(365) / 20)
ax5.bar(days, np.abs(vals), width=1, color=np.where(vals > 0, "#1f77b4", "#d62728"))
ax5.set_ylabel("Anomaly (C)")
# A confidence band around a line, and a lighter band over a darker one: context, not stacked segments.
fig6, ax6 = new()
ax6.fill_between(x, x - 1, x + 1, color="#1f77b4", alpha=0.25, linewidth=0)
ax6.fill_between(x, x - 0.5, x + 0.5, color="#1f77b4", alpha=0.25, linewidth=0)
ax6.plot(x, x, color="#1f77b4")
ax6.set_ylabel("Score")
# Heatmap cells form one surface.
fig7, ax7 = new()
ax7.pcolormesh(np.random.default_rng(1).random((5, 5)), cmap="Blues")
ax7.imshow(np.random.default_rng(2).random((5, 5)), cmap="Blues", extent=(5, 10, 0, 5))
# Violins.
fig8, ax8 = new()
ax8.violinplot([np.random.default_rng(k).normal(size=100) for k in range(3)])
ax8.set_ylabel("Score")
for i, f in enumerate([fig, fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8]):
    f.savefig(f"{i}.png")
