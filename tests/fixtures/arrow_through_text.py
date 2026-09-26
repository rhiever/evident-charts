from _clean import new

fig, ax = new()
ax.plot([0, 10], [0, 0.2], color="C0")
ax.text(5, 5, "Unrelated note", ha="center", va="center", fontsize=12)
ax.annotate("Launch", xy=(5, 1), xytext=(5, 9), ha="center",
            arrowprops=dict(arrowstyle="->", color="k"), fontsize=12)
ax.set_ylim(-1, 10)
ax.set_ylabel("Revenue ($M)")
ax.set_xlabel("Month")
fig.savefig("out.png")
