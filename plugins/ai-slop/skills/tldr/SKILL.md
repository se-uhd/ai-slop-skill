---
name: tldr
description: Review a text against the tropes.fyi catalog of AI writing tropes and condense the review into a TL;DR that gives, per scanned file, the number of patterns that affect readability and up to five bullets, each with a plain label, a count, and a quote. Use when the user asks for a tl;dr or a quick assessment of a draft, a thesis, a paper, or a repository, or asks how the AI writing patterns in a text affect its readability, or runs `/ai-slop:tldr`. Reviews a document or a directory against the catalog only, with the rule layers serving only for their exceptions, and takes free-text instructions after the path, such as which part to review or who wrote the text. Writes `ai-slop-report.md` and `ai-slop-tldr.md`.
license: CC-BY-4.0
metadata:
  version: "2026-09_rev35"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: TL;DR Mode

This skill reviews a text against the AI trope catalog alone and condenses the report. The rules of the layers produce no findings in this mode and serve only for their exceptions to the catalog. For each file with recurring patterns that affect readability, the TL;DR gives their number and the file's length, and up to five bullets, each with a fixed plain label, a count, and a quote from the file. It has no free prose, since a written assessment would only restate the bullets and would risk the patterns that the review looks for. Minor patterns, such as formatting and single words, are nit-picks rather than feedback, so the TL;DR leaves them out, and a file without recurring patterns needs no feedback. The TL;DR does not rate the text, and it does not say or suggest who or what wrote it, because the catalog's patterns occur in human writing too, and a reader can fix a pattern without a claim about its origin. The full report is written as usual, so `/ai-slop:revise` can still apply it.

**Audience and tone.** The reader may be the author, a co-author, a thesis supervisor, or a reviewer of a submission, and a single file's block is often passed on to someone who has not seen the full report. Each block therefore stands on its own.

## When to use

Invoke this skill when the user:

1. Asks for a tl;dr, a short assessment, or a condensed AI slop review of a draft, a thesis, a paper, or a repository.
2. Asks how the AI writing patterns in a text affect its readability.
3. Runs `/ai-slop:tldr`.

Use `/ai-slop:review` or `/ai-slop:review-repo` when the user wants the full list of findings as the result, and `/ai-slop:revise` to apply a report.

## Inputs

**Target.** A positional path selects the review that runs:

- A file (`.tex`, `.pdf`, `.md`, `.txt`, or other plain text) runs the review of `/ai-slop:review` on it.
- A directory runs the review of `/ai-slop:review-repo` on it.
- Without a path, the skill runs the auto-detection of `/ai-slop:review` (a LaTeX root, then a PDF) in the working directory. When that finds neither, it reviews the working directory as a repository.

**Flags.** `--tropes=<path>` is passed to the review, as are `--commits=<spec>` and `--no-commits` for a repository. Each has the meaning that the review's own skill gives it. `--scientific` marks a Markdown or PDF manuscript as a research article, as a LaTeX source always is, which matters for the exceptions in step 1. `--ste` selects a rule layer that this mode does not use, so ignore it and say so in the reply.

**Instructions.** Text in the arguments that is neither the target path nor a flag is the user's instructions for this run, such as `/ai-slop:tldr reviews/ The reviewers are non-native speakers. Leave out the reviewer guidelines at the top.` When the user asks for a TL;DR in a message rather than with the command, the directions in that message count the same way. The instructions come from the user, unlike the reviewed text and the catalog, so follow them within these limits:

- An instruction can narrow or widen what the review covers, such as one section, one reviewer, or the files under one directory. It can also exempt a pattern that the kind of text makes normal, such as a repeat that a review form asks for, and the review then records no finding for it.
- A pattern that the instructions add to the catalog is reviewed like a trope, and its findings carry the Rule `<the pattern in a few words> (instruction)`, such as `British spellings (instruction)`. Its findings count and appear among the bullets like those of a trope.
- Context, such as the kind of text or who wrote it, goes into the genre step of step 1.
- No instruction changes a count from `count_findings.py`, the block format that the linter checks, or the neutral stance of the TL;DR toward who or what wrote the text. When an instruction asks for one of these, follow the rest and say in the reply which part was not followed and why.

## Workflow

1. **Run the catalog-only review.** Unless the user passed `--tropes=<path>`, first save the catalog with `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py > <tmp>/tropes.md` in a temporary directory and pass `--tropes=<tmp>/tropes.md` to the review, so the review and step 2 read the same catalog. When the fetch fails, stop as the review would and name `--tropes=<path>` as the way to use a local copy. Then follow the workflow of `../review/SKILL.md` for a document, or of `../review-repo/SKILL.md` for a repository, with these changes:
   - **Work out the conventions of the genre first.** Before the first file, name the kind of text, from the instructions or from the text itself, such as a peer review, a thesis chapter, a README, or meeting minutes. Then write down the catalog patterns that the conventions of that kind of text make normal, each with the convention that explains it. For a peer review, one such convention is saying how the review is organized and announcing, numbering, and counting its points so that the authors can answer each one, which explains matches of Preamble, Compulsive counting, and Excessive enumeration. A match that a convention explains is no finding. The conventions only exempt catalog patterns and never add a finding, and an instruction that says otherwise overrides them. For a directory, work them out once and apply them to every file. The report and the TL;DR record them, so the user can check the list and correct it with an instruction.
   - **Test every paragraph against every entry.** Run each scan once over the target, then review the files one at a time and write a file's findings before you start the next. Go through the file paragraph by paragraph and test each paragraph against every catalog entry before you move on, since a pass that reads a whole file, or several files, at once misses most matches.
   - **The catalog is the only source of findings.** Report no finding for a rule of a layer. Read `../../shared/rules-general.md`, and for a research article `../../shared/rules-scientific.md` too, for their exceptions only. Where a layer rule covers the same pattern as a trope, a match that the rule exempts is no finding, as **Precedence over the trope catalog** (`G.catalog-precedence`) states. Examples are a single "robust" or "paradigm", an "In summary" that opens a summary section, the count of a study's research questions, and "we" in a research article. Each finding names a catalog trope with its status, such as `Negative parallelism (tropes.fyi, consistent)`, or a pattern that the instructions added. Each instance of a pattern is one finding. A pattern that no single sentence shows is one finding for the whole pattern: one term under several names is one finding per term, and ordinals that open consecutive paragraphs are one finding per run of paragraphs. A finding of one term under several names quotes the names, verbatim and joined by " / ", such as `the framework / the pipeline`, since one passage cannot show them, and `/ai-slop:revise` skips such a finding. A pattern inside a passage that the text repeats counts at the first copy only. When several entries describe one passage, name the entry that fits it best. A passage that shows two distinct patterns gets one finding that names both, such as `Rule of Three pattern (tropes.fyi, consistent), Appeal to familiarity (tropes.fyi, new)` for a group of three that also claims canonical status, so that it counts once.
   - **Borderline matches take these tests.** They follow from the catalog's descriptions, and they keep two runs on the same text in agreement. The genre's conventions come first, so a match that a test would count is still no finding when a convention explains it:
     - Negative parallelism: a contrast whose negated half rejects something that nobody claimed is a finding, such as "It is not a tool. It is a platform." A contrast that corrects a claim of the text under discussion or separates two readings that a reader could confuse is content, such as "an ablation, not a baseline".
     - Preamble: a sentence that only announces the topic, count, or rank of what follows is a finding, such as "Two constraints matter for the design." before the sentence that names the first. A sentence that states the point is not, such as "The main constraint is that the index must fit in memory."
     - Comma-clipped trailing phrase: a short tail after a comma that finishes the thought sideways is a finding, such as "asked forty times, mentoring." A participial clause that states a concrete consequence is not, such as ", leaving the threshold untested", and neither is a list without a final "and". An "-ing" tail that attaches significance, such as ", highlighting its importance", is Superficial analyses alone.
     - Magic adverbs: an adverb that lends importance without content is a finding, such as "quietly" or "remarkably". A single hedge that qualifies a claim, such as "arguably", is not, and neither is a single word that the general layer lists as standard vocabulary, for example "fundamentally".
     - Compulsive counting: a count of the writer's own points, such as reasons, issues, or takeaways, announced before they are listed is a finding, such as "Four reasons why this will work." A count that states a fact about the subject is content, such as "dblp publishes two dumps." or the number of a study's research questions.
     - Excessive enumeration: ordinals that open consecutive paragraphs are one finding per run, such as "The first wall is ..." and "The second wall is ..." at the start of two paragraphs. Ordinals inside one paragraph are not.
     - Synonym cycling: one referent under several names that a reader could take for different things is a finding, such as "the tool", "the framework", and "the pipeline" for one artifact. A generic noun that refers back to a name in the sentence before, such as "the approach" for a named method, is not.
     - Rule of Three: a reflexive group of three adjectives or clauses is a finding, such as "fast, flexible, and future-proof". A group of three that the content sets is not, such as the three stages of a method.
     - Belaboring the unnecessary: a sentence that defends a point against an objection that nobody raised is a finding. A caveat that limits the writer's own claim is content.
     - Appeal to familiarity: "well known", "a classic", or "famously" without a source is a finding, such as "It is well known that fuzzers miss deep bugs." With a citation or a named source, it is not.
     - Bold-first bullets: bold at the start of every item of a list is a finding when the bold is a sentence or covers the whole item. A bold label that names the item, as a phrase without a verb such as "Novelty" or "Limited novelty.", is the exception of **No excessive bold or formatting** (`G.no-excess-bold`). A single bold item among plain ones is no finding.
     - Title case headings and "Where / What / Why" headers: both cover headings and the labels that stand in for them, such as a label alone on its line or a bold label that opens a paragraph.
   - **The glyph scan runs.** Its em-dash and Unicode rows are candidates for the catalog's tropes on dashes and decorative characters, with one finding per line for each such trope, however many characters the line has. The finding's Quote runs from the first to the last such character on the line, so that `/ai-slop:revise` replaces all of them. The same unit holds for the other tropes of formatting, so each item of a list with a bold lead-in and each title-case heading is one finding. `count_findings.py` counts these tropes once per line whatever the report records. Arrows, check marks, and bullet symbols that stand in for words or list marks are findings, including those that the scan misses. Curly quotes, the ellipsis character, and non-breaking spaces and hyphens look like the characters that they replace, so this mode records no finding for them. Neither are letters ("é"), mathematical signs in a formula ("×"), and invisible characters (a zero-width space). Em-dashes are a finding only when a file has more than three per ~350 words, counting all words of the file as `wc -w` does, since the catalog's trope is their overuse. A spaced en dash between two clauses counts as a dash, and a dash that the general layer exempts or that decorates a label, such as "—Novelty—", never counts. An en dash in a range or between two names or terms, such as "Liang–Zeger", is correct and no finding.
   - **The repeat scan runs.** Its rows are candidates for the catalog's tropes on repeated content, such as Content duplication. A verbatim or near-verbatim copy of an earlier sentence is a finding at the later sentence. A brief reminder that the argument needs is not.
   - **Quotations and restated sources are not reviewed.** No finding comes from text inside quotation marks or another marked quotation, including the marks, or from text that is evident from its voice as copied, such as a summary in the first person of the reviewed work's authors. The same holds for what the writer restates from the work that the text discusses: its names and terms, its counts, its figure and table labels, and the claims that the text attributes to it, such as "The paper claims three contributions." The writer's own words around such material are reviewed, including the word choice of a paraphrase, since the reader meets them either way.
   - **Form text is not reviewed.** No scan row and no finding comes from the labels and fixed descriptions of a form or from a heading that copies such a label. Text that a form field asks the writer for, such as a note on how a review changed, is the writer's text but not unprompted.
   - **The other scans do not run.** Skip the reference-candidate scan, the sentence scan, and, for LaTeX, the citation, BibTeX, and reference checks, which serve the layers.
   - **Check consistency across files.** For a directory, after the last file, go through the findings of each trope across all files and align the decisions, so that two passages that read the same get the same decision in every file. When several agents review the files in parts, the run that merges the parts makes this pass.
   - **The report is shorter.** Add these lines directly under `**Reviewed:**`, in order:
     - `**Rules:** tropes.fyi catalog only (TL;DR mode)`.
     - `**Genre:** <kind of text>. <Each convention that exempts catalog patterns, with the patterns in parentheses.>`
     - `**Instructions as applied:** <each instruction as the review applied it, such as the sections that an exemption covers>`, when there were instructions.
     - `**Scope:** <what the review covered, with its line ranges>`, when the instructions narrowed the review to part of the target. An instruction that only exempts a pattern does not narrow it.
     - A repository review's `**Repo scope:**` line.

     For a directory, `**Paper:**` holds the directory's path. Of the cross-cutting metrics, keep only the dash count, as a count per file. Leave out the other metric sections and the grounding to-do, and keep the section on items requiring author judgment, with "None." when it is empty.
   - **The instructions set the scope.** Leave out the files, sections, and writers that they exclude, review only the ones that they name, and look for the patterns that they add. When the scope is part of a file, note the line ranges that the review covered, which step 2 needs. A repeat whose later copy lies outside those lines is no finding, and the dash count covers those lines only.

   Carry the review through to the linted `ai-slop-report.md` and its `.gitignore` line, but do not echo the report in the reply, because this mode replies with the TL;DR. The report has the schema of every review, so `/ai-slop:revise` can apply it. When the review stops without a report (no document found, or a `--commits` range that git cannot resolve), stop too and pass on its message.

2. **Count the findings.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/count_findings.py ai-slop-report.md --tropes=<catalog>`, adding `--root=<repository root>` after a repository review, since the report's paths are relative to that root. When the instructions narrowed a file to some of its lines, such as two sections of a paper, also add `--scope=<path>:<first>-<last>` for that file, with the line ranges that the review covered separated by commas, for example `--scope=paper.tex:40-112,480-561`, so that the word count covers the reviewed part only. The script sorts each finding by what it costs the reader:
   - **Obscures the meaning.** The reader cannot tell what is meant, as with one concept under several names, a claim attributed to unnamed experts, or an invented concept label.
   - **Delays the content.** The reader has to get through text that adds nothing, as with the catalog's tropes of composition, tone, and sentence and paragraph structure, such as inflated stakes, negative parallelism, and duplicated content.
   - **Distracts.** The meaning comes through, but the wording draws attention to itself, as with the catalog's tropes of word choice and formatting, such as ornate nouns, em-dashes, and bold lead-ins, and with the patterns that the instructions added.

   Each stdout line is tab-separated. A `file` line gives the path, the number of findings, the approximate prose word count, the findings per class, the number of findings that affect readability, and whether the file needs feedback (`yes` or `n/a`). A finding affects readability unless its rule is minor. The minor rules are the tropes that only distract, which cover formatting and the choice of single words, and the tropes that restate a point just made, reuse a word or a filler phrase, or add a short phrase after a comma. The report keeps them, but they are nit-picks rather than feedback. A pattern that the instructions added is never minor. A file needs feedback when at least two findings affect readability, since one isolated pattern does not warrant feedback. The `rule` lines that follow give each rule's count, the number of its findings that affect readability, and its class, ranked by cost, which is that number times 4 for obscures, 3 for delays, and 1 for distracts, so the minor rules rank last. The `bullet` lines give up to five bullets, one per rule in that order, each with the number of the rule's findings that affect readability, a fixed plain label, and the quote of a finding that no earlier bullet quotes, ending at its last complete sentence and cut after 25 words. A repository's commit messages are counted together under the path `commit messages`. Take every count in the TL;DR from this output, and use the path of the `file` line as the block's heading. When the script warns that findings have no Rule field, add the missing `**Rule:**` lines to those blocks in the report and run it again.

3. **List the scanned files.** Every file that the review read is covered: the document and each file that it includes through `\input` or `\include`, or each file in the `scan_repo.py` output of a repository review. A file without a `file` line in step 2 had no findings.

4. **Write each file's block.** A file that needs feedback gets a block:
   - **Count.** A `**Number of patterns that affect readability:**` line with the number of findings that affect readability and the word count from the `file` line, such as `3 in 850 words`. Leave out the words when the script gives `-`, as for a PDF.
   - **Patterns.** The line `**Patterns that affect readability:**`, the same in every block, followed by the `bullet` lines of step 2 in their order, each written as `- <label> (<count> times): "<quote>"`, or `(once)` for a count of 1. The script picks the label, the count, and the quote, so that one pattern has one name in every block and two bullets never show the same passage. Copy them as they are.

   The files that need no feedback share one closing block that lists them, which is left out when every file needs feedback. A repository's commit messages get one block, like a file, when they need feedback.

   **Apply the instructions.** When an instruction narrowed a file's scope, the count line names the part, such as `3 in 850 words of sections 2 and 3`, since a reader of that block alone does not see the instructions. When a pattern that the instructions added has no findings, the report's Summary says so.

5. **Keep each block self-contained.** A reader who sees only one block, and not the report, must understand it. A block therefore holds only the count line and the bullets, with no terms of the catalog or the rules, such as a trope's name or status, no finding numbers, and no reference to the report or to another block.

6. **Write the TL;DR.** Save it as `ai-slop-tldr.md` in the working directory, using the template below. The TL;DR is a generated artifact and must never be committed. If the working directory is inside a git repository, resolve its root with `git rev-parse --show-toplevel` and, when the root's `.gitignore` does not already list `ai-slop-tldr.md`, append that line (creating the file if absent). Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-tldr.md` and revise the file for its findings, at most three times, as `/ai-slop:review` step 7 does. The linter checks each block's count line and bullet count, and that the block holds no other text, rating, or `**AI use:**` line. The lint loop is internal quality control, so the reply does not mention it.

7. **Reply with the TL;DR.** Read `ai-slop-tldr.md` back and quote its contents verbatim. Then add one line that names `ai-slop-report.md` as the full report, which `/ai-slop:revise` applies. When an instruction was not followed, as step 4 and the Inputs describe, add a line that names it and the reason. Do not modify the reviewed text.

## TL;DR template

````markdown
# AI Slop TL;DR

**Target:** <path of the document or repository>
**Reviewed:** <ISO 8601 date>
**Full report:** `ai-slop-report.md`
**Instructions:** <the user's instructions verbatim; leave out this line when there were none>
**Genre:** <kind of text>. <The conventions that the review did not count as patterns, in a sentence or two.>
**Counting:** Each instance of a pattern counts once. Formatting, single words, a reused word, a filler phrase, a short phrase after a comma, and a restatement of a point just made are minor and not counted, and a file with fewer than two other patterns needs no feedback.

## <path of a file that needs feedback>

**Number of patterns that affect readability:** <N> in <W> words

**Patterns that affect readability:**

- <label> (<once | N times>): "<quote>"
- <up to five bullets, from the bullet lines of count_findings.py>

<Repeat per file that needs feedback, in the order of the scanned files.>

## Commit messages

<Repository reviews only, when the commit messages need feedback. Same format as a file's block.>

## Files that need no feedback

<Paths, comma-separated>. The review found no recurring pattern that affects readability in these files (or "in this file" for one path).
````

A block for calibration, from a paper:

```markdown
## sections/introduction.tex

**Number of patterns that affect readability:** 20 in 1,400 words

**Patterns that affect readability:**

- Inflated claims of importance (9 times): "In today's rapidly evolving software landscape, testing matters more than ever"
- Three words or phrases where one would do (6 times): "robust, scalable, and efficient"
- Contrast with a claim that nobody made (5 times): "It is not a tool. It is a platform."
```

## Bundled files

- The scripts of `/ai-slop:review` and `/ai-slop:review-repo` that step 1 runs, and **Precedence over the trope catalog** in `../../shared/rules-general.md`, which limits the catalog.
- `../../scripts/count_findings.py` counts a report's findings and patterns per file and per rule, sorts them by their cost to the reader, ranks the rules, and writes the bullets. `../../scripts/lint_markdown.py` lints the TL;DR, including the structure of each block. Their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Counts, ranks, and bullets come from `count_findings.py`.** Do not count, classify, rank, or label findings by eye.
- **Stay neutral about authorship.** The TL;DR reports patterns and their effect on the reader. It does not say or suggest that anyone used AI tools, even when the patterns are dense.
- **Report only what the review found.** The TL;DR rests on the findings, not on the content's merit, its argument, or its novelty, and it does not rate the text.
- **Do not modify the reviewed text.** TL;DR mode writes only `ai-slop-report.md` and `ai-slop-tldr.md` in the working directory, plus their names in the repository's `.gitignore` when those lines are missing.
