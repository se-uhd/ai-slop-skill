# AGENTS.md

Maintainer guidance for the `ai-slop` skill bundle. (This file is the
development guide for the repo itself, not the `WRITING.md` that
`/ai-slop:writing` generates for project repositories.)

## Release protocol (read before bumping the version)

Releases use CalVer with a per-month revision counter: `YYYY-MM` for the first
release of a month (implicit `rev0`), then `YYYY-MM_rev1`, `_rev2`, ... (see README
"Versioning"). Every release follows these rules, because each release is a
pushed tag that others can pull:

1. **Release once the change is settled, not once per iteration.** A rev is a
   published release, so make one only when the work is finished and has been
   checked against the main use of the bundle (academic writing) and against the
   existing rule layers, rather than at the first version that passes the smoke
   suite. Ask the maintainer before the release commit, the tag, and the push.
   A correction to a release made in the same session, such as a fix to
   the design of a rule that shipped minutes earlier, is a squash into that rev,
   not a new rev. Soft-reset to the previous release, fold the work
   into one commit, restore the version strings and merge the CHANGELOG entries
   so the record describes the settled change rather than the route to it,
   delete the extra tag locally and on the remote, and force-push `main` and the
   retargeted tag. Once the session has ended, or anyone may have pulled the tag,
   rule 3 governs instead and the fix is a new rev.
2. **Every rev bump is its own commit AND a matching git tag.** After bumping
   the version, create `git tag YYYY-MM_revN` on that commit and push it. A
   release without its tag is not done. List the current month's tags with
   `git tag -l "$(date +%Y-%m)*"`. The next rev is the highest current rev + 1
   (the bare `YYYY-MM` tag is rev0, so the release after it is `_rev1`).
3. **Never amend, rebase, or rewrite a commit that is already tagged, released,
   or pushed as part of ordinary work.** If more work is needed after a release,
   it is a NEW rev with a NEW commit and tag. Amending a released commit orphans
   its tag and breaks the linear release history. A history repair that the
   maintainer asks for is an exception, and so is the same-session squash in
   rule 1, which uses its own procedure. For a repair, rewrite with `git filter-branch
   --tag-name-filter cat -- --branches --tags` so every tag points to its corresponding rewritten
   commit. Verify against `refs/original` that the trees are unchanged and that
   no tag is left off `main`. Force-push `main` and `--tags` together, because a
   forced branch push alone leaves every tag on a commit that the branch no
   longer reaches. Record the repair in the CHANGELOG entry of the release that
   includes it, as the 2026-09_rev15 entry does.
4. **Keep the 12 version callsites in sync.** The version string is in
   `plugins/ai-slop/.claude-plugin/plugin.json` (canonical),
   `.claude-plugin/marketplace.json`, the `metadata.version` frontmatter of
   each `SKILL.md`, and the `**Skill version:**` line in the report template
   `review/references/report-template.md`. `export_rules.py` and `build_writing.py` read it from
   `plugin.json`. `test_version_strings_in_sync` in the smoke suite enforces
   this.
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
  `shared/rules-latex.md`, `shared/rules-economist.md`, or `shared/rules-ste.md`
  also needs a self-check item of that layer that cites its key, either a new
  item or an existing one, and an entry in
  `shared/rules-rationale.md` whenever a reader could push back on it. Every
  rule carries a stable key (`G.`/`S.`/`L.`/`E.`/`T.` plus a slug) that reports and
  cross-references cite. `test_rule_keys_unique_and_resolvable` in the smoke
  suite enforces the key invariants: one key per rule bullet, unique across the
  layers, a key in every self-check item, and no dangling key in the layers,
  the rationale, or a `SKILL.md`. `test_every_rule_key_in_a_self_check_item`
  fails when a key is in no self-check item of its layer. Its exempt list names
  the rules that have nothing to scan for, such as the scope of a layer.
- **Commit messages follow Conventional Commits with length limits.** The
  subject has the form `type(scope)!: description`, at most 72 characters, and
  no final period. The description is an imperative, such as
  `add a rule for noun chains`. The type is `feat`, `fix`, `docs`, `refactor`,
  `test`, `build`, `ci`, `chore`, `perf`, or `revert`, and `!` marks a breaking
  change. A change to a rule layer or a `SKILL.md` changes what the skills do,
  so it is `feat` or `fix`, and `docs` is for the README, the files under
  `docs/`, this file, and the changelog. The scope is optional. It is the name of a skill, the name of a
  rule layer (i.e., `general`, `scientific`, `latex`, `economist`, or `ste`),
  `scripts` for the helpers in `plugins/ai-slop/scripts/`, `vendor` for the
  synced linter, `manifests` for the three manifests, or `release`. A blank
  line and 1 to 5 bullets follow the subject. Each bullet starts with a hyphen
  and a space and has at most 2 lines of at most 72 characters, with
  continuation lines indented by two spaces. The trailers, such as `Co-Authored-By:`, come last,
  after a blank line. A release commit has the subject
  `chore(release): YYYY-MM_revN`, and its bullets summarize the release.
- **`scripts/check_commit_message.py` enforces the format.** Enable its Git
  hook once per clone with `git config core.hooksPath .githooks`. The Claude
  Code hook in `.claude/settings.json` checks each commit that an agent makes
  and returns the violations to the agent. The workflow `commit-messages.yml`
  checks the commits of a pull request and of a push to `main`. The check skips
  the commits up to the tag `2026-11_rev9`, since rule 3 keeps their released
  messages. The smoke suite tests the script and both hooks.
- **Commit messages also follow the general layer.** They are prose, and
  `/ai-slop:review-repo` scans them with every other file. Correcting a pushed
  message means rewriting history, which rule 3 above allows only as a
  deliberate repair, so the check happens before `git commit`. The recurring
  failures are a semicolon joining two independent clauses, a literal em-dash
  glyph (U+2014), a British spelling, and a comma splice. A semicolon in a
  parenthetical list, in quoted output, or in a code span stays.
- **The trope catalog has one source and no bundled copy.** `fetch_tropes.py`
  reads tropes.fyi and exits non-zero when it cannot. Do not add a mirror or a
  bundled snapshot. A stale copy that outranks the live catalog is worse than
  failing to fetch the catalog. `--tropes=<path>` supplies the catalog for an
  offline or pinned run.
- **The bundle follows its own rules.** When a rule is added or tightened, sweep
  the prose of the repository itself for the pattern in the same rev: the
  Markdown files, the skill files, and the Python docstrings and
  comments. The opt-in STE layer is an exception. Only the changelog follows
  it, so an STE rule change needs no sweep. Between sweeps,
  `test_first_party_prose_avoids_the_plain_words_seeds` runs `scan_repo.py` over
  the repository and fails when "lives in", "shape", or "cut" before a release,
  tag, branch, or reference appears outside a quoted example, and
  `test_first_party_prose_avoids_possessives_on_text_units` fails when 's follows
  a text or repository unit such as "report" or "sentence" outside a quoted
  example or code span.
  `/ai-slop:review-repo` finds clause-joining semicolons on the next sweep,
  since a count cannot tell them from list separators. Released `CHANGELOG.md`
  entries are edited only to correct or complete the record, or in a sweep of
  their prose or format that the maintainer asks for, and never to change what
  they record. Upstream-owned files are left to their own repo.
- **The changelog has one bullet per change.** Each release in `CHANGELOG.md`
  lists its changes under the headings `### Added`, `### Changed`,
  `### Removed`, `### Fixed`, and `### Unchanged`, in this order and only
  where they apply. A bullet records one change, which is a change to one
  component or one behavior, with its details and reasons. Unlike the rest of
  the bundle prose, the changelog follows the STE layer.
- **`scripts/check_markdown_limits.py` checks the length and structure of the
  Markdown files.** `scripts/markdown_limits.toml` sets each limit with its
  source: the structure of the changelog, at most 4 sentences per bullet in
  `[Unreleased]` and later releases, at most 5,000 tokens in the body of a
  `SKILL.md`, at most 200 lines in `AGENTS.md` and `CLAUDE.md` together, and
  at most 200 lines and 60 lines per section in `README.md`. To meet a limit,
  move text instead of cutting it. Reference material of a skill goes into
  its `references/` directory, with a pointer at the step that needs it, and
  a README section goes into `docs/`. The smoke suite runs the check.
- **The root `package.json` is the pi package manifest and has no `version`
  field on purpose.** Do not add one. Pi pins a git install to a release tag,
  so the tag carries the version and the version callsites stay at twelve.
  The manifest lists `./plugins/ai-slop/skills` under `pi.skills`, so pi picks
  up a new skill directory without a manifest change.
  `test_pi_package_manifest` in the smoke suite enforces this.
- **The glossary format and the repository scan are shared.**
  `shared/glossary-format.md` defines the `GLOSSARY.md` format for
  `/ai-slop:glossary` and `/ai-slop:glossary-repo`, and neither `SKILL.md`
  repeats it. `scan_glossary.py` parses the table of vocabulary to avoid in
  that format and in the older formats that its docstring lists, so a change
  to the Avoid column changes the parser and its smoke tests in the same rev.
  A glossary term is never a word to avoid. `scan_glossary.py --lint` reports
  a glossary that lists one, both glossary skills run it after writing a
  glossary, and `test_scan_glossary_reports_avoided_terms` covers it.
  `scan_repo.py` extracts the text for `/ai-slop:review-repo` and
  `/ai-slop:glossary-repo`, and `scan_glossary.py` imports its `extract_file`
  to read files in the same way.
- Generated artifacts (`ai-slop-report.md`, `grounding-cites.json`,
  `grounding-quotes.json`) are never committed. The skills add them to the
  `.gitignore` of the target repo.
