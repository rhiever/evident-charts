import numpy as np

from _clean import new

regions = ["North", "South", "East", "West"]
# Stacked bars: each segment's fill runs straight into the next.
fig, ax = new()
low = ax.bar(regions, [3, 4, 2, 5], color="#1f77b4", label="Online")
ax.bar(regions, [2, 3, 4, 1], bottom=[3, 4, 2, 5], color="#aec7e8", label="Store")
ax.set_ylabel("Sales ($M)")
# Pie wedges without wedge edges.
fig1, ax1 = new()
ax1.pie([45, 30, 25], colors=["#1f77b4", "#6baed6", "#c6dbef"], labels=["Rent", "Food", "Other"])
# Stackplot layers without edges.
fig2, ax2 = new()
x = np.arange(10)
ax2.stackplot(x, 1 + 0.1 * x, 2 + 0.05 * x, colors=["#1f77b4", "#aec7e8"])
ax2.set_ylabel("Users (M)")
# Edges drawn in black instead of the background color.
fig3, ax3 = new()
ax3.barh(regions, [3, 4, 2, 5], color="#1f77b4", edgecolor="black", linewidth=1)
ax3.barh(regions, [2, 3, 4, 1], left=[3, 4, 2, 5], color="#aec7e8", edgecolor="black", linewidth=1)
ax3.set_xlabel("Sales ($M)")
for i, f in enumerate([fig, fig1, fig2, fig3]):
    f.savefig(f"{i}.png")
