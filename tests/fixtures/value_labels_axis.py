from _clean import new

fig, ax = new("Store B sold the most units")
bars = ax.bar(["A", "B", "C", "D"], [80, 95, 85, 60], color="C0")
ax.bar_label(bars, fmt="%.0fk", fontsize=12)
ax.set_ylabel("Units sold (k)")
fig.text(0.02, 0.02, "Source: Acme Corp., 2024 annual report", fontsize=11)
fig.savefig("out.png")
