import matplotlib.pyplot as plt

# fig0: two panels squeezed by a huge gap -> plot-area-tiny on both.
fig, (a, b) = plt.subplots(1, 2, figsize=(8, 5))
for ax in (a, b):
    ax.plot([1, 2, 3], [1, 3, 2])
fig.subplots_adjust(left=0.3, right=0.95, wspace=6)
# fig1: a small inset and a 6-panel row of normal small multiples -> no finding.
fig1, axes = plt.subplots(1, 6, figsize=(12, 3))
for ax in axes:
    ax.plot([1, 2, 3], [1, 3, 2])
inset = axes[0].inset_axes([0.6, 0.6, 0.3, 0.3])
inset.plot([1, 2], [1, 2])
fig.savefig("a.png")
fig1.savefig("b.png")
