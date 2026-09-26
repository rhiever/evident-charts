from _clean import new

fig, ax = new()
for k, c in enumerate(["#0072B2", "#D55E00", "#009E73"]):
    ax.plot([2019, 2020, 2021], [k, k + 1, k + 3], color=c, label=f"Series {k}")
ax.legend()
ax.set_ylabel("Revenue ($M)")
fig.savefig("out.png")
