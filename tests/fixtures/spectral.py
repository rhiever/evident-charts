import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
fig, (a, b, c) = plt.subplots(1, 3, figsize=(12, 4))
a.imshow(rng.random((5, 5)) * 2 - 1, cmap="Spectral")          # diverging: warn
b.imshow(rng.random((5, 5)), cmap="Spectral_r")                  # sequential: fail
c.imshow(rng.random((5, 5)), cmap="viridis")                     # fine
fig.suptitle("Temperatures rose everywhere", fontsize=16)
fig.savefig("out.png")
