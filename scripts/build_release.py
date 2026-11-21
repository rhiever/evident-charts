#!/usr/bin/env python3
"""Build a reproducible plugin ZIP from an explicit file list, or the script-free
Claude plugin directory edition (editions/claude-directory/edition.json). Python 3.12+."""

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
EDITION = "editions/claude-directory/edition.json"
THEMES_MD = "skills/evident-charts/references/themes.md"
CHECK_ENDING = re.compile(r"(?<=\.) check: [a-z0-9, -]+$", re.MULTILINE)
FENCES = {".mplstyle": "text", ".R": "r", ".css": "css", ".js": "js"}


def read_file(root, name):
    path = root / name
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root):
        raise ValueError(f"symlink resource: {name}")
    if not path.is_file():
        raise ValueError(f"missing release file: {name}")
    return path.read_bytes()


def release_files(root):
    """Validate before writing; return the version and frozen package bytes."""
    content = {name: read_file(root, name) for name in FILES}
    versions = {}
    manifests = {}
    for name in (
        "plugin.json",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "gemini-extension.json",
    ):
        manifests[name] = json.loads(content[name])
        versions[name] = manifests[name]["version"]
    match = re.search(
        r'^\s+version:\s*"?([^"\n]+)"?',
        content["skills/evident-charts/SKILL.md"].decode(),
        re.MULTILINE,
    )
    if not match:
        raise ValueError("missing skill version")
    versions["SKILL.md"] = match.group(1).strip()
    version = versions["plugin.json"]
    if len(set(versions.values())) != 1 or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"release versions must agree: {versions}")
    interface = manifests["plugin.json"]["extensions"]["com.openai"]["interface"]
    if interface != manifests[".codex-plugin/plugin.json"]["interface"]:
        raise ValueError("OpenAI interface metadata must agree")
    for field, limit in (
        ("displayName", 30),
        ("shortDescription", 30),
        ("longDescription", 4000),
        ("developerName", 80),
    ):
        value = interface.get(field)
        if not isinstance(value, str) or not 0 < len(value) <= limit:
            raise ValueError(f"{field} must contain 1-{limit} characters")
    for field in ("logo", "composerIcon"):
        path = interface.get(field, "")
        if not path.startswith("./") or path[2:] not in content:
            raise ValueError(f"missing packaged {field}: {path}")
    return version, content


def themes_markdown(root, names):
    parts = [
        (
            "# Themes\n\n"
            "House look for stacks without a JSON theme. Write a block to a file in "
            "a scratch folder, then use it as its header comment shows. Sizes "
            "mirror `assets/presets.json`.\n"
        )
    ]
    for name in names:
        body = read_file(root, name).decode().strip()
        if "```" in body:
            raise ValueError(f"theme contains a code fence: {name}")
        fence = FENCES.get(Path(name).suffix)
        if fence is None:
            raise ValueError(f"no code fence for theme type: {name}")
        parts.append(f"\n## {Path(name).name}\n\n```{fence}\n{body}\n```\n")
    return "".join(parts)


def directory_files(root):
    """Return the Claude directory edition as {path: bytes}, validated."""
    _, content = release_files(root)
    spec = json.loads(read_file(root, EDITION))
    named = [*spec["copy"], *spec["copy_as"], *spec["copy_as"].values()]
    named += [*spec["overlays"], *spec["themes"], *spec["exclude"], *spec["replace"]]
    named += [overlay["from"] for overlay in spec["overlays"].values()]
    for name in named:
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError(f"edition path must stay inside the repo: {name}")
    sources = {*spec["copy"], *spec["copy_as"].values(), *spec["overlays"]}
    accounted = sources | {*spec["themes"], *spec["exclude"]}
    if missing := sorted(set(FILES) - accounted):
        raise ValueError(f"edition.json must copy or exclude: {', '.join(missing)}")
    copied = {name: read_file(root, name) for name in spec["copy"]}
    copied |= {dest: read_file(root, src) for dest, src in spec["copy_as"].items()}
    text = {n: d.decode() for n, d in copied.items() if not n.endswith(".png")}
    for name, overlay in spec["overlays"].items():
        expected = overlay.get("source_sha256")
        if hashlib.sha256(content[name]).hexdigest() != expected:
            raise ValueError(
                f"stale overlay for {name}: update {overlay['from']} to match, "
                "then set its source_sha256"
            )
        text[name] = read_file(root, overlay["from"]).decode()
    text[THEMES_MD] = themes_markdown(root, spec["themes"])
    for name in spec["strip_checks"]:
        text[name] = CHECK_ENDING.sub("", text[name])
    for name, pairs in spec["replace"].items():
        for old, new in pairs:
            if text[name].count(old) != 1:
                raise ValueError(f"replacement not found once in {name}: {old[:60]!r}")
            text[name] = text[name].replace(old, new)
    manifest = json.loads(content[".claude-plugin/plugin.json"])
    for field in spec["plugin"]["drop"]:
        manifest.pop(field, None)
    manifest["description"] = spec["plugin"]["description"]
    text[".claude-plugin/plugin.json"] = json.dumps(manifest, indent=2) + "\n"
    skill = text["skills/evident-charts/SKILL.md"]
    match = re.search(r'^\s+version:\s*"?([^"\n]+)"?', skill, re.MULTILINE)
    if not match or match.group(1).strip() != manifest["version"]:
        raise ValueError("edition SKILL.md version must match plugin.json")
    files = copied | {name: data.encode() for name, data in text.items()}
    for name, data in files.items():
        if name != "LICENSE" and Path(name).suffix not in spec["allowed_suffixes"]:
            raise ValueError(f"file type not allowed in the edition: {name}")
        if name.endswith(".png"):
            continue
        for pattern in spec["banned"]:
            if re.search(pattern, data.decode(), re.MULTILINE):
                raise ValueError(f"banned text {pattern!r} in {name}")
        if name.endswith(".json"):
            json.loads(data)
    return files


def write_directory(root, output):
    files = directory_files(root)
    if output.exists() and any(p.name != ".git" for p in output.iterdir()):
        raise ValueError(f"output must be empty apart from .git: {output}")
    for name in sorted(files):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[name])
    print(f"{output.resolve()} ({len(files)} files)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--output",
        type=Path,
        help="ZIP path (default: dist/evident-charts-VERSION.zip)",
    )
    target.add_argument(
        "--claude-directory",
        type=Path,
        metavar="DIR",
        help="write the script-free Claude directory edition to DIR (empty or .git only)",
    )
    args = parser.parse_args()
    try:
        if args.claude_directory:
            write_directory(ROOT, args.claude_directory)
            return 0
        version, content = release_files(ROOT)
        output = args.output or ROOT / "dist" / f"evident-charts-{version}.zip"
        if output.resolve() in {(ROOT / name).resolve() for name in FILES}:
            raise ValueError("output would overwrite a release file")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
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
