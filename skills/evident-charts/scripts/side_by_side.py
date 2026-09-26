#!/usr/bin/env python3
"""Compose chart images side by side (before/after or candidates) into one PNG.

Usage: python side_by_side.py a.png b.png [c.png ...] -o out.png [--labels Before After]
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt


def compose(images, labels, width=7.0):
    """Figure with each image `width` inches wide, all top-aligned under one row of left-aligned labels."""
    imgs = [mpimg.imread(p) for p in images]
    n = len(imgs)
    pad, gap, band = 0.1, 0.25, 0.6  # inches: outer margin, gap between panels, label band above the images
    heights = [width * im.shape[0] / im.shape[1] for im in imgs]  # each panel's height follows its own aspect
    fig_w, fig_h = 2 * pad + n * width + (n - 1) * gap, band + max(heights) + pad
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    top = (fig_h - band) / fig_h  # labels and images share one top line whatever their aspect ratios
    for i, (im, h, label) in enumerate(zip(imgs, heights, labels)):
        x = (pad + i * (width + gap)) / fig_w
        ax = fig.add_axes((x, top - h / fig_h, width / fig_w, h / fig_h))
        ax.imshow(im)
        ax.set_axis_off()
        fig.text(x, 1 - pad / fig_h, label, fontsize=16, fontweight="bold", color="#333333", ha="left", va="top")
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--labels", nargs="*", default=None)
    ap.add_argument("--width", type=float, default=7.0, help="inches per panel")
    args = ap.parse_args()

    missing = [p for p in args.images if not p.exists()]
    if missing:
        raise SystemExit(f"missing: {', '.join(map(str, missing))}")
    labels = args.labels or [p.stem for p in args.images]
    if len(labels) != len(args.images):
        raise SystemExit("--labels count must match image count")
    compose(args.images, labels, args.width).savefig(args.out, facecolor="white")
    print(args.out.resolve())


if __name__ == "__main__":
    main()
