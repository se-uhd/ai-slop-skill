# CLAUDE.md

Maintainer guidance for the `ai-slop` skill bundle. (This is the repo's own
development guide — not the `WRITING.md` that `/ai-slop:init` generates for paper
repos.)

## Release protocol — read before bumping the version

Releases use CalVer with a per-month revision counter: `YYYY-MM` for the first
release of a month (implicit `rev0`), then `YYYY-MM_rev1`, `_rev2`, … (see README
"Versioning"). Every release MUST follow these rules — they exist because they
have been broken before:

1. **Every rev bump is its own commit AND a matching git tag.** After bumping
   the version, create `git tag YYYY-MM_revN` on that commit and push it. A
   release without its tag is not done. List the current month's tags with
   `git tag -l "$(date +%Y-%m)*"`; the next rev is the highest current rev + 1
   (the bare `YYYY-MM` tag is rev0, so the release after it is `_rev1`).
2. **Never amend, rebase, or rewrite a commit that is already tagged, released,
   or pushed.** If more work is needed after a release, it is a NEW rev with a
   NEW commit and tag — never a re-cut of the released one. Amending a released
   commit orphans its tag and breaks the linear release history. (This is the
   mistake that produced the dangling-tag situation at the release now
   numbered `2026-05_rev15`.)
3. **Keep the 10 version callsites in sync.** The version string lives in
   `plugins/ai-slop/.claude-plugin/plugin.json` (canonical),
   `.claude-plugin/marketplace.json`, the `version:` frontmatter of each
   `SKILL.md`, the `**Skill version:**` line in `review/SKILL.md`'s report
   template, and the `skill version <X>` line in `init/SKILL.md`'s WRITING.md
   header. `test_version_strings_in_sync` in the smoke suite enforces this.
4. **Run the smoke suite before every commit:**
   `python3 plugins/ai-slop/scripts/tests/run_smoke.py` — it must be green.
5. **Release tags must be ancestors of `main`.** The release history is linear:
   `… revN → revN+1 → …`. If a tag is not reachable from `main`, the history is
   broken and must be repaired before the next release.
6. **Refresh the bundled tropes snapshot with every rev.** Before bumping, run
   `python3 plugins/ai-slop/scripts/refresh_tropes.py` to re-pull
   `plugins/ai-slop/shared/tropes-snapshot.md` from upstream so the offline
   fallback never drifts from the live catalog. The snapshot is kept
   bit-identical to upstream: when upstream is unchanged the script reports
   "already up to date" and leaves the file untouched, so the rev carries no
   snapshot change; when it has changed, commit the refreshed catalog as part
   of the rev. Never hand-edit the snapshot — edits are overwritten on the next
   refresh (see `tropes-snapshot.ATTRIBUTION.md`).

## Other conventions

- First-party Python helpers are stdlib-only; the only vendored code is
  PyMarkdown (plus its pure-Python deps) under `scripts/_vendor/`. Only
  `lint_markdown.py` and `check_baseline.py` may import from the vendored
  tree — both are synced from the upstream pymarkdown-skill repo (with
  `refresh_vendor.py`), so do not edit them here; fix them upstream and
  re-sync. Do not add pip-installed runtime deps.
- All first-party Markdown must lint clean:
  `python3 plugins/ai-slop/scripts/lint_markdown.py <file>`.
- Generated artifacts (`ai-slop-report.md`, `grounding-cites.json`,
  `grounding-quotes.json`) are never committed; the skills add them to the
  target repo's `.gitignore`.
