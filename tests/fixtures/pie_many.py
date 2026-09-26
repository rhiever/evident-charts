import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie([30, 20, 15, 10, 10, 8, 7], labels=list("ABCDEFG"), textprops={"fontsize": 12})
fig.suptitle("Product A leads with 30% of sales", fontsize=16)
fig.savefig("out.png")
