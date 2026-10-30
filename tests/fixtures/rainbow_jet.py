import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(np.random.default_rng(0).random((10, 10)), cmap="jet")
fig.colorbar(im)
ins = ax.inset_axes([0.65, 0.65, 0.3, 0.3])  # child axes, not in fig.axes
ins.imshow(np.random.default_rng(1).random((4, 4)), cmap="turbo")
fig.suptitle("Heat is highest in the northeast", fontsize=16)
fig.savefig("out.png")
