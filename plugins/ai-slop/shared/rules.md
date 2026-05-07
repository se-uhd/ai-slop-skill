# Research writing rules for empirical SE manuscripts

This file is loaded by the `ai-slop:review` and `ai-slop:revise` skills. It assumes LaTeX manuscripts. Notation like `\cite{}`, `\textbf{}`, and `%` comments refers to LaTeX conventions.

These rules draw on empirical studies of AI-to-human word frequency ratios, APA style guidelines (7th ed.), and IEEE/ACM conventions for SE publications. The general AI-trope list (banned words, formulaic openings, formatting tics, anaphora and tricolon abuse) is fetched at runtime from the upstream Gist maintained by ossama.is, with `https://tropes.fyi/tropes-md` and a bundled snapshot as fallbacks. This file carries the research-specific additions, the restricted-words table with alternatives, and the self-check.

## Language

- **Use American English consistently.** That means analyze (not analyse), behavior (not behaviour), organization (not organisation), modeling (not modelling), color (not colour). Check for British spellings introduced by co-authors or spell-checkers set to the wrong locale.
- **Treat "data" as singular.** "The data shows" and "the data is," not "the data show" or "the data are." This is a deliberate project convention. Both forms are accepted in style guides, but we use singular consistently.

## Research-coded phrases to avoid

Tropes.fyi covers general AI vocabulary. The phrases below are the ones that recur specifically in academic abstracts, introductions, and discussions. Do not use them.

- "aims to explore"
- "sheds light on"
- "provides valuable insights into" (state the actual finding)
- "this highlights the fact that"
- "has emerged as"
- "extends far beyond"
- "navigating the complexities of"
- "plays a crucial / pivotal / significant role"
- "paving the way for"
- "a growing body of work" (cite the actual works)
- "recent studies suggest" (say who found what)

## Restricted Words — Use Sparingly

Legitimate in academic SE writing but overused by AI. Each use should be intentional. If a simpler word works, use it.

**"Significant" requires special care.** In empirical SE, "significant" has a precise statistical meaning. Using it as a generic intensifier ("a significant contribution," "significant improvements") creates ambiguity about whether a statistical test was performed. Reserve "significant / significantly / significance" for reporting statistical results (e.g., "statistically significant at *p* < 0.05"). For non-statistical emphasis, use large, substantial, considerable, or important.

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
| navigate | handle, manage, deal with | n/a |
| landscape | field, area, environment, situation | n/a |
| nuanced | detailed, subtle, qualified | n/a |
| multifaceted | complex, varied, many-sided | n/a |
| intricate | complex, detailed, elaborate | n/a |
| meticulous | careful, thorough, rigorous | n/a |
| transformative | n/a | Only when genuinely describing transformation |

**Standard academic vocabulary (novel, robust, comprehensive, insights, mitigate, enhance, innovative, paradigm, framework, stakeholder, fundamentally, inherently)** is not restricted. These words are common and appropriate in SE papers. Just do not overuse them. If a simpler word works equally well, prefer it.

**Transition words (moreover, furthermore, notably, conversely, crucially, etc.)** are also standard and not restricted. Do not overuse them. If more than two appear in a single paragraph, check whether any can be dropped without losing logical flow.

## Terminology Consistency

- **Use one term for one concept.** Once you introduce a term for a concept, use that same term throughout the paper. Do not alternate between synonyms for variety. What reads as elegant variation in literary writing creates ambiguity in technical writing. If "code review" is the term, do not switch to "code inspection," "review process," and "code assessment" in subsequent paragraphs. The reader will wonder whether these refer to the same thing or to different things.
- **Define terms on first use, then reuse exactly.** If a concept needs a definition or explanation, provide it once. After that, the established term carries the meaning without re-explanation.
- **Synonyms are acceptable only for genuinely different concepts.** If two terms refer to distinct things, use both, but make the distinction explicit.

## Voice and Verb Tense

- **Prefer active voice.** Use passive only when the actor is unknown, irrelevant, or when passive genuinely reads better. If a sentence works in active voice, use active voice.
- **Use consistent tense within and across adjacent paragraphs.** Unmotivated tense shifts are distracting. Switch tense only when the temporal frame genuinely changes.

Verb tense varies by section. The rules below follow APA conventions and standard practice in empirical SE:

| Section | Default tense | Example |
|---|---|---|
| Abstract / Context | Present | "Developers increasingly rely on AI code generators." |
| Abstract / Objective | Present | "We investigate how teams detect..." |
| Abstract / Method | Past | "We surveyed 450 developers and analyzed..." |
| Abstract / Results | Past | "Response rates differed across groups." |
| Abstract / Conclusions | Present | "These results indicate that current tools..." |
| Introduction (general facts) | Present | "Code review is a core practice in modern SE." |
| Introduction (specific prior work) | Past or present perfect | "Smith et al. found..." / "Researchers have examined..." |
| Method | Past | "We recruited participants through..." |
| Results | Past | "Participants rated the tool 4.2 out of 5 on average." |
| Discussion (interpreting results) | Present | "These results suggest that..." |
| Discussion (summarizing own results) | Past | "We observed a strong correlation..." |
| Conclusion / implications | Present | "Practitioners can use these findings to..." |
| Future work | Present or modal verbs | "Future studies should examine..." |

A shift from past to present within a paragraph is acceptable when moving from what was found to what it means. Make the shift deliberate, not accidental.

**Describing the paper itself vs. describing the study.** Statements about what the paper *is* or *does* (its contributions, definitions, scope, structure) take present tense, because the paper exists in the reader's hands now. Statements about empirical actions performed during the study take past tense. Both can sit side by side in a contributions list without inconsistency:

> (1) We **document** eight configuration mechanisms ... *(what the paper contains)*
> (2) We **analyzed** the adoption of these mechanisms in 2,853 repositories ... *(empirical action)*
> (3) We **analyzed** the adoption of \textsc{Context Files}, ... *(empirical action)*

Other present-tense verbs that describe the paper itself: *we define, we propose, we present, we introduce, we show, we argue, we contribute*. Other past-tense verbs that describe the study: *we surveyed, we measured, we coded, we interviewed, we observed*.

Structured abstracts (e.g., EMSE with Context / Objective / Method / Results / Conclusions headings) follow the same tense logic per subsection.

## Punctuation

- **Em-dashes.** Maximum 2 to 3 per page. Do not swap em-dashes for parentheses. Both are signs of a sentence doing too much. Split into separate sentences instead. Reserve em-dashes for genuine interruptions.
- **Colons.** Maximum 2 per page in running prose. A colon is appropriate before a list, a definition, or a deliberate setup-and-payoff that the colon's pause genuinely earns. It is not a generic mid-sentence pause. Two failure modes to watch for. First, colon-followed-by-list patterns appearing in every other paragraph. This is an AI tic in its own right. Second, colons that have crept in as substitutes for em-dashes or parentheses when those were forbidden. AI text tends to fall back to colons (and semicolons) for the same mid-sentence pause. If a colon could be replaced by a period with light rewriting, use the period. Headings, table captions, and `figure:`-style labels are exempt; the limit applies to running prose.
- **Sentence length.** Vary deliberately. Mix short sentences (5 to 10 words) with longer compound ones (25 to 35 words). AI text is detectable by its uniformity (around 15 to 25 words per sentence, low burstiness). Do not homogenize sentence length when editing.
- **Oxford comma.** Use it, but do not let comma-heavy constructions substitute for clearer sentence structure.
- **LaTeX quotation marks.** Use LaTeX-style quotes, not straight `"` or `'`. Double quotes: `` ``...'' `` (two backticks to open, two apostrophes to close). Single quotes: `` `...' `` (one backtick to open, one apostrophe to close). Straight quotes render as two closing quotes in typeset output.

## Structure

- **No formulaic section openings.** Never open a section or subsection with "In today's...", "In the realm of...", "In an era of...", "As we explore...", or "[Topic] has become increasingly...". Start with the substance.
- **No formulaic closings.** Do not use "Overall, ...," "In summary, ...," or "In conclusion, ..." to close a single paragraph by restating what it already said. These phrases are acceptable when they do genuine work: "In summary" and "In conclusion" in actual summary or conclusion sections, "Overall" when synthesizing across multiple data points or conditions (e.g., "Overall, the pattern held across all three groups").
- **No rule-of-three defaults.** Do not reflexively group things in threes. If there are two items, list two. If there are four, list four.
- **Keep enumerations short.** Examples introduced by "e.g.,", "such as", "including", or numbered markers like "(1) ... (2) ... (3) ..." should illustrate, not exhaustively iterate. Two or three representative items are almost always enough. If the full set matters, use a table, figure, or dedicated list. Do not pack it into a parenthetical or running sentence. When in doubt, cut the enumeration to the clearest examples and stop.
- **No lists in prose.** Use running text, not bullet points, in the paper body. Tables and figures handle structured data.
- **No excessive bold or formatting.** Do not bold phrases for emphasis in running text. Reserve bold for subsection-level headers or matching the paper's existing conventions.
- **Avoid redundant content; cross-reference instead.** State each definition, method detail, finding, or introduction of an external resource (supplementary material, replication package, appendix) once, in the place where it belongs, and cross-reference it from elsewhere with `\autoref{}` or an explicit `\ref{}`. Do not restate method details in Results, repeat findings verbatim in Discussion, recap the same motivation in both Introduction and Related Work, or formally re-introduce the same supplementary package across multiple sections. Brief one-sentence reminders are acceptable when needed to follow an argument; full paragraphs of restatement are not. References to specific contents of an already-introduced resource (e.g., "the full codebook is in Appendix B") are fine. A reader who needs the information again should be pointed to where it lives, not given a second copy.

## Tone

- **Match the existing paper's voice.** Read the draft before writing. Mirror its register, its level of formality, and how it handles transitions.
- **Use "we" consistently.** First-person plural throughout.
- **Be concrete.** Instead of "provides valuable insights into X," state the actual finding.
- **Hedge from evidence, not from timidity.** "Our data suggests X" is appropriate when the data is ambiguous. "One could argue that X" is filler unless you then explain who argues it and why.
- **Take positions.** When the evidence points one direction, say so. Do not present artificial balance.

## Citations

- **No vague citation clusters.** Never write "several studies have shown [1,2,3,4,5]" or "prior work has found [X to Z]." If citing more than two works together, state what each contributes. A citation that does not tell the reader why it is there is dead weight.
- **Cite, do not gesture.** Replace "a growing body of work" with the actual works. Replace "recent studies suggest" with who found what.
- **Ground every new citation.** Verify the cited paper actually says what you claim. Read the relevant section, not just the abstract. Add a LaTeX comment (`% GROUNDING: "..."`) after the `\cite{}` with a direct quote supporting the claim. These comments leave an audit trail for co-authors.
- **Prefer `\citeauthor{}` over spelled-out author names.** When referring to authors in running text, use `\citeauthor{key}` (and `\citeyear{key}` where a year is needed) rather than typing names directly. This keeps author names synchronized with the BibTeX entry and avoids spelling or ordering errors. Write `\citeauthor{smith2020}` instead of "Smith et al." The same applies to possessives (`\citeauthor{smith2020}'s framework`) and first-mention full forms.

## Related Work

- **Analyze, do not compliment.** Say what prior work did, how it relates to this paper, and where gaps remain. No book-jacket blurbs ("X et al. present a comprehensive framework for...").
- **State the gap you fill.** Every related work discussion should make clear why the cited work leaves room for the current paper.

## Numbers and Statistics

Rules below follow APA 7th edition conventions where they align with SE practice. Where APA and IEEE/ACM conventions diverge, we follow IEEE/ACM.

### Writing numbers in text

- **Spell out numbers below ten in running text.** Exceptions: when paired with a unit (5 MB), in a series that includes numbers ten or above ("3, 7, and 15 participants"), in statistical results, or as percentages (8%).
- **Never start a sentence with a numeral.** Spell it out or restructure: "Twelve participants..." not "12 participants..."
- **Use numerals for numbers ten and above,** for all measurements with units, for statistical values, for ages, for scores, and for exact sums of money.
- **Use commas in numbers above 999** (1,000 not 1000), except in page numbers, binary code, serial numbers, temperatures, acoustic frequencies, and degrees of freedom.

### Decimal places and rounding

- **Round to aid comprehension, not to pad precision.** Two decimal places is the default for most statistics (correlations, *t*, *F*, chi-square). Use one decimal place for means and standard deviations when that is sufficient to show meaningful differences. Rescale measurements if they would otherwise require more than two decimal places.
- **Use consistent decimal places** within a table or result set. Do not mix one and three decimal places in the same column.

### Reporting statistical results

- **Report effect sizes alongside p-values.** A *p*-value alone does not tell the reader whether a result matters practically. Include Cohen's *d*, *r*, eta-squared, or the appropriate effect size measure for your test.
- **Report exact p-values** to two or three decimal places (e.g., *p* = 0.034), not as inequalities (*p* < 0.05), unless *p* < 0.001.
- **Always include leading zeros** before decimal values (e.g., *p* = 0.034, *r* = 0.82, *d* = 0.45). SE papers follow IEEE/ACM conventions, not APA, on this point.
- **Confidence intervals.** Report as "95% CI [lower, upper]" using square brackets.
- **Use *N* for total sample size, *n* for subgroup sizes.** Both are italicized.
- **Italicize statistical symbols** that are Latin letters: *M*, *SD*, *t*, *F*, *p*, *n*, *N*, *d*, *r*, *R²*, *df*. Do not italicize Greek letters (α, β, χ²) or abbreviations that are not variables (ANOVA, CI, OR).
- **Spell out statistical terms when used as nouns in running text.** Write "the mean was 4.2" not "the *M* was 4.2." Use the symbol form inside parentheses: (*M* = 4.2, *SD* = 1.1).
- **Do not repeat in text what a table already shows.** Highlight key findings and refer the reader to the table for full results.

## Figures, Tables, and Cross-References

- **Capitalize cross-references.** Write "Section 3", "Figure 2", "Table 1", never lowercase. In LaTeX, use `\autoref{}` with capitalized autoref names or explicit references like `Section~\ref{sec:...}`.
- **Captions must be specific.** "Overview of our approach" says nothing. State what is shown: "Distribution of response times by participant group." Do not editorialize; save interpretation for the text.
- **Refer to every figure and table in the text.** If a figure or table is not discussed in the body, it does not belong in the paper.
- **Number figures and tables sequentially.** Do not skip numbers or reuse them.

## Threats to Validity

- **Be specific to your study.** Name the specific bias, explain why it applies here, and describe the mitigation. Do not write generic threats that apply to any study of the same type.
- **No performative hedging.** If a threat is real, explain the mitigation. If it is not real, leave it out.

## BibTeX

- **Verify every entry.** AI-generated BibTeX entries frequently contain wrong years, wrong venues, invented page numbers, or hallucinated DOIs. Every entry must be checked against a reliable source before it goes into the `.bib` file.
- **Source priority.** (1) DBLP, if the work appears there. DBLP entries are curated and consistently formatted. (2) The publisher page, if a DOI is provided; resolve the DOI and pull metadata from the landing page. (3) Google Scholar or a general web search as a last resort, cross-checked against the actual paper.
- **Check at minimum.** Author names and ordering, title (exact, including capitalization in the original), year, venue name (full and abbreviated), volume / number / pages, and DOI.
- **Do not invent fields.** If a field (e.g., pages, volume) cannot be confirmed, omit it. A missing field is better than a wrong one.

## Self-Check Before Presenting Text

Before presenting any written or edited text, scan it against these checks:

1. **Word-level scan.** Search for banned words (per tropes.fyi) and replace any that appear. Count restricted words (per the table above); if more than 2 to 3 appear in a single paragraph, rewrite to reduce.
2. **Em-dash count.** If more than 2 per page-equivalent (~350 words), replace some.
3. **Colon count.** If more than 2 colons per page-equivalent appear in running prose, examine each. Any colon that could be replaced by a period with light rewriting should be replaced. Watch especially for colons that have crept in as substitutes for em-dashes or parentheses, and for colon-followed-by-list patterns repeating across paragraphs.
4. **Sentence length variance.** If three consecutive sentences are within 5 words of each other in length, revise at least one.
5. **Opening / closing patterns.** Verify no section starts with a formulaic opener or ends with "Overall, ..." or "In summary, ...".
6. **Participial openings.** If more than one sentence per page starts with a present participle clause ("-ing, ..."), rewrite.
7. **Hedging density.** If a paragraph contains more than two hedging phrases (may, might, could, perhaps, to some extent), evaluate whether each is evidence-based. Remove those that are not.
8. **Passive voice.** If more than one-third of sentences in a paragraph are passive, rewrite the avoidable ones in active voice.
9. **"Significant" audit.** If any use of "significant / significantly / significance" is not reporting a statistical test, replace it.
10. **Citation checks.** Verify that any citation cluster with three or more references explains what each cited work contributes. For every new `\cite{}` added, verify a `% GROUNDING: "..."` comment follows it with a direct quote from the cited paper.
11. **Related work tone.** Scan for complimentary language ("seminal," "pioneering," "impressive") that describes prior work without analyzing it. Rewrite to be analytical.
12. **Threats specificity (if applicable).** Verify each threat names a specific risk to this study and describes a concrete mitigation. Remove generic threats.
13. **BibTeX verification (if applicable).** Verify each entry against DBLP (preferred), the publisher page via DOI, or Google Scholar. Confirm author names, title, year, venue, and DOI. Omit any field that cannot be confirmed.
14. **Verb tense consistency.** Check that each section uses the tense prescribed by the verb tense table. Fix unmotivated tense shifts within a paragraph.
15. **Statistical formatting.** Verify exact *p*-values (not *p* < 0.05 unless *p* < 0.001), check that effect sizes accompany *p*-values, confirm leading zeros before all decimal values, and verify that statistical symbols are italicized where required.
16. **American English spelling.** Search for common British variants: analyse, behaviour, organisation, modelling, colour, favour, centre, defence, licence (verb). Replace with American equivalents.
17. **Figure and table captions.** Rewrite vague captions ("Overview of our approach," "Experimental results") to state what the figure or table actually shows.
18. **Redundancy check.** Scan for definitions, method details, findings, or formal introductions of supplementary resources that are stated in full in more than one section. Replace duplicated content with a cross-reference to the section where it is first stated. One-sentence reminders are fine; restated paragraphs and re-introductions are not.
19. **Terminology consistency.** Verify each key concept is referred to by the same term throughout. Standardize cases where synonyms are used interchangeably for the same concept.
