# Reference checking and grounding — implementation plan

Status: **planned, not implemented.** This document records the agreed design for
two LaTeX-mode features so it can be picked up later.

1. Always surface a grounding to-do list (every `\cite{}` lacking a
   `% GROUNDING:` comment).
2. Harden the reference check so a review can catch hallucinated references
   (fabricated DOIs, wrong year/venue), not just missing BibTeX fields.

## Current state

- `find_citation_issues.py` already emits `missing-grounding` findings (a
  `\cite`-style call with no `% GROUNDING:` comment nearby). Today
  `review/SKILL.md` treats them as *informational* — "whether to ask the author
  to add `% GROUNDING:` comments is a project-internal decision" — so they are
  easy to skip.
- `check_bib_fields.py` only flags entries with **missing required fields**. It
  does not check whether field *values* are real.
- The `rules-latex.md` BibTeX rule and the `rules-scientific.md` reference rule
  instruct the writer to verify entries against DBLP/DOI, but nothing automates
  it.

## hallucite: what it is, and why ai-slop differs

The separate `hallucite` skill (se-uhd, read at v1.8.0) audits **other people's**
paper PDF files for fabricated references. Its design is deliberately heavy:

- Reference extraction is **non-LLM and deterministic** (the `hallucinator` pip
  package plus `pdftotext`), because a hallucination verdict is an accusation
  against named authors and must trace to tool output, never to an LLM reading a
  bibliography. Its first rule: **no script output ⇒ no verdict.**
- Verification runs against an **offline DBLP SQLite dump (~2.5 GB at
  `~/hallucite/dblp.db`)** plus CrossRef, arXiv, OpenAlex, and Semantic Scholar.
- Only the database-unconfirmed residue is sent to an LLM web-search triage step.
- It needs Python 3.12, the `hallucinator` package, the DBLP dump, and a
  provisioned venv.

ai-slop's situation is different: it checks **your own** paper, where the `.bib`
or `.bbl` is in hand and trusting the LLM to extract and reason about references
is acceptable (you are the author, not a program-committee reviewer). So ai-slop
**borrows hallucite's principles, not its machinery**: it stays self-contained
(stdlib + optional network), uses the LLM for extraction, and points users to
`hallucite` for the rigorous adversarial audit of submissions under review.

## Phase 1 — always-on grounding to-do list

Small; no new code (the data already exists).

- `review/SKILL.md` step 6 and the report template: add an always-emitted
  **"Grounding to-do"** subsection listing every ungrounded `\cite{}` as
  `file:line — <keys>`. Drop the "informational / project decision" hedge.
- `rules-latex.md`: reword the grounding rule and its self-check item so a LaTeX
  review always produces the list.
- `review-diff/SKILL.md`: same, scoped to changed `\cite{}` calls.
- `revise` always inserts `% GROUNDING: TODO verify <key>` stubs after the
  ungrounded cites as part of applying the grounding to-do — these are TODO
  markers for the author to fill in, never fabricated quotes.

## Phase 2 — reference verification (LLM-assisted + lightweight script)

- **Extraction: LLM.** Reuse `check_bib_fields.py`'s brace-counting parser for
  structured entries; the LLM resolves the rest from the paper's own source. No
  `hallucinator` dependency, no non-LLM extractor — that is hallucite's job.
- **`scripts/verify_references.py` (stdlib; queries online when a network is reachable, skips the lookups when it is not):**
  - DOI present → CrossRef (`api.crossref.org/works/{doi}`, polite `--mailto`).
    A `404` is `doi-not-found` (likely fabricated); otherwise compare normalized
    title, year, and venue → `ok` / `title-mismatch` / `year-mismatch` /
    `venue-mismatch`.
  - No DOI → DBLP search API (`dblp.org/search/publ/api`) plus CrossRef title
    search; no close match → `not-found`.
  - Any network failure → `unchecked-offline` for that entry; exit 0 — no
    network means the lookups are skipped, not that the run fails (the same way
    `fetch_tropes.py` falls back to the bundled snapshot).
  - Output `<key>\t<verdict>\t<detail>` plus a one-line stderr summary, matching
    the other scripts. Bound the number of network calls and cache by DOI/title
    within a run; `log` whatever was skipped (no silent caps).
  - **Pure `compare_entry(bib, record) -> verdict` split from the fetch layer**
    so smoke tests assert the comparison logic against fixture records with **no
    network** (match, year-mismatch, title-mismatch, no-DOI, injected-offline).
- **Canonical source: DBLP BibTeX is the gold standard.** When the work appears
  in DBLP, treat its curated BibTeX as the authoritative metadata for matching
  and for any suggested correction — DBLP is hand-curated and consistently
  formatted for CS/SE venues. Exception: DBLP sometimes holds only a preprint
  (arXiv/CoRR) for a paper that has since appeared at a venue; when the
  authoritative published version's metadata is available via the publisher/DOI
  (CrossRef), prefer that over DBLP's preprint record.
- **Optional offline DBLP dump (opt-in, never automatic):** if a local DBLP
  database is present (check `$AI_SLOP_DBLP`, and reuse `$HALLUCITE_DBLP` if the
  user already has hallucite's), use it for speed and offline coverage;
  otherwise **offer** to download or build one, but never pull multiple GB
  unprompted. When downloaded, write it into the paper repo (the working
  directory) so the author sees it and can delete it later, and add it to
  `.gitignore` so it is never committed.
- **Web-search fallback (LLM):** references that no database confirms get an LLM
  web-search pass to validate — the analogue of hallucite's triage stage.
- **"Never fabricate a verdict" principle, borrowed:** the report says *"could
  not confirm"* (advisory, sanity-check). It calls a DOI fabricated only when
  CrossRef actually returns `404`. No hallucination claims from eyeballing.

## Phase 3 — optional

- Richer venue matching (preprint vs published, abbreviation handling).
- Maintainer recipe for building or refreshing a local DBLP dump.

## Decisions made

- **Network policy:** auto online lookups when a network is reachable, skipped
  (entries marked `unchecked-offline`) when it is not; the DBLP dump download is
  opt-in only.
- **Reuse vs build:** a light in-repo check with LLM extraction; do not depend on
  `hallucite` or `hallucinator`; point to `hallucite` for adversarial audits.
- **Canonical metadata:** DBLP BibTeX is the gold standard when present; fall
  back to publisher/DOI metadata when DBLP holds only a preprint of a paper that
  has since been published.
- **Never commit generated artifacts:** the review's `ai-slop-report.md` and any
  downloaded DBLP dump live in the paper repo but must be added to `.gitignore`
  and never committed.
- **Scope:** Phase 1 first; Phase 2 after; Phase 3 optional.

## Files to touch (when implemented)

- New `scripts/verify_references.py` and its smoke tests.
- `review/SKILL.md` (step 6 + report template), `review-diff/SKILL.md`.
- `rules-latex.md` (BibTeX rule, grounding rule, self-checks) and
  `rules-scientific.md` ("verify every reference").
- `README.md` (dependencies note about optional outbound API use; repository
  layout) and the maintainer notes.
- Version bump.
