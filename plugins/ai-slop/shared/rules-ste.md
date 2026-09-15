# Writing rules: STE layer

This layer is optional. A skill loads it on top of the other layers when it is
passed `--ste`. The layer applies part of ASD-STE100 Simplified Technical
English (STE), a controlled language first developed for aerospace maintenance
documentation. It leaves out the STE dictionary of approved words, keeps the
STE rules on sentences, voice, paragraphs, words, and articles, and changes the
STE rules on sentence length and style. The rationale behind the rules that a
reader might push back on is in `rules-rationale.md`, which the skills do not
load.

## Scope and precedence

- **Apply the layer to all prose you write or edit** (`T.scope`). The rules cover every natural-language text written or edited in STE mode: documents, code comments, commit messages, reports, and the replies that an assistant writes while it works under these rules. Quotations and literal strings are the exception (see `T.quotations` and `T.literals`).
- **Precedence over the other layers** (`T.precedence`). This layer adds to the general, scientific, and LaTeX layers and relaxes none of their rules. Where this layer and another layer set different limits for the same thing, the limit in this layer applies. **Use active voice** (`T.active-voice`) is such a case. It narrows the exceptions of **Prefer active voice** (`G.active-voice`).

## Sentences

- **Keep most sentences short** (`T.short-sentences`). Give each sentence one main idea. Put the subject and the main verb near the start, before any long opening phrase or clause. Split a sentence when the reader must hold several clauses in mind before the point arrives, as in "Because the parser, which the build loads before any test runs, accepts unterminated strings, the report can lose data." -> "The parser accepts unterminated strings, so the report can lose data. The build loads the parser before any test runs." Aim for 25 words or fewer. The count is approximate, so the target has a tolerance band. A sentence of 26 to 35 words stays when it has one main idea and the reader does not have to hold several clauses before its point. Split a sentence of more than 35 words at a clause boundary, or move a qualification into a sentence of its own. A quotation or a literal string counts as one word.
- **Vary sentence length** (`T.vary-length`). Put a short sentence next to a long one that builds an idea, for example a five-word sentence next to a 24-word one. Do not write several sentences of similar length in a row. Three consecutive sentences within 5 words of each other in length are a flag. The long sentence still follows the length band of **Keep most sentences short** (`T.short-sentences`).
- **Use active voice** (`T.active-voice`). Make the actor the subject, as in "The script writes the report," not "The report is written by the script." Use the passive voice only when the actor is unknown. **Prefer active voice** (`G.active-voice`) also allows the passive when the actor is irrelevant or when the passive reads better, and this layer drops both exceptions. In a research article, the actor of the study's actions is "we" (see `S.we`).

## Paragraphs

- **Cover one topic in each paragraph** (`T.one-topic`). When a paragraph moves to a second topic, split it where the topic changes, or move the sentences on the second topic to the paragraph that covers it. A split must not leave a stray one-sentence paragraph (see **Paragraph length** (`G.paragraph-length`)).

## Words

- **Give each word one meaning** (`T.one-meaning`). Once a word carries a meaning in a text, do not use it for a second meaning. A document that uses "run" for executing a test and for "a run of sentences" makes the reader work out which meaning applies each time. The same holds for "issue" as a GitHub issue and as a problem, or "check" as a verification step and as a checkbox. Choose another word for the second meaning. The rule is the other half of **Use one term for one concept** (`G.one-term`). Together they give each concept one term and each term one concept.
- **Replace nominalizations with verbs** (`T.verbs-not-nouns`). Write "decide," not "make a decision." Write "analyze the logs," not "perform an analysis of the logs," and "the parser validates the input," not "validation of the input is performed by the parser." A nominalization adds words and often hides the actor. Keep the noun when it names a thing rather than an action ("the decision log," "the installation guide") or when it is an established term ("code review"). The rule differs from the verbs-as-nouns part of **No invented compounds or verbs-as-nouns** (`G.no-coinages`), which targets a bare verb used as a noun ("the ask," "a write").
- **Keep articles** (`T.keep-articles`). Write "a," "an," and "the" wherever grammar requires one, including list items, table cells, captions, code comments, and commit messages. Write "Click the button to open the file," not "Click button to open file." A dropped article saves a word and leaves the reader to guess whether the noun refers to something new, to anything of its kind, or to something already mentioned. Which article to choose is the subject of **Definite article only for known referents** (`G.definite-article`).

## Style

- **Use one stylistic device per unit, at most** (`T.one-device`). A stylistic device is a metaphor, an aside, or a vivid sentence written for effect. A unit is one reply, one headed section, or one text without headings. Use at most one device in each unit, and keep the sentences around it plain. The limit narrows what the other layers permit and permits nothing new. A metaphor must still meet **No figurative language** (`G.no-figurative-language`), so the only metaphor allowed is one marked analogy that helps a reader understand an unfamiliar concept, never an idiom, a cliché, or personification. An aside must still meet **No author-voice metacommentary in published prose** (`G.no-metacommentary`). A parenthetical that expands an abbreviation, defines a term, or lists examples is not an aside.

## Text that stays as written

- **Leave quotations as written** (`T.quotations`). Do not paraphrase, shorten, or simplify quoted text, whether a quotation in running text, a block quotation, the quote in a `% GROUNDING` comment, or quoted program output. The rules apply to the sentence around a quotation, and the quotation counts as one word toward the length of that sentence.
- **Leave literal strings as written** (`T.literals`). Code, commands, file names, identifiers, configuration keys, URLs, and error messages stay exactly as they are. Do not add an article inside a literal string or replace a noun in it with a verb. A literal string counts as one word toward the length of its sentence.

## Editing existing text

- **Keep a sentence that a rewrite would weaken** (`T.keep-original`). When you edit existing text and the STE rewrite of a sentence loses meaning, precision, or force, keep the original sentence. Keep only the sentence at stake and rewrite its neighbors as usual. The other layers still apply to the kept sentence.

## Self-Check Before Presenting Text (STE)

Apply these in addition to the self-checks of the other layers in scope:

1. **Sentence length** (`T.short-sentences`, `T.quotations`, `T.literals`). Count the words in each sentence, with each quotation and literal string as one word. Split every sentence of more than 35 words. Split a sentence of 26 to 35 words when it has more than one main idea or makes the reader hold several clauses before its point.
2. **Length variation** (`T.vary-length`). If three consecutive sentences are within 5 words of each other in length, lengthen or shorten one of them. Check that each long sentence builds an idea and is next to a short sentence.
3. **Subject and verb first** (`T.short-sentences`). For each sentence that opens with a long phrase or clause, move the subject and the main verb forward. Split a sentence that makes the reader hold several clauses before its point.
4. **Voice** (`T.active-voice`). For each passive verb, make the actor the subject. Keep the passive only when the actor is unknown.
5. **Nominalizations** (`T.verbs-not-nouns`). Scan for a light verb followed by an action noun ("make a decision," "perform an analysis," "carry out a validation," "give an explanation") and for an action noun as the subject of a sentence. Replace each with the verb, unless the noun names a thing or is an established term.
6. **Articles** (`T.keep-articles`). Read list items, table cells, captions, code comments, and commit messages for a dropped "a," "an," or "the," and restore it.
7. **Paragraph topics** (`T.one-topic`). Name the topic of each paragraph in a few words. Split a paragraph that needs two names.
8. **Word meanings** (`T.one-meaning`). For each key word, check that it keeps one meaning through the text. Choose another word where it takes a second meaning.
9. **Stylistic devices** (`T.one-device`). Count the metaphors, asides, and vivid sentences in each unit. Keep at most one, and make the text around it plain.
10. **Quotations and literals** (`T.quotations`, `T.literals`). Compare each quotation and each literal string with its source, and undo any change.
11. **Kept sentences** (`T.keep-original`). For each sentence left in its original form, confirm that a rewrite would lose meaning, precision, or force. Rewrite the others.
