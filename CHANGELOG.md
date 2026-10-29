# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`), described in the README "Versioning" section. Every release is also a git tag. Releases before `2026-06_rev13` are recorded only in the git tags.

## [2026-10_rev12] - 2026-10-29

- **Removed:** the command wrappers in `plugins/ai-slop/commands/`. Claude Code now serves each `/ai-slop:` command from its skill and loads the `SKILL.md` directly, with the same commands and arguments.
- **Fixed:** `/ai-slop:writing` also adds its reference to an empty `AGENTS.override.md`, which Codex and pi read instead of `AGENTS.md`, and `/ai-slop:init` does the same in the pi agent directory.
- **Fixed:** init and the README no longer cite the 32 KiB Codex limit for the global instruction file, since it applies only to project files.

## [2026-10_rev11] - 2026-10-29

- **Changed:** `lint_markdown.py`, `refresh_vendor.py`, and `_vendor/` come from pymarkdown-skill 0.3.0. It vendors PyMarkdown 0.9.40.
- **Fixed:** the README told maintainers to run `refresh_vendor.py` here, which `AGENTS.md` rules out. It now describes the refresh in pymarkdown-skill and the sync.

## [2026-10_rev10] - 2026-10-29

- **Changed:** `/ai-slop:writing` builds `WRITING.md` with the new `scripts/build_writing.py` instead of having the model copy the rule layers and the trope catalog by hand. The script keeps the layers verbatim, self-checks included, and adds the layer name to a repeated heading, as in `## Voice (scientific)`, so the file lints clean. It does not replace an existing `WRITING.md` without `--force`, so the skill still asks first.
- **Changed:** the version string has eleven callsites. The `WRITING.md` header takes the version from `plugin.json`, as the init export already did.
- **Fixed:** `/ai-slop:review-diff` reviews untracked files, which `git diff` does not list, such as a new chapter not yet added to git.
- **Changed:** `/ai-slop:review` lists a doubt about whether a citation supports a claim under **Items requiring author judgment** instead of recording a finding that revise mode would apply. `/ai-slop:ground` checks such a claim against the retrieved source.
- **Changed:** `/ai-slop:review-repo` runs `scan_reference.py`, as the other two review modes do.
- **Fixed:** self-check item 6 of the general layer states the semicolon default of its rule, a period between two independent clauses, and three self-check items no longer join clauses with a semicolon. `/ai-slop:glossary` no longer calls ripgrep, which is not a listed dependency, and the rationale names the Economist layer and init mode.

## [2026-10_rev9] - 2026-10-29

- **Added:** `--economist` selects an optional layer based on the core advice in Lane Greene's *Writing with Style: The Economist Guide* (2023). It covers reader knowledge, precise words, actors and actions, sentence flow, argument, concision, tone, imagery, and numerical context and precision. The book is not bundled or required at runtime.
- **Changed:** review, diff, repository, writing, and init modes support the layer, including offline exports with `--tropes=<path>`. Its rules carry `E.` keys, it preserves project and research conventions, and it combines with `--ste` under the stricter STE limits.

## [2026-10_rev8] - 2026-10-27

- **Added:** the repository root is a pi package, so `pi install git:github.com/se-uhd/ai-slop-skill@<tag>` installs the eight skills, which pi invokes as `/skill:<name>`. Its `package.json` lists `plugins/ai-slop/skills` under `pi.skills` and declares no extensions or prompts, which keeps the Claude Code command wrappers out of pi. Claude Code and Codex are unaffected.
- **Added:** `/ai-slop:init` sets up pi. It writes `ai-slop.md` into the pi agent directory (`PI_CODING_AGENT_DIR` or `~/.pi/agent`) and appends a read instruction once to the first global context file there (a nonempty `AGENTS.override.md`, then `AGENTS.md`, then `CLAUDE.md`, and otherwise a new `AGENTS.md`). An explicit output path still writes only the file.
- **Changed:** every `SKILL.md` names the pi invocation next to the Claude Code and Codex ones, and the `WRITING.md` that `/ai-slop:writing` generates names `/skill:review`. The README has an "Install in pi" section on pinned and unpinned installs, updates, and name collisions.
- **Unchanged:** the versioning stays CalVer. The pi manifest has no version field, since pi pins a git install to a tag, and the version callsites stay at twelve.

## [2026-10_rev7] - 2026-10-26

- **Fixed:** cross-references in the rationale and the STE layer name each rule as the general layer does, where some had used "No figurative language" for `G.no-figurative-language` or a label of their own, such as "Short paragraphs" for `G.paragraph-length`. Self-check item 23 cites `G.one-example-signal` instead of `G.parenthetical-lists`.

## [2026-10_rev6] - 2026-10-26

- **Changed:** the general layer is about 6k characters shorter, with every rule, key, test, threshold, and exception kept. Each rule states its test once, keeps fewer examples, and no longer restates a neighboring rule, so the file that `/ai-slop:init` writes takes up less of the 150k characters of instruction files above which Claude Code warns. The self-check and the rationale are unchanged.

## [2026-10_rev5] - 2026-10-23

- **Added:** `G.possessive-on-things` flags the possessive 's on a thing or an abstraction ("the sentence's purpose") and prefers an of-phrase, a preposition, or a noun adjunct. The form stays for a person, group, organization, or named tool, for a document standing for its authors, in fixed phrases, and where the possessor is the topic under discussion.
- **Changed:** the README, maintainer guide, command and skill files, rule layers, and Python docstrings and comments follow the new rule. The smoke suite checks the first-party prose for 's on the text and repository units that the bundle writes about most.

## [2026-10_rev4] - 2026-10-22

- **Added:** `/ai-slop:glossary` creates or updates `GLOSSARY.md`, proposes definitions, and flags competing names or inconsistent meanings. It finds the main document when no filename is supplied. `--check` validates without updating the glossary, and `--glossary=<path>` selects another glossary.
- **Changed:** `review`, `review-diff`, and `review-repo` use project glossaries for terminology checks.
- **Added:** `G.connected-prose` requires a clear progression across sentences and paragraphs. Concision and punctuation edits preserve useful transitions.
- **Changed:** `G.paragraph-length` treats one- and two-sentence paragraphs as exceptions in sustained prose.

## [2026-10_rev3] - 2026-10-21

- **Removed:** `/ai-slop:tldr` and its command, skill, counting helper, schema check, recall helper, and synthetic fixtures. Use `/ai-slop:review` for a document, `/ai-slop:review-diff` for changed lines, or `/ai-slop:review-repo` for a repository.
- **Changed:** the README, maintainer guidance loaded through `CLAUDE.md`, rule rationale, and ignore rules describe the seven remaining modes and eleven version callsites.

## [2026-10_rev2] - 2026-10-08

- **Added:** `G.context-first` requires a reason for stylistic edits based on the surrounding passage. Word matches, trope statuses, and counts prompt inspection rather than automatic replacements. Edits preserve purpose, logical relations, distinctions, scope, emphasis, evidence, and author voice.
- **Changed:** the general rules and self-checks keep useful abstractions, familiar metaphors, clear references, and natural sentence rhythm. Explicit conventions such as spelling, terminology, citations, and statistical reporting still apply.
- **Changed:** review, diff, repository, and TL;DR workflows require a problem in context before reporting a stylistic finding, and review findings include a reason for the proposed replacement. Revision checks preserve the argument as well as the facts and skip a loss of meaning unless the user explicitly approved it.

## [2026-10_rev1] - 2026-10-02

- **Changed:** `G.plain-words` treats a vague "checkpoint" as it treats a vague "gate": Name the build, test, or command that must pass and, when it matters, before which action. The word stays for a saved state that a process resumes from, such as a model or database checkpoint.

## [2026-10] - 2026-10-01

- **Changed:** `G.plain-words` adds examples that replace a vague "gate" with wording that fits the context and names what must pass and, when it matters, before which action. Established technical senses stay.

## [2026-09_rev37] - 2026-09-30

- **Changed:** `G.be-concrete` flags vague uses of "moved" and "shifted" in descriptions of a revision. State the actual change or current behavior, and give version history only when it helps comparison, upgrading, reproduction, or understanding a change. Actual relocation, physical movement, and established technical senses stay.

## [2026-09_rev36] - 2026-09-30

- **Changed:** all eight skills resolve bundled helpers from their installed `SKILL.md` location in both Codex and Claude Code, without a Claude-specific environment variable. Claude slash commands and plugin manifests remain compatible, and the README documents Codex installation and invocation.
- **Changed:** writing setup references `WRITING.md` from `AGENTS.md`, keeps Claude Code loading through a `CLAUDE.md` import, and preserves existing instructions and references.
- **Added:** init setup for Codex exports its rules to the Codex home directory and adds a reference in the effective global instruction file. Claude Code retains its rules-directory default, and explicit export paths still write only the requested file.

## [2026-09_rev35] - 2026-09-27

- **Changed:** the file that `/ai-slop:init` writes is about 15k characters smaller (69k instead of 84k with the current catalog). It leaves out the self-check of each layer, asking for the check in its opening paragraph instead, and drops the status and category line of each catalog entry, its `**Avoid patterns like:**` label, and the `---` line after it. The layer files keep their self-checks for the review modes.
- **Changed:** the details that only a self-check item stated are now in their rules, so the exported file loses no test. `G.american-english` names favor, center, defense, and license, and `G.restricted-words` gains the limit of 2 to 3 per paragraph. `G.em-dashes` excludes en dashes in ranges, minus signs, and `--` in code listings from the count, and `G.em-dash-glyphs` names `---` for LaTeX and keeps an em-dash glyph in a quotation or code listing. `G.parenthetical-lists` defaults to "e.g.," for a list that is not obviously exhaustive, and `G.plain-language` asks for a scan for the sample words. In the STE layer, `T.one-topic` gains the test of naming the topic of a paragraph, and `T.verbs-not-nouns` names the light verb form. Self-check item 14 drops the "(verb)" note on "licence".

## [2026-09_rev34] - 2026-09-27

- **Changed:** `/ai-slop:export` is now `/ai-slop:init`, and the former `/ai-slop:init`, which writes the `WRITING.md` of a project, is now `/ai-slop:writing`. The new init replaces a rules file from `/ai-slop:export` without `--force`.
- **Changed:** `G.plain-words` lists "cut" for creating or publishing, as in "cut a release" -> "publish a release", and keeps it for removing or shortening. `CLAUDE.md` and the README no longer use it in that sense, and the seed test fails on "re-cut" and on "cut" before a release, tag, branch, or reference.

## [2026-09_rev33] - 2026-09-27

- **Changed:** `/ai-slop:tldr` checks a text against the tropes.fyi catalog only. The layer rules no longer produce findings but still supply their exceptions, so a single "robust" or "we" in a paper is not flagged. `--ste` no longer applies to this mode.
- **Changed:** the TL;DR no longer rates a text. The `**AI use:**` verdict, the five-level impact rating, the share of the prose that needs a rewrite, and the written assessment are gone. Each block gives the number of patterns that affect readability and the word count, as in "3 in 850 words", and up to five bullets under "Patterns that affect readability", which `count_findings.py` writes with a fixed label, a count, and a quote. Minor patterns, such as formatting or a reused word, stay in the report but do not count, and a file with fewer than two other patterns is only listed.
- **Added:** a genre step, in which the skill determines before the review which catalog patterns are normal in the kind of text, such as numbered concerns in a peer review. It records no finding for them and lists them in the report and the TL;DR.
- **Added:** instructions for `/ai-slop:tldr`, given as text after the path. They can narrow the review, exempt or add a pattern, and give context for the genre step, but they cannot change a count. The report states how the review applied each instruction.
- **Added:** tests for borderline matches of tropes such as Negative parallelism and Preamble, and a unit for each finding. A passage with two tropes is one finding, one term under several names is one finding that quotes the names, and em-dashes count only above three per 350 words.
- **Changed:** the review skips quotations, text that the writer restates from the work under discussion, form text, and curly quotes, and tests every paragraph against every catalog entry, one file at a time. For a directory, a last pass aligns the decisions on each trope across files.
- **Changed:** `count_findings.py` gives the number of patterns per file and whether the file needs feedback, and ranks the rules by cost, with the minor rules last and `new` and `rising` tropes first on ties. It counts character and formatting tropes once per line, and `--scope=<path>:<ranges>` limits the word count to the lines that the review covered.
- **Fixed:** `count_findings.py` counted LaTeX `%` comments as prose, missed catalog names in quotation marks such as `"Delve" and friends`, and split "Preamble (announce-then-answer)" into two rules.

## [2026-09_rev32] - 2026-09-27

- **Changed:** `G.plain-words` lists "shape" as a word to replace, with structure, format, or pattern for the noun and structure or influence for the verb. It keeps "shape" for geometry, statistical distributions, and array dimensions.
- **Changed:** the bundle no longer uses "shape" outside quoted examples and old commit messages. The lint check `tldr-block-shape` is now `tldr-block-format`, `check_baseline.py` comes from pymarkdown-skill 0.2.7, and the seed test now fails on "shape".
- **Changed:** 21 rules in the general, scientific, and STE layers give their examples as "phrase" -> "rewrite" pairs, where some had given only the replacement word or no rewrite.

## [2026-09_rev31] - 2026-09-24

- **Changed:** thresholds that only the self-check of the general layer stated are now also in their rules: more than one-third passive sentences in a paragraph (`G.active-voice`), more than two hedges in a paragraph (`G.hedge-from-evidence`), three consecutive sentences within 5 words of each other in length (`G.sentence-length`), and around 5 pause marks per page-equivalent (`G.pause-mark-count`). The thresholds and self-check items are unchanged.

## [2026-09_rev30] - 2026-09-24

- **Added:** an export mode, `/ai-slop:export`, which writes the general layer and the AI trope catalog into one Markdown file with an instruction to apply the rules to all prose that Claude writes or changes, with the writing conventions of a project taking precedence. The default output, `~/.claude/rules/ai-slop.md`, loads in every Claude Code session and project without an import, a path under `.claude/rules/` in a repository loads in that project only, and any other path writes the file for another use. `--ste` adds the STE layer. The scientific and LaTeX layers stay out, and `/ai-slop:init` still writes them into `WRITING.md`.
- **Added:** `export_rules.py`, which assembles and writes the file, with each layer under its own heading and without the title and preamble of the catalog, and reports the approximate size in tokens on stderr. Running the mode again replaces an earlier export, which the generation sentence in its header marks, and the skill asks before replacing any other file.
- **Changed:** the version string has twelve callsites, with one in the new `SKILL.md`.

## [2026-09_rev29] - 2026-09-24

- **Added:** `scan_repeats.py`, a candidate scan for **Refer back instead of repeating** (`G.refer-back`). It lists every sentence that repeats an earlier sentence of the same file, as a verbatim copy, a copy with a changed ending (a shared run of six words), or a short sentence pasted twice, except a sentence that recurs three or more times, such as a form label. `/ai-slop:review`, `/ai-slop:review-diff`, and `/ai-slop:review-repo` test each row against the rule, so a second copy is a finding and a brief reminder stays.
- **Changed:** catalog tropes with the status `fading` are weak evidence for the AI-use verdict of the TL;DR, and a sign of unassisted writing in the same paragraph discounts them, as it discounts figurative phrasing and padding.
- **Fixed:** `count_findings.py` no longer reads the word that joins two rules in a Rule field, such as "matching", as part of the trope name.
- **Fixed:** the TL;DR fixtures plant the rules that the layers assign, and `check_fixture_recall.py` counts a rule and a catalog trope that name the same pattern, such as `G.refer-back` and "Self-echo", as one.

## [2026-09_rev28] - 2026-09-24

- **Added:** a TL;DR mode, `/ai-slop:tldr`, which runs `/ai-slop:review` on a document or `/ai-slop:review-repo` on a directory, with the same flags, and condenses the report into `ai-slop-tldr.md`. Each file with findings gets a self-contained block with the impact level, a fixed AI-use verdict, an assessment of one to five sentences, and up to three bullets with the worst patterns under a fixed line, each with its count and a short quote. Files without findings are listed together, commit messages get one block, and `/ai-slop:revise` still applies the full report.
- **Added:** the impact scale. A finding obscures the meaning (e.g., an unclear referent), delays the content (e.g., padding), or only distracts (e.g., punctuation). A paragraph needs a rewrite when at least two of its findings obscure or delay, and at least one per 100 words. The level is the share of the prose in such paragraphs: None when no finding obscures or delays, Minor under a tenth, Moderate under a third, Major under two thirds, and Severe above, with at least three such paragraphs for Major and Severe.
- **Added:** the AI-use verdict, which `count_findings.py` computes from the AI-typical findings, i.e., the catalog tropes and the rules for patterns that AI output overproduces, without grammar slips, dropped words, spelling, unclear pronouns, or curly quotes. It is Little sign of AI tools with fewer than two such findings or fewer than one per page-equivalent, Harder to read when the level is Moderate or above and one of them is in a paragraph that needs a rewrite, and Reasonable otherwise.
- **Added:** counter-evidence for the verdict. The report gains a `## Signs of unassisted writing` section with the typos, grammar slips, missing articles, and missing words of each file. In a paragraph with such a sign, patterns that non-native and hurried writers produce as readily as models, such as figurative phrasing and hedges, stop counting as AI evidence. The reply lists files where the text contradicts the verdict under `Verdicts to check:`.
- **Added:** nine synthetic reviews under `scripts/tests/fixtures/tldr/`, each with planted findings and the level and verdict that it must get, and `scripts/tests/check_fixture_recall.py`, which compares a real review of a fixture with its planted findings. `scan_repo.py` now skips `fixtures` and `testdata` directories.
- **Added:** `count_findings.py`, which computes everything in a TL;DR that a count can settle, so that two runs over the same report agree. It counts findings per file and rule, ranks the rules of each file by count weighted 4 for obscures, 3 for delays, and 1 for distracts, and gives the paragraphs that need a rewrite and the level and verdict of each file. A finding counts once for each rule that it cites, and the script warns when a finding has no rule.
- **Added:** a `tldr-block-shape` check in `schema_checks.py`, which the linter runs on `ai-slop-tldr.md`. It flags a block without an impact level from the scale, an AI-use verdict, or an assessment, with more than five sentences in it, with more than three bullets, or with bullets that lack the fixed line before them.
- **Changed:** the version string has eleven callsites, with one in the new `SKILL.md`, and `ai-slop-tldr.md` joins the generated artifacts that are never committed.

## [2026-09_rev27] - 2026-09-22

- **Changed:** the personification clause of **No figurative language** (`G.no-figurative-language`) covers any subject that is not a person or a group, where it had named code, models, tests, and data. A desire, feeling, belief, duty, or merit given to a document, a tool, or an abstract noun is a finding ("a period does the job"), and the fix names the mechanism or observable behavior. Verbs that name a defined behavior ("a parser expects a token") and author metonymy ("the paper argues") stay literal.
- **Fixed:** one personification in the revise skill, which now applies the suggested revisions of a report as written where it had trusted them.

## [2026-09_rev26] - 2026-09-22

- **Changed:** **Be concrete** (`G.be-concrete`) becomes a rule on empty head nouns, such as thing, aspect, or item, and the quantifiers before them, such as "various". The test is to write the specific noun in the slot. Where the text cannot supply it, the finding goes to author judgment with the candidate readings instead of a guessed noun. A generic noun stays where the generality is the claim, and no density threshold applies.
- **Fixed:** empty nouns in the prose of the bundle, such as "the same thing", which became "the same construction".

## [2026-09_rev25] - 2026-09-22

- **Changed:** the release protocol in `CLAUDE.md` opens with a rule to publish a rev once the work is settled and checked against the main use of the bundle and the existing rule layers, not at the first version that passes the smoke suite. A correction in the same session is squashed into that rev, and rule 3 governs once the session has moved on or anyone may have pulled the tag. The other rules are renumbered.

## [2026-09_rev24] - 2026-09-22

- **Added:** **Consequence connectives** (`G.consequence-connectives`) in the general layer. AI text marks nearly every consequence with one word, "so" in general prose and "therefore" or "thus" in academic prose, and the rule tests whichever word a document uses most.
- **Added:** an order of fixes for the rule: delete a connective that the order of the content already implies, then recast with because or since, and substitute another connective last, counting it toward the two-per-paragraph limit on transition words. A sentence-initial "So" in formal prose is deleted, and the rule prefers "therefore" and "thus" mid-sentence ("The counts are therefore unreliable").
- **Added:** a count over the family of connectives. More than two or three per page-equivalent (~350 words) flags a text, and the concentration on one word counts only at or above that density. Parallelism across items of the same kind, the intensifier, "so that", the correlative, and quoted material are out of scope.
- **Changed:** the transition-word note in the restricted-words section points to the new rule.
- **Fixed:** the README, `fetch_tropes.py`, `find_citation_issues.py`, and `rules-rationale.md` follow the new rule. The exit-code listings in the ground and revise skills keep their connectives under the parallelism exception.

## [2026-09_rev23] - 2026-09-15

- **Changed:** the bundle applies the findings of an `/ai-slop:review-repo` run over its own repository, mostly dropped *that*, semicolons or colons used as pauses, parenthetical lists without "e.g.,", invented compounds, and colorful words. The fixes cover the README, `CLAUDE.md`, released entries of this changelog, the commands, rule layers, rationale, skills, and script docstrings and comments, and no script code changed.
- **Changed:** the questions for author judgment from that review were settled from the rule layers. Noun stacks such as "AI trope catalog" lose their hyphens (`G.compound-hyphens`), and the nouns "cite" and "fetch" became "citation" and plain phrases (`G.no-coinages`). "Em-dash" has one spelling, the headings of the rule layers use sentence case, and the skills no longer bold words for emphasis.
- **Changed:** **Em dashes are unspaced** is now **Em-dashes are unspaced**, and **Keep metacommentary in comment-commands** is now **Keep metacommentary in comment macros**, with their keys unchanged.
- **Fixed:** the README no longer says that the directory denylist applies only outside a git repository, and the em-dash rule no longer offers parentheses as a replacement, which the same rule forbids.
- **Removed:** the rationale entries for `G.such-as` and for the concision rules, which gave no reason.
- **Changed:** the upstream-owned `lint_markdown.py`, `check_baseline.py`, and `refresh_vendor.py` come from pymarkdown-skill 0.2.6, which applies the review findings for those files.
- **Changed:** the commit history. Of the 85 commit messages that the review checked, 44 were rewritten to follow the general layer, under the history repair that `CLAUDE.md` describes. Every tag moved with its commit, and every tree is unchanged.

## [2026-09_rev22] - 2026-09-15

- **Fixed:** prose that the rev21 sweep missed, such as "doing a dash's work", semicolons joining independent clauses, lowercase sentences after a colon, "sits" or "lies" for where something is (`G.plain-words`), and an "orchestration" banner in `verify_references.py`. The fixes cover the script docstrings and comments, `CLAUDE.md`, the README, the review-diff skill, and the restricted-words table.

## [2026-09_rev21] - 2026-09-15

- **Fixed:** README, `CLAUDE.md`, and manifest statements that no longer matched the bundle, on the three helpers that reach the network (`check_quotes.py` included), the report schema that all three review modes share, the ten version callsites, the glyph and reference scans, `--ste`, the author of the trope catalog, and the three places of a rule change.
- **Fixed:** skill steps that contradicted the scripts. A trope finding carries the catalog status, and revise puts a `% GROUNDING: TODO verify` stub on its own line below the citation, since a stub inside the line comments out the rest of it. The review skill says that only the ASCII dash pass skips fences and `%` comments, review-diff reads a `passive` or `nominalization` row at the matched words, and review-repo applies the directory denylist inside a git repository too. Init prints two summary lines and lists every script that it runs, and ground shows the `source` field of a downgraded quote.
- **Fixed:** script docstrings and comments that misdescribed their code, among them a `scan_repo.py` limitation about a second comment on one line, which the extractor does read, and the `unchecked-offline` verdict of `verify_references.py`, which an HTTP error also produces.
- **Fixed:** drift inside the rule layers. The self-check and rationale for `G.paragraph-padding` count aphorisms, as the rule does, cross-references use the rule names that their keys define, and the rationale no longer says that the layers carry only additions to the catalog or that the skills load the catalog by path.
- **Changed:** the prose of the bundle follows its rules again, with fixes for semicolons joining independent clauses, lowercase sentences after a colon, dropped *that*, stand-in words, figurative wording such as "escape hatch", and a negative-parallelism sentence in the ground skill.
- **Fixed:** the blank line between steps 1 and 2 of `revise/SKILL.md`, which rev20 removed.

## [2026-09_rev20] - 2026-09-15

- **Changed:** sentence length in STE mode has a tolerance band instead of a hard 25-word cutoff. Up to 25 words is the target, a sentence of 26 to 35 words stays when it has one main idea and the reader does not have to hold several clauses before its point, and a longer one is split. `T.precedence` no longer overrides `G.sentence-length` on length, and `scan_sentences.py` still lists every sentence over 25 words.
- **Removed:** the `[KEPT: reason]` marker, the **Kept sentences** report section, the revise step that inserted the marker, and the scanner code that skipped marked sentences. The rule stays as `T.keep-original` (formerly `T.keep-and-mark`): A sentence that an STE rewrite would weaken keeps its original form, and a review lists it under **Items requiring author judgment** with the reason.

## [2026-09_rev19] - 2026-09-15

- **Added:** an STE mode. `--ste` loads `shared/rules-ste.md` on top of the layers that the scope selects, in `/ai-slop:review`, `/ai-slop:review-diff`, `/ai-slop:review-repo`, and `/ai-slop:init`. The layer adapts part of ASD-STE100 Simplified Technical English, such as short sentences, active voice, one topic per paragraph, and verbs instead of nominalizations. It departs from STE with sentence length that varies within a 25-word limit and with at most one stylistic device per reply, headed section, or text without headings. Quotations and literal strings stay as written, and the rules carry `T.` keys.
- **Added:** the `[KEPT: reason]` marker (`T.keep-and-mark`) for a sentence that an STE rewrite would weaken. A review lists such a sentence under a new **Kept sentences** report section, `/ai-slop:revise` inserts the marker inside a comment in LaTeX and Markdown, and a later STE review skips a marked sentence.
- **Added:** `scan_sentences.py`, which lists the STE candidates in a Markdown, plain-text, or LaTeX file: sentences over 25 words, runs of three or more sentences within 5 words of each other in length, passive verbs, and a light verb followed by an action noun. The review skills run it in STE mode.
- **Fixed:** the Bundled files list of `/ai-slop:review-repo` names `scan_glyphs.py`, which its metrics step already ran.
- **Unchanged:** the prose of the bundle, since the STE layer is opt-in and needs no sweep.

## [2026-09_rev18] - 2026-09-09

- **Removed:** the semicolon ratchet test added in rev17, which could not tell a list separator from a clause joiner. Clause-joining semicolons are left to the `/ai-slop:review-repo` sweep, and the "lives in" test stays.

## [2026-09_rev17] - 2026-09-09

- **Fixed:** `scan_repo.py` no longer drops a prose file that merely mentions "generated by" or "do not edit". A file counts as generated only when the marker is on a comment line within its first ten lines, or is the `@generated` tag or the uppercase `DO NOT EDIT` banner, and stderr names every skipped file.
- **Fixed:** the `WRITING.md` structure check in `schema_checks.py` accepts the H1 "Writing rules for this project" that init writes, besides "Writing rules for this paper", so its findings fire on a real file.
- **Fixed:** `fetch_tropes.py` accepts only a body with a Markdown H1 and at least five `##` trope headings, so an error body or error page no longer passes as the catalog. It decodes a base64 data URI, rejects a body over two megabytes, and prints the size, heading count, and content hash of what it accepted to stderr.
- **Fixed:** `scan_glyphs.py` no longer counts dashes in `%` comments of a `.tex` file, such as the ` -- ` separator of `% GROUNDING:` comments, or runs of four or more dashes toward the dash density. Its fence tracking, which it shares with `scan_reference.py`, honors nesting.
- **Fixed:** `verify_references.py` flagged correct entries. A year now matches any year that CrossRef (online-first or print) or DBLP records for the work, DOI entries merge in the DBLP record as `L.source-priority` says, and venue comparison expands common SE abbreviations (e.g., TOSEM, EMSE, ICSE) and matches database abbreviations such as "Empir. Softw. Eng." by word prefix.
- **Fixed:** `find_citation_issues.py` follows `\input` / `\include` and finds a `\cite` with a key list that spans lines, so the grounding to-do of the review and the site list of ground see the same calls. `insert_grounding.py` places the comment after the line where a multi-line call ends.
- **Fixed:** `find_latex_root.py` no longer treats the chapters of a `subfiles` project as roots.
- **Fixed:** `scan_repo.py` rejects a `--commits` value that starts with a dash, which git had read as an option, and exits 2 with git's message when a range cannot be resolved, instead of reporting zero commits. It also skips YAML front matter, indented code blocks, dependency pins such as `requirements.txt`, and license texts.
- **Fixed:** `bib_parse.py` reads a backslash-escaped quote inside a quoted value, joins `#` concatenations, and resolves TeX accents (e.g., `{\"u}`, `\c{c}`, `\ss`) to Unicode.
- **Added:** `check_quotes.py`, which re-reads the `source` (URL or local path) that each grounding agent now returns and confirms that the quote occurs in it after normalization, downgrading a quote that it cannot find to `TODO verify -- unverified`. A PDF or an unreachable source goes back to the skill to check by hand, and the ground skill states that the agents send claim sentences to search engines.
- **Changed:** `/ai-slop:review-diff` decides the rule layers per changed file and diffs `.tex`, `.md`, and `.txt` together, so a code repository with a paper in a subdirectory still gets its Markdown changes reviewed, and its metrics run `scan_glyphs.py` and `scan_reference.py`. `/ai-slop:init` takes `--general` to force the general layer for such a repository.
- **Changed:** `/ai-slop:revise` accepts the Markdown or plain-text document that a review names in its `**Paper:**` header, where it had stopped without a LaTeX root, and applies a repo-mode report one file at a time, from the blocks under the `### <relpath>` heading of each file.
- **Changed:** the review, review-diff, review-repo, and ground skills resolve the repository root with `git rev-parse --show-toplevel` before appending to `.gitignore`. The dash heading of the report template names both dash kinds.
- **Changed:** the general layer describes the v2 catalog. `G.catalog-precedence` names the entries that it overrides (i.e., "Delve" and friends, Signposted conclusion, Rule of Three pattern, and Bold-first bullets) instead of a banned-word list, and self-check item 1 scans for the word-level entries of the catalog. `S.we` gains the single-author case, and `L.editorial-comments` no longer names the author macros of one project.
- **Changed:** the init skill and its `WRITING.md` template, `verify_references.py`, the README, the review and review-diff skills, and the rationale no longer describe the snapshot fallback, fetch chain, or plural sources that rev16 removed.
- **Changed:** the prose of the bundle follows its rules again, with fixes for semicolons joining independent clauses, "lives in", lowercase sentences after a colon, announced counts, and the claim that pushed history is immutable, which rev15 disproved. Two smoke tests check the prose between sweeps, one counting prose semicolons in the first-party Markdown and one failing on "lives in".

## [2026-09_rev16] - 2026-09-09

- **Removed:** the gist mirror and the bundled snapshot, with `refresh_tropes.py`, `shared/tropes-snapshot.md`, the attribution sidecar, and the snapshot-refresh step of the release protocol. `fetch_tropes.py` reads only tropes.fyi and exits 1 when the site is unreachable, and the four skills that load the catalog stop and say so. `--tropes=<path>` remains the way to review offline or against a pinned catalog.
- **Changed:** `scan_glyphs.py` counts the dash rather than the character. A new `ascii-dash` category matches `--` and `---` used as a dash, but not a command-line flag, numeric range, table separator, fenced block, or inline code span, and the density metric of the review adds it to `em-dash`, so a LaTeX em dash written as `---` now counts.
- **Changed:** the review uses the status tags of the catalog. A trope finding names the status, as in `Negative parallelism (tropes.fyi, consistent)`. Every `new` and `rising` match is reported, a `fading` match is confirmed against the passage first, and a rule layer still outranks the catalog wherever they disagree.

## [2026-09_rev15] - 2026-09-09

- **Changed:** every commit message in the history was rewritten to follow the general layer, and all 59 release tags moved with their commits, with byte-identical trees. Semicolons became periods between independent clauses and commas between two actions in a subject line, and em-dash glyphs became periods or commas. Semicolons in lists, quoted output, or code spans stay, as do the two glyphs quoted as examples. The pass also fixed a British spelling, a comma splice, and an inhabitance framing.
- **Changed:** the release protocol allows a maintainer-requested history repair as the exception to its rule against rewriting a released commit. Every tag moves with `--tag-name-filter`, the trees are verified against `refs/original`, and `main` and the tags are force-pushed together. The commit-message convention no longer claims that a pushed message cannot be corrected.

## [2026-09_rev14] - 2026-09-09

- **Added:** a commit-message convention in `CLAUDE.md`, which puts the check of a message before `git commit` and names the recurring failures: a semicolon joining two independent clauses, a literal em-dash glyph, and counts announced in front of continuous prose. The release suffix of the subject line stays as the one semicolon that the convention keeps.
- **Unchanged:** the messages already pushed, since rule 2 of the release protocol rules out rewriting a released commit.

## [2026-09_rev13] - 2026-09-09

- **Fixed:** the `2026-09_rev11` and `2026-09_rev12` entries below record what those releases changed and no longer break rules that the bundle enforces, such as `G.no-list-cramming`, `G.parenthetical-lists`, and `G.short-enumerations`.
- **Fixed:** the README no longer calls the bundled snapshot a copy of the gist, and its Acknowledgements and License sections name the tropes.fyi page as the source since rev11.
- **Changed:** README semicolons that joined two independent clauses became sentences, per `G.semicolons`. Those inside a parenthetical and those separating items in the review-repo language list stay.
- **Added:** `CLAUDE.md` records that changing a rule means editing the layer, its self-check item, and `rules-rationale.md`, and that adding or tightening a rule means sweeping the prose of the bundle for the pattern in the same rev. The snapshot-refresh step names its source order.

## [2026-09_rev12] - 2026-09-09

- **Added:** **Announce a count only when the reader tracks it** (`G.no-announced-counts`), from the Compulsive counting and Preamble entries of the v2 catalog. A count stays where the reader checks items against it, such as a checklist or the research questions of a study, and is removed before continuous prose. The test is whether a later sentence refers back to the number.
- **Added:** **No enumerated list disguised as paragraphs** (`G.no-prose-listicle`), from the Excessive enumeration entry. Ordinals inside one paragraph are structure, and the same markers opening consecutive paragraphs are an unmarked list.
- **Added:** a **Phrases to Avoid** entry for **"famously" / "notoriously" / "as is well known" / "a classic"**, from the Appeal to familiarity entry.
- **Changed:** rules in the general layer that half-covered a v2 entry now cover it: `G.no-formulaic-openings` the announce-then-answer opener, `G.no-metacommentary` a sentence that narrates the reasoning behind the writing, `G.no-coinages` an abstract label of a domain word plus a problem-noun ("supervision paradox"), `G.plain-words` "lives" for where something is defined, `G.paragraph-length` a bare fragment set as its own paragraph, `G.paragraph-padding` an aphorism written to be quoted, and `G.no-excess-bold` the bold-first bullet. `G.em-dash-glyphs` states that rewriting the glyph as `--` leaves the dash in place.
- **Changed:** `S.cite-specific-works` requires a quantity word to match the citations behind it, so "several studies" in front of two references is inflation.
- **Changed:** the prose of the bundle no longer frames a file or module as a place where something lives ("the skill's workflow lives in ..." became "is in ...").
- **Added:** self-check items 26 and 27 for the two new rules, the new patterns in items 9, 13, and 21, and `rules-rationale.md` entries for the two new rules and the dash-glyph clarification.

## [2026-09_rev11] - 2026-09-09

- **Changed:** the trope catalog comes from tropes.fyi first and the upstream gist second, since only the site carries the v2 catalog. The bundled snapshot is refreshed to v2, with 49 tropes instead of 37, each tagged with a category and one of the statuses new, rising, consistent, and fading. About twenty entries are new, such as Reasoning leak, Premise stacking, Compulsive counting, and Synonym cycling.
- **Fixed:** the site step of the fetch chain could hand a rendered HTML page to the review skills in place of the catalog. `fetch_tropes.py` now sends a user agent and unwraps the Markdown from the `data:text/markdown` URI of the download link or the `<pre>` block, and a page that yields neither falls through to the next source.
- **Changed:** `/ai-slop:init` inserts a blank line between each `**Avoid patterns like:**` line and the bullet list under it when it inlines the catalog, so the lint loop no longer has to repair those lists in `WRITING.md`. The normalization examples follow the v2 headings.
- **Changed:** the README, the four skill files that load the catalog, the two command files, and `tropes-snapshot.ATTRIBUTION.md` document the source order, and the attribution file names the site as the source of the snapshot and the gist as an earlier mirror.

## [2026-09_rev10] - 2026-09-05

- **Added:** a **Phrases to Avoid** entry in the general layer against **"arm"**, with "condition" or "treatment" for an experimental manipulation, "group" for a set of subjects, "variant" or "configuration" for a version of a prompt, model, or pipeline, and "split" for a data partition. "Arm" stays for a randomized trial group or a bandit option.

## [2026-09_rev9] - 2026-09-03

- **Added:** **Rewrite *whose* clauses on things** (`G.whose-on-things`) in the general layer. A restrictive *whose* clause on a thing ("entries whose keys appear in the new citations") becomes *with*, a participle or verb on the head, or the property as the subject of its own clause. *Whose* stays for a person or group and where every restatement is longer or repeats the head noun, and more than one per page-equivalent is a secondary signal.
- **Changed:** the rule layers, skill files, README, this changelog, and Python docstrings and comments follow the new rule, except the upstream-owned `lint_markdown.py`. `review/SKILL.md` replaces the coinages "post-colon clause" and "post-colon text" with "the clause after it" and "the text after it".

## [2026-09_rev8] - 2026-09-01

- **Changed:** `scan_repo.py` reviews the contents of a fence with a prose info string (i.e., `markdown`, `md`, `mdx`, `text`, `txt`, `plain`), such as the templates quoted in the skill files. Fences nest: A bare code fence inside a prose fence stays skipped, and a fence closes only on a bare marker of its character with at least its length.
- **Fixed:** the review-repo section of the README has its full language list again instead of the pointer to the `COMMENT_SPECS`/`NAME_SPECS` tables that the 2026-09_rev4 sweep left.
- **Fixed:** the intro of the general layer no longer stacks "the contested rules, the rules that a reader might push back on" or joins its clauses with semicolons.

## [2026-09_rev7] - 2026-09-01

- **Fixed:** prose inside the fenced templates, which the repository scan skips as code. The report disclaimer of every generated report no longer joins two clauses with a semicolon, and its Summary placeholder no longer asks for "headline metrics". The `WRITING.md` header and the two maintainer comments read the same way.
- **Fixed:** the 2026-06_rev13 entry below has the language list again that the 2026-09_rev4 sweep had shortened.

## [2026-09_rev6] - 2026-09-01

- **Fixed:** `CLAUDE.md` and the README name all five upstream-owned paths (i.e., `lint_markdown.py`, `check_baseline.py`, `refresh_vendor.py`, `_vendor/`, `bundled_licenses/`), where they had named only the first two. The `sync/sync_to_skill.sh` script of pymarkdown-skill copies them in and stamps the version in `scripts/.pymarkdown-skill-version`.

## [2026-09_rev5] - 2026-09-01

- **Changed:** synced the pymarkdown-skill helpers at upstream release 0.2.4, which carries the em-dash and wording fixes that the 2026-09_rev4 sweep had applied to `lint_markdown.py` and `refresh_vendor.py` here. No behavior change.

## [2026-09_rev4] - 2026-09-01

- **Changed:** every rule in the three layers carries a stable key after its name (e.g., `G.semicolons`, `S.significant`, `L.grounding-comments`), and cross-references in the layers, rationale, and self-check items cite keys, so a rename or an insertion no longer breaks a reference. The `Rule:` field of a report carries the name followed by the key, as in `Semicolons (G.semicolons)`.
- **Changed:** rule names are plain directives without punctuation or metaphor. Renamed: "Name the relation with a connective; don't just drop the pause" to **Name the relation with a connective**; "Cite, do not gesture" to **Cite specific works**; "Name the thing instead of pointing at it" to **No stand-in words**; "Anchor every sentence-initial *This*, *These*, *That*, or *It* to a noun" to **Anchor sentence-initial pronouns**; "Use *the* only for a referent the reader can already identify" to **Definite article only for known referents**; "Watch the combined load" to **Combined pause-mark count**; "Hedge from evidence, not from timidity" to **Hedge only from evidence**; "Introducer punctuation: `:` not `.` before a list or continuation" to **Colon before a list or continuation**; "Pick one example-list signal and stay with it" to **One example signal per document**; "Signal whether a parenthetical list is examples or exhaustive" to **Mark parenthetical lists as examples or exhaustive**; "Avoid redundant content; refer back instead" to **Refer back instead of repeating**; the LaTeX caption rule to **Caption punctuation**; the "significant" rule to **Reserve "significant" for statistics**; and the paper-versus-study tense rule to **Present tense for the paper, past tense for the study**.
- **Added:** **Participial openings** (`G.participial-openings`) as a rule in the general layer, where it had been only a self-check item.
- **Changed:** the prose of the bundle follows its rules. A `/ai-slop:review-repo` sweep fixed findings such as em-dash glyphs, semicolons joining independent clauses, and dropped *that* in the rule layers, skill and command files, README, `CLAUDE.md`, this changelog, docstrings and comments, manifest descriptions, and H1 titles. The `"before" -> "after"` notation uses an ASCII arrow, and `lint_markdown.py` was fixed here and synced back to pymarkdown-skill.
- **Fixed:** `init/SKILL.md` step 3 points to step 9 for the summary, not step 7.

## [2026-09_rev3] - 2026-09-01

- **Changed:** **Cut padding at the paragraph level** (`G.paragraph-padding`) defines windup as a sentence that announces what its own paragraph then does. A paragraph that opens a section is legitimate when it states the claim or purpose of the section or orients the reader across the subsections beyond the headings, and windup when it merely lists the subsection headings or repeats content stated elsewhere.
- **Added:** a density signal in the same rule for generic-truth sentences, true of any document on the subject, and evaluative sentences, which grade the preceding claim without adding to it. One can open a section or mark that a result matters, and more than one per paragraph, or more than two or three per page-equivalent, is filler.
- **Changed:** the **Reference** and **Clause Boundaries** rules, self-check item #24, and the rationale use periods where a colon or semicolon joined clauses ("Test: do X; if Y, do Z" is now "To test it, do X. If Y, do Z."). No rule content changes.

## [2026-09_rev2] - 2026-09-01

- **Added:** a fourth **Reference** rule, **No stand-in words** (`G.stand-ins`), which replaces a stand-in word that the sentence could state directly (e.g., *ones*, *the former / the latter*, *respectively*) with the noun, restructuring the clause if it then repeats ("detect flaky tests among the generated ones" -> "detect which of the generated tests are flaky").
- **Changed:** `scan_reference.py` lists a third kind of candidate, `stand-in` (*ones*, *the former*, *the latter*, *respectively*, *do / did so*, *those of / that / which / with*), and the metrics step of the review skill names it.

## [2026-09_rev1] - 2026-09-01

- **Changed:** two sentences in `rules-rationale.md` (**Reference and clause boundaries**) use plain language instead of terms such as "frame" and "definite-heavy register". No rule or skill behavior changes.

## [2026-09] - 2026-09-01

- **Added:** a **Reference** section in the general layer with three rules that share one test ("which one?"). Anchor every sentence-initial *This / These / That / It* to a noun. A summarizing noun must name something that the text has listed. Use *the* only for a referent that the reader can already identify.
- **Added:** a **Clause Boundaries** rule in the general layer, **Keep *that* in formal prose** (`G.keep-that`). It restores the relativizer of a restrictive object relative ("the metrics that the benchmark reports") and the complementizer after a reporting verb ("the results show that the effect persists"), except after fixed heads, in quoted text, and in deliberately informal text (e.g., commit messages, code comments).
- **Added:** `scan_reference.py`, which lists a `<file>:<line>:<col>` row for each sentence-initial *This / These / That / It* followed directly by a verb and each *such* + noun, outside LaTeX comments, code blocks, and common dummy-*it* frames. `/ai-slop:review` tests each row against the rule and lists a reference with an antecedent that it cannot determine under **Items requiring author judgment** instead of guessing a noun.

## [2026-08_rev1] - 2026-08-27

- **Changed:** **No invented compounds or verbs-as-nouns** (`G.no-coinages`) also covers a noun phrase coined ad hoc to name a specific artifact, document, or table, hyphenated or not, which a description replaces ("data-sources table" -> "a table listing all data sources").

## [2026-08] - 2026-08-26

- **Added:** a punctuation rule in the LaTeX layer, **Em dashes are unspaced.** Write `word---word` without surrounding spaces, the American convention. The rule governs spacing only, and **Em-dashes** (`G.em-dashes`) and **Literal em-dash glyphs in source** (`G.em-dash-glyphs`) govern the choice of mark and the glyph. Verbatim quotes keep the spacing of their source.

## [2026-07_rev2] - 2026-07-24

- **Added:** a **Phrases to Avoid** entry in the general layer against **"headline numbers" / "headline figures"**, in favor of naming the figures plainly (e.g., "the largest claims", "the most-cited figures", "the figures").

## [2026-07_rev1] - 2026-07-09

- **Added:** a punctuation rule in the general layer, **Name the relation with a connective.** When a flagged em-dash or colon introduces an example or a restatement, the fix is a connective that names the relation, such as "e.g.," or "that is", rather than a bare period or comma. A mark that sets up a single payoff clause or introduces a true list stays.

## [2026-07] - 2026-07-01

- **Added:** `refresh_tropes.py`, a maintainer script that re-pulls the bundled trope snapshot (`shared/tropes-snapshot.md`) from the gist, then tropes.fyi, and keeps it bit-identical to upstream. It reports "already up to date" without rewriting when the fetch matches the snapshot, and exits non-zero without touching it when both sources are unreachable.
- **Changed:** the release protocol refreshes the bundled snapshot with every rev (`CLAUDE.md` rule 6 and the README "Maintainer notes"), and the README recipe for the refresh uses the script instead of a raw `curl`.

## [2026-06_rev16] - 2026-06-29

- **Added:** `scan_glyphs.py`, a deterministic recheck for glyphs that the per-section LLM pass undercounts. It prints a `<file>:<line>:<col>` row for each literal em-dash, en-dash, arrow, curly quote, ellipsis, or non-breaking space, and `/ai-slop:review` takes the em-dash density from it. Every em-dash, arrow, curly-quote, ellipsis, and non-breaking-space row becomes a per-section finding, while en-dashes in ranges and glyphs inside quotes or code are left to judgment.
- **Changed:** **Plain, literal language** (`G.plain-language`) names the systems-jargon count nouns "a write", "a read", "a create", and "a delete" as verbs used as nouns, with the rewrite "a write request" or "a write operation".

## [2026-06_rev15] - 2026-06-29

- **Added:** `/ai-slop:review-repo` also scans commit messages, which `scan_repo.py` reads from `git log` under a `commit <short-sha>` pseudo-path, so the report groups their findings by commit. Merge commits and standard trailer lines (e.g., `Co-authored-by`, `Signed-off-by`) are skipped.
- **Added:** commit-message scope controls. The default covers the most recent 200 commits. `--commits=<N>` sets another count, `--commits=all` the full history, `--commits=<range>` a git revision range (e.g., `main..HEAD`), and `--no-commits` turns commit scanning off. Commit-message findings are advisory, and `/ai-slop:revise` does not apply them.

## [2026-06_rev14] - 2026-06-26

- **Added:** `/ai-slop:review-repo` also scans LaTeX (`.tex`) files and reviews the document body and the `%` comments as prose against the general rules. The LaTeX layer of `/ai-slop:review` remains the tool for citations, BibTeX, and section-aware checks.

## [2026-06_rev13] - 2026-06-26

- **Added:** a repo mode, `/ai-slop:review-repo`, which checks every Markdown and plain-text file and the comments and doc-comments of source and config files against the general rules and the trope catalog, and writes `ai-slop-report.md` with findings grouped by file.
- **Added:** `scan_repo.py`, the extractor for the new mode. It reads comments in Shell, Java, Kotlin, Python (including docstrings), JavaScript, and TypeScript; the rest of the C family (C, C++, C#), Go, Rust, Swift, Scala, Dart, Groovy/Gradle, Ruby, PHP, Perl, R, Lua, and Lisp/Clojure; the web and styling formats HTML, XML, Vue, Svelte, CSS, SCSS, and Less; SQL; and config formats such as YAML, TOML, INI, `.properties`, `.env`, Dockerfile, Makefile, CMake, and Terraform. The `COMMENT_SPECS` and `NAME_SPECS` tables in `scan_repo.py` are the authoritative list. Comment detection ignores a `//` or `#` inside a string literal and skips a shell shebang.
- **Added:** the extractor honors `.gitignore` in a git repository (it scans the tracked files) and skips generated files (a "DO NOT EDIT" or `@generated` header), lockfiles, binaries, vendored directories, and (in this revision) `.tex` source.
- **Changed:** the version string is in ten callsites, with one in the new `review-repo` `SKILL.md`.
