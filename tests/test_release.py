"""Exercise the release archive, including failures that must not emit a ZIP."""

import json
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "source"
    shutil.copytree(
        ROOT,
        path,
        ignore=shutil.ignore_patterns(
            ".git", ".local", "__pycache__", ".pytest_cache", ".venv", "dist"
        ),
    )
    return path


def build(source, output):
    return subprocess.run(
        [
            sys.executable,
            str(source / "scripts/build_release.py"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )


def test_archive_is_complete_and_reproducible(source, tmp_path):
    (source / ".local").mkdir()
    (source / ".local/private.txt").write_text("private")
    (source / "skills/evident-charts/scripts/__pycache__").mkdir()
    (source / "skills/evident-charts/scripts/__pycache__/noise.pyc").write_bytes(
        b"noise"
    )
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = build(source, first)
    assert result.returncode == 0, result.stderr
    assert build(source, second).returncode == 0
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        names = set(archive.namelist())
        assert {
            "plugin.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            "gemini-extension.json",
            "LICENSE",
            "README.md",
            "CHANGELOG.md",
            "docs/acceptance.md",
            "examples/hero.png",
        } <= names
        resources = {
            p.relative_to(source).as_posix()
            for p in (source / "skills/evident-charts").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        assert resources <= names
        assert not any(
            n.startswith(("tests/", ".local/", ".git/", "scripts/"))
            or "__pycache__" in n
            or n == "AGENTS.md"
            for n in names
        )
        root = json.loads(archive.read("plugin.json"))
        overlay = json.loads(archive.read(".codex-plugin/plugin.json"))
        interface = root["extensions"]["com.openai"]["interface"]
        assert interface == overlay["interface"]
        assert 0 < len(interface["shortDescription"]) <= 30
        assert 0 < len(interface["longDescription"]) <= 4000
        skill_ui = archive.read("skills/evident-charts/agents/openai.yaml").decode()
        skill_subtitle = re.search(
            r'^\s+short_description:\s*"([^"]+)"', skill_ui, re.MULTILINE
        ).group(1)
        assert 25 <= len(skill_subtitle) <= 64
        for field in ("logo", "composerIcon"):
            data = archive.read(interface[field].removeprefix("./"))
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            width, height = struct.unpack(">II", data[16:24])
            assert width == height and width > 0

        links = re.findall(r"\]\(([^\s)]+)\)", archive.read("README.md").decode())
        for link in links:
            if "://" not in link and not link.startswith("#"):
                target = link.split("#")[0]
                present = (
                    any(n.startswith(target) for n in names)
                    if target.endswith("/")
                    else target in names
                )
                assert present, f"missing README target: {link}"


def test_missing_icon_fails_without_archive(source, tmp_path):
    manifest = json.loads((source / "plugin.json").read_text())
    icon = manifest["extensions"]["com.openai"]["interface"]["logo"]
    (source / icon).unlink()
    output = tmp_path / "release.zip"
    result = build(source, output)
    assert result.returncode != 0
    assert "missing" in result.stderr.lower()
    assert not output.exists()


def test_version_mismatch_fails_without_archive(source, tmp_path):
    path = source / "gemini-extension.json"
    manifest = json.loads(path.read_text())
    manifest["version"] = "99.0.0"
    path.write_text(json.dumps(manifest))
    output = tmp_path / "release.zip"
    result = build(source, output)
    assert result.returncode != 0
    assert "version" in result.stderr.lower()
    assert not output.exists()


def test_symlink_resource_is_rejected(source, tmp_path):
    path = source / "skills/evident-charts/assets/palettes.json"
    outside = tmp_path / "outside.json"
    path.rename(outside)
    path.symlink_to(outside)
    output = tmp_path / "release.zip"
    result = build(source, output)
    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()
    assert not output.exists()


def build_directory(source, output):
    return subprocess.run(
        [
            sys.executable,
            str(source / "scripts/build_release.py"),
            "--claude-directory",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def tree(path):
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in sorted(path.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(path).parts
    }


DIRECTORY_BANNED = (
    r"scripts/",
    r"check_(chart|svg|palette)",
    r"side_by_side",
    r"\bev\.",
    r"\bevident\.(?!mplstyle\b)\w",
    r"\bcheck: ",
)


def test_claude_directory_edition_ships_only_allowed_files(source, tmp_path):
    spec = json.loads((source / "editions/claude-directory/edition.json").read_text())
    first, second = tmp_path / "first", tmp_path / "second"
    result = build_directory(source, first)
    assert result.returncode == 0, result.stderr
    assert build_directory(source, second).returncode == 0
    files = tree(first)
    assert files == tree(second)
    assert {
        ".claude-plugin/plugin.json",
        "LICENSE",
        "README.md",
        "skills/evident-charts/SKILL.md",
        "skills/evident-charts/references/themes.md",
    } <= set(files)
    assert ".claude-plugin/icon.png" in files
    for name, data in files.items():
        assert name == "LICENSE" or Path(name).suffix in {".md", ".json", ".png"}
        if name.endswith(".png"):
            continue
        text = data.decode()
        for pattern in DIRECTORY_BANNED:
            assert not re.search(pattern, text), (name, pattern)
        if name.endswith(".json"):
            json.loads(text)
        for path in re.findall(r"`((?:references|assets)/[\w./-]+\.\w+)`", text):
            assert f"skills/evident-charts/{path}" in files, (name, path)
    manifest = json.loads(files[".claude-plugin/plugin.json"])
    assert "supportUrl" not in manifest
    assert manifest["description"] == spec["plugin"]["description"]
    skill = files["skills/evident-charts/SKILL.md"].decode()
    version = re.search(r'^\s+version:\s*"([^"]+)"', skill, re.MULTILINE).group(1)
    assert manifest["version"] == version
    readme = files["README.md"].decode()
    assert len(readme.split()) >= 40
    for link in re.findall(r"\]\(([^\s)]+)\)", readme):
        assert "://" in link or link in files, link
    themes = files["skills/evident-charts/references/themes.md"].decode()
    for theme in spec["themes"]:
        body = (source / theme).read_text().strip()
        assert body.splitlines()[-1] in themes


def test_claude_directory_overlay_drift_fails(source, tmp_path):
    skill = source / "skills/evident-charts/SKILL.md"
    skill.write_text(skill.read_text() + "\nNew rule.\n")
    output = tmp_path / "edition"
    result = build_directory(source, output)
    assert result.returncode != 0
    assert "stale overlay" in result.stderr.lower()
    assert not output.exists()


def test_claude_directory_replacement_drift_fails(source, tmp_path):
    critique = source / "skills/evident-charts/references/critique.md"
    critique.write_text(critique.read_text().replace("scripts/side_by_side.py", "x"))
    output = tmp_path / "edition"
    result = build_directory(source, output)
    assert result.returncode != 0
    assert "replacement not found" in result.stderr.lower()
    assert not output.exists()


def test_claude_directory_refuses_nonempty_output(source, tmp_path):
    output = tmp_path / "edition"
    output.mkdir()
    (output / ".git").write_text("gitdir: elsewhere")
    (output / "stale.md").write_text("stale")
    result = build_directory(source, output)
    assert result.returncode != 0
    assert "must be empty" in result.stderr.lower()
    (output / "stale.md").unlink()
    assert build_directory(source, output).returncode == 0
    assert (output / ".git").read_text() == "gitdir: elsewhere"


def test_claude_directory_rejects_script_mentions(source, tmp_path):
    libraries = source / "skills/evident-charts/references/libraries.md"
    libraries.write_text(libraries.read_text() + "\nRun check_chart.py --dest blog.\n")
    output = tmp_path / "edition"
    result = build_directory(source, output)
    assert result.returncode != 0
    assert "banned text" in result.stderr.lower()
    assert not output.exists()


def test_claude_directory_accounts_for_every_release_file(source, tmp_path):
    path = source / "editions/claude-directory/edition.json"
    spec = json.loads(path.read_text())
    spec["copy"].remove("skills/evident-charts/references/sources.md")
    path.write_text(json.dumps(spec))
    output = tmp_path / "edition"
    result = build_directory(source, output)
    assert result.returncode != 0
    assert "must copy or exclude" in result.stderr.lower()
    assert not output.exists()
