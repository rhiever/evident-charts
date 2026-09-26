import numpy as np
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(projection="3d")
ax.bar3d([0, 1, 2], [0, 0, 0], [0, 0, 0], 0.5, 0.5, [3, 5, 2])
fig.suptitle("Region B sold the most units", fontsize=16)
fig.savefig("out.png")
