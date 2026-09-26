import numpy as np

from _clean import new

# Value labels with the value axis hidden: one readout.
fig, ax = new("Store B sold the most units")
bars = ax.barh(["A", "B", "C", "D"], [80, 95, 85, 60], color="C0")
ax.bar_label(bars, labels=[f"{v}k" for v in (80, 95, 85, 60)], padding=4, fontsize=12)
ax.xaxis.set_visible(False)
ax.spines["bottom"].set_visible(False)
fig.text(0.02, 0.02, "Source: Acme Corp., 2024 annual report", fontsize=11)
# Many bars: keep the axis and annotate only the headline value.
fig2, ax2 = new("Sales peaked in 2021")
vals = [3.1, 3.4, 4.0, 4.2, 5.8, 6.3, 5.9, 5.1, 4.8, 4.6, 4.4, 4.5]
ax2.bar(np.arange(2012, 2024), vals, color="C0")
ax2.text(2017, 6.45, "6.3", ha="center", fontsize=12)
ax2.set_ylabel("Sales ($M)")
fig2.text(0.02, 0.02, "Source: Acme Corp., annual reports", fontsize=11)
fig.savefig("a.png")
fig2.savefig("b.png")
