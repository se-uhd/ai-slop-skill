# Rule layers

The writing rules ship as five layers. Which of the first three load depends on whether the input is LaTeX source (detected automatically by `scripts/detect_scope.py`) and whether you pass `--scientific`:

| Input | general | scientific | latex |
|---|:---:|:---:|:---:|
| LaTeX source (`.tex`) | yes | yes | yes |
| Anything else, no flag | yes | no | no |
| Anything else, `--scientific` | yes | yes | no |

`rules-general.md` applies to any prose (e.g., vocabulary, punctuation, structure, tone). Every rule carries a stable key (`G.semicolons`, `S.significant`, `L.grounding-comments`) that reports, cross-references, and the self-checks cite alongside its name. `rules-scientific.md` adds research article conventions (e.g., verb tense by section, citations, statistics, threats to validity). `rules-latex.md` adds LaTeX source mechanics (e.g., LaTeX quotes, `\citeauthor`, `% GROUNDING`, BibTeX). A LaTeX paper is always treated as a research article, so the scientific layer loads automatically. For a non-LaTeX manuscript (Markdown or PDF), `--scientific` opts into it.

`rules-ste.md` is the optional STE layer, and `--ste` adds it to any row of the table. It applies part of ASD-STE100 Simplified Technical English: short sentences with the subject and verb near the start, active voice, one topic per paragraph, one meaning per word, verbs instead of nominalizations, and no dropped articles. It changes the ASD-STE100 rules on sentence length and style. Sentence length varies around a target of 25 words, with a tolerance up to 35. Each unit (a reply, a headed section, or a text without headings) carries one stylistic device at most. Quotations and literal strings stay as written. Where the STE layer and the general layer set different limits for the same construction, the STE limit applies. The STE rules carry `T.` keys.

When an STE rewrite of an existing sentence would lose meaning, precision, or force, the sentence stays as written, and a review lists it for author judgment. `scripts/scan_sentences.py` lists the candidates that a count or a word pattern can find: sentences over 25 words, runs of sentences of similar length, passive verbs, and a light verb followed by an action noun ("make a decision"). It reads each table cell as a paragraph of its own, so the rows of a table are not compared with each other.

`rules-economist.md` is the optional Economist layer, selected by `--economist`.
It distills the core advice in Lane Greene's *Writing with Style: The Economist
Guide* (2023): explain unfamiliar knowledge to intelligent readers, choose plain
and precise words, make actors and actions clear, connect the argument, remove
padding, use a civil tone, and put numbers in context. It also checks numerical
precision and comparability. The rules carry `E.` keys and include a self-check.
The book is not bundled and is not needed at runtime.

Economist mode keeps project and academic conventions, including the default
American spelling and required statistical detail. It sets no sentence-length
limit, numerical quota, or automatic rounding rule. `--economist --ste` combines
both optional layers, retaining the stricter STE limits. An unresolved fact or
interpretation goes under author judgment instead of a speculative rewrite.

Examples:

```text
/ai-slop:review draft.md --economist
/ai-slop:review paper.pdf --scientific --economist
/ai-slop:review-diff main --economist
/ai-slop:review-repo --economist
/ai-slop:writing --economist
/ai-slop:init --economist
```
