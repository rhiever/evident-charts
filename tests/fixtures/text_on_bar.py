from _clean import new

# fig0: a note centered on a bar end (straddles its edge) and a label spanning two grouped bars -> text-overlap.
fig, ax = new()
ax.bar([0, 1, 2], [4, 6, 3], width=0.8, color="C0")
ax.text(1, 6, "Peak", ha="center", va="center", fontsize=12)
ax.bar([3.6, 4.4], [5, 5], width=0.8, color="C1")
ax.text(4, 2.5, "Both years", ha="center", va="center", fontsize=12)
ax.set_ylabel("Units (k)")
# fig1: value labels past the bar ends, a label wholly inside a wide bar, a boxed label above the bars -> clean.
fig1, ax1 = new()
bars = ax1.barh([0, 1, 2], [40, 60, 30], height=0.7, color="C0")
ax1.bar_label(bars, padding=4, fontsize=12)
ax1.text(30, 1, "Inside", ha="center", va="center", fontsize=12, color="white")
ax1.text(20, 0, "Boxed note", ha="center", va="center", fontsize=12, zorder=5,
         bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
ax1.set_xlim(0, 80)
ax1.set_xlabel("Units (k)")
fig.savefig("a.png")
fig1.savefig("b.png")
