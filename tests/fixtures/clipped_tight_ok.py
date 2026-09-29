from _clean import new

fig, ax = new()
ax.plot([2019, 2020, 2021], [1, 2, 3], color="C0")
ax.set_xticks([2019, 2020, 2021])
ax.set_ylabel("Revenue ($M)")
fig.text(0.8, 0.02, "Source: a very long source line that runs off the right edge", fontsize=10)
fig.savefig("out.png", bbox_inches="tight")
