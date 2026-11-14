# AGENTS.md

evident-charts is an agent skill for explanatory charts. The installable skill is `skills/evident-charts/`; everything else supports it.

## Commands

- Setup: `uv sync --locked` (uv 0.13.7 or newer, Python 3.14.10 by default).
- Ruff pre-commit checks: `prek run --all-files`. Keep the managed Gitleaks hook when enabling prek.
- Python lint and format: `uv run --locked ruff check .` and `uv run --locked ruff format --check .`. Pre-commit and CI require formatting to pass and report lint findings as advisory.
- Tests: `uv run --locked python -m pytest -q tests`. Set `CHROME_PATH` to a Chrome or Chromium binary for SVG layout tests. The suite also tests spec checks without Chrome.
- Audit automation changes: `python3 scripts/check-zizmor.py --local-changes`.
- Lint a matplotlib chart: `python skills/evident-charts/scripts/check_chart.py <chart.py> --dest <preset>` (`--list-checks` for names)
- Lint an SVG from any other stack: `python skills/evident-charts/scripts/check_svg.py <chart.svg> --dest <preset> [--spec <json>]` (needs Chrome)
- Validate palettes: `python skills/evident-charts/scripts/check_palette.py --preset all`
- Prepare a release: sync versions in root, Claude, Codex, Gemini, and skill metadata; update `CHANGELOG.md`; run tests, palette checks, `gh skill publish --dry-run`, `claude plugin validate --strict .`, and `uvx --from "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" skills-ref validate skills/evident-charts`.
- Package: `python3 scripts/build_release.py` writes `dist/evident-charts-VERSION.zip` and prints its SHA256. Update its explicit file list when adding resources. Keep root and Codex OpenAI interface metadata identical; paths start with `./` and resolve from the plugin root.
- Acceptance: use `docs/acceptance.md` from the unpacked ZIP; record results and skipped checks in `.local/`. Check user-facing prose with writing-humanizer; instructions and code are excluded by that skill.
- Publish only when explicitly requested: push and run `gh skill publish --tag vX.Y.Z`, or upload the ZIP to the OpenAI dashboard. Developer verification, hosted scans, review, and approval happen outside this repo.

## Reviewing pull requests

- Review `Code scanning results / CodeQL` in PR Checks and inline annotations before merging, even when the check is advisory. Fix confirmed findings introduced by the PR and report any unresolved findings with the reason.
- For pull requests that change `pyproject.toml` or `uv.lock`, open `CI / Dependency review` in PR Checks and read the job summary and warning annotations before merging. Verify that the run obtained dependency data. Address confirmed vulnerabilities introduced by the PR or explain why they remain.

## Writing the skill

- The audience is agents. Be concise; use minimal formatting.
- Encode behavior as data (`assets/*.json`), code (`scripts/`), or CLI commands first. Use prose only for judgment, and keep it short.
- Edit holistically: revise or remove outdated text instead of appending. The skill must always read as if written once.
- SKILL.md is a router (workflow, core defaults, file table). Details live in `references/`, read only when their decision comes up.
- Rule format, one line each: `ID [tag] rule. Break: escape hatch. check: name`. Tags: `[E]` experimental evidence, `[P]` practitioner consensus, `[T]` taste or convention.
- Charts the skill produces are finished products: nothing addressed to the user appears on a chart.
- Cite and paraphrase third-party guidance; never copy its text.

## Changing rules

- Tag each new or changed rule honestly and key its citation in `references/sources.md` to the same ID.
- Renumber cleanly (no suffixed IDs) and update every cross-reference.
- `check:` names must match `check_chart.py --list-checks` or `palette`; `check_svg.py` reuses a subset of them.
- Any script behavior change gets a fixture and a test in `tests/`.

## Evaluating

- Keep private notes, eval data, and results in `.local/` (gitignored). Never commit them.
- Iterate on dev cases; measure on held-out cases you never tune on.
- Never copy eval data or answers into rule examples.
- Compare against the same agent without the skill, judging rendered images, not code.

<!-- shared-dev-standards:start -->
## Shared development rules (v1)

- Start edits in an isolated worktree from a verified base. A managed cloud checkout counts as isolation.
- Before cleanup, preserve commits, changes, and artifacts. Verify the merge or handoff, stop associated processes, and remove only the finished worktree.
- Require a PR and passing CI for default-branch changes. Route checks from the complete PR diff. Include affected contracts and dependencies. Run full checks for unknown scope.
- Use pinned tools and locked installs. Use the same repo checks in CI and dev. Add focused regressions and report checks that skipped.
- Keep private inputs, credentials, and artifacts out of Git and cloud setup. Use synthetic fixtures and disposable services in CI. Scan for secrets and minimize CI permissions.
- Keep dependency changes focused. Test public compatibility floors separately from the dev runtime.
- Follow the repo's release rules. Treat a merge that deploys as a release. Verify the live revision and record the rollback target.
<!-- shared-dev-standards:end -->
