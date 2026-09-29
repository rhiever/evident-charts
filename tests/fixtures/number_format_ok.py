import datetime as dt

import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, StrMethodFormatter

from _clean import new

years = [2018, 2019, 2020, 2021, 2022]
# Millions abbreviated by hand on whole-year ticks.
fig, ax = new()
ax.plot(years, [1.2e6, 1.5e6, 1.9e6, 2.3e6, 2.6e6], color="C0")
ax.set_xticks(years)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:.1f}M"))
ax.set_ylabel("Downloads")
# Values between 1,000 and 2,200 with separators are counts, not years: their ticks step by 200.
fig1, ax1 = new()
ax1.plot(years, [1050, 1400, 1700, 1900, 2150], color="C0")
ax1.set_xticks(years)
ax1.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax1.set_ylabel("Members")
# A bare 0 beside 0.5, 1.0, 1.5 keeps one precision.
fig2, ax2 = new()
ax2.plot(years, [0.1, 0.6, 0.9, 1.3, 1.7], color="C0")
ax2.set_xticks(years)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v:.1f}"))
ax2.set_ylabel("Revenue ($M)")
ax2.set_ylim(0, 2)
# Two label sets on one chart, each with one precision: $#.#M and #%.
fig3, ax3 = new()
x = [0, 1, 2]
money = ax3.bar([v - 0.2 for v in x], [1.2, 2.5, 3.1], width=0.4, color="C0")
share = ax3.bar([v + 0.2 for v in x], [40, 25, 35], width=0.4, color="C1")
ax3.bar_label(money, labels=["$1.2M", "$2.5M", "$3.1M"])
ax3.bar_label(share, labels=["40%", "25%", "35%"])
ax3.set_xticks(x, ["North", "South", "West"])
ax3.set_ylabel("Revenue ($M) and share (%)")
# Log axis ticks (10^0, 10^1, ...) are not scientific notation on a linear axis.
fig4, ax4 = new()
ax4.plot(years, [1, 10, 100, 1000, 10000], color="C0")
ax4.set_xticks(years)
ax4.set_yscale("log")
ax4.set_ylabel("Cases (log scale)")
# A date formatter's offset text (2021-Apr) is the year on the first label, not a numeric offset.
fig5, ax5 = new()
days = [dt.date(2021, 3, 1) + dt.timedelta(days=k) for k in range(40)]
ax5.plot(days, range(40), color="C0")
locator = mdates.AutoDateLocator()
ax5.xaxis.set_major_locator(locator)
ax5.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
ax5.set_ylabel("Orders (k)")
# Value axes inside the year range are measurements: pressure ticks 1010.00, 1010.25, ... and counts 1,000, 1,005, ...
fig6, ax6 = new()
ax6.plot(years, [1010.1, 1010.4, 1010.9, 1011.0, 1010.7], color="C0")
ax6.set_xticks(years)
ax6.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
ax6.set_ylabel("Pressure (hPa)")
fig7, ax7 = new()
ax7.plot(years, [1000, 1004, 1011, 1017, 1022], color="C0")
ax7.set_xticks(years)
ax7.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax7.set_ylabel("Members")
for i, f in enumerate([fig, fig1, fig2, fig3, fig4, fig5, fig6, fig7]):
    f.savefig(f"{i}.png")
