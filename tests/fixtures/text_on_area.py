import numpy as np
from _clean import new

x = np.arange(2010, 2021)
low, high = np.full(len(x), 10.0), np.full(len(x), 10.0)
# fig0: a two-layer stack with labels.
fig, ax = new()
ax.stackplot(x, low, high, colors=["#0072B2", "#E69F00"])
ax.text(2015, 5, "Coal", ha="center", va="center", fontsize=12, color="white")        # inside its layer: ok
ax.text(2015, 15, "Gas", ha="center", va="center", fontsize=12, color="black")        # inside its layer: ok
ax.text(2012, 10, "Straddles", ha="center", va="center", fontsize=12)                # across the layer edge: fail
ax.text(2018, 10, "Boxed", ha="center", va="center", fontsize=12,
        bbox=dict(fc="white", ec="none"))                                             # opaque box: ok
ax.text(2018, 15, "Faint", ha="center", va="center", fontsize=12, color="#F0E442")   # inside, 1.3:1: fail
ax.set_ylim(0, 25)
ax.set_ylabel("Output (TWh)")
# fig1: an annotated heatmap: one value per cell passes, a long note across cells fails.
fig1, ax1 = new()
v = np.arange(16).reshape(4, 4)
ax1.imshow(v, cmap="Blues")
for (i, j), val in np.ndenumerate(v):
    ax1.text(j, i, str(val), ha="center", va="center", fontsize=12, color="white" if val > 10 else "black")
ax1.text(1.5, 1.5, "Across many cells", ha="center", va="center", fontsize=12, color="red")
# fig2: pcolormesh with one label inside a cell.
fig2, ax2 = new()
ax2.pcolormesh(np.arange(4), np.arange(4), np.arange(9).reshape(3, 3), cmap="viridis")
ax2.text(0.5, 0.5, "Low", ha="center", va="center", fontsize=12, color="white")
for f in (fig, fig1, fig2):
    f.savefig("out.png")
