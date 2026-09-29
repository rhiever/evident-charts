"""Regenerate the Vega-Lite fixtures: uv run --with vl-convert-python python tests/fixtures_svg/export_vegalite.py

Compiles each <name>.vl.json next to this file to <name>.vg.json (Vega) and renders <name>.svg.
"""
import json
from pathlib import Path

import vl_convert as vlc

HERE = Path(__file__).resolve().parent
for src in sorted(HERE.glob("*.vl.json")):
    spec = json.loads(src.read_text())
    name = src.name[:-len(".vl.json")]
    (HERE / f"{name}.vg.json").write_text(json.dumps(vlc.vegalite_to_vega(spec), indent=1))
    (HERE / f"{name}.svg").write_text(vlc.vegalite_to_svg(spec))
