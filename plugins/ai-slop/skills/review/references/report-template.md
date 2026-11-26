# Report template

The report schema is stable so that revise mode can parse it. Each finding has `Rule`, `Location`, `Quote`, and `Suggested revision`. Revise mode locates the `Quote` in the paper and replaces it with `Suggested revision`.

````markdown
# AI Slop Review

**Paper:** <path>
**Skill version:** 2026-11_rev9
**Reviewed:** <ISO 8601 date>

> This report applies the writing rules at
> <https://github.com/se-uhd/ai-slop-skill> as a self-check.
> Findings are revision suggestions. Nothing is grounds for rejection.

## Summary

<What reads well, what needs revision, and the main counts, in one short paragraph.>

## Findings by section

### <Section name, e.g., Abstract>

#### Finding <N>

- **Rule:** <rule name and key from a rule layer, e.g. Semicolons (G.semicolons), or trope name with its catalog status, e.g. Negative parallelism (tropes.fyi, consistent)>
- **Location:** `<file:line>` or `Section: <name>` if line not available
- **Quote:** `<verbatim quote of the offending text, with enough surrounding context to be unique>`
- **Suggested revision:** `<concrete replacement text>`
- **Reason:** <problem in context and benefit of the replacement, or the explicit convention being corrected>

<Repeat per finding within the section.>

### <Next section>
...

## Cross-cutting metrics

### Dash density (em-dash and ascii-dash)
- Per-page-equivalent count: <N> (target: ≤ 2 to 3)
- Locations: <list>

### Colon density (running prose)
- Per-page-equivalent count: <N> (target: ≤ 2)
- Locations: <list>

### Capitalization after a colon
- Colons followed by a complete sentence with a lowercase first word (the first item of an enumerated series is exempt): <list>
- Colons followed by a fragment or list with an uppercase first word: <list>

### Semicolon density (running prose)
- Per-page-equivalent count: <N> (target: ≤ 1 to 2)
- Locations: <list>

### Combined pause-punctuation signal
- Per-page-equivalent count (dash + colon + semicolon): <N> (target: ≤ 5)
- Pages over the combined cap: <list>

### Restricted-word density
- Paragraphs over threshold: <list with paragraph pointers>

### Verb-tense compliance
- Prior-work attributions in present tense where past or present perfect is required: <list with pointers>
- Unmotivated tense shifts within a paragraph or clause: <list>

### Spelling (American vs. British)
- British variants found: <list>

### "Significant" audit
- Non-statistical uses: <list>

### Cross-references (LaTeX only)
- Figures and tables that the text never references: <list>
- Lowercase, doubled, or hard-coded references: <list>

### Citations
- Citation clusters lacking per-work explanation: <list>
- Spelled-out author names that should use `\citeauthor{}`: <list>

### Grounding to-do
- `\cite{}` calls with no grounding comment (always listed, with `% GROUNDING <key>:` counted as grounded): <file:line, keys>

### BibTeX (if applicable)
- Entries with missing or unverifiable required fields: <list>

### Reference verification (if applicable)
- DBLP database used, or that DBLP was not checked: <database and build date, or the setup command>
- Entries flagged by `verify_references.py`, with verdict and detail: <list>
- Entries that returned `unchecked-offline` (no network at review time): <list>

### STE metrics (STE mode only)
- Sentences over 35 words: <N>, at <list>
- Sentences of 26 to 35 words that fail the clause test: <list>
- Runs of three or more sentences within 5 words of each other in length: <list>
- Passive verbs with a known actor: <list>
- Light verb + action noun: <list>
- Units with more than one stylistic device: <list>

## Items requiring author judgment

<Findings that the skill cannot resolve automatically: terminology choices, threats-to-validity specificity,
gap statements in related work, hedging that depends on evidence that the skill has not assessed,
and, in STE mode, sentences that an STE rewrite would weaken, each with the rule and the reason.
Phrase each as a suggestion, not a command. Revise mode will not act on these.>
````
