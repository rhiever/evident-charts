from _clean import new

fig, ax = new("Store B sold the most units")
ax.barh(["A", "B", "C"], [80, 95, 85], color="C0")
ax.set_xlabel("Units sold (k)")
# Floating bars (Gantt-style) are not required to start at zero.
fig2, ax2 = new("The project finished two weeks early")
ax2.barh(["Design", "Build"], [3, 5], left=[10, 13], color="C1")
ax2.set_xlabel("Week of year")
fig.savefig("a.png")
fig2.savefig("b.png")
