from _clean import new

fig, ax = new("Alpha Industries sold the most")
names = ["Alpha Industries", "Beta Holdings", "Gamma Group", "Delta Partners"]
ax.bar(names, [9, 7, 5, 3], color="C0")
ax.tick_params(axis="x", rotation=45)
ax.set_ylabel("Units sold (k)")
fig.subplots_adjust(bottom=0.3)
fig.savefig("out.png")
