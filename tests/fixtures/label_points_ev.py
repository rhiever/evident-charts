import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

fig, ax = ev.figure("blog")
x = [1400, 1470, 1600, 1750, 1900, 1520]
y = [134, 120, 90, 70, 50, 60]
names = ["Norway", "Denmark", "France", "Italy", "Chile", "Japan"]
ax.scatter(x, y, s=ev.size("marker", fig) ** 2, color=ev.GRAY, zorder=3)
ev.label_points(ax, x, y, names, offsets={"Chile": "left", "Japan": "below"}, highlight="Norway")
ax.set_xlim(1300, 2000)
ax.set_ylim(0, 160)
ax.set_xlabel("Hours worked per year")
ax.set_ylabel("GDP per hour ($)")
ev.titles(fig, "Norway produces the most per hour", subtitle="GDP per hour worked, US dollars")
ev.save(fig, "out.png")
