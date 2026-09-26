from _clean import new

fig, ax = new("Store B sold the most units")
ax.barh(["A", "B", "C"], [80, 9500, 850], color="C0")
ax.set_xscale("log")
ax.set_xlabel("Units sold")
fig.savefig("out.png")
