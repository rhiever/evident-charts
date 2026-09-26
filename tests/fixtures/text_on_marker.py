from _clean import new

# fig0: a scatter label centered on its own dot, and a note sitting on a line's markers -> text-overlap.
fig, ax = new()
ax.scatter([1, 2, 3, 4], [2, 3, 5, 4], s=60, color="C0")
ax.annotate("Chile", xy=(3, 5), ha="center", va="center", fontsize=12)
ax.plot([1, 2, 3, 4], [1, 1.5, 1.2, 1.8], "o-", color="C1", ms=7)
ax.text(2, 1.5, "Dip here", ha="center", va="center", fontsize=12)
ax.set_xlim(0, 5)
ax.set_ylim(0, 6)
ax.set_ylabel("Units (k)")
# fig1: labels beside their dots, and a number inside a big bubble -> clean.
fig1, ax1 = new()
ax1.scatter([1, 2, 3], [2, 3, 5], s=60, color="C0")
ax1.annotate("Chile", xy=(3, 5), xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=12)
ax1.scatter([4], [2], s=3000, color="#0072B2")
ax1.text(4, 2, "12", ha="center", va="center", fontsize=12, color="white")
ax1.set_xlim(0, 5)
ax1.set_ylim(0, 6)
ax1.set_ylabel("Units (k)")
fig.savefig("a.png")
fig1.savefig("b.png")
