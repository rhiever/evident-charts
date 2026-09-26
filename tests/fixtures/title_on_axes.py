import numpy as np
import matplotlib.pyplot as plt
from _clean import clean

# Figure 0: the chart title is ax.set_title on the top panel only (no suptitle), a legitimate overall title.
# Figure 1: same-size titles on both panels are panel titles, so the chart still lacks an overall title.
x = np.arange(2015, 2026)
for both in (False, True):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    top.plot(x, 50 + 3 * (x - 2015), color="C0", lw=2)
    bottom.plot(x, np.full(len(x), 3.0) + 0.1 * np.sin(x), color="C1", lw=2)
    top.set_title("Sales doubled while prices held steady", loc="left", fontsize=16)
    if both:
        bottom.set_title("Prices held steady after the launch", loc="left", fontsize=16)
    top.set_ylabel("Sales ($k)")
    bottom.set_ylabel("Price ($)")
    for a in (top, bottom):
        clean(a)
    fig.text(0.02, 0.01, "Source: Example Co. annual report", fontsize=10)
    fig.savefig(f"out-{both}.png")
