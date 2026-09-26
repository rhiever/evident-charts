import numpy as np
from _clean import new

# A flat target line threads between the two lines of its own note: the text-on-line check must see the leading
# between lines as part of the label. The two-line note below the trend is clear of every line.
fig, ax = new("Output passed the target in 2021")
x = np.arange(2010, 2026)
ax.plot(x, 10 + 1.5 * (x - 2010), color="C0", lw=2, label="Output")
ax.plot([2010, 2025], [30, 30], color="C1", lw=2, label="Target")
ax.text(2012.5, 30, "Target\nset in 2012", ha="center", va="center", fontsize=12)
ax.text(2021, 20, "Second plant\nopens", ha="center", va="center", fontsize=12)
ax.set_ylabel("Units (k)")
fig.savefig("out.png")
