# Rationale for the writing rules

This file records the *why* behind the rules in the three rule layers
(`rules-general.md`, `rules-scientific.md`, `rules-latex.md`). It is
documentation only: the `ai-slop:review`, `ai-slop:review-diff`, `ai-slop:init`,
and `ai-slop:revise` skills load the layers their scope calls for (and the trope
catalog) by explicit path, and none of them read this file. Keeping the
justification here lets the layers carry only the operative directive, example,
and exception for each rule, while the explanatory background that does not
change how a rule is applied lives in one place a maintainer can consult.

When a rule changes, update both: the directive in the relevant layer and the
justification here. The sections below are grouped by topic; each topic lives in
the general layer (any prose), the scientific layer (research articles), or the
LaTeX layer (markup mechanics), and several cross-cutting topics state a
principle in a lower layer and its mechanics in the LaTeX layer.

## Sources

The rules draw on three bodies of evidence:

- Empirical studies of AI-to-human word-frequency ratios, which identify the
  vocabulary, transitions, and punctuation marks that large language models
  over-produce relative to human authors.
- APA style (7th edition), for number formatting, statistical reporting, and
  verb tense by section.
- IEEE and ACM author conventions for software-engineering venues, which take
  precedence over APA wherever the two diverge (most visibly on leading zeros
  before decimals).

The general AI-trope catalog (banned words, formulaic openings, formatting
tics, anaphora and tricolon abuse) is fetched at runtime from the upstream
sources; the rule layers carry only the additions beyond that catalog.

## Language

- **American English.** SE venues expect it; co-authors and locale-misconfigured
  spell-checkers are the usual source of British spellings, so the check targets
  imported drift rather than original prose.
- **"Data" as singular.** Both the singular and plural agreement are accepted in
  style guides. The project fixes one form so the manuscript reads consistently;
  the choice is conventional, not grammatical.
- **"Such as" over "like."** `Like` is colloquial when introducing examples;
  `such as` is the academic register. `Like` stays correct as a verb and in
  deliberate similes.

## Restricted words

The listed words are legitimate in academic SE writing but appear far more often
in AI-generated text than in human prose, which is what makes a paragraph read
as machine-written even when no single word is wrong. The table gives plainer
substitutes so each remaining use is a deliberate choice.

"Significant" is singled out because in empirical work it carries a precise
statistical meaning. Used as a generic intensifier it creates ambiguity about
whether a statistical test was actually run, so it is reserved for reporting
statistical results.

"Navigate" is restricted only in its metaphorical sense (navigating complexity, challenges, or a landscape), the pattern that reads as AI prose. Its literal sense, moving through a UI, website, menu, or file tree, is precise and not flagged. "Worked example" sits in the phrases-to-avoid list because the "worked" qualifier is usually empty padding that "example" already carries, with the lone exception of a fully solved problem presented step by step.

## Terminology consistency

What reads as elegant variation in literary writing creates ambiguity in
technical writing: a reader who sees "code review," "code inspection," and
"review process" cannot tell whether these name one concept or three. One term
per concept removes the doubt.

## Voice and verb tense

The tense table follows APA conventions and standard SE practice. The
paper-versus-study distinction (present tense for what the paper *is* and does,
past tense for empirical actions performed during the study) is what lets a
contributions list mix "we document" and "we analyzed" without inconsistency:
the paper exists in the reader's hands now, while the study happened in the past.

## Punctuation

Most punctuation rules target the same underlying phenomenon: AI text leans on
mid-sentence pause marks (em dashes, colons, semicolons) far more than human
text, and restricting one mark merely displaces the load onto the others. The
primary test is per mark — is each pause genuinely the right choice? — and the
per-page counts are a secondary signal of over-reliance, since a raw count
cannot tell a well-placed dash from a lazy one.

- **Em dashes.** An em dash (and the parenthesis it is often swapped for) usually
  signals a sentence trying to do too much; splitting into two sentences is the
  fix. The carve-outs (comma-bearing appositives, nested-parenthesis avoidance,
  quoted material) are cases where the dash does structural work the commas or
  parentheses cannot, so they do not count as over-reliance.
- **Colons.** AI text falls back to colons for a generic mid-sentence pause and
  reaches for the colon-then-list shape reflexively, which is why both are flagged
  even when each individual colon is defensible.
- **Introducer punctuation (`:` not `.`).** AI text systematically ends a list- or
  continuation-introducing clause with a period for three reinforcing reasons:
  periods vastly outnumber colons after clause-final tokens in the training data;
  the visual break of a blank line or list markers lets a period feel complete on
  its own and quietly substitutes for the colon's syntactic job; and a period
  commits to nothing about what follows, which RLHF tends to reward. The mechanical
  test in the introducer-punctuation rule resolves each case without relying on
  this background.
- **Caption punctuation.** The run-in caption default (`.`, switching to `:` before
  a list or grammatical continuation) follows the same training-data bias toward
  the period.
- **Capitalization after a colon.** AI-generated prose reliably lowercases the first
  word after a colon regardless of whether a full sentence follows, so the
  project convention to capitalize after a sentence-completing colon catches a
  frequent tic.
- **Semicolons.** Like colons and em dashes, semicolons become filler punctuation
  in AI text; two sentences usually read more clearly.
- **Sentence length.** AI text is detectable by its uniformity (roughly 15 to 25
  words per sentence, low burstiness), so deliberate variation is itself a signal
  of human editing.
- **Hyphenation of compound modifiers.** AI text over-hyphenates noun-noun stacks
  placed before another noun ("code-generation benchmarks"). The hyphen earns its
  place only when dropping it invites a real misread, typically when one element
  is a participle that could re-attach as a verb.

## Structure

- **Formulaic openings and closings.** "In today's...", "In summary," and their
  kin are high-frequency AI scaffolding that adds no content; they are allowed
  only where they do genuine consolidating work.
- **Rule-of-three defaults.** AI text groups items in threes by habit; the rule
  forces the count to match the actual number of items.
- **No list-cramming in a single sentence.** AI text maximizes information per
  sentence, flattening what should be several sentences into one colon- or
  dash-led chain of semicolon-joined clauses. The pile-up reads as machine prose
  and hurts the reader; splitting restores burstiness and lets each claim carry
  its own citation cleanly. It also resolves the capitalization-after-a-colon
  edge case, where a colon introducing a series of independent clauses falls
  between the capitalize-a-sentence and lowercase-a-list halves of that rule:
  once the clauses are separate sentences, the question does not arise.
- **One-sentence paragraphs.** AI text breaks prose into one-sentence paragraphs
  for manufactured emphasis. They are kept only where a single sentence does
  structural work (opening a section, introducing a list or figure, marking a
  transition).
- **Concision.** Sentence- and paragraph-level padding is a distinct failure from
  vagueness, inflated vocabulary, and cross-section redundancy: a phrase can be
  concrete, plainly worded, and unique to its location yet still spend more words
  than its content needs. The subtractive test (delete anything whose removal
  costs no meaning, emphasis, or precision) is the shared diagnostic.
- **Reformulate, do not delete.** The concision and hedging rules license
  deletion, which a model can over-apply by resolving any flagged statement
  through removal. This rule bounds that: deletion is for content that says
  nothing, while substantive claims, examples, and qualifications are rewritten
  so the author's meaning survives the fix. Deleting a substantive statement is
  appropriate only on explicit author request.

## Citations

- **Grounding.** AI-generated citations frequently misattribute claims, so each
  new citation carries a `% GROUNDING` comment with a supporting quote; the audit
  trail lets co-authors verify without re-reading the source. The grounding check
  reads the whole cited paper when its full text is available, not just the
  abstract: an abstract drops the caveats, scope conditions, and negative results
  that decide whether a claim is supported, so a sentence that matches the
  abstract can still misstate what the study found.
- **No citations in the abstract.** Many ACM, EMSE, and IEEE author guidelines
  require the abstract to stand alone, so references move to the introduction.
- **The body must stand independent of the abstract.** The abstract is consumed
  independently by readers, indexers, and search engines, and a body reader may
  skip it, so no section of the body can depend on it. Anything the abstract
  introduces — an acronym, term, definition, or notation — must be introduced
  again at its first occurrence in the body; the re-introduction is required, not
  duplication, which is also why the abstract is exempt from the cross-section
  restatement rule. (Acronyms are the common case.)

## Numbers, statistics, figures, threats, and BibTeX

These sections are largely mechanical applications of APA 7th edition and
IEEE/ACM house style; the justification is conformance to those guidelines rather
than an AI-specific tic. The two exceptions worth noting: leading zeros before
decimals follow IEEE/ACM rather than APA, and BibTeX verification exists because
AI-generated entries frequently carry wrong years, venues, page numbers, or
hallucinated DOIs.
