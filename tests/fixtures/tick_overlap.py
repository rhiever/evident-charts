from _clean import new

fig, ax = new("Alpha Industries sold the most", figsize=(5, 4))
names = ["Alpha Industries Inc", "Beta Holdings Group", "Gamma Group Global", "Delta Partners LLC"]
ax.bar(names, [9, 7, 5, 3], color="C0")
ax.set_ylabel("Units sold (k)")
fig.savefig("out.png")
