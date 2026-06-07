# Writing rules — scientific layer

This layer adds conventions for empirical research articles on top of
`rules-general.md`. Load it together with the general layer when reviewing or
writing a paper; add `rules-latex.md` on top when the source is LaTeX. The
rules here draw on APA style (7th ed.) and IEEE/ACM conventions for SE
publications. The justification behind the rules lives in `rules-rationale.md`,
which the skills do not load.

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
- "keyed to" (use "specific to" or "for")
- "a growing body of work" (cite the actual works)
- "recent studies suggest" (say who found what)

## The word "significant"

**"Significant" requires special care.** In empirical SE, "significant" has a precise statistical meaning. Using it as a generic intensifier ("a significant contribution," "significant improvements") creates ambiguity about whether a statistical test was performed. Reserve "significant / significantly / significance" for reporting statistical results (e.g., "statistically significant at *p* < 0.05"). For non-statistical emphasis, use large, substantial, considerable, or important.

## Voice

- **Use "we" consistently.** First-person plural throughout.

## Verb Tense by Section

Verb tense varies by section. The table below follows APA conventions and standard practice in empirical SE:

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

## Structure

- **No lists in prose.** Use running text, not bullet points, in the paper body. Tables and figures handle structured data.
- **Avoid restatement across sections.** Do not restate method details in Results, repeat findings verbatim in Discussion, recap the same motivation in both Introduction and Related Work, or formally re-introduce the same supplementary package (replication material, appendix) across multiple sections. State each once and cross-reference it. References to specific contents of an already-introduced resource (e.g., "the full codebook is in Appendix B") are fine.

## Citations

- **No vague citation clusters.** Never write "several studies have shown [1,2,3,4,5]" or "prior work has found [X to Z]." If citing more than two works together, state what each contributes. A citation that does not tell the reader why it is there is dead weight.
- **Cite, do not gesture.** Replace "a growing body of work" with the actual works. Replace "recent studies suggest" with who found what.
- **Ground every claim you attribute to a citation.** Verify the cited work actually says what you claim. Read the relevant section, not just the abstract.
- **Avoid citations in the abstract.** ACM, EMSE, and many IEEE-journal author guidelines prohibit references in abstracts; the abstract is intended to stand alone without bibliographic dependencies. When a proposed rewrite tempts a reference into the abstract, rephrase to drop it — the underlying claim can move to the introduction. Check the venue's author guidelines before adding any reference to an abstract; the safe default is to keep abstracts citation-free.
- **Re-introduce acronyms in the body, even if defined in the abstract.** The abstract is self-contained — readers, indexers, and search engines may consume it independently of the paper — so any acronym it introduces is local to that abstract. Define the acronym again on its first occurrence in the body (typically in the introduction). Do not flag a second `Term (TLA)` in the body as redundant when the first occurrence sits in the abstract; that re-definition is required, not a duplication.

## Related Work

- **Analyze, do not compliment.** Say what prior work did, how it relates to this paper, and where gaps remain. No book-jacket blurbs ("X et al. present a comprehensive framework for...").
- **State the gap you fill.** Every related work discussion should make clear why the cited work leaves room for the current paper.

## References

- **Verify every reference.** AI-generated references frequently contain wrong years, wrong venues, invented page numbers, or hallucinated DOIs. Check each one against a reliable source (DBLP, the publisher page via DOI, or the actual paper) before it goes into the manuscript.
- **Do not invent fields.** If a bibliographic field (e.g., pages, volume) cannot be confirmed, omit it. A missing field is better than a wrong one.

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

- **Capitalize cross-references.** Write "Section 3", "Figure 2", "Table 1", never lowercase.
- **Captions must be specific.** "Overview of our approach" says nothing. State what is shown: "Distribution of response times by participant group." Do not editorialize; save interpretation for the text.
- **Refer to every figure and table in the text.** If a figure or table is not discussed in the body, it does not belong in the paper.
- **Number figures and tables sequentially.** Do not skip numbers or reuse them.

## Threats to Validity

- **Be specific to your study.** Name the specific bias, explain why it applies here, and describe the mitigation. Do not write generic threats that apply to any study of the same type.
- **No performative hedging.** If a threat is real, explain the mitigation. If it is not real, leave it out.

## Self-Check Before Presenting Text (scientific)

Apply these in addition to the general-layer self-check:

1. **"Significant" audit.** If any use of "significant / significantly / significance" is not reporting a statistical test, replace it.
2. **Citation clusters.** Verify that any citation cluster with three or more references explains what each cited work contributes.
3. **Grounding.** Verify each claim attributed to a citation is supported by the cited work, not just plausibly associated with it.
4. **Related work tone.** Scan for complimentary language ("seminal," "pioneering," "impressive") that describes prior work without analyzing it. Rewrite to be analytical.
5. **Threats specificity (if applicable).** Verify each threat names a specific risk to this study and describes a concrete mitigation. Remove generic threats.
6. **Verb tense consistency.** Check that each section uses the tense prescribed by the verb-tense table. Fix unmotivated tense shifts within a paragraph.
7. **Statistical formatting.** Verify exact *p*-values (not *p* < 0.05 unless *p* < 0.001), check that effect sizes accompany *p*-values, confirm leading zeros before all decimal values, and verify that statistical symbols are italicized where required.
8. **Figure and table captions.** Rewrite vague captions ("Overview of our approach," "Experimental results") to state what the figure or table actually shows.
9. **Cross-section redundancy.** Scan for method details, findings, or formal introductions of supplementary resources stated in full in more than one section. Replace duplicated content with a cross-reference to the section where it is first stated.
10. **Reference verification.** Verify each reference against a reliable source (DBLP, the publisher page via DOI, or the actual paper). Confirm author names, title, year, and venue. Omit any field that cannot be confirmed.
