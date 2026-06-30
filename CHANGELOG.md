# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`); see the README "Versioning" section. Every release is also a git tag. Releases before `2026-06_rev13` are recorded only in the git tags.

## [2026-07] - 2026-07-01

- **Added:** `refresh_tropes.py`, a maintainer script that re-pulls the bundled AI-trope snapshot (`shared/tropes-snapshot.md`) from upstream — the same Gist-then-tropes.fyi chain `fetch_tropes.py` serves at review time, minus the bundled fallback. It keeps the snapshot bit-identical to upstream, reports "already up to date" without rewriting when the fetch matches the bundled copy, and leaves the snapshot untouched (exiting non-zero) when both sources are unreachable rather than clobbering it.
- **Changed:** the release protocol now refreshes the bundled tropes snapshot with every rev (`CLAUDE.md` rule 6 and the README "Maintainer notes"), so the offline fallback never drifts from the live catalog. The README "Refreshing the tropes.fyi snapshot" recipe is now the script instead of a raw `curl`.
- **Added:** smoke tests for `refresh_tropes.py` (writes the fetched body, falls back to the viewer, no-op when identical, leaves the snapshot unchanged when offline, and the usage error).

## [2026-06_rev16] - 2026-06-29

- **Added:** `scan_glyphs.py`, a deterministic recheck for the Unicode "tells" the per-section LLM pass undercounts. It reads the paper byte for byte and prints one row per literal `—` (em-dash), `–` (en-dash), arrow (`→` and family), curly quote, ellipsis, or non-breaking space, with a `<file>:<line>:<col>` location, so two em-dashes on one line are two distinct rows and the count is exact. `/ai-slop:review` runs it at the start of the cross-cutting-metrics step and takes the em-dash-density count from it instead of an eyeball; every em-dash, arrow, curly-quote, ellipsis, and nbsp row becomes a per-section finding, while en-dashes in ranges and glyphs inside quotes or code are left to the caller's judgment.
- **Changed:** the **Plain, literal language** rule (general layer) now names the systems-jargon count nouns "a write", "a read", "a create", and "a delete" as verb-as-noun seeds (alongside the existing "a full delete", "the ask"), with the rewrite to "a write request" or "a write operation". The plain-language self-check lists them too, so the reviewer stops walking past "each write", "the failed write", or "repeat the create".
- **Added:** smoke tests for `scan_glyphs.py` (exact per-category counts including a code-comment em-dash, distinct columns for two glyphs on one line, the ASCII-is-clean case, and the unreadable and partial-read exit codes).

## [2026-06_rev15] - 2026-06-29

- **Added:** `/ai-slop:review-repo` now also scans the repository's commit messages. `scan_repo.py` reads each commit's subject and body from `git log` and emits them under a `commit <short-sha>` pseudo-path, so the report groups commit-message findings by commit alongside the per-file groups. Merge commits and the standard trailer lines (`Co-authored-by`, `Signed-off-by`, ...) are dropped, since neither is hand-written prose.
- **Added:** commit-message scope controls. The default covers the most recent 200 commits; `--commits=<N>` sets another count, `--commits=all` the full history, `--commits=<range>` a git revision range (e.g. `main..HEAD` for one branch), and `--no-commits` turns commit scanning off. Because published commit history is immutable, commit-message findings are advisory (a guide for future messages, or for rewording a branch's unpushed commits) and are not applied by `/ai-slop:revise`.
- **Added:** smoke tests for commit-message extraction, the `--no-commits` flag, the count selector, and the bad-value usage error.

## [2026-06_rev14] - 2026-06-26

- **Added:** `/ai-slop:review-repo` now also scans LaTeX (`.tex`) files. A `.tex` file is reviewed as prose, its document body and its `%` comments alike (the comments are content too, just as comments are in source files), against the general rules. The dedicated `/ai-slop:review` LaTeX layer remains the tool for citations, BibTeX, and section-aware checks.

## [2026-06_rev13] - 2026-06-26

- **Added:** a repo mode, `/ai-slop:review-repo`, that reviews the natural-language text across a whole codebase rather than a single document (`/ai-slop:review`) or a diff (`/ai-slop:review-diff`). It extracts every Markdown and plain-text file in full, plus the comments and doc-comments of the source and config files, scans that prose against the general rules and the AI-trope catalog, and writes `ai-slop-report.md` with findings grouped by file. It catches slop that has drifted into committed comments over many commits, the kind a diff review never revisits.
- **Added:** a `scan_repo.py` extractor that surfaces the repository's prose for the new mode. It reads comments from a broad set of languages and formats: Shell, Java, Kotlin, Python (including docstrings), JavaScript, and TypeScript; the rest of the C family (C, C++, C#), Go, Rust, Swift, Scala, Dart, Groovy/Gradle, Ruby, PHP, Perl, R, Lua, and Lisp/Clojure; the web and styling formats HTML, XML, Vue, Svelte, CSS, SCSS, and Less; SQL; and config formats such as YAML, TOML, INI, `.properties`, `.env`, Dockerfile, Makefile, CMake, and Terraform. The `COMMENT_SPECS` and `NAME_SPECS` tables in `scan_repo.py` are the authoritative list. Comment detection is string-aware, so a `//` or `#` inside a string literal is not mistaken for a comment, and a shell shebang is not read as prose.
- **Added:** the extractor honors `.gitignore` in a git repository (it scans the tracked files) and skips generated files (a "DO NOT EDIT" or `@generated` header), lockfiles, binaries, vendored directories, and (in this revision) `.tex` source.
- **Added:** smoke tests covering the extractor: per-language comment extraction, the prose/generated/lockfile/binary classification, `.gitignore` and vendored-directory exclusion, and the shebang skip.
- **Changed:** the version now lives in ten callsites (the new `review-repo` `SKILL.md` adds one); the smoke suite enforces all of them.
