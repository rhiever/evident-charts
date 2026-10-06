#!/usr/bin/env python3
"""Build a reproducible plugin ZIP from an explicit file list. Python 3.10+."""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    "gemini-extension.json",
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "docs/acceptance.md",
    "examples/hero.png",
    "assets/logo.svg",
    "assets/logo.png",
    "assets/composer-icon.png",
    "skills/evident-charts/SKILL.md",
    "skills/evident-charts/agents/openai.yaml",
    "skills/evident-charts/assets/evident.mplstyle",
    "skills/evident-charts/assets/palettes.json",
    "skills/evident-charts/assets/presets.json",
    "skills/evident-charts/assets/themes/evident_d3.css",
    "skills/evident-charts/assets/themes/evident_d3_tokens.js",
    "skills/evident-charts/assets/themes/evident_plotly.json",
    "skills/evident-charts/assets/themes/evident_vegalite.json",
    "skills/evident-charts/assets/themes/theme_evident.R",
    "skills/evident-charts/references/candidates.md",
    "skills/evident-charts/references/choosing.md",
    "skills/evident-charts/references/color.md",
    "skills/evident-charts/references/critique.md",
    "skills/evident-charts/references/integrity.md",
    "skills/evident-charts/references/libraries.md",
    "skills/evident-charts/references/sources.md",
    "skills/evident-charts/references/text.md",
    "skills/evident-charts/scripts/check_chart.py",
    "skills/evident-charts/scripts/check_palette.py",
    "skills/evident-charts/scripts/check_svg.py",
    "skills/evident-charts/scripts/evident.py",
    "skills/evident-charts/scripts/measure_svg.js",
    "skills/evident-charts/scripts/side_by_side.py",
)


def release_files(root):
    """Validate before writing; return the version and frozen package bytes."""
    content = {}
    for name in FILES:
        path = root / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root):
            raise ValueError(f"symlink resource: {name}")
        if not path.is_file():
            raise ValueError(f"missing release file: {name}")
        content[name] = path.read_bytes()
    versions = {}
    manifests = {}
    for name in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
                 "gemini-extension.json"):
        manifests[name] = json.loads(content[name])
        versions[name] = manifests[name]["version"]
    match = re.search(r'^\s+version:\s*"?([^"\n]+)"?',
                      content["skills/evident-charts/SKILL.md"].decode(), re.M)
    if not match:
        raise ValueError("missing skill version")
    versions["SKILL.md"] = match.group(1).strip()
    version = versions["plugin.json"]
    if len(set(versions.values())) != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"release versions must agree: {versions}")
    interface = manifests["plugin.json"]["extensions"]["com.openai"]["interface"]
    if interface != manifests[".codex-plugin/plugin.json"]["interface"]:
        raise ValueError("OpenAI interface metadata must agree")
    for field, limit in (("displayName", 30), ("shortDescription", 30),
                         ("longDescription", 4000), ("developerName", 80)):
        value = interface.get(field)
        if not isinstance(value, str) or not 0 < len(value) <= limit:
            raise ValueError(f"{field} must contain 1-{limit} characters")
    for field in ("logo", "composerIcon"):
        path = interface.get(field, "")
        if not path.startswith("./") or path[2:] not in content:
            raise ValueError(f"missing packaged {field}: {path}")
    return version, content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="ZIP path (default: dist/evident-charts-VERSION.zip)")
    args = parser.parse_args()
    try:
        version, content = release_files(ROOT)
        output = args.output or ROOT / "dist" / f"evident-charts-{version}.zip"
        if output.resolve() in {(ROOT / name).resolve() for name in FILES}:
            raise ValueError("output would overwrite a release file")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(content):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content[name], compresslevel=9)
        print(f"{output.resolve()} ({len(content)} files)")
        print(f"SHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}")
    except (OSError, ValueError, KeyError) as error:
        print(f"Release error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
