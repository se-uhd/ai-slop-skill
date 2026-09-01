# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`); see the README "Versioning" section. Every release is also a git tag. Releases before `2026-06_rev13` are recorded only in the git tags.

## [2026-09_rev7] - 2026-09-01

- **Fixed:** prose inside the fenced templates, which the repository scan skips as code. The report disclaimer no longer joins two clauses with a semicolon, the Summary placeholder no longer asks for "headline metrics" (a phrase the general layer bans), and the `WRITING.md` header and the two maintainer comments read the same way. The report-template change reaches every generated report.
- **Fixed:** restored the language list in the 2026-06_rev13 entry below, which the 2026-09_rev4 sweep had shortened. A release record keeps its facts.

## [2026-09_rev6] - 2026-09-01

- **Fixed:** `CLAUDE.md` and the README named only `lint_markdown.py` and `check_baseline.py` as upstream-owned. The sync set is five paths (`lint_markdown.py`, `check_baseline.py`, `refresh_vendor.py`, `_vendor/`, `bundled_licenses/`), copied in by pymarkdown-skill's `sync/sync_to_skill.sh` and stamped in `scripts/.pymarkdown-skill-version`. The gap cost an extra upstream release (0.2.4) when a re-sync reverted a local edit to `refresh_vendor.py`.

## [2026-09_rev5] - 2026-09-01

- **Changed:** synced the pymarkdown-skill helpers at upstream release 0.2.4 (`.pymarkdown-skill-version` now reads `0.2.4`). The upstream 0.2.3 and 0.2.4 releases carry the em-dash and wording fixes that the 2026-09_rev4 sweep had applied to `lint_markdown.py` and `refresh_vendor.py` here, so the synced copies and upstream are identical again. No behavior change.

## [2026-09_rev4] - 2026-09-01

- **Changed:** every rule in the three layers now carries a stable key after its name (`G.semicolons`, `S.significant`, `L.grounding-comments`). Cross-references in the layers, the rationale entries, and the self-check items cite keys instead of names alone or list positions, so a rename or an insertion no longer breaks a reference. The report's `Rule:` field carries the name followed by the key, as in `Semicolons (G.semicolons)`. A new smoke test checks that keys are unique, that every rule bullet defines one, that every self-check item cites one, and that every cited key exists.
- **Changed:** rule names are plain directives without punctuation or metaphor. Renamed: "Name the relation with a connective; don't just drop the pause" to **Name the relation with a connective**; "Cite, do not gesture" to **Cite specific works**; "Name the thing instead of pointing at it" to **No stand-in words**; "Anchor every sentence-initial *This*, *These*, *That*, or *It* to a noun" to **Anchor sentence-initial pronouns**; "Use *the* only for a referent the reader can already identify" to **Definite article only for known referents**; "Watch the combined load" to **Combined pause-mark count**; "Hedge from evidence, not from timidity" to **Hedge only from evidence**; "Introducer punctuation: `:` not `.` before a list or continuation" to **Colon before a list or continuation**; "Pick one example-list signal and stay with it" to **One example signal per document**; "Signal whether a parenthetical list is examples or exhaustive" to **Mark parenthetical lists as examples or exhaustive**; "Avoid redundant content; refer back instead" to **Refer back instead of repeating**; the LaTeX caption rule to **Caption punctuation**; the "significant" rule to **Reserve "significant" for statistics**; and the paper-versus-study tense rule to **Present tense for the paper, past tense for the study**.
- **Added:** **Participial openings** (`G.participial-openings`) as a rule in the general layer. It had existed only as a self-check item.
- **Changed:** the bundle's own prose now follows its rules. A sweep applied the 400 file findings of an `/ai-slop:review-repo` run over this repository (literal em-dash glyphs, semicolons joining independent clauses, lowercase sentences after a colon, unanchored *This*, stand-in words, a dropped *that* after reporting verbs, a few figurative phrases) to the rule layers, the skill and command files, the README, `CLAUDE.md`, this changelog, and the Python docstrings and comments. The manifest descriptions, the H1 titles, the README table symbols, and the `"before" -> "after"` rewrite notation (ASCII arrow instead of the glyph) got the same treatment. `lint_markdown.py` was fixed here and synced back to the pymarkdown-skill repo.
- **Fixed:** `init/SKILL.md` step 3 pointed at step 7 for the summary; the summary is step 9.

## [2026-09_rev3] - 2026-09-01

- **Changed:** the **Cut padding at the paragraph level** (`G.paragraph-padding`) rule (general layer) now defines windup as a sentence that announces what its own paragraph then does, and names the section-opening paragraph as legitimate when it states the section's claim or purpose or orients the reader across the subsections with something the headings do not carry. Only a paragraph that merely lists the subsection headings or repeats content stated elsewhere is windup.
- **Added:** to the same rule, a density signal for generic-truth sentences (true of any document on the subject) and evaluative sentences (which grade the preceding claim without adding to it). One of either can open a section or mark that a result matters. More than one per paragraph, or more than two or three per page-equivalent, is filler. Self-check item #19 carries both changes, and `rules-rationale.md` records why this is a density signal and not a ban.
- **Changed:** the **Reference** and **Clause Boundaries** rules, self-check item #24, and the rationale section added in 2026-09 through 2026-09_rev2 now use periods where a colon or semicolon joined clauses ("Test: do X; if Y, do Z" is now "To test it, do X. If Y, do Z."). No rule content changes.

## [2026-09_rev2] - 2026-09-01

- **Added:** a fourth **Reference** rule (general layer), **No stand-in words** (`G.stand-ins`). A stand-in word for a noun or clause the sentence could state directly (*ones*, *those*, *the former / the latter*, *the same*, *respectively*, *do so*) costs the reader a lookup. Put the noun back and restructure the clause if it then repeats ("detect flaky tests among the generated ones" -> "detect which of the generated tests are flaky"). Self-check item #24 covers it, and `rules-rationale.md` explains why a left-to-right generator produces a stand-in instead of restructuring the clause.
- **Changed:** `scan_reference.py` lists a third kind, `stand-in` (*ones*, *the former*, *the latter*, *respectively*, *do / did so*, *those of / that / which / with*), with a smoke test; the review skill's metrics step names it.

## [2026-09_rev1] - 2026-09-01

- **Changed:** two sentences in `rules-rationale.md` (**Reference and clause boundaries**) restated in plain language. The first-mention *the* explanation no longer relies on "frame" and "definite-heavy register", and the cost of a dropped *that* is described as what the reader does ("first takes 'the effect' as the object of 'show' and has to re-read once 'persists' arrives") instead of the term for it. No rule or skill behavior changes; no skill loads the rationale file.

## [2026-09] - 2026-09-01

- **Added:** a general-layer **Reference** section with three rules that share one test ("the [noun] just mentioned" / "which one?"). Anchor every sentence-initial *This / These / That / It* to a noun ("This causes silent data loss" -> "This leniency causes silent data loss"). A summarizing noun must name something the text has listed ("such tools" after a list of tasks -> "tools for these tasks"). Use *the* only for a referent the reader can already identify ("the rerun infrastructure" at first mention -> "infrastructure to rerun ..."). Self-check item #24 wires them in.
- **Added:** a general-layer **Clause Boundaries** rule, **Keep *that* in formal prose** (`G.keep-that`). Restore the relativizer of a restrictive object relative ("the metrics that the benchmark reports") and the complementizer after a reporting verb ("the results show that the effect persists"). Fixed heads, quoted text, and deliberately informal text (commit messages, code comments) are exempt. Self-check item #25 wires it in. `rules-rationale.md` records the mechanism both sections share: the model resolves a reference against its whole context, the reader against one or two sentences of surface text.
- **Added:** `scan_reference.py`, a recall aid for the **Reference** rules in the style of `scan_glyphs.py`: one `<file>:<line>:<col>` row per sentence-initial *This / These / That / It* followed directly by a verb and per *such* + noun, skipping LaTeX comments, code blocks, and the common dummy-*it* frames. `/ai-slop:review` runs it in the cross-cutting-metrics step. Each row is a candidate that the rule's test confirms or clears, and a reference whose antecedent cannot be determined goes under **Items requiring author judgment** rather than getting a guessed noun. Smoke tests cover the scan.

## [2026-08_rev1] - 2026-08-27

- **Changed:** the **No invented compounds or verbs-as-nouns** (`G.no-coinages`) rule (general layer) now also covers noun phrases coined ad hoc to name a specific artifact, document, or table, hyphenated or not ("data sources table" and "track changes file" are the same coinages unhyphenated). The fix is to describe what the thing is: "track-changes file" -> "the accompanying PDF" (or "the latexdiff PDF"); "data-sources table" -> "a table listing all data sources". Self-check item #21 names the pattern too.

## [2026-08] - 2026-08-26

- **Added:** a LaTeX-layer punctuation rule, **Em dashes are unspaced.** Write `word---word` in LaTeX source with no surrounding spaces, the American typographic convention, which matches the general layer's American English rule. The rule governs spacing only. Whether a dash is the right mark at all stays with the general layer's **Em-dashes** (`G.em-dashes`) judgment, and the literal `—` glyph with **Literal em-dash glyphs in source** (`G.em-dash-glyphs`). Verbatim quotes keep their source's spacing. Self-check item #8 wires it into the LaTeX pass.

## [2026-07_rev2] - 2026-07-24

- **Added:** a **Phrases to Avoid** entry (general layer) banning **"headline numbers" / "headline figures"** in favor of naming the figures plainly (e.g., "the largest claims", "the most-cited figures", or just "the figures"). "Headline" imports a journalistic, attention-grabbing register that editorializes the numbers instead of stating them.

## [2026-07_rev1] - 2026-07-09

- **Added:** a general-layer punctuation rule, **Name the relation with a connective.** When a flagged em-dash or colon is introducing an example or a restatement, the fix is the connective that names that relation rather than a bare period or comma: an example connective (such as, e.g., for example, including) or a restatement connective (i.e., that is, in other words, namely). These connectives are routine in academic prose and under-produced by AI text, which reaches for a dash or colon instead, so the swap sharpens the meaning and removes a tell. The rule is meaning-gated (a mark that sets up a single payoff clause or introduces a true list is left alone) and defers to the parenthetical-list rules on keeping one example signal per document. Self-check item #23 wires it into the em-dash and colon passes, and `rules-rationale.md` records the rationale.

## [2026-07] - 2026-07-01

- **Added:** `refresh_tropes.py`, a maintainer script that re-pulls the bundled AI-trope snapshot (`shared/tropes-snapshot.md`) from upstream, the same Gist-then-tropes.fyi chain that `fetch_tropes.py` serves at review time, minus the bundled fallback. It keeps the snapshot bit-identical to upstream, reports "already up to date" without rewriting when the fetch matches the bundled copy, and leaves the snapshot untouched (exiting non-zero) when both sources are unreachable rather than clobbering it.
- **Changed:** the release protocol now refreshes the bundled tropes snapshot with every rev (`CLAUDE.md` rule 6 and the README "Maintainer notes"), so the offline fallback never drifts from the live catalog. The README "Refreshing the tropes.fyi snapshot" recipe is now the script instead of a raw `curl`.
- **Added:** smoke tests for `refresh_tropes.py` (writes the fetched body, falls back to the viewer, no-op when identical, leaves the snapshot unchanged when offline, and the usage error).

## [2026-06_rev16] - 2026-06-29

- **Added:** `scan_glyphs.py`, a deterministic recheck for the Unicode "tells" the per-section LLM pass undercounts. It reads the paper byte for byte and prints one row per literal `—` (em-dash), `–` (en-dash), arrow (`->` and family), curly quote, ellipsis, or non-breaking space, with a `<file>:<line>:<col>` location, so two em-dashes on one line are two distinct rows and the count is exact. `/ai-slop:review` runs it at the start of the cross-cutting-metrics step and takes the em-dash-density count from it instead of from a visual estimate. Every em-dash, arrow, curly-quote, ellipsis, and nbsp row becomes a per-section finding, while en-dashes in ranges and glyphs inside quotes or code are left to the caller's judgment.
- **Changed:** the **Plain, literal language** (`G.plain-language`) rule (general layer) now names the systems-jargon count nouns "a write", "a read", "a create", and "a delete" as verb-as-noun seeds (alongside the existing "a full delete", "the ask"), with the rewrite to "a write request" or "a write operation". The plain-language self-check lists them too, so the reviewer stops overlooking "each write", "the failed write", or "repeat the create".
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
