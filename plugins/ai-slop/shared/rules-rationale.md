# Rationale for the writing rules

This file records the *why* behind the rules in the three rule layers
(`rules-general.md`, `rules-scientific.md`, `rules-latex.md`). It is
documentation only. The `ai-slop:review`, `ai-slop:review-diff`, and
`ai-slop:init` skills load the layers that their scope calls for plus the trope
catalog by explicit path. `ai-slop:revise` and `ai-slop:ground` reference only
the layers (revise applies a finished report, so it needs no trope source, and
ground reads the LaTeX layer's grounding convention). None of them read this
file. Keeping the
justification here lets the layers carry only the operative directive, example,
and exception for each rule, while the explanatory background that does not
change how a rule is applied lives in one place a maintainer can consult.

Not every rule has an entry. The mechanical rules carry their own short
justification in the layer or need none. When a rule with an entry here
changes, update both: the directive in the relevant layer and the
justification here. The sections below are grouped by topic. Each topic lives in
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
sources. The rule layers carry only the additions beyond that catalog.

## Language

- **American English** (`G.american-english`). SE venues expect it. Co-authors and locale-misconfigured
  spell-checkers are the usual source of British spellings, so the check targets
  imported drift rather than original prose.
- **"Data" as singular** (`G.data-singular`). Both the singular and plural agreement are accepted in
  style guides. The project fixes one form so the manuscript reads consistently.
  The choice is conventional, not grammatical.
- **"Such as" over "like."** (`G.such-as`). `Like` is colloquial when introducing examples.
  `Such as` is the academic register. `Like` stays correct as a verb and in
  deliberate similes.

## Restricted words

The listed words (`G.restricted-words`) are legitimate in academic SE writing but appear far more often
in AI-generated text than in human prose, which is what makes a paragraph read
as machine-written even when no single word is wrong. The table gives plainer
substitutes so each remaining use is a deliberate choice.

"Significant" is singled out because in empirical work it carries a precise
statistical meaning. Used as a generic intensifier it creates ambiguity about
whether a statistical test was actually run, so it is reserved for reporting
statistical results.

"Navigate" is restricted only in its metaphorical sense (navigating complexity, challenges, or a landscape), the pattern that reads as AI prose. Its literal sense, moving through a UI, website, menu, or file tree, is precise and not flagged. "Worked example" sits in the phrases-to-avoid list because the "worked" qualifier is usually empty padding that "example" already carries, with the lone exception of a fully solved problem presented step by step.

The **Plain, literal language** (`G.plain-language`) rules (`G.plain-language`) extend the same logic from single listed words to three classes the table cannot enumerate: invented compounds and verb-to-noun coinages, colorful or insider synonyms for plain words, and figurative language. A closed list cannot catch these because the offenders are unbounded, so the rules state a test (keep the word only for precision the plain form loses) and carry a short seed list for recall. The seed list also guards against the reviewer sharing the writer's blind spot. A literal match flags a known word even when the prose reads fine to a model with the same habit.

## Terminology consistency

What reads as elegant variation in literary writing creates ambiguity in
technical writing. A reader who sees "code review," "code inspection," and
"review process" cannot tell whether these name one concept or three. One term
per concept (`G.one-term`) removes the doubt.

## Reference and clause boundaries

Both rule sections target one asymmetry. A model resolves a pronoun, a
summarizing noun, a definite article, a stand-in word, or a dropped *that*
against its whole context, where every candidate antecedent and the intended
category are equally present. A reader has the surface text and a window of one
or two sentences. Function words and head nouns are redundancy for the reader's
benefit, and a generator tuned for fluency and concision strips redundancy.

- **Reference** (`G.anchor-pronouns`, `G.summarizing-nouns`, `G.definite-article`). Bare *This* is what joins a claim to the comment on it ("This
  highlights..."). The head noun requires an editorial choice the bare form
  defers. *It* over the repeated noun follows general anti-repetition advice the
  terminology rule already rejects. Distance costs attention nothing, so an
  antecedent three sentences back is as available to the model as the previous
  clause. The mismatched summarizing noun ("such tools" after a list of tasks)
  is the same mechanism one level up. The noun names the category the writer had
  in mind, not the one the text instantiated. The first-mention *the* is the
  same again for articles. *The* claims the reader can already identify the
  thing, and the generator treats as already known whatever is fixed in its own
  plan. Two habits from the training data add to it, "the" before any noun
  followed by a purpose phrase ("the tools needed to ...") and the high rate of
  "the" in academic prose generally.
- **Stand-in words** (`G.stand-ins`). By the time the model reaches "among the ___" in "detect
  flaky tests among the generated ones", it has already committed to "detect
  flaky tests" and cannot go back to restructure the clause, so the only way
  left to avoid repeating *tests* is a stand-in at the current position. The
  advice not to repeat a word is enforced one token at a time, and "among the
  [adjective] ones" is itself a frequent chunk. A human editor rewrites the
  clause instead. The reader of the unedited version has to fetch the noun and
  work out the relation.
- **Explicit *that*** (`G.keep-that`). The zero form is standard in conversation and fiction and
  rare in academic prose (Biber et al., *Longman Grammar of Spoken and Written
  English*). Its appearance in formal text is a conversational default imported
  by the model, reinforced by the copyediting advice to cut *that*. The reader
  first takes "the effect" as the object of "show" and has to re-read once
  "persists" arrives.
- **Relative *whose* on things** (`G.whose-on-things`). *Whose* is the only relative pronoun that attaches
  a property of the head noun in one word. *With* needs a noun phrase for the
  property, a participle needs a verb that the head can take, and a conditional
  needs the sentence restructured from its start. Once the model has written
  "report only entries", the condition has to follow *entries*, and *whose* is
  the one form in that position that fits any property and any predicate, so
  it is selected for the same reason as a stand-in word above.
  Specifications, standards, and legal prose, all dense in the training data,
  use it the same way. Usage guides have accepted *whose* for things since
  Fowler, and the Longman Grammar's corpus counts (Biber et al.) show it as rare
  in every register, academic prose included, so the rule is a test per instance and a
  density signal rather than a ban. A human editor plans the sentence whole and
  makes the property the subject or uses a verb.

## Voice and verb tense

The tense table (`S.tense-by-section`, `S.paper-vs-study`) follows APA conventions and standard SE practice. The
paper-versus-study distinction (present tense for what the paper *is* and does,
past tense for empirical actions performed during the study) is what lets a
contributions list mix "we document" and "we analyzed" without inconsistency.
The paper exists in the reader's hands now, while the study happened in the past.

## Punctuation

Most punctuation rules target the same underlying phenomenon. AI text uses
mid-sentence pause marks (em dashes, colons, semicolons) far more than human
text, and restricting one mark merely displaces the load onto the others. The
primary test is per mark, asking whether each pause is genuinely the right choice, and the
per-page counts are a secondary signal of over-reliance, since a raw count
cannot tell a well-placed dash from a lazy one.

- **Em dashes** (`G.em-dashes`). An em dash (and the parenthesis it is often swapped for) usually
  signals a sentence that carries too much. Splitting into two sentences is the
  fix. The exceptions (comma-bearing appositives, nested-parenthesis avoidance,
  quoted material) are cases where the dash does structural work the commas or
  parentheses cannot, so they do not count as over-reliance.
- **Literal em-dash glyphs in source** (`G.em-dash-glyphs`). Word processors autocorrect `--` into `—`;
  code editors don't. So a literal `—` in Markdown, source, or `.tex` (where the
  em-dash is `---`) rarely comes from a human and usually marks pasted or
  generated text.
- **Colons** (`G.colons`). AI text defaults to colons for a generic mid-sentence pause and
  uses the colon-then-list shape reflexively, which is why both are flagged
  even when each individual colon is defensible.
- **Colon before a list or continuation** (`G.introducer-colon`). AI text systematically ends a list- or
  continuation-introducing clause with a period for three reinforcing reasons.
  Periods vastly outnumber colons after clause-final tokens in the training data.
  the visual break of a blank line or list markers lets a period feel complete on
  its own and substitutes for the colon's syntactic job. A period
  commits to nothing about what follows, which RLHF tends to reward. The mechanical
  test in the introducer-punctuation rule resolves each case without relying on
  this background.
- **Caption punctuation** (`L.caption-punctuation`). The run-in caption default (`.`, switching to `:` before
  a list or grammatical continuation) follows the same training-data bias toward
  the period.
- **Capitalization after a colon** (`G.colon-capitalization`). AI-generated prose reliably lowercases the first
  word after a colon regardless of whether a full sentence follows, so the
  project convention to capitalize after a sentence-completing colon catches a
  frequent tic.
- **Semicolons** (`G.semicolons`). Like colons and em dashes, semicolons become filler punctuation
  in AI text. Two sentences usually read more clearly.
- **Example/restatement connectives** (`G.connectives`). The pause-mark rules above tell the reviewer
  which marks to remove. This rule supplies the positive alternative they were
  standing in for. AI text tends to name a logical relation with a generic mid-sentence
  pause (a dash or colon) rather than the explicit connective, so `e.g.`/`such as` and
  `i.e.`/`that is`/`namely` are comparatively under-produced even though they are
  routine in academic prose. Recommending them where the mark introduces an example or
  a restatement therefore has two effects. It removes an over-used pause and restores
  a construction that AI text under-uses, and the under-use is itself a tell. The rule is deliberately
  dependent on meaning (illustrates vs. renames vs. sets up a payoff clause) so it does not
  become a mechanical dash-to-`e.g.` swap that merely shifts the load onto a new formula.
- **Sentence length** (`G.sentence-length`). AI text is detectable by its uniformity (roughly 15 to 25
  words per sentence, low burstiness), so deliberate variation is itself a signal
  of human editing.
- **Hyphenation of compound modifiers** (`G.compound-hyphens`). AI text over-hyphenates noun-noun stacks
  placed before another noun ("code-generation benchmarks"). The hyphen is needed
  only when dropping it invites a real misread, typically when one element
  is a participle that could re-attach as a verb.

## Structure

- **Formulaic openings and closings** (`G.no-formulaic-openings`, `G.no-formulaic-closings`). "In today's...", "In summary," and their
  kin are high-frequency AI scaffolding that adds no content. They are allowed
  only where they do genuine consolidating work.
- **Rule-of-three defaults** (`G.no-rule-of-three`). AI text groups items in threes by habit. The rule
  forces the count to match the actual number of items.
- **No list-cramming in a single sentence** (`G.no-list-cramming`). AI text maximizes information per
  sentence, flattening what should be several sentences into one colon- or
  dash-led chain of semicolon-joined clauses. The pile-up reads as machine prose
  and hurts the reader. Splitting restores burstiness and lets each claim carry
  its own citation cleanly. It also resolves the capitalization-after-a-colon
  edge case, where a colon introducing a series of independent clauses falls
  between the two halves of that rule (capitalize a sentence, lowercase a list).
  Once the clauses are separate sentences, the question does not arise.
- **One-sentence paragraphs** (`G.paragraph-length`). AI text breaks prose into one-sentence paragraphs
  for manufactured emphasis. They are kept only where a single sentence does
  structural work (opening a section, introducing a list or figure, marking a
  transition).
- **Concision** (`G.sentence-padding`, `G.paragraph-padding`). Sentence- and paragraph-level padding is a distinct failure from
  vagueness, inflated vocabulary, and cross-section redundancy. A phrase can be
  concrete, plainly worded, and unique to its location yet still spend more words
  than its content needs. The subtractive test (delete anything that can be
  removed at no cost to meaning, emphasis, or precision) is the shared diagnostic.
- **Section openers, generic truths, and evaluative sentences** (`G.paragraph-padding`). The windup rule
  targets a sentence that announces what its own paragraph then does. Read at
  section level it would remove every orienting paragraph, and style guides
  treat a heading followed directly by a subheading as poor form, so the rule
  names the section-opening paragraph as legitimate when it states the section's
  claim ("The two analyses for RQ2 disagree. This section explains why.") or
  carries what the headings do not. Generic-truth and evaluative sentences get
  the same density treatment as restricted words, hedges, and one-sentence
  paragraphs, a signal rather than a ban. One can open a section or mark that a
  result matters. Accumulation is the filler.
- **Reformulate, do not delete** (`G.reformulate`). The concision and hedging rules license
  deletion, which a model can over-apply by resolving any flagged statement
  through removal. This rule bounds that. Deletion is for content that says
  nothing, while substantive claims, examples, and qualifications are rewritten
  so the author's meaning survives the fix. Deleting a substantive statement is
  appropriate only on explicit author request.

## Citations

- **Grounding** (`S.ground-claims`, `L.grounding-comments`). AI-generated citations frequently misattribute claims, so each
  new citation carries a `% GROUNDING` comment with a supporting quote. The audit
  trail lets co-authors verify without re-reading the source. The grounding check
  reads the whole cited paper when its full text is available, not just the
  abstract. An abstract drops the caveats, scope conditions, and negative results
  that decide whether a claim is supported, so a sentence that matches the
  abstract can still misstate what the study found.
- **No citations in the abstract** (`S.no-abstract-citations`). Many ACM, EMSE, and IEEE author guidelines
  require the abstract to stand alone, so references move to the introduction.
- **The body must stand independent of the abstract** (`S.body-independent`). The abstract is read
  independently by readers, indexers, and search engines, and a body reader may
  skip it, so no section of the body can depend on it. Anything that the abstract
  introduces, whether an acronym, term, definition, or notation, must be introduced
  again at its first occurrence in the body. The re-introduction is required, not
  duplication, which is also why the abstract is exempt from the cross-section
  restatement rule. (Acronyms are the common case.)

## Numbers, statistics, figures, threats, and BibTeX

These sections are largely mechanical applications of APA 7th edition and
IEEE/ACM house style. The justification is conformance to those guidelines rather
than an AI-specific tic. Two exceptions: leading zeros before
decimals follow IEEE/ACM rather than APA, and BibTeX verification exists because
AI-generated entries frequently carry wrong years, venues, page numbers, or
hallucinated DOIs.
