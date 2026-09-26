import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter, FixedLocator, PercentFormatter
from _clean import new

# Axis 0 puts "%" on the top tick only (0, 3, 6, 9%): a unit on some ticks reads as two scales even with a
# subtitle that states the unit. Axis 1 formats every tick with the unit and passes.
fig, (a, b) = plt.subplots(1, 2, figsize=(9, 4.5))
for ax in (a, b):
    ax.plot([2020, 2021, 2022, 2023], [4.1, 5.2, 6.8, 7.4], color="C0", lw=2)
    ax.set_ylim(0, 9)
    ax.set_xticks([2020, 2023])
    ax.yaxis.set_major_locator(FixedLocator([0, 3, 6, 9]))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
a.yaxis.set_major_formatter(FixedFormatter(["0", "3", "6", "9%"]))
b.yaxis.set_major_formatter(PercentFormatter(decimals=0))
fig.subplots_adjust(top=0.8)
fig.suptitle("Usage rose every year since 2020", x=0.05, ha="left", fontsize=16)
fig.text(0.05, 0.86, "Percent of adults, 2020-2023", fontsize=11)
fig.text(0.05, 0.01, "Source: Example Survey", fontsize=10)
fig.savefig("out.png")
