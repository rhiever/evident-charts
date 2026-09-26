import matplotlib.pyplot as plt
from _clean import clean

# A short kicker title over a larger hero number: the number and its caption carry the claim -> no default-title.
fig, ax = plt.subplots(figsize=(8, 8))
clean(ax)
fig.subplots_adjust(top=0.55)
fig.text(0.05, 0.96, "Solar power", fontsize=20, weight="bold", va="top")
fig.text(0.05, 0.9, "+57%", fontsize=64, weight="bold", va="top")
fig.text(0.05, 0.7, "More solar output than a year earlier", fontsize=14, va="top")
ax.plot([2021, 2022, 2023, 2024], [1, 1.4, 2.1, 3.3], color="C0")
ax.set_ylabel("Output (TWh)")
fig.savefig("a.png")
