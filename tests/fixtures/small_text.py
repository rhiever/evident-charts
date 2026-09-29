from _clean import new

fig, ax = new(figsize=(20, 10))
ax.plot([2019, 2020, 2021], [1, 2, 3], color="C0")
ax.set_xticks([2019, 2020, 2021])
ax.set_ylabel("Revenue ($M)", fontsize=8)
ax.tick_params(labelsize=7)
fig.savefig("out.png")
