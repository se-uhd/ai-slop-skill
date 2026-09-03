# Writing rules: scientific layer

This layer adds conventions for empirical research articles on top of
`rules-general.md`. Load it together with the general layer when reviewing or
writing a paper; add `rules-latex.md` on top when the source is LaTeX. The
rules here draw on APA style (7th ed.) and IEEE/ACM conventions for SE
publications. The rationale behind the contested rules lives in
`rules-rationale.md`, which the skills do not load.

## Research-coded phrases to avoid

**Research-coded phrases** (`S.research-coded-phrases`). Tropes.fyi covers general AI vocabulary. The phrases below recur specifically in academic abstracts, introductions, and discussions. Do not use them.

- "aims to explore"
- "sheds light on"
- "provides valuable insights into" (state the actual finding)
- "this highlights the fact that"
- "has emerged as"
- "extends far beyond"
- "navigating the complexities of"
- "plays a crucial / pivotal / significant role"
- "paving the way for"
- "keyed to" (use "specific to" or "for")
- "a growing body of work" (cite the actual works)
- "recent studies suggest" (say who found what)

## The word "significant"

**Reserve "significant" for statistics** (`S.significant`). In empirical SE, "significant" has a precise statistical meaning. Using it as a generic intensifier ("a significant contribution," "significant improvements") creates ambiguity about whether a statistical test was performed. Reserve "significant / significantly / significance" for reporting statistical results (e.g., "statistically significant at *p* < 0.05"). For non-statistical emphasis, use large, substantial, considerable, or important.

## Voice

- **Use "we" consistently** (`S.we`). First-person plural throughout.

## Verb Tense by Section

**Verb tense by section** (`S.tense-by-section`). Verb tense varies by section. The table below follows APA conventions and standard practice in empirical SE:

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

**Present tense for the paper, past tense for the study** (`S.paper-vs-study`). Statements about what the paper *is* or *does* (its contributions, definitions, scope, structure) take present tense, because the paper exists in the reader's hands now. Statements about empirical actions performed during the study take past tense. Both can sit side by side in a contributions list without inconsistency:

> (1) We **document** eight configuration mechanisms ... *(what the paper contains)*
> (2) We **analyzed** the adoption of these mechanisms in 2,853 repositories ... *(empirical action)*
> (3) We **analyzed** the adoption of \textsc{Context Files}, ... *(empirical action)*

Other present-tense verbs that describe the paper itself: *we define, we propose, we present, we introduce, we show, we argue, we contribute*. Other past-tense verbs that describe the study: *we surveyed, we measured, we coded, we interviewed, we observed*.

The same distinction governs cited prior work. An action that a study performed (it *surveyed*, *found*, *measured*) takes past or present perfect, while a claim that its paper makes (it *argues*, *proposes*, *defines*) can stay present. Do not mix the two within one attribution clause: "they *surveyed* ... and *found* ...", not "they *survey* ... and *found* ...".

Structured abstracts (e.g., EMSE with Context / Objective / Method / Results / Conclusions headings) follow the same tense logic per subsection.

## Structure

- **No lists in prose** (`S.no-lists`). Use running text, not bullet points, in the paper body. Tables and figures handle structured data.
- **Avoid restatement across sections** (`S.no-restatement`). Do not restate method details in Results, repeat findings verbatim in Discussion, recap the same motivation in both Introduction and Related Work, or formally re-introduce the same supplementary package (replication material, appendix) across multiple sections. State each once and cross-reference it. References to specific contents of an already-introduced resource (e.g., "the full codebook is in Appendix B") are fine. The abstract is exempt. It compresses the whole paper, so its overlap with the body is expected (see **The body must stand independent of the abstract** (`S.body-independent`)).
- **The body must stand independent of the abstract** (`S.body-independent`). The abstract is read on its own, since indexers, search engines, and abstract-only listings use it without the paper and a reader of the body may skip it, so no section of the body may rely on it. Anything the abstract introduces (an acronym, abbreviation, coined or defined term, or piece of notation) is local to the abstract and counts as not yet introduced in the body: introduce it again at its first occurrence in the body, whatever section that is, expanding the acronym, defining the term, or declaring the notation as though the abstract were not there. The body must read completely with the abstract deleted. This re-introduction is required, not redundant. Do not flag a body definition, acronym expansion, or term introduction as a duplicate of one in the abstract, and the abstract's overlap with the body is never a restatement violation.

## Citations

- **No vague citation clusters** (`S.citation-clusters`). Never write "several studies have shown [1,2,3,4,5]" or "prior work has found [X to Z]." If citing more than two works together, state what each contributes. A citation that does not tell the reader why it is there adds nothing.
- **Cite specific works** (`S.cite-specific-works`). Replace "a growing body of work" with the actual works. Replace "recent studies suggest" with who found what.
- **Ground every claim you attribute to a citation** (`S.ground-claims`). Verify the cited work actually says what you claim. Read the whole paper when its full text is available, not just the abstract. The abstract compresses away the caveats, scope conditions, and negative results that decide whether a claim holds. Fall back to the relevant section only when the full text cannot be obtained.
- **Avoid citations in the abstract** (`S.no-abstract-citations`). ACM, EMSE, and many IEEE-journal author guidelines prohibit references in abstracts. The abstract is intended to stand alone without bibliographic dependencies. When a proposed rewrite would put a reference into the abstract, rephrase to drop it. The underlying claim can move to the introduction. Check the venue's author guidelines before adding any reference to an abstract. The safe default is to keep abstracts citation-free.

## Related Work

- **Analyze, do not compliment** (`S.analyze-prior-work`). Say what prior work did, how it relates to this paper, and where gaps remain. No complimentary summaries ("X et al. present a comprehensive framework for...").
- **State the gap you fill** (`S.state-the-gap`). Every related work discussion should make clear why the cited work leaves room for the current paper.

## References

- **Verify every reference** (`S.verify-references`). AI-generated references frequently contain wrong years, wrong venues, invented page numbers, or hallucinated DOIs. Check each one against a reliable source (DBLP, the publisher page via DOI, or the actual paper) before it goes into the manuscript. DBLP's curated record is the preferred source for CS/SE venues. Fall back to the publisher/DOI metadata when DBLP holds only a preprint of a paper that has since been published.
- **Do not invent fields** (`S.no-invented-fields`). If a bibliographic field (e.g., pages, volume) cannot be confirmed, omit it. A missing field is better than a wrong one.

## Numbers and Statistics

Rules below follow APA 7th edition conventions where they align with SE practice. Where APA and IEEE/ACM conventions diverge, we follow IEEE/ACM.

### Writing numbers in text

- **Spell out numbers below ten in running text** (`S.spell-out-below-ten`). Exceptions: when paired with a unit (5 MB), in a series that includes numbers ten or above ("3, 7, and 15 participants"), in statistical results, or as percentages (8%).
- **Never start a sentence with a numeral** (`S.no-initial-numeral`). Spell it out or restructure: "Twelve participants..." not "12 participants..."
- **Use numerals for numbers ten and above** (`S.numerals-from-ten`), for all measurements with units, for statistical values, for ages, for scores, and for exact sums of money.
- **Use commas in numbers above 999** (`S.thousands-separator`) (1,000 not 1000), except in page numbers, binary code, serial numbers, temperatures, acoustic frequencies, and degrees of freedom.

### Decimal places and rounding

- **Round to aid comprehension, not to pad precision** (`S.rounding`). Two decimal places is the default for most statistics (correlations, *t*, *F*, chi-square). Use one decimal place for means and standard deviations when that is sufficient to show meaningful differences. Rescale measurements if they would otherwise require more than two decimal places.
- **Use consistent decimal places** (`S.consistent-decimals`) within a table or result set. Do not mix one and three decimal places in the same column.

### Reporting statistical results

- **Report effect sizes alongside p-values** (`S.effect-sizes`). A *p*-value alone does not tell the reader whether a result matters practically. Include Cohen's *d*, *r*, eta-squared, or the appropriate effect size measure for your test.
- **Report exact p-values** (`S.exact-p-values`) to two or three decimal places (e.g., *p* = 0.034), not as inequalities (*p* < 0.05), unless *p* < 0.001.
- **Always include leading zeros** (`S.leading-zeros`) before decimal values (e.g., *p* = 0.034, *r* = 0.82, *d* = 0.45). SE papers follow IEEE/ACM conventions, not APA, on this point.
- **Confidence intervals** (`S.confidence-intervals`). Report as "95% CI [lower, upper]" using square brackets.
- **Use *N* for total sample size, *n* for subgroup sizes** (`S.sample-size-symbols`). Both are italicized.
- **Italicize statistical symbols** (`S.italic-symbols`) that are Latin letters: *M*, *SD*, *t*, *F*, *p*, *n*, *N*, *d*, *r*, *R²*, *df*. Do not italicize Greek letters (α, β, χ²) or abbreviations that are not variables (ANOVA, CI, OR).
- **Spell out statistical terms when used as nouns in running text** (`S.spell-out-statistics`). Write "the mean was 4.2" not "the *M* was 4.2." Use the symbol form inside parentheses: (*M* = 4.2, *SD* = 1.1).
- **Do not repeat in text what a table already shows** (`S.no-table-repetition`). Highlight key findings and refer the reader to the table for full results.

## Figures, Tables, and Cross-References

- **Capitalize cross-references** (`S.capitalize-cross-references`). Write "Section 3", "Figure 2", "Table 1", never lowercase.
- **Captions must be specific** (`S.specific-captions`). "Overview of our approach" says nothing. State what is shown: "Distribution of response times by participant group." Do not editorialize. Save interpretation for the text.
- **Refer to every figure and table in the text** (`S.refer-to-every-figure`). If a figure or table is not discussed in the body, it does not belong in the paper.
- **Number figures and tables sequentially** (`S.sequential-numbering`). Do not skip numbers or reuse them.

## Threats to Validity

- **Be specific to your study** (`S.specific-threats`). Name the specific bias, explain why it applies here, and describe the mitigation. Do not write generic threats that apply to any study of the same type.
- **No performative hedging** (`S.no-performative-hedging`). If a threat is real, explain the mitigation. If it is not real, leave it out.

## Self-Check Before Presenting Text (scientific)

Apply these in addition to the general-layer self-check:

1. **"Significant" audit** (`S.significant`). If any use of "significant / significantly / significance" is not reporting a statistical test, replace it.
2. **Citation clusters** (`S.citation-clusters`). Verify that any citation cluster with three or more references explains what each cited work contributes.
3. **Grounding** (`S.ground-claims`). Verify that each claim attributed to a citation is supported by the cited work, not just plausibly associated with it. Read the whole paper where its full text is available, not just the abstract.
4. **Related work tone** (`S.analyze-prior-work`). Scan for complimentary language ("seminal," "pioneering," "impressive") that describes prior work without analyzing it. Rewrite to be analytical.
5. **Threats specificity (if applicable)** (`S.specific-threats`). Verify that each threat names a specific risk to this study and describes a concrete mitigation. Remove generic threats.
6. **Verb tense consistency** (`S.tense-by-section`, `S.paper-vs-study`). Check the tense of every clause with a citation or author name as its subject: an empirical action a cited study performed takes past or present perfect, not present. Do not clear a section from its dominant tense alone. A present-tense prior-work clause can sit inside an otherwise-correct section. Fix unmotivated tense shifts within a paragraph.
7. **Statistical formatting** (`S.exact-p-values`, `S.effect-sizes`, `S.leading-zeros`, `S.italic-symbols`). Verify exact *p*-values (not *p* < 0.05 unless *p* < 0.001), check that effect sizes accompany *p*-values, confirm leading zeros before all decimal values, and verify that statistical symbols are italicized where required.
8. **Figure and table captions** (`S.specific-captions`). Rewrite vague captions ("Overview of our approach," "Experimental results") to state what the figure or table actually shows.
9. **Cross-section redundancy** (`S.no-restatement`). Scan for method details, findings, or formal introductions of supplementary resources stated in full in more than one section. Replace duplicated content with a cross-reference to the section where it is first stated.
10. **Reference verification** (`S.verify-references`, `S.no-invented-fields`). Verify each reference against a reliable source (DBLP, the publisher page via DOI, or the actual paper). Confirm author names, title, year, and venue. Omit any field that cannot be confirmed.
11. **Abstract independence** (`S.body-independent`). Verify that the body re-introduces every term, acronym, abbreviation, definition, or notation first seen in the abstract, at its first body occurrence (any section). The body must read completely without the abstract. Do not flag these re-introductions as redundant.
