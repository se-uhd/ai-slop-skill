# Writing rules: LaTeX layer

This layer adds mechanics for LaTeX source on top of `rules-general.md` and
`rules-scientific.md`. Load all three when reviewing or editing a `.tex`
manuscript. The rules here cover markup that only exists in LaTeX, and several
of them are the LaTeX expression of a principle stated more generally in a lower
layer. The rationale behind the contested rules lives in
`rules-rationale.md`, which the skills do not load.

## Quotation marks

- **LaTeX quotation marks** (`L.quotes`). Use LaTeX-style quotes, not straight `"` or `'`. Double quotes: <code>``...''</code> (two backticks to open, two apostrophes to close). Single quotes: <code>`...'</code> (one backtick to open, one apostrophe to close). Straight quotes render as two closing quotes in typeset output.

## Dashes

- **Em dashes are unspaced** (`L.unspaced-em-dashes`). Write `word---word` in LaTeX source, with no spaces around the `---`. The unspaced form is the American typographic convention, matching the general layer's **Use American English consistently** (`G.american-english`) rule. This rule governs spacing only. Whether a dash is the right mark at all is the general layer's **Em-dashes** (`G.em-dashes`) judgment, and the literal `—` glyph is covered there by **Literal em-dash glyphs in source** (`G.em-dash-glyphs`). Verbatim quotes keep their source's spacing.

## Caption punctuation

- **Caption punctuation** (`L.caption-punctuation`). Run-in paragraph captions end with a period by default. These are `\paragraph{Title.}`, `\subparagraph{Title.}`, and the LaTeX-template pattern `\textbf{Title.}` used to lead a paragraph. The caption is a self-contained label, and the body that follows is a separate sentence on the captioned topic. Substitute a colon when the caption grammatically introduces what follows: a list (`itemize` / `enumerate` / a `(1) ... (2) ... (3) ...` numbered structure), a definition or paraphrase that completes the caption's phrase, or a run of examples. AI text systematically defaults to `.` here. Display headings (`\section{}`, `\subsection{}`, `\subsubsection{}`) usually take no terminal punctuation.

## Cross-references

- **Use cross-reference macros** (`L.cross-reference-macros`). This rule is the LaTeX expression of the scientific layer's **Capitalize cross-references** (`S.capitalize-cross-references`) rule. Use `\autoref{}` with capitalized autoref names, or explicit references like `Section~\ref{sec:...}`, never lowercase "section 3". Cross-reference repeated content with `\autoref{}` or an explicit `\ref{}` rather than restating it (the **Avoid restatement across sections** (`S.no-restatement`) rule). Forward references to later sections are fine as `\autoref{}` / `\Cref{}` pointers.

## Citations

- **Prefer `\citeauthor{}` over spelled-out author names** (`L.citeauthor`). When referring to authors in running text, use `\citeauthor{key}` (and `\citeyear{key}` where a year is needed) rather than typing names directly. This keeps author names synchronized with the BibTeX entry and avoids spelling or ordering errors. Write `\citeauthor{smith2020}` instead of "Smith et al." The same applies to possessives (`\citeauthor{smith2020}'s framework`) and first-mention full forms.
- **Leave a grounding comment on every new citation** (`L.grounding-comments`). This rule is the LaTeX mechanism for the scientific layer's **Ground every claim you attribute to a citation** (`S.ground-claims`) rule. Add a LaTeX comment leading with the `% GROUNDING` marker after the `\cite{}` with a direct quote supporting the claim. Two key-placement forms are accepted and the tooling recognizes both: `% GROUNDING: "..."` (or `% GROUNDING: <key> -- "..."`), and `% GROUNDING <key>: "..."` with the key named before the colon. The per-key form is the better choice when one sentence cites several keys, since each key gets its own grounded quote on its own line. These comments leave an audit trail for co-authors. A review always lists every `\cite{}` still missing a grounding comment as a grounding to-do. Revise inserts `% GROUNDING: TODO verify <key>` stubs for the author to fill. `/ai-slop:ground` fills the comments outright. It fetches each cited source and inserts a retrieved verbatim quote (or a `TODO verify -- <reason>` stub when the source cannot be retrieved, never a quote from memory).

## Editorial comments

- **Keep metacommentary in comment-commands** (`L.editorial-comments`). This rule is the LaTeX placement for the general layer's **No author-voice metacommentary in published prose** (`G.no-metacommentary`) rule. Author-voice asides and notes-to-self belong inside editorial comment-commands (`\todo{}`, `\sba{}`, `\as{}`) or `%` comments, where they do not render, rather than in body text.

## BibTeX

- **Verify every entry** (`L.verify-bibtex`). This rule is the BibTeX expression of the scientific layer's **Verify every reference** (`S.verify-references`) rule. AI-generated BibTeX entries frequently contain wrong years, wrong venues, invented page numbers, or hallucinated DOIs. Every entry must be checked against a reliable source before it goes into the `.bib` file. A review runs an automated reference check (CrossRef by DOI then title, DBLP by title) that flags unresolvable DOIs and title/year/venue mismatches. Its output is advisory. Confirm before acting, and never call a reference fabricated on the basis of a visual check.
- **Source priority** (`L.source-priority`). (1) DBLP, if the work appears there. DBLP entries are curated and consistently formatted. (2) The publisher page, if a DOI is provided. Resolve the DOI and pull metadata from the landing page. (3) Google Scholar or a general web search as a last resort, cross-checked against the actual paper.
- **Check at minimum** (`L.check-fields`). Author names and ordering, title (exact, including capitalization in the original), year, venue name (full and abbreviated), volume / number / pages, and DOI.
- **Do not invent fields** (`L.no-invented-fields`). This rule restates the scientific layer's **Do not invent fields** (`S.no-invented-fields`) rule for the `.bib` file. If a field (e.g., pages, volume) cannot be confirmed, omit it. A missing field is better than a wrong one.

## Self-Check Before Presenting Text (LaTeX)

Apply these in addition to the general- and scientific-layer self-checks:

1. **Caption punctuation** (`L.caption-punctuation`). For every `\paragraph{}`, `\subparagraph{}`, and run-in `\textbf{}` caption, check what immediately follows. If the body is a separate sentence on the captioned topic, the caption ends with `.`. If it introduces a list, a numbered structure (`(1) ... (2) ... (3) ...`), or a clause that grammatically completes the caption, it ends with `:`. AI defaults to `.` here regardless of context. Display headings (`\section{}`, etc.) usually take no terminal punctuation.
2. **LaTeX quotation marks** (`L.quotes`). Replace straight `"` and `'` with <code>``...''</code> and <code>`...'</code>.
3. **Cross-reference macros** (`L.cross-reference-macros`). Verify cross-references are capitalized and use `\autoref{}` / `\ref{}` / `\Cref{}`, not lowercase or hard-coded numbers.
4. **Author names** (`L.citeauthor`). Replace spelled-out author names in running text with `\citeauthor{}` (and `\citeyear{}` where a year is needed).
5. **Grounding comments** (`L.grounding-comments`). List every `\cite{}` that lacks a grounding comment as a grounding to-do (always, not conditionally). A complete grounding comment leads with `% GROUNDING` (either `% GROUNDING: "..."` or `% GROUNDING <key>: "..."`) and carries a direct quote from the cited paper.
6. **Metacommentary placement** (`L.editorial-comments`). Move any author-voice aside or note-to-self out of body text into a `\todo{}` / `\sba{}` / `%` comment.
7. **BibTeX verification (if applicable)** (`L.verify-bibtex`, `L.check-fields`, `L.no-invented-fields`). Verify each entry against DBLP (preferred), the publisher page via DOI, or Google Scholar. Confirm author names, title, year, venue, and DOI. Omit any field that cannot be confirmed. Run `verify_references.py` to flag unresolvable DOIs and metadata mismatches; sanity-check before treating an entry as fabricated.
8. **Em-dash spacing** (`L.unspaced-em-dashes`). Replace spaced ` --- ` with unspaced `word---word`. Leave verbatim quotes as their source spaces them.
