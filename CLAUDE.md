# CLAUDE.md

Maintainer guidance for the `ai-slop` skill bundle. (This file is the repo's own
development guide, not the `WRITING.md` that `/ai-slop:init` generates for project
repositories.)

## Release protocol (read before bumping the version)

Releases use CalVer with a per-month revision counter: `YYYY-MM` for the first
release of a month (implicit `rev0`), then `YYYY-MM_rev1`, `_rev2`, ... (see README
"Versioning"). Every release MUST follow these rules. They exist because they
have been broken before:

1. **Release once the change is settled, not once per iteration.** A rev is a
   published release, so cut it when the work is finished and has been checked
   against the bundle's main use (academic writing) and against the existing
   rule layers, rather than at the first version that passes the smoke suite. A
   correction to a release made in the same session is a squash into that rev, not
   a new rev. Soft-reset to the previous release, fold the work into one commit,
   restore the version strings and merge the CHANGELOG entries so the record
   describes the settled change rather than the route to it, delete the extra
   tag locally and on the remote, and force-push `main` and the moved tag. Once
   the session has moved on, or anyone may have pulled the tag, rule 3 governs
   instead and the fix is a new rev. (Shipping a new rule and then correcting
   its design minutes later is what produced the squashed release now numbered
   `2026-09_rev24`.)
2. **Every rev bump is its own commit AND a matching git tag.** After bumping
   the version, create `git tag YYYY-MM_revN` on that commit and push it. A
   release without its tag is not done. List the current month's tags with
   `git tag -l "$(date +%Y-%m)*"`. The next rev is the highest current rev + 1
   (the bare `YYYY-MM` tag is rev0, so the release after it is `_rev1`).
3. **Never amend, rebase, or rewrite a commit that is already tagged, released,
   or pushed as part of ordinary work.** If more work is needed after a release,
   it is a NEW rev with a NEW commit and tag, never a re-cut of the released
   commit. Amending a released commit orphans its tag and breaks the linear
   release history. (Amending a released commit is the mistake that produced the
   dangling-tag situation at the release now numbered `2026-05_rev15`.) A
   history repair that the maintainer asks for is an exception, and so is the
   same-session squash in rule 1, which uses its own procedure. A repair comes
   with obligations. Rewrite with `git filter-branch --tag-name-filter cat --
   --branches --tags` so every tag moves with its commit. Verify against
   `refs/original` that the trees are unchanged and that no tag is left off
   `main`. Force-push `main` and `--tags` together, because a forced branch
   push alone leaves every tag on a commit that the branch no longer reaches. The
   commit message cleanups recorded in the 2026-09_rev15 and 2026-09_rev23
   changelog entries are the precedent.
4. **Keep the 12 version callsites in sync.** The version string is in
   `plugins/ai-slop/.claude-plugin/plugin.json` (canonical),
   `.claude-plugin/marketplace.json`, the `version:` frontmatter of each
   `SKILL.md`, the `**Skill version:**` line in `review/SKILL.md`'s report
   template, and the `skill version <X>` line in `init/SKILL.md`'s WRITING.md
   header. `test_version_strings_in_sync` in the smoke suite enforces this.
5. **Run the smoke suite before every commit:**
   `python3 plugins/ai-slop/scripts/tests/run_smoke.py`. It must be green.
6. **Release tags must be ancestors of `main`.** The release history is linear:
   `... revN -> revN+1 -> ...`. If a tag is not reachable from `main`, the history is
   broken and must be repaired before the next release.

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
- **Changing the rules is an edit in three places.** A new or reworded rule in
  `shared/rules-general.md`, `shared/rules-scientific.md`,
  `shared/rules-latex.md`, or `shared/rules-ste.md` also needs its numbered
  item in that layer's self-check section, and an entry in
  `shared/rules-rationale.md` whenever a reader could push back on it. Every
  rule carries a stable key (`G.`/`S.`/`L.`/`T.` plus a slug) that reports and
  cross-references cite. `test_rule_keys_unique_and_resolvable` in the smoke
  suite enforces the key invariants: one key per rule bullet, unique across the
  layers, a key in every self-check item, and no dangling key in the layers,
  the rationale, or a `SKILL.md`.
- **Commit messages follow the general layer.** They are prose, and
  `/ai-slop:review-repo` scans them with every other file. Correcting a pushed
  message means rewriting history, which rule 3 above allows only as a
  deliberate repair, so the check happens before `git commit`. The September
  2026 cleanup rewrote the whole history and fixed the recurring failures: a
  semicolon joining two independent clauses (in 50 of the 76 messages, among
  them the boilerplate "Version bumped to X at all ten callsites; the tropes
  snapshot was already up to date", which is two sentences), a literal em-dash
  glyph (U+2014) in 8 messages, one British spelling, and one comma splice. A
  semicolon in a parenthetical list, in quoted output, or in a code span stays.
  Write the subject line as an imperative ending in `; release YYYY-MM_revN` on
  a release commit. That suffix is the one semicolon that the convention keeps,
  and the rest of the subject takes commas.
- **The trope catalog has one source and no bundled copy.** `fetch_tropes.py`
  reads tropes.fyi and exits non-zero when it cannot. A stale copy that
  outranks the live catalog is worse than failing to fetch the catalog, which
  is why the gist mirror and the bundled snapshot were both dropped in
  2026-09_rev16. `--tropes=<path>` supplies the catalog for an offline or
  pinned run.
- **The bundle follows its own rules.** When a rule is added or tightened,
  sweep the repository's own prose for the pattern in the same rev: the
  Markdown files, the skill and command files, and the Python docstrings and
  comments. The synthetic reviews under `scripts/tests/fixtures/` are sloppy on
  purpose and exempt, and `scan_repo.py` skips them. The opt-in STE layer is
  the other exception. The bundle's prose does not
  follow it, so an STE rule change needs no sweep. Between sweeps,
  `test_first_party_prose_avoids_the_plain_words_seeds` runs `scan_repo.py`
  over the repository and fails on "lives in" outside a quoted example.
  `/ai-slop:review-repo` finds clause-joining semicolons on the next sweep,
  since a count cannot tell them from list separators. Released `CHANGELOG.md`
  entries are edited only to correct or complete the record, never to restate
  it. Upstream-owned files are left to their own repo.
- Generated artifacts (`ai-slop-report.md`, `ai-slop-tldr.md`,
  `grounding-cites.json`, `grounding-quotes.json`) are never committed. The
  skills add them to the target repo's `.gitignore`.
