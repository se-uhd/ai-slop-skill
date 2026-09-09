# CLAUDE.md

Maintainer guidance for the `ai-slop` skill bundle. (This file is the repo's own
development guide, not the `WRITING.md` that `/ai-slop:init` generates for paper
repos.)

## Release protocol (read before bumping the version)

Releases use CalVer with a per-month revision counter: `YYYY-MM` for the first
release of a month (implicit `rev0`), then `YYYY-MM_rev1`, `_rev2`, ... (see README
"Versioning"). Every release MUST follow these rules. They exist because they
have been broken before:

1. **Every rev bump is its own commit AND a matching git tag.** After bumping
   the version, create `git tag YYYY-MM_revN` on that commit and push it. A
   release without its tag is not done. List the current month's tags with
   `git tag -l "$(date +%Y-%m)*"`; the next rev is the highest current rev + 1
   (the bare `YYYY-MM` tag is rev0, so the release after it is `_rev1`).
2. **Never amend, rebase, or rewrite a commit that is already tagged, released,
   or pushed.** If more work is needed after a release, it is a NEW rev with a
   NEW commit and tag, never a re-cut of the released commit. Amending a released
   commit orphans its tag and breaks the linear release history. (Amending a released commit is the
   mistake that produced the dangling-tag situation at the release now
   numbered `2026-05_rev15`.)
3. **Keep the 10 version callsites in sync.** The version string is in
   `plugins/ai-slop/.claude-plugin/plugin.json` (canonical),
   `.claude-plugin/marketplace.json`, the `version:` frontmatter of each
   `SKILL.md`, the `**Skill version:**` line in `review/SKILL.md`'s report
   template, and the `skill version <X>` line in `init/SKILL.md`'s WRITING.md
   header. `test_version_strings_in_sync` in the smoke suite enforces this.
4. **Run the smoke suite before every commit:**
   `python3 plugins/ai-slop/scripts/tests/run_smoke.py`. It must be green.
5. **Release tags must be ancestors of `main`.** The release history is linear:
   `... revN -> revN+1 -> ...`. If a tag is not reachable from `main`, the history is
   broken and must be repaired before the next release.
6. **Refresh the bundled tropes snapshot with every rev.** Before bumping, run
   `python3 plugins/ai-slop/scripts/refresh_tropes.py` to re-pull
   `plugins/ai-slop/shared/tropes-snapshot.md` from upstream so the offline
   fallback never drifts from the live catalog. The script reads the same
   chain `fetch_tropes.py` uses, the tropes.fyi page first and the gist
   mirror second, and prints the source it took to stderr. The snapshot is kept
   bit-identical to upstream. When upstream is unchanged, the script reports
   "already up to date" and leaves the file untouched, so the rev carries no
   snapshot change. When it has changed, commit the refreshed catalog as part
   of the rev. Never hand-edit the snapshot. Edits are overwritten on the next
   refresh (see `tropes-snapshot.ATTRIBUTION.md`).

## Other conventions

- First-party Python helpers are stdlib-only. The only vendored code is
  PyMarkdown (plus its pure-Python deps) under `scripts/_vendor/`. Only
  `lint_markdown.py` and `check_baseline.py` may import from the vendored
  tree. Five paths are owned by the upstream pymarkdown-skill repo and
  copied in by its `sync/sync_to_skill.sh`, which stamps the upstream
  version in `scripts/.pymarkdown-skill-version`: `lint_markdown.py`,
  `check_baseline.py`, `refresh_vendor.py`, `_vendor/`, and
  `bundled_licenses/`. Do not edit any of them here. Fix them upstream,
  release there, and re-sync. Do not add pip-installed runtime deps.
- All first-party Markdown must lint clean:
  `python3 plugins/ai-slop/scripts/lint_markdown.py <file>`.
- **Changing the rules is a three-file edit.** A new or reworded rule in
  `shared/rules-general.md`, `shared/rules-scientific.md`, or
  `shared/rules-latex.md` also needs its numbered item in that layer's
  self-check section, and an entry in `shared/rules-rationale.md` whenever a
  reader could push back on it. Every rule carries a stable key
  (`G.`/`S.`/`L.` plus a slug) that reports and cross-references cite.
  `test_rule_keys_unique_and_resolvable` in the smoke suite enforces the key
  invariants: one key per rule bullet, unique across the layers, a key in
  every self-check item, and no dangling key in the layers, the rationale, or
  a `SKILL.md`.
- **Commit messages follow the general layer.** They are prose, and
  `/ai-slop:review-repo` scans them with every other file. A pushed message
  cannot be corrected afterwards, because rule 2 of the release protocol rules
  out rewriting a released commit, so the check happens before `git commit`.
  A scan of this repository's 76 commits found the recurring failures: a
  semicolon joining two independent clauses in 50 of them (100 uses, among them
  the boilerplate "Version bumped to X at all ten callsites; the tropes snapshot
  was already up to date", which is two sentences), a literal em-dash glyph
  (U+2014) in 8, and a count announced in front of continuous prose ("Eight
  existing rules take ..."). Write the subject line as an imperative ending in
  `; release YYYY-MM_revN` on a release commit. That suffix is the one semicolon
  the convention keeps, and the rest of the subject takes commas.
- **The bundle follows its own rules.** When a rule is added or tightened,
  sweep the repository's own prose for the pattern in the same rev: the
  Markdown files, the skill and command files, and the Python docstrings and
  comments. Released `CHANGELOG.md` entries are edited only to correct or
  complete the record, never to restate it. Upstream-owned files are left to
  their own repo.
- Generated artifacts (`ai-slop-report.md`, `grounding-cites.json`,
  `grounding-quotes.json`) are never committed. The skills add them to the
  target repo's `.gitignore`.
