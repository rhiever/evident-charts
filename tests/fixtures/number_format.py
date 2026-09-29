import numpy as np
from matplotlib.ticker import FormatStrFormatter, FuncFormatter, StrMethodFormatter

from _clean import new

years = [2018, 2019, 2020, 2021, 2022]
# Offset text: the y ticks read 1.2 to 2.6 under a "1e6" in the corner.
fig, ax = new()
ax.plot(years, [1.2e6, 1.5e6, 1.9e6, 2.3e6, 2.6e6], color="C0")
ax.set_xticks(years)
ax.set_ylabel("Downloads")
# Monthly data on a year axis: the x ticks read 0.0 to 0.8 under "+2.019e3".
fig1, ax1 = new()
ax1.plot(2019 + np.arange(12) / 12, np.arange(12), color="C0")
ax1.set_ylabel("Orders (k)")
# Scientific-notation tick labels.
fig2, ax2 = new()
ax2.plot(years, [1e6, 2e6, 3e6, 4e6, 5e6], color="C0")
ax2.set_xticks(years)
ax2.yaxis.set_major_formatter(FormatStrFormatter("%.1e"))
ax2.set_ylabel("Downloads")
# A few integer years with default ticks print 2019.00, 2019.25, ...
fig3, ax3 = new()
ax3.plot([2019, 2020, 2021], [3, 5, 4], color="C0")
ax3.set_ylabel("Rate (%)")
# Thousands separators on years.
fig4, ax4 = new()
ax4.plot(years, [3, 5, 4, 6, 7], color="C0")
ax4.set_xticks(years)
ax4.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax4.set_ylabel("Rate (%)")
# "{:g}" ticks: $0.5M beside $1M.
fig5, ax5 = new()
ax5.plot(years, [0.2, 0.9, 1.1, 1.6, 2.0], color="C0")
ax5.set_xticks(years)
ax5.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:g}M"))
ax5.set_ylabel("Revenue")
# Raw floats as bar labels: 13.3333, 8.5, 6, 2.25.
fig6, ax6 = new()
bars = ax6.barh(["Oslo", "Bergen", "Tromso", "Bodo"], [2.25, 6, 8.5, 13.3333], color="C0")
ax6.bar_label(bars)
ax6.set_xlabel("Rainfall (mm)")
for i, f in enumerate([fig, fig1, fig2, fig3, fig4, fig5, fig6]):
    f.savefig(f"{i}.png")
