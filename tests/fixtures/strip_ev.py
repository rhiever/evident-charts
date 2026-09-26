import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "evident-charts" / "scripts"))
import evident as ev  # noqa: E402

fig, ax = ev.figure("blog")
rng = np.random.default_rng(3)
teams = np.repeat(["Alpha", "Beta", "Gamma", "Delta"], 30)
scores = np.round(rng.normal(10, 2, len(teams)))
ev.strip(ax, teams, scores, highlight="Beta")
ax.set_xlabel("Score (points)")
ev.titles(fig, "Beta scores sit in the middle of the pack", subtitle="Scores per game, 2025 season",
          source="Source: illustrative data")
ev.save(fig, "out.png")
