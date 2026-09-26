from _clean import new

fig, ax = new("Norway produces the most per hour")
x = [1400, 1470, 1600, 1750, 1900]
y = [134, 120, 90, 70, 50]
names = ["Norway", "Denmark", "France", "Italy", "Chile"]
ax.scatter(x, y, s=60, color="0.75")
ax.scatter(x[:1], y[:1], s=60, color="#D55E00")  # highlight redrawn over the context dot
for xi, yi, name in zip(x, y, names):
    ax.annotate(name, xy=(xi, yi), xytext=(7, 0), textcoords="offset points",
                ha="left", va="center", fontsize=12)
ax.annotate("Longer hours, less output", xy=(1750, 70), xytext=(1500, 30),
            arrowprops=dict(arrowstyle="-", color="0.5"), fontsize=12)
ax.text(0.98, 0.95, "r = -0.99", transform=ax.transAxes, ha="right", fontsize=12)
ax.set_xlim(1300, 2000)
ax.set_ylim(0, 160)
ax.set_xlabel("Hours worked per year")
ax.set_ylabel("GDP per hour ($)")
fig.savefig("out.png")
