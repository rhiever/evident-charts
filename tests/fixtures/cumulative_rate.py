import numpy as np
from _clean import new

# fig0: a running total of weekly cases drawn under a rate label -> cumulative-as-rate fail.
weekly = np.array([3, 5, 2, 6, 4, 7, 5, 8, 6, 9])
weeks = np.arange(1, 11)
fig, ax = new("Measles spread fastest in March")
ax.plot(weeks, np.cumsum(weekly), color="C0", lw=2)
ax.set_ylabel("Cases per 100,000")
ax.set_xlabel("Week")
# fig1: the same running total, labeled cumulative -> no finding.
fig1, ax1 = new("Measles spread fastest in March")
ax1.plot(weeks, np.cumsum(weekly), color="C0", lw=2)
ax1.set_ylabel("Cumulative cases per 100,000")
ax1.set_xlabel("Week")
# fig2: the weekly rate itself, which dips -> no finding.
fig2, ax2 = new("Measles spread fastest in March")
ax2.plot(weeks, weekly, color="C0", lw=2)
ax2.set_ylabel("Cases per 100,000")
ax2.set_xlabel("Week")
# fig3: stacked running totals under a share label -> fail (areas), and stacked-area stays quiet at 2 layers.
fig3, ax3 = new("Solar and wind took the lead")
ax3.stackplot(weeks, np.cumsum(weekly), np.cumsum(weekly[::-1]), colors=["C0", "C1"])
ax3.set_ylabel("Share of generation (%)")
ax3.set_xlabel("Week")
for f in (fig, fig1, fig2, fig3):
    f.savefig("out.png")
