from _clean import new

fig, ax = new("Unemployment fell for three straight years")
ax.plot([2019, 2020, 2021, 2022], [3.7, 8.1, 5.4, 3.6], color="C0", lw=2)
ax.set_ylabel("Unemployment rate (%)")
ax.invert_yaxis()
fig.text(0.02, 0.02, "Source: BLS, Current Population Survey", fontsize=11)
fig.savefig("out.png")
