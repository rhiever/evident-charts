from _clean import new

fig, ax = new()
ax.plot([0, 1, 2, 3], [1, 3, 2, 4], color="C0")
ax.text(0.5, 3.5, "Peak demand here", fontsize=12)
ax.text(0.6, 3.45, "Another note", fontsize=12)
ax.set_ylabel("Units (k)")
ax.set_xlabel("Quarter")
fig.savefig("out.png")
