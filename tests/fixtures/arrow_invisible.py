from pathlib import Path

import matplotlib.pyplot as plt

plt.style.use(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "assets" / "evident.mplstyle")
from _clean import new  # noqa: E402

fig, ax = new()  # house style: patch.linewidth 0 and a white patch edge hide unstyled arrows
ax.plot([0, 10], [0, 8])
ax.annotate("Default", xy=(2, 1.6), xytext=(1, 6), arrowprops=dict(arrowstyle="->"))
ax.annotate("Colored, no width", xy=(5, 4), xytext=(4, 7), arrowprops=dict(arrowstyle="-|>", color="#595959"))
ax.annotate("Width, white", xy=(8, 6.4), xytext=(7, 2), arrowprops=dict(arrowstyle="->", lw=1))
ax.set_ylabel("Revenue ($M)")
fig.savefig("out.png")
