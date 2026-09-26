# AGENTS.md

evident-charts is an agent skill for explanatory charts. The installable skill is `skills/evident-charts/`; everything else supports it.

## Commands

- Tests: `uv run --with matplotlib --with numpy --with pandas --with pytest pytest -q tests`
- Lint a matplotlib chart: `python skills/evident-charts/scripts/check_chart.py <chart.py> --dest <preset>` (`--list-checks` for names)
- Validate palettes: `python skills/evident-charts/scripts/check_palette.py --preset all`
- Release: bump the version (kept in sync by `tests/test_versions.py`), update `CHANGELOG.md`, run tests plus `gh skill publish --dry-run`, `claude plugin validate --strict .` and `uvx --from "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" skills-ref validate skills/evident-charts`, push, then `gh skill publish --tag vX.Y.Z`.

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
- `check:` names must match `check_chart.py --list-checks` or `palette`.
- Any script behavior change gets a fixture and a test in `tests/`.

## Evaluating

- Keep private notes, eval data, and results in `.local/` (gitignored). Never commit them.
- Iterate on dev cases; measure on held-out cases you never tune on.
- Never copy eval data or answers into rule examples.
- Compare against the same agent without the skill, judging rendered images, not code.
