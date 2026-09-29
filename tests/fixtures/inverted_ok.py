import numpy as np

from _clean import new

# Category order on horizontal bars: the inverted axis holds categories, not values.
fig, ax = new("Store B sold the most units")
ax.barh(["B", "C", "A"], [95, 85, 80], color="C0")
ax.invert_yaxis()
ax.set_xlabel("Units sold (k)")
fig.text(0.02, 0.02, "Source: Acme Corp., 2024 annual report", fontsize=11)
# Ranks may run 1 at the top when the axis says so.
fig2, ax2 = new("Norway climbed to first place in 2022")
ax2.plot([2019, 2020, 2021, 2022], [4, 3, 2, 1], color="C0", lw=2, marker="o")
ax2.set_xticks([2019, 2020, 2021, 2022])
ax2.set_ylabel("Rank (1 = best)")
ax2.set_yticks([1, 2, 3, 4])
ax2.invert_yaxis()
fig2.text(0.02, 0.02, "Source: UN, World Happiness Report", fontsize=11)
# Heatmaps put row 0 on top by convention.
fig3, ax3 = new("Cases cluster in winter months")
ax3.pcolormesh(np.arange(13), np.arange(2015, 2025), np.random.default_rng(0).random((9, 12)), cmap="Blues")
ax3.invert_yaxis()
ax3.set_xlabel("Month")
ax3.set_ylabel("Year")
fig3.text(0.02, 0.02, "Source: CDC, NNDSS", fontsize=11)
fig.savefig("a.png")
fig2.savefig("b.png")
fig3.savefig("c.png")
