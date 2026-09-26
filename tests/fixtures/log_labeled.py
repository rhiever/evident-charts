from matplotlib.ticker import FixedLocator, FuncFormatter

from _clean import new

fig, ax = new("Solar costs fell a hundredfold since 1980")
ax.plot([1980, 1990, 2000, 2010, 2020], [30, 8, 4, 1.5, 0.3], color="C0", lw=2)
ax.set_yscale("log")
ax.yaxis.set_major_locator(FixedLocator([0.1, 1, 10, 100]))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.yaxis.set_minor_locator(FixedLocator([]))
ax.set_ylabel("Cost per watt ($, log scale)")
fig.text(0.02, 0.02, "Source: IRENA, Renewable Power Generation Costs", fontsize=11)
fig.savefig("out.png")
