# Writing rules — LaTeX layer

This layer adds mechanics for LaTeX source on top of `rules-general.md` and
`rules-scientific.md`. Load all three when reviewing or editing a `.tex`
manuscript; the rules here cover markup that only exists in LaTeX, and several
of them are the LaTeX expression of a principle stated more generally in a lower
layer. The justification behind the rules lives in `rules-rationale.md`, which
the skills do not load.

## Quotation marks

- **LaTeX quotation marks.** Use LaTeX-style quotes, not straight `"` or `'`. Double quotes: <code>``...''</code> (two backticks to open, two apostrophes to close). Single quotes: <code>`...'</code> (one backtick to open, one apostrophe to close). Straight quotes render as two closing quotes in typeset output.

## Caption punctuation

- **Caption punctuation: `.` by default, `:` before a list or continuation.** Run-in paragraph captions — `\paragraph{Title.}`, `\subparagraph{Title.}`, and the LaTeX-template pattern `\textbf{Title.}` used to lead a paragraph — end with a period by default. The caption is a self-contained label, and the body that follows is a separate sentence on the captioned topic. Substitute a colon when the caption grammatically introduces what follows: a list (`itemize` / `enumerate` / a `(1) … (2) … (3) …` numbered structure), a definition or paraphrase that completes the caption's phrase, or a run of examples. AI text systematically defaults to `.` here. Display headings (`\section{}`, `\subsection{}`, `\subsubsection{}`) usually take no terminal punctuation.

## Cross-references

- **Use cross-reference macros.** This is the LaTeX expression of the scientific layer's **Capitalize cross-references** rule. Use `\autoref{}` with capitalized autoref names, or explicit references like `Section~\ref{sec:...}`, never lowercase "section 3". Cross-reference repeated content with `\autoref{}` or an explicit `\ref{}` rather than restating it (the **Avoid restatement across sections** rule). Forward references to later sections are fine as `\autoref{}` / `\Cref{}` pointers.

## Citations

- **Prefer `\citeauthor{}` over spelled-out author names.** When referring to authors in running text, use `\citeauthor{key}` (and `\citeyear{key}` where a year is needed) rather than typing names directly. This keeps author names synchronized with the BibTeX entry and avoids spelling or ordering errors. Write `\citeauthor{smith2020}` instead of "Smith et al." The same applies to possessives (`\citeauthor{smith2020}'s framework`) and first-mention full forms.
- **Leave a grounding comment on every new citation.** This is the LaTeX mechanism for the scientific layer's **Ground every claim you attribute to a citation** rule. Add a LaTeX comment (`% GROUNDING: "..."`) after the `\cite{}` with a direct quote supporting the claim. These comments leave an audit trail for co-authors. A review always lists every `\cite{}` still missing a `% GROUNDING:` comment as a grounding to-do, and revise inserts `% GROUNDING: TODO verify <key>` stubs for the author to fill.

## Editorial comments

- **Keep metacommentary in comment-commands.** This is the LaTeX placement for the general layer's **No author-voice metacommentary** rule. Author-voice asides and notes-to-self belong inside editorial comment-commands (`\todo{}`, `\sba{}`, `\as{}`) or `%` comments, where they do not render, rather than in body text.

## BibTeX

- **Verify every entry.** AI-generated BibTeX entries frequently contain wrong years, wrong venues, invented page numbers, or hallucinated DOIs. Every entry must be checked against a reliable source before it goes into the `.bib` file. A review runs an automated reference check (CrossRef by DOI then title, DBLP by title) that flags unresolvable DOIs and title/year/venue mismatches; its output is advisory — confirm before acting, and never call a reference fabricated from eyeballing.
- **Source priority.** (1) DBLP, if the work appears there. DBLP entries are curated and consistently formatted. (2) The publisher page, if a DOI is provided; resolve the DOI and pull metadata from the landing page. (3) Google Scholar or a general web search as a last resort, cross-checked against the actual paper.
- **Check at minimum.** Author names and ordering, title (exact, including capitalization in the original), year, venue name (full and abbreviated), volume / number / pages, and DOI.
- **Do not invent fields.** If a field (e.g., pages, volume) cannot be confirmed, omit it. A missing field is better than a wrong one.

## Self-Check Before Presenting Text (LaTeX)

Apply these in addition to the general- and scientific-layer self-checks:

1. **Caption punctuation.** For every `\paragraph{}`, `\subparagraph{}`, and run-in `\textbf{}` caption, check what immediately follows. If the body is a separate sentence on the captioned topic, the caption ends with `.`; if it introduces a list, a numbered structure (`(1) … (2) … (3) …`), or a clause that grammatically completes the caption, it ends with `:`. AI defaults to `.` here regardless of context. Display headings (`\section{}`, etc.) usually take no terminal punctuation.
2. **LaTeX quotation marks.** Replace straight `"` and `'` with <code>``...''</code> and <code>`...'</code>.
3. **Cross-reference macros.** Verify cross-references are capitalized and use `\autoref{}` / `\ref{}` / `\Cref{}`, not lowercase or hard-coded numbers.
4. **Author names.** Replace spelled-out author names in running text with `\citeauthor{}` (and `\citeyear{}` where a year is needed).
5. **Grounding comments.** List every `\cite{}` that lacks a `% GROUNDING: "..."` comment as a grounding to-do (always, not conditionally); a complete grounding comment carries a direct quote from the cited paper.
6. **Metacommentary placement.** Move any author-voice aside or note-to-self out of body text into a `\todo{}` / `\sba{}` / `%` comment.
7. **BibTeX verification (if applicable).** Verify each entry against DBLP (preferred), the publisher page via DOI, or Google Scholar. Confirm author names, title, year, venue, and DOI. Omit any field that cannot be confirmed. Run `verify_references.py` to flag unresolvable DOIs and metadata mismatches; sanity-check before treating an entry as fabricated.
