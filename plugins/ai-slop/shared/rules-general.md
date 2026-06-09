# Writing rules — general layer

This is the base layer of the writing rules. It applies to any prose, scientific
or not, in any format. Two further layers build on it: `rules-scientific.md`
adds conventions for empirical research articles, and `rules-latex.md` adds
mechanics for LaTeX source. A skill loads the layers its scope calls for
(general only; general + scientific; or all three).

These rules target AI slop and the habits that make machine-written prose
recognizable, plus universal points of clean writing. The general AI-trope list
(banned words, formulaic openings, formatting tics, anaphora and tricolon abuse)
is fetched separately from the upstream catalog; this layer carries the
restricted-words table with alternatives and a self-check. The justification
behind the rules lives in `rules-rationale.md`, which the skills do not load.

## Language

- **Use American English consistently.** That means analyze (not analyse), behavior (not behaviour), organization (not organisation), modeling (not modelling), color (not colour). Check for British spellings introduced by collaborators or spell-checkers set to the wrong locale.
- **Treat "data" as singular.** "The data shows" and "the data is," not "the data show" or "the data are." Project convention: both forms are accepted in style guides, but we use singular consistently.
- **Use "such as" not "like" to introduce examples.** Write "scenarios such as code completion," not "scenarios like code completion." `Like` is colloquial in this construction; `such as` is the more formal register. Apply this even when the original prose already uses `like` — do not carry it over verbatim into a rewrite. `Like` remains correct as a verb ("readers like terse prose") and in deliberate similes.

## Restricted Words — Use Sparingly

Legitimate words that AI overuses. Each use should be intentional. If a simpler word works, use it.

| Restricted | Preferred alternative(s) | When the restricted form is acceptable |
|---|---|---|
| utilize | use | Only when the distinction from "use" matters |
| leverage | use, apply, employ | Only when the lever metaphor is intentional |
| facilitate | enable, support, help, allow | n/a |
| foster | encourage, support, promote | n/a |
| streamline | simplify, reduce, speed up | Acceptable in process-improvement contexts |
| underscore | emphasize, highlight, stress | n/a |
| harness | use, apply, employ | n/a |
| encompass | include, cover, span | n/a |
| navigate | handle, manage, deal with | Only for literal movement through a UI, website, menu, or file tree (e.g., "navigate the codebook"); never as a metaphor for handling difficulty ("navigate the challenges") |
| landscape | field, area, environment, situation | n/a |
| nuanced | detailed, subtle, qualified | n/a |
| multifaceted | complex, varied, many-sided | n/a |
| intricate | complex, detailed, elaborate | n/a |
| meticulous | careful, thorough, rigorous | n/a |
| transformative | n/a | Only when genuinely describing transformation |

**Standard vocabulary (novel, robust, comprehensive, insights, mitigate, enhance, innovative, paradigm, framework, stakeholder, fundamentally, inherently)** is not restricted. Do not overuse it; if a simpler word works equally well, prefer it.

**Transition words (moreover, furthermore, notably, conversely, crucially, etc.)** are also standard and not restricted. Do not overuse them. If more than two appear in a single paragraph, check whether any can be dropped without losing logical flow.

## Phrases to Avoid

Stock formulations that read as AI filler or stilted register. Replace each with the plain alternative. The trope catalog (fetched separately) covers the broader banned-phrase list; this section holds project-specific additions.

- **"worked example(s)"** → "example(s)". The qualifier "worked" rarely adds information and reads as padded pedagogical register. Keep it only in the narrow technical sense of a fully solved problem walked through step by step (a textbook "worked solution"), where the contrast with an unsolved exercise is the point.

## Terminology Consistency

- **Use one term for one concept.** Once you introduce a term for a concept, use that same term throughout the document. Do not alternate between synonyms for variety; what reads as elegant variation in literary writing creates ambiguity in technical writing. If "code review" is the term, do not switch to "code inspection," "review process," and "code assessment" in subsequent paragraphs.
- **Define terms on first use, then reuse exactly.** If a concept needs a definition or explanation, provide it once. After that, the established term carries the meaning without re-explanation.
- **Synonyms are acceptable only for genuinely different concepts.** If two terms refer to distinct things, use both, but make the distinction explicit.

## Voice

- **Prefer active voice.** Use passive only when the actor is unknown, irrelevant, or when passive genuinely reads better. If a sentence works in active voice, use active voice.
- **Use consistent tense within and across adjacent paragraphs.** Unmotivated tense shifts are distracting. Switch tense only when the temporal frame genuinely changes.

## Punctuation

- **Em-dashes.** Judge each dash on its own: is an em-dash genuinely the right mark, or is it standing in for a period, comma, or parentheses that would read better? Reserve it for a genuine interruption or an appositive that needs setting off; if splitting into two sentences or using a comma works, do that, and never swap an em-dash for parentheses — both signal a sentence doing too much. Count is only a secondary signal: more than 2 to 3 per page-equivalent (~350 words) of running prose flags over-reliance and is worth a second pass, but one dash used wrongly is a worse problem than three used well. Two structural uses are legitimate and are not over-reliance: (a) appositives whose interior already contains commas, where outer commas around the appositive would be ambiguous (`Three reviewers — Alice, Bob, and Carol — flagged the issue`); and (b) a parenthetical that itself contains parentheses, where em dashes stand in for an outer pair of parens to avoid nesting (`the corpus — built from public repositories (GitHub, GitLab) — covers ...`). Em dashes inside quoted source material likewise do not count, since they belong to the quotation, not to the writer.
- **Colons.** Judge each colon: it is appropriate before a list, a definition, or a deliberate setup-and-payoff that the pause genuinely earns, not as a generic mid-sentence pause. If a colon could be replaced by a period with light rewriting, use the period. Two failure modes to watch for. First, colon-followed-by-list patterns appearing in every other paragraph. Second, colons that have crept in as substitutes for em-dashes or parentheses when those were forbidden. Count is a secondary signal: more than 2 per page-equivalent in running prose flags over-reliance. Headings, table captions, and `figure:`-style labels are exempt; the rule applies to running prose.
- **Introducer punctuation: `:` not `.` before a list or continuation.** When a sentence introduces an enumerated list, a numbered structure (e.g., `(1) ... (2) ... (3) ...`), or a paragraph that grammatically completes or elaborates the introducer, end the introducer with `:`, not `.`. AI text systematically defaults to `.` here. Mechanical test: if the following block is a list or directly continues the introducer, use `:`; if the following block stands as an independent sentence on its own topic, the period is correct. Introducer colons doing this grammatical job are exempt from the colon count above, which targets mid-sentence colons used as filler pauses, em-dash substitutes, or decorative setup.
- **Capitalization after a colon.** In running prose, capitalize the first word after a colon when what follows is a complete sentence (an independent clause). Keep it lowercase when the colon introduces a fragment, phrase, single word, or list. Examples: "We adopt one rule: Capitalize after a colon when a full sentence follows." vs. "We considered three options: speed, accuracy, and cost." Headings and `figure:` / `table:` labels are exempt. Project convention; AI prose reliably defaults to lowercase here regardless of clause completeness.
- **Semicolons.** Judge each semicolon: it is appropriate to join two closely related independent clauses where the connection adds meaning a period would lose, or to separate items in a complex list where commas would create ambiguity. It is not a generic mid-sentence pause or a default substitute for a period when both clauses can stand alone; if it could be replaced by a period with no loss, use the period. Two separate sentences are often more natural. The most common misuse is a semicolon that glues a second independent clause onto the first, often one opening with a pronoun (we, it, this, they, these). Default to a period there. Count is a secondary signal: more than 1 to 2 per page-equivalent in running prose flags over-reliance.
- **Watch the combined load.** Em-dashes, colons, and semicolons all create mid-sentence pauses, and AI text shifts the load between them when any single mark is restricted, so judging each mark alone misses the pattern. The primary test stays per mark: is each pause the right choice? As a combined secondary signal, a page near all three individual ceilings at once (say 3 em-dashes, 2 colons, 2 semicolons) is over-punctuated even though no single ceiling is exceeded; for each mark, ask whether a split into two sentences reads better.
- **Sentence length.** Vary deliberately. Mix short sentences (5 to 10 words) with longer compound ones (25 to 35 words). AI text is detectable by its uniformity (around 15 to 25 words per sentence, low burstiness). Do not homogenize sentence length when editing.
- **Hyphenation of compound modifiers.** AI text over-hyphenates noun-noun stacks placed before another noun ("code-generation benchmarks", "code-translation performance", "prompt-format sensitivity", "data-collection process", "model-evaluation pipeline"). These three-noun stacks are usually unambiguous without the hyphen ("code generation benchmarks"); drop it. Keep the hyphen only when the unhyphenated form invites a real misread, typically when one element is a participle that could re-attach as a verb ("instruction-following ability" stays hyphenated because "instruction following ability" briefly reads as "instruction following" + "ability" with "following" as a verb). Genuine compound adjectives where one element is an adjective or participle (high-quality, well-known, large-scale, fine-grained) keep the hyphen.
- **Oxford comma.** Use it, but do not let comma-heavy constructions substitute for clearer sentence structure.

## Structure

- **No formulaic section openings.** Never open a section or subsection with "In today's...", "In the realm of...", "In an era of...", "As we explore...", or "[Topic] has become increasingly...". Start with the substance.
- **No formulaic closings.** Do not use "Overall, ...," "In summary, ...," or "In conclusion, ..." to close a single paragraph by restating what it already said. These phrases are acceptable when they do genuine work: "In summary" and "In conclusion" in actual summary or conclusion sections; "Overall" when synthesizing across multiple data points or conditions (e.g., "Overall, the pattern held across all three groups"); and "In summary, ..." when introducing an enumerated list that consolidates several preceding paragraphs of prose into a checklist (e.g., "In summary, our recommendation is to report: (1) X; (2) Y; (3) Z."). The diagnostic is whether the phrase consolidates content the reader has not yet seen in list form. If the next construct is a numbered or bulleted list distilling earlier prose, the opener earns its keep; if it introduces a sentence or two that just restates the paragraph above, it is filler.
- **Paragraph length.** A paragraph normally contains more than one sentence. Avoid the AI tic of breaking prose into one-sentence paragraphs for manufactured emphasis. A one-sentence paragraph is acceptable when it serves a clear structural purpose, such as opening a section with a framing or topic sentence, introducing an enumerated list or figure, marking a section transition, or carrying a topic sentence that genuinely stands alone. The diagnostic is whether absorbing the paragraph into its neighbor would lose something the prose needs. Flag any page with more than one or two single-sentence paragraphs, or any run of three or more consecutive single-sentence paragraphs.
- **No rule-of-three defaults.** Do not reflexively group things in threes. If there are two items, list two. If there are four, list four.
- **Keep enumerations short.** Examples introduced by "e.g.,", "such as", "including", or numbered markers like "(1) ... (2) ... (3) ..." should illustrate, not exhaustively iterate. Two or three representative items are almost always enough. If the full set matters, use a table, figure, or dedicated list. Do not pack it into a parenthetical or running sentence. When in doubt, cut the enumeration to the clearest examples and stop.
- **Signal whether a parenthetical list is examples or exhaustive.** A bare parenthetical with 2+ comma-separated items reads ambiguously: the reader cannot tell whether the list is representative or complete. Open it with "e.g.," (examples) or "i.e.," (definition or full enumeration), or restructure. Same goes for inline lists in running text introduced by nothing — use "such as" or "including." Exception: an abbreviation expansion (e.g., "large language models (LLMs)") or a parenthetical that names a single concept.
- **Pick one example-list signal and stay with it.** Don't mix `e.g.,` with `etc.` in the same parenthetical: "(e.g., a, b, etc.)" is redundant. Across a document, prefer `e.g., …` at the start over `…, etc.` at the end and apply the choice consistently.
- **No excessive bold or formatting.** Do not bold phrases for emphasis in running text. Reserve bold for subsection-level headers or matching the document's existing conventions.
- **Avoid redundant content; refer back instead.** State each definition, point, or finding once, in the place where it belongs, and refer back to it from elsewhere rather than restating it. Brief one-sentence reminders are acceptable when needed to follow an argument; full paragraphs of restatement are not. A reader who needs the information again should be pointed to where it lives, not given a second copy.
- **Cut padding at the sentence level.** Prefer the shortest phrasing that preserves meaning and precision. This is distinct from vagueness (*Be concrete*), inflated vocabulary (the restricted-words table), and duplication (*Avoid redundant content*): a phrase can be concrete, plain, and unique yet still spend more words than its content needs. Replace multi-word filler with its shorter equivalent ("in order to" → "to", "due to the fact that" → "because", "in the event that" → "if", "has the ability to" → "can", "the majority of" → "most", "at this point in time" → "now"). Delete empty lead-ins ("it is important to note that", "it should be mentioned that", "as can be seen"). Cut redundant doublets where one word already implies the other ("end result", "future plans", "completely eliminate"). The diagnostic is subtractive: if deleting a word or clause costs no meaning, emphasis, or precision, delete it.
- **Cut padding at the paragraph level.** A paragraph should make its point in as many sentences as it needs and no more. Remove windup sentences that announce what the paragraph will do rather than doing it, and any sentence that restates its predecessor without adding a claim, qualification, or evidence. A paragraph that takes five sentences to deliver one sentence of content is padded, even when every sentence is individually clean. This is the opposite failure from the **Paragraph length** rule above, which guards against paragraphs cut too short for manufactured emphasis.
- **Reformulate, do not delete.** When prose is flagged, the default fix is to rewrite it into a clear, correct form that keeps the author's intended content. Delete only genuine filler (the padding, windup sentences, and non-evidence-based hedges the rules above target) or when the author explicitly asks for a cut. A flagged claim, example, or qualification carries information the author chose to include; resolving the flag by deleting it discards that silently.

## Tone

- **Match the existing document's voice.** Read the draft before writing. Mirror its register, its level of formality, and how it handles transitions.
- **Be concrete.** Instead of "provides valuable insights into X," state the actual finding.
- **Hedge from evidence, not from timidity.** "The data suggests X" is appropriate when the data is ambiguous. "One could argue that X" is filler unless you then explain who argues it and why.
- **Take positions.** When the evidence points one direction, say so. Do not present artificial balance.
- **No author-voice metacommentary in published prose.** Asides like "reader beware," "the reader is warned," "we shall see," "spoiler alert," or "(more on this below)" break the formal register and address the reader directly about the act of reading. Remove them from rendered body text, or move them into editorial notes that do not render. Treat them as a clear finding when they appear in body text, not as a stylistic judgment call. Forward references to later sections are fine as plain pointers, not as winks.

## Self-Check Before Presenting Text

Before presenting any written or edited text, scan it against these checks:

1. **Word-level scan.** Search for banned words (per tropes.fyi) and replace any that appear. Count restricted words (per the table above); if more than 2 to 3 appear in a single paragraph, rewrite to reduce.
2. **Em-dashes.** Check each em-dash: is it the right mark, or would a period, comma, or parentheses read better? Replace the ones not earning their place. As a secondary signal, more than 2 to 3 per page-equivalent (~350 words) of running prose flags over-reliance. Exclude from any count: em dashes inside quoted source material, and glyphs that are not em dashes at all — en dashes in numeric or page ranges (`pp. 12–18`), minus signs in math, and hyphens or `--` sequences inside code listings. Also exclude the two structural exceptions noted in the **Em-dashes** rule (comma-bearing appositives and nested-parens avoidance).
3. **Colons.** Examine each colon: any that could be replaced by a period with light rewriting should be. Watch especially for colons substituting for em-dashes or parentheses, and for colon-followed-by-list patterns repeating across paragraphs. As a secondary signal, more than 2 per page-equivalent in running prose flags over-reliance.
4. **Introducer punctuation.** For every sentence immediately followed by an enumerated list, a numbered structure (e.g., `(1) ... (2) ... (3) ...`), a bulleted block, or a paragraph that grammatically continues or elaborates it, verify the introducer ends with `:`, not `.`. AI text systematically defaults to `.` here; the `:` is correct and does not count toward the colon signal.
5. **Capitalization after a colon.** For every colon in running prose, check whether the text that follows is a complete sentence. If it is, the first word must be capitalized. If it is a fragment, phrase, single word, or list, keep the first word lowercase. Fix mismatches.
6. **Semicolons.** Examine each semicolon: replace it with a period and two sentences when both clauses can stand alone. Reserve semicolons for genuine list disambiguation and for tightly coupled independent clauses where the link adds meaning a period would lose. As a secondary signal, more than 1 to 2 per page-equivalent in running prose flags over-reliance.
7. **Combined pause-punctuation signal.** After judging em-dashes, colons, and semicolons individually, count the three together per page-equivalent as a secondary check: a page within each individual ceiling can still be over-punctuated (3 + 2 + 2 = 7 mid-sentence pause marks). Around 5 or fewer per page in running prose is a reasonable target; prefer a period whenever the sentence allows.
8. **Sentence length variance.** If three consecutive sentences are within 5 words of each other in length, revise at least one.
9. **Opening / closing patterns.** Verify no section starts with a formulaic opener or ends with "Overall, ..." or "In summary, ...". When `In summary,` / `In conclusion,` / `Overall,` does appear, confirm it introduces a real synthesis (an enumerated list distilling earlier prose, or a synthesis across multiple data points) rather than restating a single preceding paragraph.
10. **Participial openings.** If more than one sentence per page starts with a present participle clause ("-ing, ..."), rewrite.
11. **Hedging density.** If a paragraph contains more than two hedging phrases (may, might, could, perhaps, to some extent), evaluate whether each is evidence-based. Remove those that are not.
12. **Passive voice.** If more than one-third of sentences in a paragraph are passive, rewrite the avoidable ones in active voice.
13. **Paragraph length.** Count single-sentence paragraphs per page. More than one or two on a page, or any run of three or more in a row, is a flag. Fold each into a neighbor unless it does work that absorbing it would lose, such as opening a section, introducing a list or figure, marking a section transition, or carrying a stand-alone topic sentence.
14. **American English spelling.** Search for common British variants: analyse, behaviour, organisation, modelling, colour, favour, centre, defence, licence (verb). Replace with American equivalents.
15. **Redundancy check.** Scan for definitions, points, or findings stated in full more than once. Replace duplicated content with a reference back to where it is first stated. One-sentence reminders are fine; restated paragraphs are not.
16. **Terminology consistency.** Verify each key concept is referred to by the same term throughout. Standardize cases where synonyms are used interchangeably for the same concept.
17. **Hyphenation audit.** Scan for hyphenated noun-noun stacks placed before another noun (e.g., "code-generation benchmarks", "code-translation performance", "data-collection process"). Drop the hyphen unless one element is a participle that would otherwise re-attach as a verb (e.g., "instruction-following ability" stays).
18. **Parenthetical-list signaling.** Scan for `(X, Y, Z)` patterns with 2+ comma-separated items. Verify each is signaled as examples (`e.g.,`) or as a definition/full enumeration (`i.e.,`); if neither and the list isn't obviously exhaustive, add `e.g.,`. Also flag any parenthetical that mixes `e.g.,` with `etc.`, or that uses `etc.` while the rest of the document signals examples with `e.g.,` — pick one signal per document and apply it consistently. Skip abbreviation expansions like "large language models (LLMs)".
19. **Concision.** Scan for sentence-level padding (multi-word filler such as "in order to", "due to the fact that", "has the ability to"; empty lead-ins such as "it is important to note that"; redundant doublets such as "end result") and replace or delete it. Then scan each paragraph for windup sentences and for sentences that restate a predecessor without adding a claim, qualification, or evidence; cut them. Apply the subtractive test: if deleting a word, clause, or sentence costs no meaning, emphasis, or precision, delete it.
