# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`); see the README "Versioning" section. Every release is also a git tag. Releases before `2026-06_rev13` are recorded only in the git tags.

## [2026-06_rev13] - 2026-06-26

### Added

- A repo mode, `/ai-slop:review-repo`, that reviews the natural-language text across a whole codebase rather than a single document (`/ai-slop:review`) or a diff (`/ai-slop:review-diff`). It extracts every Markdown and plain-text file in full, plus the comments and doc-comments of the source and config files, scans that prose against the general rules and the AI-trope catalog, and writes `ai-slop-report.md` with findings grouped by file. It catches slop that has drifted into committed comments over many commits, the kind a diff review never revisits.
- A `scan_repo.py` extractor that surfaces the repository's prose for the new mode. It reads comments from Shell, Java, Kotlin, Python (including docstrings), JavaScript, and TypeScript, plus C/C++, C#, Go, Rust, CSS/SCSS, HTML/XML, SQL, and config formats (YAML, TOML, INI, `.properties`, and more). Comment detection is string-aware, so a `//` or `#` inside a string literal is not mistaken for a comment, and a shell shebang is not read as prose.
- The extractor honors `.gitignore` in a git repository (it scans the tracked files) and skips generated files (a "DO NOT EDIT" or `@generated` header), lockfiles, binaries, vendored directories, and `.tex` source.
- Smoke tests covering the extractor: per-language comment extraction, the prose/generated/lockfile/binary classification, `.gitignore` and vendored-directory exclusion, and the shebang skip.

### Changed

- The version now lives in ten callsites (the new `review-repo` `SKILL.md` adds one); the smoke suite enforces all of them.
