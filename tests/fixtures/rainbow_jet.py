import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(np.random.default_rng(0).random((10, 10)), cmap="jet")
fig.colorbar(im)
fig.suptitle("Heat is highest in the northeast", fontsize=16)
fig.savefig("out.png")
