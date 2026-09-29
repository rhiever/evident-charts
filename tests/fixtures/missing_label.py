import matplotlib.pyplot as plt
from _clean import clean

fig, ax = plt.subplots(figsize=(8, 5))
clean(ax)
ax.plot([2019, 2020, 2021, 2022], [120, 340, 560, 910], color="C0")
ax.set_xticks([2019, 2020, 2021, 2022])
ax.set_title("Downloads tripled after the redesign", fontsize=16)
fig.savefig("out.png")
