---
name: tldr
description: Run a regular AI slop review and condense it into a TL;DR with one short assessment per scanned file of whether the authors used AI tools in a reasonable way or in a way that makes the text harder to read, plus up to three bullets naming the worst patterns that the review found. Use when the user asks for a tl;dr or a quick verdict on a draft, a thesis, a paper, or a repository, or asks whether the AI use in a text is reasonable, or runs `/ai-slop:tldr`. Reviews a document like `/ai-slop:review` and a directory like `/ai-slop:review-repo`, with the same flags. Writes `ai-slop-report.md` and `ai-slop-tldr.md`.
license: CC-BY-4.0
metadata:
  version: "2026-09_rev30"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: TL;DR Mode

This skill runs a regular review and condenses its report. For each file that the review scanned, it writes an assessment of one to five sentences of whether the authors used AI tools in a reasonable way or in a way that makes the text harder to read, up to three bullets with the worst patterns that the review found, and a rating of the patterns' impact on readability on a five-level scale. The full report is written as usual, so `/ai-slop:revise` can still apply it.

**Audience and tone.** The reader may be the author, a co-author, a thesis supervisor, or a reviewer of a submission, and a single file's block is often passed on to someone who has not seen the full report. Each block therefore stands on its own. State the assessment plainly and base it on the findings.

## When to use

Invoke this skill when the user:

1. Asks for a tl;dr, a short verdict, or a condensed AI slop review of a draft, a thesis, a paper, or a repository.
2. Asks whether the authors of a text used AI tools in a reasonable way.
3. Runs `/ai-slop:tldr`.

Use `/ai-slop:review` or `/ai-slop:review-repo` when the user wants the full list of findings as the result, and `/ai-slop:revise` to apply a report.

## Inputs

**Target.** A positional path selects the review that runs:

- A file (`.tex`, `.pdf`, `.md`, `.txt`, or other plain text) runs the review of `/ai-slop:review` on it.
- A directory runs the review of `/ai-slop:review-repo` on it.
- Without a path, the skill runs the auto-detection of `/ai-slop:review` (a LaTeX root, then a PDF) in the working directory. When that finds neither, it reviews the working directory as a repository.

**Flags.** `--scientific`, `--ste`, and `--tropes=<path>` are passed to the review, as are `--commits=<spec>` and `--no-commits` for a repository. Each has the meaning that the review's own skill gives it.

## Workflow

1. **Run the review.** Unless the user passed `--tropes=<path>`, first save the catalog with `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py > <tmp>/tropes.md` in a temporary directory and pass `--tropes=<tmp>/tropes.md` to the review, so the review and step 2 read the same catalog. When the fetch fails, stop as the review would and name `--tropes=<path>` as the way to use a local copy. Then follow the workflow of `../review/SKILL.md` for a document, or of `../review-repo/SKILL.md` for a repository, with the flags above. Carry it through to the linted `ai-slop-report.md` and its `.gitignore` line, but do not echo the report in the reply, because this mode replies with the TL;DR. When the review stops without a report (no document found, or a `--commits` range that git cannot resolve), stop too and pass on its message.

   Then record the signs of unassisted writing, which current models rarely produce and which no rule of the layers covers. Read each file with findings and append a `## Signs of unassisted writing` section to `ai-slop-report.md`, with one bullet per sign: its location in backticks, its kind, and a verbatim quote, as in ``- `review.txt:27` grammar slip: `Evaluation use only` ``. The kinds are typos, grammar slips such as a verb that does not agree with its subject or a wrong word order, missing or wrong articles, and missing words. Record only errors that a spelling or grammar checker would flag, not choices of style, and nothing inside text that the file quotes from another source. Lint the report again afterwards. The section is data for step 2 and is not part of the findings that `/ai-slop:revise` applies.

2. **Count and rate the findings.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/count_findings.py ai-slop-report.md --tropes=<catalog>`, adding `--root=<repository root>` after a repository review, since the report's paths are relative to that root. The script sorts each finding by what it costs the reader:
   - **Obscures the meaning.** The reader cannot tell what is meant, as with an unclear referent, one concept under several names, an empty head noun, a vague claim, or a reference that no database knows.
   - **Delays the content.** The reader has to get through text that adds nothing, as with padding, restatement, signposting, stacked hedges, figurative wording, and the catalog's rhetorical tropes.
   - **Distracts.** The meaning comes through, but the wording draws attention to itself, as with word choice, punctuation, glyphs, spelling, and markup.

   Each stdout line is tab-separated. A `file` line gives the path, the number of findings, the approximate prose word count, the findings per class, the file's impact level, the share of the prose that needs a rewrite, the number of AI-typical findings, the number of those in paragraphs that need a rewrite, the number of signs of unassisted writing, and the AI-use verdict. The `rule` lines that follow give each rule's count and class, ranked by cost, which is the count weighted 4 for obscures, 3 for delays, and 1 for distracts, so one finding that obscures or delays outweighs three or four that distract. The `para` lines give the line ranges of the paragraphs that need a rewrite, which are the paragraphs with at least two findings that obscure or delay and at least one per 100 words. A repository's commit messages are counted together under the path `commit messages`. Take every count, class, level, share, and verdict in the TL;DR from this output, and use the path of the `file` line as the block's heading. When the script warns that findings have no Rule field, add the missing `**Rule:**` lines to those blocks in the report and run it again.

3. **List the scanned files.** Every file that the review read is covered: the document and each file that it includes through `\input` or `\include`, or each file in the `scan_repo.py` output of a repository review. A file without a `file` line in step 2 had no findings.

4. **Take the impact level.** The level on the `file` line rates the patterns' impact on readability by how much of the prose needs a rewrite:

   | Impact | Share of the prose that needs a rewrite | The text needs |
   |---|---|---|
   | None | No finding obscures or delays. | Nothing, or a proofreading pass. |
   | Minor | Under a tenth. | Edits of single words and sentences. |
   | Moderate | A tenth to under a third. | A rewrite of some passages. |
   | Major | A third to under two thirds. | A rewrite of large parts. |
   | Severe | Two thirds or more. | A rewrite of most of the text. |

   Major and Severe also need at least three paragraphs that need a rewrite, since in a short text one or two paragraphs make up most of the prose. With fewer, the script gives Moderate. Use the level as given. Where the script gives `-` because it cannot read the file, as for a PDF, estimate the share from the findings and the extracted text with the same table.

   **Take the AI-use verdict.** The verdict on the `file` line answers the question of this mode with one of three fixed values. It rests on the AI-typical findings, which are the catalog's tropes and the rules for the patterns that AI output overproduces, such as restricted words, padding, restatement, formulaic openings and closings, announced counts, em-dashes, excess bold, and performative hedges. Grammar slips, dropped words, spelling, and unclear pronouns do not count, since hurried human writing produces them too. Curly quotes and other glyphs that the editor or the web form inserts never count. In a paragraph with a sign of unassisted writing, the patterns that non-native and hurried writers produce as readily as models stop counting as well: figurative phrasing, padding phrases, long sentences, enumerations in running text, colorful words, coined compounds, ASCII dashes, and hedges. A sign counts for its own paragraph only, since in a file with several writers the other paragraphs may be someone else's. A file with several writers is rated as a whole, so a clean text next to a heavily assisted one lowers the file's level, and the first sentence names the writer who drives the verdict.

   | AI use | The file's findings |
   |---|---|
   | Little sign of AI tools | Fewer than two AI-typical findings, or fewer than one per page-equivalent of ~350 words. |
   | Harder to read | Otherwise, when the level is Moderate or above and at least one AI-typical finding is in a paragraph that needs a rewrite. |
   | Reasonable | Otherwise. |

   Use the verdict as given. Where the script gives `-`, as for a PDF, apply the same table with the estimated share.

5. **Write each file's block.** A file with at least one finding gets a block:
   - **Impact.** An `**Impact on readability:**` line with the level from step 4, followed by the share in parentheses, as in `Moderate (12% of the prose needs a rewrite)`. The share shows the reader how close the file is to the next level.
   - **AI use.** An `**AI use:**` line with the verdict from step 4.
   - **Assessment.** One to five sentences. The first states the verdict in fixed words, with the writers named by their role, such as the authors of a paper or the reviewers of a submission: "The <writers> used AI tools in a reasonable way.", "The <writers> used AI tools in a way that makes the <text> harder to read.", or "The <text> shows little sign of AI tools." Do not soften or blend the verdict, as in "adds some friction" or "without derailing". When a file holds texts by several writers, such as several reviews of one paper, the first sentence names the writer who drives the verdict, which the `para` lines locate, and may add how the other parts read, as in "The second reviewer used AI tools in a way that makes the review harder to read, while the other two reviews show little sign of AI tools." With "Little sign of AI tools" and a level of Moderate or above, the next sentence names what slows the reader instead, such as the grammar slips and vague nouns of hurried writing. The other sentences say which patterns recur, where they cluster, what they cost the reader, and what reads well. Describe where the patterns cluster in words, without counts of your own.
   - **Worst patterns.** The line `**Patterns that most affect readability:**`, the same in every block, followed by the first three `rule` lines of step 2 as bullets, fewer when the file has fewer rules. When two lines name the same pattern for the reader, such as one concept under several names in a layer rule and in a catalog trope, keep the higher one and take the next line instead. Each bullet names the pattern in plain words, gives the line's count as "(once)" or "(<N> times)", and quotes one example verbatim from the file, at most about twelve words, cut at a word boundary and without its markup, such as the `**` of bold text. Choose the clearest instance. A pattern that one quote cannot show, such as one concept under two names, takes two short quotes.

   The files without findings share one closing block that lists them. A repository's commit messages get one block, like a file.

6. **Keep each block self-contained.** A reader who sees only one block, and not the report, must understand it. A block therefore names no rule keys (such as `G.semicolons`), no finding numbers, no report sections, and no catalog statuses, and it does not refer to another block. The TL;DR is prose too, so it follows the general layer, and the STE layer as well with `--ste`.

7. **Write the TL;DR.** Save it as `ai-slop-tldr.md` in the working directory, using the template below. The TL;DR is a generated artifact and must never be committed. If the working directory is inside a git repository, resolve its root with `git rev-parse --show-toplevel` and, when the root's `.gitignore` does not already list `ai-slop-tldr.md`, append that line (creating the file if absent). Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-tldr.md` and revise the file for its findings, at most three times, as in `/ai-slop:review` step 7. The linter checks each block's impact level, AI-use verdict, sentence count, and bullet count. The lint loop is internal quality control, so the reply does not mention it.

8. **Reply with the TL;DR.** Read `ai-slop-tldr.md` back and quote its contents verbatim. Then add one line that names `ai-slop-report.md` as the full report, which `/ai-slop:revise` applies. When the text of a file contradicts its verdict, for example a review rated Harder to read that reads as the plain work of a non-native writer, keep the verdict in the TL;DR and add a line `Verdicts to check:` that names each file where the text contradicts the verdict, with the reason in a few words. Those files show where the verdict rule fails. Do not modify the reviewed text.

## TL;DR template

````markdown
# AI Slop TL;DR

**Target:** <path of the document or repository>
**Reviewed:** <ISO 8601 date>
**Full report:** `ai-slop-report.md`

## <path of a file with findings>

**Impact on readability:** <None | Minor | Moderate | Major | Severe> (<N>% of the prose needs a rewrite)

**AI use:** <Reasonable | Harder to read | Little sign of AI tools>

<One to five sentences. The first states the verdict in its fixed words.>

**Patterns that most affect readability:**

- <pattern in plain words> (<once | N times>), as in "<verbatim quote of at most about twelve words>"
- <up to three bullets>

<Repeat per file with findings, in the order of the scanned files.>

## Commit messages

<Repository reviews only, when the commit messages have findings. Same shape as a file's block.>

## Files without findings

<Paths, comma-separated.> The review found none of its patterns in these files.
````

Blocks for calibration, first two from a paper:

```markdown
## sections/method.tex

**Impact on readability:** None (0% of the prose needs a rewrite)

**AI use:** Little sign of AI tools

The section shows little sign of AI tools. It names the tool, the sample, and each step of the analysis, and a proofreading pass would fix its few findings, which are British spellings and one em-dash.

**Patterns that most affect readability:**

- British spellings (3 times), as in "we analysed the logs"
- An em-dash in place of a comma (once), as in "the sample — 212 repositories — came from"

## sections/introduction.tex

**Impact on readability:** Major (45% of the prose needs a rewrite)

**AI use:** Harder to read

The authors used AI tools in a way that makes the introduction harder to read. Most paragraphs open with a claim about the importance of the field and close with a restatement, so the research question appears only in the last paragraph. The list of contributions repeats the pattern in groups of three adjectives.

**Patterns that most affect readability:**

- Windup sentences before the point (9 times), as in "In today's rapidly evolving software landscape, testing matters"
- Sentences that open with a bare "This" (5 times), as in "This highlights the need for better tools."
- Groups of three adjectives (6 times), as in "robust, scalable, and efficient"
```

A block for a file with the reviews of one submission by three reviewers:

```markdown
## reviews/paper-42.txt

**Impact on readability:** Moderate (18% of the prose needs a rewrite)

**AI use:** Harder to read

The second reviewer used AI tools in a way that makes the review harder to read, while the other two reviews show little sign of AI tools. The second review repeats its strengths and weaknesses almost word for word in its detailed comments and calls the proposed tool by three names. The first and third reviews are terse and name concrete problems, and their findings are dropped words and missing commas that a proofreading pass would fix.

**Patterns that most affect readability:**

- Strengths and weaknesses repeated in the detailed comments (4 times), as in "The approach is novel and well motivated"
- One tool under several names (3 times), as in "the framework" and "the pipeline"
- A dropped "that" after a reporting verb (11 times), as in "The authors claim the results generalize"
```

## Bundled files

- The rule layers and scripts of `/ai-slop:review` and `/ai-slop:review-repo`, which step 1 runs.
- `../../scripts/count_findings.py` counts a report's findings per file and per rule, sorts them by their cost to the reader, ranks the rules, finds the paragraphs that need a rewrite, and gives each file's impact level and AI-use verdict. `../../scripts/lint_markdown.py` lints the TL;DR, including the shape of each block. Their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Counts, classes, ranks, levels, and verdicts come from `count_findings.py`.** Do not count, classify, rank, or rate findings by eye.
- **Quote verbatim.** Each bullet's example is the file's own text.
- **Rate only what the review found.** The assessment and the rating rest on the findings, not on the content's merit, its argument, or its novelty.
- **Do not modify the reviewed text.** TL;DR mode writes only `ai-slop-report.md` and `ai-slop-tldr.md` in the working directory, plus their names in the repository's `.gitignore` when those lines are missing.
