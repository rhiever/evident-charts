from _clean import new

# Red and green lines told apart only by a legend: they merge for deuteranopes.
fig, ax = new()
years = [2018, 2019, 2020, 2021, 2022]
ax.plot(years, [10, 12, 15, 19, 24], color="#D62728", lw=2, label="Online")
ax.plot(years, [9, 10, 10, 11, 12], color="#2CA02C", lw=2, label="Stores")
ax.legend(frameon=False)
ax.set_ylabel("Revenue ($M)")
fig.savefig("out.png")
