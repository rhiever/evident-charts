import matplotlib.pyplot as plt
from _clean import new

fig, ax = new("Rural wages grew faster than urban wages")
ax.plot([0, 1], [10, 20], color="C0", lw=2)
ax.plot([0, 1], [15, 16], color="C1", lw=2)
# Label sits in the middle of the 2-point line.
ax.text(0.5, 15, "Rural", ha="center", va="center", fontsize=12)
ax.set_xticks([0, 1], ["2010", "2020"])
ax.set_ylabel("Median wage ($/hr)")
fig.savefig("out.png")
