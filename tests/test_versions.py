"""The version must match everywhere users' installers read it."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_versions_match():
    def manifest(path):
        return json.loads((ROOT / path).read_text())["version"]

    skill = (ROOT / "skills/evident-charts/SKILL.md").read_text()
    versions = {
        ".claude-plugin/plugin.json": manifest(".claude-plugin/plugin.json"),
        ".codex-plugin/plugin.json": manifest(".codex-plugin/plugin.json"),
        "gemini-extension.json": manifest("gemini-extension.json"),
        "SKILL.md": re.search(r'^\s+version:\s*"?([^"\n]+)"?', skill, re.M).group(1),
    }
    assert len(set(versions.values())) == 1, versions
