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
    shutil.copytree(ROOT, path, ignore=shutil.ignore_patterns(
        ".git", ".local", "__pycache__", ".pytest_cache", ".venv", "dist"))
    return path


def build(source, output):
    return subprocess.run([sys.executable, str(source / "scripts/build_release.py"),
                           "--output", str(output)], capture_output=True, text=True)


def test_archive_is_complete_and_reproducible(source, tmp_path):
    (source / ".local").mkdir()
    (source / ".local/private.txt").write_text("private")
    (source / "skills/evident-charts/scripts/__pycache__").mkdir()
    (source / "skills/evident-charts/scripts/__pycache__/noise.pyc").write_bytes(b"noise")
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = build(source, first)
    assert result.returncode == 0, result.stderr
    assert build(source, second).returncode == 0
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        names = set(archive.namelist())
        assert {"plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json",
                ".claude-plugin/marketplace.json", "gemini-extension.json", "LICENSE",
                "README.md", "CHANGELOG.md", "docs/acceptance.md", "examples/hero.png"} <= names
        resources = {p.relative_to(source).as_posix()
                     for p in (source / "skills/evident-charts").rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts}
        assert resources <= names
        assert not any(n.startswith(("tests/", ".local/", ".git/", "scripts/"))
                       or "__pycache__" in n or n == "AGENTS.md" for n in names)
        root = json.loads(archive.read("plugin.json"))
        overlay = json.loads(archive.read(".codex-plugin/plugin.json"))
        interface = root["extensions"]["com.openai"]["interface"]
        assert interface == overlay["interface"]
        assert 0 < len(interface["shortDescription"]) <= 30
        assert 0 < len(interface["longDescription"]) <= 4000
        skill_ui = archive.read("skills/evident-charts/agents/openai.yaml").decode()
        skill_subtitle = re.search(r'^\s+short_description:\s*"([^"]+)"', skill_ui, re.M).group(1)
        assert 25 <= len(skill_subtitle) <= 64
        for field in ("logo", "composerIcon"):
            data = archive.read(interface[field].removeprefix("./"))
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            width, height = struct.unpack(">II", data[16:24])
            assert width == height and width > 0


def test_missing_icon_fails_without_archive(source, tmp_path):
    manifest = json.loads((source / "plugin.json").read_text())
    icon = manifest["extensions"]["com.openai"]["interface"]["logo"]
    (source / icon).unlink()
    output = tmp_path / "release.zip"
    result = build(source, output)
    assert result.returncode != 0
    assert "missing" in result.stderr.lower()
    assert not output.exists()


def test_readme_links_resolve_in_archive(source, tmp_path):
    output = tmp_path / "release.zip"
    result = build(source, output)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        links = re.findall(r'\]\(([^\s)]+)\)', archive.read("README.md").decode())
        for link in links:
            if "://" not in link and not link.startswith("#"):
                target = link.split("#")[0]
                present = any(n.startswith(target) for n in names) if target.endswith("/") else target in names
                assert present, f"missing README target: {link}"


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
