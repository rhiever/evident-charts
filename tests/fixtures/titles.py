import matplotlib.pyplot as plt
from _clean import clean

for title in ["Revenue by region", "Sales vs. price over time", None]:
    fig, ax = plt.subplots(figsize=(8, 5))
    clean(ax)
    ax.plot([2019, 2020, 2021], [1, 2, 3], color="C0")
    ax.set_ylabel("Revenue ($M)")
    if title:
        ax.set_title(title, fontsize=16)
    fig.savefig(f"out-{title}.png")
