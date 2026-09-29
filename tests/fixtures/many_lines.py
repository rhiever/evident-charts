import matplotlib.pyplot as plt
from _clean import new

fig, ax = new()
for k in range(8):
    ax.plot([2019, 2020, 2021], [k, k + 1, k + 2], color=f"C{k}", marker="os^Dv<>p"[k])  # markers: cvd warns, not fails
ax.set_ylabel("Revenue ($M)")
ax.set_xticks([2019, 2020, 2021])
fig2, ax2 = new()
for k in range(12):  # gray context plus one highlight: fine
    ax2.plot([2019, 2020, 2021], [k, k + 1, k + 2], color="#cccccc")
ax2.plot([2019, 2020, 2021], [3, 8, 14], color="C3")
ax2.set_xticks([2019, 2020, 2021])
ax2.set_ylabel("Revenue ($M)")
fig.savefig("a.png")
fig2.savefig("b.png")
