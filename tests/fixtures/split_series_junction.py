import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# One series drawn as a gray context line meeting an accent highlight line; the callout is centered on the
# junction, so the continuous visible line runs through it even though both pieces end there.
fig, ax = ev.figure("blog")
ax.plot([2010, 2011, 2012, 2013, 2014, 2015], [80, 70, 60, 50, 40, 20], color=ev.GRAY)
ax.plot([2015, 2016, 2017, 2018, 2019, 2020], [20, 40, 55, 65, 75, 85], color=ev.ACCENT)
ax.text(2015, 20, "Low", ha="center", va="center", fontsize=ev.size("annotation", fig), color=ev.DARK)
ax.set_ylim(0, 100)
ax.set_ylabel("Sales (units)")
ev.titles(fig, "Sales recovered after 2015", subtitle="Units sold, thousands", source="Source: illustrative data")
ev.save(fig, "out.png")
