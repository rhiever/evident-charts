from _clean import new

fig, ax = new("Store B sold the most units")
ax.bar(["A", "B", "C"], [80, 95, 85], color="C0")
ax.set_ylim(70, 100)
ax.set_ylabel("Units sold (k)")
fig.savefig("out.png")
