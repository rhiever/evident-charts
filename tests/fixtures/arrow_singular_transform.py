from _clean import new
from matplotlib.patches import FancyArrowPatch
from matplotlib.transforms import Affine2D

fig, ax = new()
ax.text(0.5, 0.5, "Overlapped label", ha="center", va="center", transform=ax.transAxes)
# Collapse the arrow onto a horizontal line through the label.
transform = Affine2D().scale(1, 0).translate(0, 0.5) + ax.transAxes
ax.add_artist(FancyArrowPatch((0.1, 0), (0.9, 1), arrowstyle="->", transform=transform))
