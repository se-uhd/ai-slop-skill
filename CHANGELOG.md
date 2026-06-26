# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`); see the README "Versioning" section. Every release is also a git tag. Releases before `2026-06_rev13` are recorded only in the git tags.

## [2026-06_rev14] - 2026-06-26

- **Added:** `/ai-slop:review-repo` now also scans LaTeX (`.tex`) files. A `.tex` file is reviewed as prose, its document body and its `%` comments alike (the comments are content too, just as comments are in source files), against the general rules. The dedicated `/ai-slop:review` LaTeX layer remains the tool for citations, BibTeX, and section-aware checks.

## [2026-06_rev13] - 2026-06-26

- **Added:** a repo mode, `/ai-slop:review-repo`, that reviews the natural-language text across a whole codebase rather than a single document (`/ai-slop:review`) or a diff (`/ai-slop:review-diff`). It extracts every Markdown and plain-text file in full, plus the comments and doc-comments of the source and config files, scans that prose against the general rules and the AI-trope catalog, and writes `ai-slop-report.md` with findings grouped by file. It catches slop that has drifted into committed comments over many commits, the kind a diff review never revisits.
- **Added:** a `scan_repo.py` extractor that surfaces the repository's prose for the new mode. It reads comments from a broad set of languages and formats: Shell, Java, Kotlin, Python (including docstrings), JavaScript, and TypeScript; the rest of the C family (C, C++, C#), Go, Rust, Swift, Scala, Dart, Groovy/Gradle, Ruby, PHP, Perl, R, Lua, and Lisp/Clojure; the web and styling formats HTML, XML, Vue, Svelte, CSS, SCSS, and Less; SQL; and config formats such as YAML, TOML, INI, `.properties`, `.env`, Dockerfile, Makefile, CMake, and Terraform. The `COMMENT_SPECS` and `NAME_SPECS` tables in `scan_repo.py` are the authoritative list. Comment detection is string-aware, so a `//` or `#` inside a string literal is not mistaken for a comment, and a shell shebang is not read as prose.
- **Added:** the extractor honors `.gitignore` in a git repository (it scans the tracked files) and skips generated files (a "DO NOT EDIT" or `@generated` header), lockfiles, binaries, vendored directories, and (in this revision) `.tex` source.
- **Added:** smoke tests covering the extractor: per-language comment extraction, the prose/generated/lockfile/binary classification, `.gitignore` and vendored-directory exclusion, and the shebang skip.
- **Changed:** the version now lives in ten callsites (the new `review-repo` `SKILL.md` adds one); the smoke suite enforces all of them.
