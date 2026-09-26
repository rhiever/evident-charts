import matplotlib.pyplot as plt
import numpy as np

x = np.arange(20)
# fig0: a title block squeezing a slide-size canvas leaves a 5:1 plot -> plot-aspect (wide).
fig0, ax = plt.subplots(figsize=(19.2, 10.8))
ax.plot(x, np.sin(x))
fig0.subplots_adjust(left=.05, right=.95, bottom=.1, top=.4)
# fig1: a line chart on a narrow, tall canvas -> plot-aspect (tall).
fig1, ax = plt.subplots(figsize=(4, 10))
ax.plot(x, np.sin(x))
# fig2: 30 horizontal bars on the same tall canvas: height follows the rows -> no finding.
fig2, ax = plt.subplots(figsize=(4, 10))
ax.barh([f"Item {i}" for i in range(30)], np.arange(30) + 1)
# fig3: four stacked wide panels (small multiples) -> no finding.
fig3, axes = plt.subplots(4, 1, figsize=(12, 8))
for a in axes:
    a.plot(x, np.sin(x))
# fig4: a hero-number card over a wide sparkline-style plot -> no finding.
fig4, ax = plt.subplots(figsize=(10.8, 10.8))
fig4.text(.07, .95, "Spending keeps climbing", fontsize=30, va="top")
fig4.text(.07, .85, "+57%", fontsize=110, weight="bold", va="top")
ax.plot(x, x ** 1.2)
fig4.subplots_adjust(bottom=.1, top=.2)
# fig5: a sparkline with its axes off, and fig6: an image with a fixed data aspect -> no finding.
fig5, ax = plt.subplots(figsize=(8, 1))
ax.plot(x, np.sin(x))
ax.axis("off")
fig6, ax = plt.subplots(figsize=(12, 3))
ax.imshow(np.random.default_rng(0).random((10, 60)))
for i, f in enumerate((fig0, fig1, fig2, fig3, fig4, fig5, fig6)):
    f.savefig(f"{i}.png")
