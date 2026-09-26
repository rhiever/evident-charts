from _clean import new

fig, ax = new("Store B sold the most units")
vals = [5, 9, 7]
for i, v in enumerate(vals):
    ax.plot([0, v], [i, i], color="C0", lw=2)
    ax.plot(v, i, "o", color="C0")
    ax.text(v + 0.2, i, f"{v}k", va="center", fontsize=12)
ax.set_yticks(range(3), ["A", "B", "C"])
ax.set_xlim(0, 11)
ax.set_xlabel("Units sold (k)")
fig.savefig("out.png")
