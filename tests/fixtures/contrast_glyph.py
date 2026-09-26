"""A light-gray symbol used as a color key passes at the mark floor (3:1), not the text floor."""
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot([0, 1, 2], [1, 3, 2], color="#333333")
ax.set_title("Values rose then fell")
ax.set_ylabel("Value")
fig.text(0.1, 0.02, "●", color="#8c8c8c", fontsize=14)
fig.text(0.13, 0.02, "Source: example data", color="#595959", fontsize=10)
fig.savefig("contrast_glyph.png")
