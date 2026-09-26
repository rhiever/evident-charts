import matplotlib.pyplot as plt

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(projection="3d")
colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#882255", "#117733", "#AA4499"]
ax.bar3d(range(9), [0] * 9, [0] * 9, 0.5, 0.5, range(1, 10), color=colors)
ax.tick_params(labelsize=5)
fig.suptitle("Region I sold the most units", fontsize=16)
fig.savefig("out.png")
