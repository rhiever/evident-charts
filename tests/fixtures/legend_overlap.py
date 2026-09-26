from _clean import new

# The legend sits below the axes on top of the x-axis label: its line handle covers "Quarter".
fig, ax = new()
ax.plot([1, 2, 3, 4], [1, 3, 2, 4], color="C0", label="Online revenue")
ax.set_xlabel("Quarter", fontsize=12)
ax.set_ylabel("Revenue ($M)", fontsize=12)
ax.legend(loc="center left", bbox_to_anchor=(0.42, -0.11), handlelength=6, fontsize=12)
fig.savefig("out.png")
