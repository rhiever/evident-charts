import numpy as np
import matplotlib.pyplot as plt
from _clean import clean

# A phone-width canvas (mobile preset, 360 x 450) with a tall title block: figure 0 forces a square plot box,
# which centers a narrow plot between wide empty margins; figure 1 lets the plot take the full width.
rng = np.random.default_rng(3)
x = rng.uniform(30, 70, 40)
y = 0.8 * x + rng.normal(0, 4, 40)
for square in (True, False):
    fig, ax = plt.subplots(figsize=(3.6, 4.5))
    clean(ax)
    fig.subplots_adjust(left=0.2, right=0.95, top=0.6, bottom=0.2)
    ax.scatter(x, y, s=20, color="C0")
    if square:
        ax.set_box_aspect(1)
    ax.set_xlabel("Rate A (%)", fontsize=12)
    ax.set_ylabel("Rate B (%)", fontsize=12)
    ax.tick_params(labelsize=12)
    fig.suptitle("Places high on A are\nhigh on B too", x=0.05, y=0.95, ha="left", va="top", fontsize=15)
    fig.text(0.05, 0.02, "Source: Example Survey", fontsize=12)
    fig.savefig(f"out-{square}.png")
