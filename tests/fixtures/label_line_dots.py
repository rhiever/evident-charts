from _clean import new

# Dots plus labels attached to other marks: a line's end label, a reference rule's label, a median
# tick's label. Each sits between two dots, but none names a dot, so none is an ambiguous point label.
fig, ax = new("Most stores beat the target")
ax.scatter([1, 2, 5.4, 5.4, 6.5, 6.5, 2.9, 3.9], [48, 50, 58, 52, 70.5, 65.5, 67, 67], s=60, color="0.6")
ax.plot([1, 6], [50, 68], color="C0", lw=2)
ax.annotate("Trend", xy=(6, 68), xytext=(5, 0), textcoords="offset points", va="center", fontsize=12)
ax.axhline(55, color="0.4", lw=1)
ax.text(5.0, 55, "Target", fontsize=12, va="center")
ax.plot([3.4, 3.4], [60, 63], color="k", lw=2)
ax.text(3.4, 63.4, "Median", fontsize=12, va="bottom", ha="center")
ax.set_xlim(0.5, 7)
ax.set_ylim(45, 75)
ax.set_xlabel("Store number")
ax.set_ylabel("Sales ($k)")
fig.savefig("out.png")
