from _clean import new

fig, ax = new("Rural wages grew faster than urban wages")
ax.plot([0, 1], [10, 20], color="C0", lw=2, marker="o")
ax.plot([0, 1], [15, 16], color="#D55E00", lw=2, marker="o")
# Direct labels at the ends of each segment.
ax.text(-0.03, 10, "Rural $10", ha="right", va="center", fontsize=12)
ax.text(-0.03, 15, "Urban $15", ha="right", va="center", fontsize=12)
ax.text(1.03, 20, "$20", ha="left", va="center", fontsize=12)
ax.text(1.0, 16, "$16", ha="left", va="center", fontsize=12)  # exactly at the endpoint
ax.set_xlim(-0.4, 1.3)
ax.set_xticks([0, 1], ["2010", "2020"])
ax.set_ylabel("Median wage ($/hr)")
fig.savefig("out.png")
