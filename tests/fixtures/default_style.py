import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot([2019, 2020, 2021], [1, 2, 3])
ax.grid(True)
ax.set_ylabel("Revenue ($M)")
ax.set_title("Revenue tripled in two years", fontsize=16)
fig.savefig("out.png")
