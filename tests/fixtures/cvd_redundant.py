from _clean import new

# The same red/green pair, each time with a second cue: cvd warns instead of failing.
years = [2018, 2019, 2020, 2021, 2022]
on, st = [10, 12, 15, 19, 24], [9, 10, 10, 11, 12]
# fig0: labeled lines named by dark direct labels at their ends.
fig, ax = new()
ax.plot(years, on, color="#D62728", lw=2, label="Online")
ax.plot(years, st, color="#2CA02C", lw=2, label="Stores")
ax.text(2022.1, 24, "Online", va="center", fontsize=12)
ax.text(2022.1, 12, "Stores", va="center", fontsize=12)
ax.set_xlim(2017.8, 2023)
ax.set_ylabel("Revenue ($M)")
# fig1: unlabeled lines, end labels in a darker shade of each line's hue.
fig1, ax1 = new()
ax1.plot(years, on, color="#D62728", lw=2)
ax1.plot(years, st, color="#2CA02C", lw=2)
ax1.text(2022.1, 24, "Online", va="center", fontsize=12, color="#B01E1F")
ax1.text(2022.1, 12, "Stores", va="center", fontsize=12, color="#1E6F1E")
ax1.set_xlim(2017.8, 2023)
ax1.set_ylabel("Revenue ($M)")
# fig2: a legend, but one line is dashed.
fig2, ax2 = new()
ax2.plot(years, on, color="#D62728", lw=2, label="Online")
ax2.plot(years, st, color="#2CA02C", lw=2, ls="--", label="Stores")
ax2.legend(frameon=False)
ax2.set_ylabel("Revenue ($M)")
# fig3: error bars with round vs square markers.
fig3, ax3 = new()
ax3.errorbar(years, on, yerr=1, fmt="o", color="#D62728", label="Online")
ax3.errorbar(years, st, yerr=1, fmt="s", color="#2CA02C", label="Stores")
ax3.legend(frameon=False)
ax3.set_ylabel("Revenue ($M)")
for f in (fig, fig1, fig2, fig3):
    f.savefig("out.png")
