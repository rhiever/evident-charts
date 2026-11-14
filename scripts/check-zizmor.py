#!/usr/bin/env python3
"""Run the pinned zizmor release offline against this repository."""

import argparse
import hashlib
import hmac
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

VERSION = "1.32.0"
RELEASE = f"https://github.com/zizmorcore/zizmor/releases/download/v{VERSION}"
ASSETS = {
    ("Darwin", "arm64"): (
        "aarch64-apple-darwin",
        "6efed18c4539a663fd3c851a2be9533fd8456c4e646d9416206da059154a0d3c",
    ),
    ("Darwin", "x86_64"): (
        "x86_64-apple-darwin",
        "6983143c719ada6845a69cc4dd2bacc215f971662fecd8bbd2678388e5ce5969",
    ),
    ("Linux", "aarch64"): (
        "aarch64-unknown-linux-gnu",
        "cb152b207f815116d7fa1c1ee4614f61578803351395052908095e79adfd9fd0",
    ),
    ("Linux", "x86_64"): (
        "x86_64-unknown-linux-gnu",
        "bb110cc765eca9cd7efb2e284a956be5974c60027b0970f16397d86208a9957b",
    ),
}
ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    ".github/workflows/actions.lock",
    ".github/zizmor.yml",
    ".github/zizmor.yaml",
    "zizmor.yml",
    "zizmor.yaml",
}


def input_path(path: str) -> bool:
    parts = path.split("/")
    filename = parts[-1]
    if path in CONFIG:
        return True
    if not filename.endswith((".yml", ".yaml")):
        return False
    return (
        (len(parts) == 3 and parts[:2] == [".github", "workflows"])
        or (
            len(parts) == 2
            and parts[0] == ".github"
            and filename in {"dependabot.yml", "dependabot.yaml"}
        )
        or filename in {"action.yml", "action.yaml"}
        or path in {".pre-commit-config.yaml", ".pre-commit-hooks.yaml"}
    )


def audit_path(path: str) -> bool:
    return (
        input_path(path)
        or path in {"scripts/check-zizmor.py", ".github/check-zizmor.py"}
        or path.split("/")[-1] == ".gitignore"
    )


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def changed_audit_input(
    ci_base: str | None, local_base: str | None, staged: bool
) -> bool:
    diff = ("diff", "--name-only", "--no-renames", "-z")
    try:
        if ci_base is not None:
            if not re.fullmatch(r"[0-9a-f]{40}", ci_base):
                raise ValueError("Missing or invalid pull request base")
            git("merge-base", "--is-ancestor", ci_base, "HEAD")
            paths = git(*diff, ci_base, "HEAD", "--")
        elif local_base is not None:
            revision = git(
                "rev-parse", "--verify", "--end-of-options", f"{local_base}^{{commit}}"
            )
            base = git("merge-base", revision.decode().strip(), "HEAD").decode().strip()
            paths = b"\0".join(
                (
                    git(*diff, base, "HEAD", "--"),
                    git(*diff, "--cached", "HEAD", "--"),
                    git(*diff, "--"),
                    git("ls-files", "--others", "--exclude-standard", "-z"),
                )
            )
        elif staged:
            paths = git(*diff, "--cached", "--")
        else:
            return True
    except (subprocess.CalledProcessError, ValueError):
        print(
            "Could not determine changed paths; scanning automation configuration.",
            flush=True,
        )
        return True
    return any(audit_path(os.fsdecode(path)) for path in paths.split(b"\0") if path)


def copy_inputs(destination: Path, staged: bool) -> None:
    # Git keeps tracked files eligible even if a new ignore rule matches them.
    args = ["ls-files", "--cached", "-z"]
    if not staged:
        args.extend(["--others", "--exclude-standard"])
    for entry in set(git(*args).split(b"\0")):
        path = os.fsdecode(entry)
        if not input_path(path):
            continue
        if staged:
            content = git("cat-file", "blob", f":{path}")
        else:
            source = ROOT / path
            if source.resolve() != source:
                raise ValueError(f"Automation input uses a symbolic link: {path}")
            try:
                content = source.read_bytes()
            except FileNotFoundError:
                continue  # A tracked path may have been removed in the worktree.
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def scan(output_format: str, archive_path: Path | None, staged: bool) -> int:
    system, machine = platform.system(), platform.machine()
    if (system, machine) not in ASSETS:
        raise ValueError(f"Unsupported zizmor platform: {system} {machine}")
    target, digest = ASSETS[system, machine]
    filename = f"zizmor-{target}.tar.gz"
    with tempfile.TemporaryDirectory(prefix="zizmor-") as temp:
        binary = Path(temp) / "zizmor"
        if archive_path is None:
            archive_path = Path(temp) / filename
            print(
                f"Downloading zizmor {VERSION} for {target}; the audit runs offline.",
                flush=True,
            )
            with (
                urlopen(f"{RELEASE}/{filename}", timeout=60) as source,
                archive_path.open("wb") as archive,
            ):
                shutil.copyfileobj(source, archive)
        with archive_path.open("rb") as archive:
            checksum = hashlib.sha256()
            for chunk in iter(lambda: archive.read(1024 * 1024), b""):
                checksum.update(chunk)
            if not hmac.compare_digest(checksum.hexdigest(), digest):
                raise ValueError(f"zizmor archive SHA-256 mismatch: {archive_path}")
            archive.seek(0)
            with tarfile.open(fileobj=archive, mode="r:gz") as tar:
                member = tar.getmember("zizmor")
                if not member.isfile():
                    raise ValueError(
                        "The zizmor archive does not contain a regular executable"
                    )
                source = tar.extractfile(member)
                if source is None:
                    raise ValueError("Could not read the zizmor executable")
                with source, binary.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
        binary.chmod(0o700)
        env = os.environ.copy()
        for name in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "ZIZMOR_GITHUB_TOKEN",
            "ZIZMOR_CONFIG",
        ):
            env.pop(name, None)
        audit_root = Path(temp) / "inputs"
        audit_root.mkdir()
        copy_inputs(audit_root, staged)
        for name in git("rev-parse", "--local-env-vars").decode().splitlines():
            env.pop(name, None)
        subprocess.run(
            ["git", "init", "--quiet", "--template="],
            cwd=audit_root,
            env=env,
            check=True,
        )
        result = subprocess.run(
            [
                str(binary),
                "--offline",
                "--strict-collection",
                "--collect=all",
                "--no-progress",
                f"--format={output_format}",
                ".",
            ],
            cwd=audit_root,
            env=env,
            stderr=subprocess.PIPE,
            check=False,
        )
        # Upstream reserves exit 3 for a successful collection with no auditable inputs.
        if result.returncode == 3:
            print("No automation configuration to audit.")
            return 0
        sys.stderr.buffer.write(result.stderr)
        return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--changed-since", metavar="SHA", help="Compare the CI checkout to the PR base."
    )
    scope.add_argument(
        "--local-changes",
        metavar="BASE",
        nargs="?",
        const="origin/main",
        help="Check branch, staged, unstaged and untracked changes against BASE (default: origin/main).",
    )
    scope.add_argument(
        "--staged",
        action="store_true",
        help="Audit the index if relevant files are staged.",
    )
    parser.add_argument("--format", choices=("plain", "github"), default="plain")
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use a previously downloaded archive and verify it before running.",
    )
    args = parser.parse_args()
    try:
        if not changed_audit_input(args.changed_since, args.local_changes, args.staged):
            print("No automation configuration changes; skipping zizmor.")
            return 0
        return scan(args.format, args.archive, args.staged)
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
        tarfile.TarError,
    ) as exc:
        print(f"zizmor: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
