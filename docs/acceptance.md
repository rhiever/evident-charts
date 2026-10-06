# Release acceptance

Test the ZIP, not the source checkout. Keep results in `.local/`, with client versions and any skipped checks.

1. Build with `python3 scripts/build_release.py`. Unpack into a scratch directory. Confirm `plugin.json`, compatibility manifests, icons, license, and `skills/evident-charts/` are at its root.
2. Install the unpacked skill into an isolated directory: `gh skill install <unpacked-dir> evident-charts --from-local --dir <scratch-dir>/installed`. For plugin loading, start Claude Code with `claude --plugin-dir <unpacked-dir>` in a scratch project. Test Codex discovery without changing configuration: `codex -c 'marketplaces.release={source_type="local",source="<absolute-unpacked-dir>"}' plugin list --marketplace evident-charts --available --json`. Confirm the plugin name and release version. Full agent runs need a valid client login.
3. Create: ask for a chart from a small CSV. Confirm the output opens, numbers match the CSV, and the reply names checks run and review method.
4. Critique: provide a chart with overlapping labels or a truncated bar baseline. Confirm ranked fixes cite rules. Image-only critique must mark source numbers not checkable. A critique request alone must not change the chart.
5. User instructions: require self-review and a specific style. Confirm no reviewer is spawned and the style is retained. Require a truncated baseline with a note; confirm the request is preserved and the failed baseline check is reported.
6. Missing tools: test without Chrome, then without Python or image access. Supported spec checks should still run without Chrome. Every unavailable check or review must be named as skipped; no unchecked result is described as verified.
7. Irrelevant request: ask to fix an SQL query. Confirm no chart workflow starts.
8. Resource paths: run the installed scripts from outside the install directory. Confirm palettes, presets, themes, references, and `measure_svg.js` resolve. Run palette checks and a matplotlib check; run SVG checks with Chrome and a supported spec without Chrome.

Record each case as pass, fail, or skipped with a reason. Client loading and agent behavior are manual checks; script tests alone do not prove them.
