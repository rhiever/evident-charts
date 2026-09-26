"""Shared helpers for fixtures: a clean baseline style."""
import matplotlib.pyplot as plt


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def new(title="Revenue doubled after the 2020 launch", figsize=(8, 5)):
    fig, ax = plt.subplots(figsize=figsize)
    clean(ax)
    fig.subplots_adjust(top=0.85)
    fig.suptitle(title, fontsize=16, x=0.1, ha="left")
    return fig, ax
