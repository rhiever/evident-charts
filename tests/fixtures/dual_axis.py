from _clean import new

fig, ax = new("Sales rose while prices fell")
ax.plot([2019, 2020, 2021], [1, 2, 3], color="C0")
ax.set_xticks([2019, 2020, 2021])
ax.set_ylabel("Sales ($M)")
ax2 = ax.twinx()
ax2.plot([2019, 2020, 2021], [30, 20, 10], color="C1")
ax2.set_ylabel("Price ($)")
fig.savefig("out.png")
