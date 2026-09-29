import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

# The same split series with the callout beside the junction and a direct label at the true series end.
fig, ax = ev.figure("blog")
ax.plot([2010, 2011, 2012, 2013, 2014, 2015], [80, 70, 60, 50, 40, 20], color=ev.GRAY)
ax.plot([2015, 2016, 2017, 2018, 2019, 2020], [20, 40, 55, 65, 75, 85], color=ev.ACCENT)
ax.annotate("Low", xy=(2015, 20), xytext=(0, -8), textcoords="offset points", ha="center", va="top",
            fontsize=ev.size("annotation", fig), color=ev.DARK)
ax.annotate("Sales", xy=(2020, 85), xytext=(4, 0), textcoords="offset points", ha="left", va="center",
            fontsize=ev.size("label", fig), color=ev.text_color(ev.ACCENT), annotation_clip=False)
ax.set_ylim(0, 100)
ax.set_ylabel("Sales (units)")
ev.titles(fig, "Sales recovered after 2015", subtitle="Units sold, thousands", source="Source: illustrative data")
ev.save(fig, "out.png")
