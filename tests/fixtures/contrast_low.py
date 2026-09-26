from _clean import new

fig, ax = new()
years = [2018, 2019, 2020, 2021, 2022]
ax.plot(years, [1, 2, 3, 4, 5], color="#F0E442", lw=2)                  # yellow line: invisible, fail
ax.plot(years, [2, 3, 3, 4, 4], color="#E69F00", lw=2)                  # orange, unlabeled: warn
ax.plot(years, [3, 3, 4, 5, 6], color="#56B4E9", lw=2, label="Sky")     # sky blue, direct-labeled: ok
ax.text(2022.1, 6, "Sky", va="center", fontsize=12, color="#0072B2")
ax.text(2018, 5.5, "Faint note", fontsize=12, color="#AAAAAA")          # light gray text: fail
ax.text(2018, 4.5, "Big quiet", fontsize=20, color="#949494")           # large text needs only 3:1
ax.text(2020, 0.5, "Boxed", fontsize=12, color="white", bbox=dict(fc="#333333", ec="none"))
ax.set_xlim(2017.8, 2023)
ax.set_ylabel("Output (TWh)")
fig.savefig("out.png")
# fig1: exported on a near-black page, so the default black tick labels vanish (one finding per axis).
fig1, ax1 = new()
ax1.set_facecolor("white")
ax1.plot(years, [1, 2, 3, 4, 5], color="#0072B2", lw=2)
ax1.set_ylabel("Output (TWh)", color="white")
fig1.suptitle("Output tripled", color="white")
fig1.savefig("out.png", facecolor="#111111")
