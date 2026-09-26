import numpy as np
from _clean import new

x = np.arange(2010, 2021)
rng = np.random.default_rng(1)
a, b, c, d = (5 + rng.normal(0, 1, len(x)) for _ in range(4))
# fig0: stackplot with 4 layers -> warn.
fig, ax = new()
ax.stackplot(x, a, b, c, d, colors=["C0", "C1", "C2", "C3"])
ax.set_ylabel("Output (TWh)")
# fig1: fill_between stacked by hand, 3 layers -> warn.
fig1, ax1 = new()
ax1.fill_between(x, 0, a, color="C0")
ax1.fill_between(x, a, a + b, color="C1")
ax1.fill_between(x, a + b, a + b + c, color="C2")
ax1.set_ylabel("Output (TWh)")
# fig2: a line with two nested uncertainty bands -> no stack.
fig2, ax2 = new()
ax2.plot(x, a, color="C0")
ax2.fill_between(x, a - 1, a + 1, color="C0", alpha=.3)
ax2.fill_between(x, a - 2, a + 2, color="C0", alpha=.15)
ax2.set_ylabel("Output (TWh)")
for f in (fig, fig1, fig2):
    f.savefig("out.png")
