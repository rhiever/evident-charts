from _clean import new

fig, ax = new()
ax.plot([2019, 2020, 2021, 2022], [10, 12, 19, 24], color="C0", lw=2)
ax.set_ylabel("Revenue ($M)")
ax.text(2019.1, 20, "2022 value inferred; confirm before publishing", fontsize=12)
fig.text(0.02, 0.02, "Source: sales_2022.csv", fontsize=11)
fig.savefig("out.png")
