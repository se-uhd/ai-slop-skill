---
name: ground
description: Fill the grounding comments that review only flags as missing. For each `\cite{}` in a LaTeX paper that has no quote-backed grounding comment, whether no comment at all or a `TODO verify` stub left by revise mode or an earlier run, fetch the cited source, extract a verbatim quote that supports the claim, and write a `% GROUNDING` comment carrying that quote into the source, or a `TODO verify -- <reason>` stub when the source cannot be retrieved. Use when the user asks to ground citations, fill grounding comments, or close the review's grounding to-do. LaTeX source only.
license: CC-BY-4.0
metadata:
  version: "2026-09_rev18"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Ground Mode

This skill fills the grounding comments review mode flags as missing. `/ai-slop:review` lists every `\cite{}` missing a `% GROUNDING:` comment as a grounding to-do but never fills it. Ground mode fetches each cited source, extracts a verbatim quote supporting the claim the paper attributes to it, and writes the grounding comment into the LaTeX. Where the source cannot be retrieved, it writes a `TODO verify -- <reason>` stub instead, never a quote from memory. Quote-less `TODO verify` stubs, planted by `/ai-slop:revise` or by an earlier ground run, count as unfilled. Ground picks those sites up and replaces the stub with the retrieved quote.

**Audience and tone.** The default user is an author who has citations to ground before submission. The result is an audit trail in the source: a quote that co-authors and reviewers can check against each citation. Frame the summary as work completed and work still needing the author's attention, not as a verdict.

**The anti-fabrication invariant, the single most important rule.** A quote is written into the paper *only* when the source text was actually retrieved (fetched from the web or read from a local file). If it was not retrieved, the comment is `TODO verify -- <reason>`, never an approximation, paraphrase, or remembered quote. This rule matches the skill's principle of verifying rather than asserting. The grounding comment certifies that the cited source says what the paper claims, so a fabricated quote is worse than an honest TODO. Hold every grounding agent to this rule, and do not rely on the agents alone. Step 6 re-reads each named source and checks that the quote occurs in it before anything is written.

## When to use

Invoke this skill when the user:

1. Asks to ground citations, fill `% GROUNDING:` comments, or "close the grounding to-do" from an `/ai-slop:review`.
2. Runs `/ai-slop:ground`.

Do **not** invoke for a fresh review (use `/ai-slop:review`), to apply a review report's prose suggestions (use `/ai-slop:revise`), or on a non-LaTeX document. Grounding writes an inline LaTeX comment, so it is LaTeX-only. Markdown and PDF have no equivalent inline-comment mechanism for the audit trail.

## Inputs

The skill operates on the LaTeX paper in the current working directory. No arguments are required.

- **Paper.** Auto-detect by running `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_latex_root.py`. Exit 0 means the printed path is the root. Exit 2 means multiple candidate roots, so list them and ask which to ground. Exit 1 means no `.tex` root, so stop. A `.tex` path can be passed as the first argument to override the scan.
- **Scope gate.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/detect_scope.py <resolved-path>`. Proceed only on `latex`. On `general`, stop and tell the user that grounding is LaTeX-only.
- **Local sources (optional).** Paywalled articles, books, and other sources that the web does not expose can be grounded from files that the user supplies. If the user names PDFs or a directory of them, pass those paths to the grounding agents so they can read the source text directly. Mention this option when sources come back `paywalled` or `book`.
- **What leaves the machine.** Each agent searches the web with the claim sentence and the source metadata, so sentences of an unpublished manuscript reach search engines and publisher sites. Say so when the user asks about confidentiality, and use local sources for a draft that must not leave the machine.

## Workflow

1. **Resolve and gate.** Auto-detect the LaTeX root (or use the supplied path) and confirm `detect_scope.py` reports `latex`. Stop on a non-LaTeX target.

2. **Extract the citations.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/extract_cites.py <path>` and capture stdout to `grounding-cites.json` in the working directory. The JSON holds:
   - `sites`: every citation call, with `file`, `line`, `command`, `keys`, the enclosing-sentence `claim`, and `groundable` / `grounded` flags.
   - `by_key`: per unique key, the de-duplicated `claims` and the `sites` that cite it.
   - `meta`: per key, the `.bib` metadata (`type`, `title`, `author`, `year`, `doi`, `url`, `eprint`, `howpublished`) needed to identify and locate the source.

   The script prints to stderr a one-line summary (sites, unique keys, groundable sites still missing a comment, metadata coverage). Add `grounding-cites.json` and `grounding-quotes.json` to the repository root's `.gitignore` (resolve the root with `git rev-parse --show-toplevel`, and create the file if absent). Both files are generated artifacts and must not be committed.

3. **Pick the keys to ground.** From `by_key`, take the keys with at least one site where `groundable` is true and `grounded` is false. `grounded` is true only for a quote-backed comment, so sites carrying a quote-less `TODO verify` stub are selected and filled. Keys already grounded everywhere need no work. Keys that appear only in style-only helpers (`\citeauthor` / `\citeyear`, `groundable: false`) are context, not insertion targets. If a key has no entry in `meta`, note it. The `.bib` lacks that key, so the agent has only the claim text to work from, and the result is likely a `not-found` TODO.

4. **Ground each unique source, one agent per key, chunked.** Author an inline grounding **Workflow** (see the reusable pattern below). Each agent receives one key's bundle, its `meta` and its list of `claims`, and is told to:
   - Identify the source from the metadata (DOI first, then title + author + year, using the `url` / `eprint` if present, or a user-supplied local file).
   - Retrieve the source text (fetch the page or PDF, or read the local file for a paywalled or book source).
   - Find a short verbatim quote from the source that supports the claim(s). Return it **only if the source was actually retrieved and the quote is copied from it**, together with the URL or local path it read as `source`, so step 6 can check the quote against it.
   - Otherwise return a TODO with a reason: `paywalled`, `abstract-only` (only the abstract was reachable and it does not contain the support), `book` (no digital full text), `not-found` (the source could not be located), or `source-does-not-support` (the source was read but does not back the claim).

   Run the agents in **slices of about 8 at a time** so a burst does not trip server-side rate limits. The run is resumable. Any source that errored or was skipped simply stays without a quote, so its site keeps the missing comment or the `TODO verify` stub and a later `/ai-slop:ground` picks it up and fills it.

5. **Assemble the quotes file.** Collect the agents' results into `grounding-quotes.json`, mapping each key to either `{"quote": "<verbatim text>", "source": "<url or path>"}` or `{"todo": "<reason>"}`. Write nothing for a key if its agent failed entirely. Leaving it absent keeps it for a future run.

6. **Check the quotes against their sources.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/check_quotes.py grounding-quotes.json --apply [--sources-dir <dir>]`. For each quote it re-reads the named source (a local text file, or an HTML or plain-text URL) and confirms the quote occurs in it after whitespace and punctuation normalization. A quote that does not occur is downgraded in place to `{"todo": "unverified"}`, and each verdict is printed as `<key>\t<verdict>\t<detail>`. A PDF, a binary, or an unreachable source comes back `unverifiable` or `unreachable`: open that source yourself (Read for a local PDF, WebFetch for a URL), confirm the quote, and downgrade it by hand the same way when you cannot. Nothing goes into the paper that neither the script nor you have seen in the source.

7. **Insert the comments.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/insert_grounding.py grounding-cites.json grounding-quotes.json`. It writes `% GROUNDING: <key> -- "<quote>"` (or the `TODO verify -- <reason>` form) after each groundable, ungrounded cite line, matching the line's indentation. An existing quote-less `TODO verify` stub for the key is replaced in place. A site with a quote-backed comment for the key is left alone (idempotent), and each line is re-checked against the file before editing, so any site that moved is skipped. Use `--dry-run` first if the user wants to preview the edits.

8. **Summarize.** Tell the user, in plain terms:
   - How many citations were grounded with a retrieved quote, and how many of those quotes step 6 confirmed mechanically.
   - How many got a TODO, broken down by reason (`unverified` marks a returned quote the check could not find in its source).
   - **The `source-does-not-support` cases, called out first.** These cases are not mere gaps. The source was read and does not back the claim, which flags a likely miscitation (a wrong key, or a cite stretched past what the source says). Report each one with its key and the claim so the author can fix the citation, not just the comment.
   - Any keys missing `.bib` metadata.

9. **Stop.** Leave the edits in the working tree. The user inspects them with `git diff` and commits when satisfied. Do not commit, and do not run a review.

## Reusable workflow pattern

The grounding fan-out is a **chunked-`parallel()`** workflow. The per-source claim bundles are passed in as `args.sources` (built from `by_key` / `meta`), each source is one schema-validated agent, and the agents run in fixed-size slices to stay under rate limits. Author it inline:

```javascript
export const meta = {
  name: 'ground-citations',
  description: 'Fetch each cited source and extract a verbatim supporting quote',
  phases: [{ title: 'Ground' }],
}

// One bundle per key to ground, embedded from grounding-cites.json.
const SOURCES = args.sources   // [{ key, meta: {...}, claims: [...] }]
const QUOTE = {
  type: 'object',
  properties: {
    key: { type: 'string' },
    status: { enum: ['quote', 'todo'] },
    quote: { type: 'string' },   // verbatim, present iff status == 'quote'
    source: { type: 'string' },  // the URL or local path read, present iff status == 'quote'
    reason: { enum: ['paywalled', 'abstract-only', 'book', 'not-found', 'source-does-not-support'] },
  },
  required: ['key', 'status'],
}

const results = []
for (let i = 0; i < SOURCES.length; i += 8) {        // slices of ~8 -> rate-limit safe
  const slice = SOURCES.slice(i, i + 8)
  const got = await parallel(slice.map(src => () =>
    agent(
      `Ground this citation. Source metadata: ${JSON.stringify(src.meta)}. ` +
      `Claims the paper attributes to it: ${JSON.stringify(src.claims)}.\n` +
      `Retrieve the source (DOI/title/URL, or a provided local file) and copy a short ` +
      `verbatim quote that supports the claim(s). Return status:"quote" with the quote and the ` +
      `URL or file you read as source ONLY if you actually retrieved the source text. If you ` +
      `could not, return status:"todo" with ` +
      `a reason: paywalled, abstract-only, book, not-found, or source-does-not-support. ` +
      `Never return a quote from memory or a paraphrase.`,
      { label: `ground:${src.key}`, phase: 'Ground', schema: QUOTE },
    ).then(r => ({ ...r, key: src.key }))   // pin the key, never trust the model to echo it
  ))
  results.push(...got.filter(Boolean))
}
return results
```

Map each result to `grounding-quotes.json`: `status: 'quote'` becomes `{quote, source}`, and `status: 'todo'` becomes `{todo: reason}`. If the Workflow tool is unavailable in the client, fan the same per-source prompts out with individual sub-agents, or process them sequentially. The schema and the anti-fabrication rule are unchanged.

## Bundled files

- `../../scripts/extract_cites.py`: resolves the LaTeX root, follows `\input` / `\include`, and emits the `sites` / `by_key` / `meta` JSON. Shares its cite scanner with `find_citation_issues.py` (`cite_scan.py`) and its `.bib` parser with `check_bib_fields.py` / `verify_references.py` (`bib_parse.py`).
- `../../scripts/check_quotes.py`: checks each returned quote against the source it names and downgrades the ones it cannot find.
- `../../scripts/insert_grounding.py`: writes the `% GROUNDING:` comments back idempotently from the quotes JSON.
- `../../scripts/find_latex_root.py`, `../../scripts/detect_scope.py`: locate the root and gate the skill to LaTeX.
- `../../shared/rules-latex.md`: defines the `% GROUNDING:` convention this skill fills. It is referenced as a fallback when the user asks why grounding matters.

## Constraints

- **Never fabricate a quote.** A quote is written only when the source was retrieved and the text was copied from it, and step 6 checks each quote against its source before insertion. Otherwise it is `TODO verify -- <reason>`. This rule has no exceptions.
- **Report `source-does-not-support` as a finding.** It marks a likely miscitation, not a missing quote. Report these prominently with the key and claim.
- **LaTeX only.** Stop on a non-LaTeX target. Only LaTeX has the inline source comment that this audit trail relies on.
- **Edit only the grounding comments.** Do not change prose, citations, figures, or BibTeX. The only edits to the paper are the inserted `% GROUNDING:` lines. The skill also adds its two generated JSON files to the repository's `.gitignore`.
- **Stay within rate limits.** Chunk the agent fan-out (~8 per slice). The run is resumable over still-ungrounded sites.
- **Do not commit.** Leave the edits and the generated JSON (gitignored) in the working tree. The user owns the commit.
