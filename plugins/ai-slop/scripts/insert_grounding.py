#!/usr/bin/env python3
r"""insert_grounding.py <extract.json> <quotes.json> [--dry-run]

Write grounding comments back into a LaTeX source, closing the loop that
extract_cites.py opens. It takes the extract JSON (citation sites) and a quotes
JSON (one result per cited key, produced by a grounding workflow) and inserts,
after each groundable cite line, a comment of the form

    % GROUNDING: <key> -- "<verbatim supporting quote>"

when a quote was retrieved, or

    % GROUNDING: <key> -- TODO verify -- <reason>

when it was not (reasons such as paywalled, abstract-only, book, not-found, or
source-does-not-support). The TODO form is the anti-fabrication guarantee: a
quote appears ONLY when the workflow actually retrieved the source text;
otherwise the comment records why it could not, for a human to resolve. This
script never invents a quote — it writes exactly what the quotes JSON carries.

quotes JSON schema — one entry per cited key, each with EITHER a quote OR a todo:

    {
      "smith2020": {"quote": "the exact sentence retrieved from the source"},
      "jones2019": {"todo": "paywalled"}
    }

A key absent from the quotes JSON is left untouched, so a run can ground a
subset and later runs can fill the rest (resumable over the still-TODO keys).

Behavior:
  - Only `groundable` sites (the cite macros find_citation_issues.py flags) are
    annotated; style-only \citeauthor / \citeyear sites are skipped.
  - Idempotent: a (line, key) that already has a quote-backed `% GROUNDING:`
    comment naming that key is left alone, so re-running is safe.
  - A quote-less `TODO verify` stub naming the key — planted by revise mode
    (`% GROUNDING: TODO verify <key>`) or by an earlier run of this script —
    does NOT count as grounded: it is replaced in place with the new comment,
    so a later grounding run can fill what a stub only marks. Replacing a stub
    with identical content is a no-op. A stub on the cite's own line is never
    edited (mid-line edits risk the code); the new comment is inserted below
    and the inline stub is left for the author to drop.
  - Each comment matches the cite line's indentation and is inserted on its own
    line directly after it (a `%` comment's trailing newline is consumed by
    LaTeX, so the surrounding markup still renders unchanged).
  - The cite line is re-checked against the file before editing; if the source
    moved since extraction (the line no longer holds that key) the site is
    skipped with a warning rather than edited blindly.
  - --dry-run prints what would change without writing.

A one-line summary is printed to stderr, with a per-reason breakdown of the
TODOs (source-does-not-support is called out — it flags a likely miscitation,
not merely an ungrounded claim). Exits 0 on success; 2 if an input JSON cannot
be read or parsed.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_scan import (  # noqa: E402
    CITE_PATTERN, is_grounding_comment, is_quote_grounding, iter_comment_block,
    parse_keys, split_code_and_comment,
)

# Characters that may appear inside a BibTeX key; used to bound the key when
# testing whether a comment already grounds it (so "smith2020" does not match
# inside "smith2020a").
KEYCHARS = r'A-Za-z0-9_:.\-+/'


def load_json(path, label):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except OSError as e:
        print(f"error: cannot read {label} {path!r}: {e.strerror or e}", file=sys.stderr)
        raise SystemExit(2)
    except ValueError as e:
        print(f"error: {label} {path!r} is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)


def comment_for(key, result):
    """Build the GROUNDING comment body (without indentation) for one key.
    Returns (text, kind) where kind is 'quote' or a TODO reason. A non-string or
    whitespace-only quote is treated as no quote and routed to a TODO, so an
    empty or malformed quote never crosses the anti-fabrication boundary into a
    `% GROUNDING: <key> -- ""` that falsely asserts a retrieved quote."""
    raw = result.get('quote')
    quote = ' '.join(raw.split()) if isinstance(raw, str) else ''  # one line, collapsed
    if quote:
        return f'% GROUNDING: {key} -- "{quote}"', 'quote'
    todo = result.get('todo')
    reason = ' '.join(todo.split()) if isinstance(todo, str) and todo.strip() else 'not-found'
    return f'% GROUNDING: {key} -- TODO verify -- {reason}', reason


def grounds_key(text, key):
    """True if `text` is a GROUNDING comment whose key field names `key`.
    Recognizes both `% GROUNDING: <key> -- "<quote>"` (the form this script
    writes) and `% GROUNDING <key>: "<quote>"` (the per-key form authors use when
    one sentence cites several keys, each grounded on its own line). Only the
    header (before the quote, the ` -- ` TODO separator, and a trailing
    key/quote-delimiter colon) is examined, so a key appearing inside a quote
    body does not count as already grounding that key — preserving resumability
    over still-ungrounded keys."""
    if not is_grounding_comment(text):
        return False
    header = text.split(' -- ', 1)[0].split('"', 1)[0].rstrip().rstrip(':')
    return re.search(rf'(?<![{KEYCHARS}]){re.escape(key)}(?![{KEYCHARS}])', header) is not None


def already_grounded(lines, idx, key):
    """True if the cite on line `idx` already has a quote-backed GROUNDING
    comment for `key`, either inline or in the attached comment block. A
    quote-less `TODO verify` stub for the key does NOT count: stubs are
    placeholders this script upgrades in place (see find_todo_stub), so
    treating them as grounded would permanently block the fill."""
    _, same_comment = split_code_and_comment(lines[idx])
    return any(grounds_key(text, key) and is_quote_grounding(text)
               for _, text in iter_comment_block(lines, idx, same_comment))


def find_todo_stub(lines, idx, key):
    """Return the index of the first quote-less GROUNDING comment line for
    `key` attached to the cite on line `idx`, or None. The cite's own line is
    excluded — an inline stub is never edited; the replacement logic only
    rewrites whole comment lines."""
    _, same_comment = split_code_and_comment(lines[idx])
    for j, text in iter_comment_block(lines, idx, same_comment):
        if j == idx:
            continue
        if grounds_key(text, key) and not is_quote_grounding(text):
            return j
    return None


def line_has_key(line, key):
    """True if a cite call on `line` (code portion) lists `key`."""
    code, _ = split_code_and_comment(line)
    for m in CITE_PATTERN.finditer(code):
        if key in parse_keys(m.group(2)):
            return True
    return False


def leading_ws(line):
    return line[:len(line) - len(line.lstrip())]


def plan_file(lines, sites, quotes, stats):
    """Return (inserts, replacements) for one file — {line_index: [comment
    lines]} of new comments to insert after a cite line, and {line_index: new
    line} of TODO-stub lines to rewrite in place — updating `stats` in place.
    Each site is a dict with line/keys/groundable."""
    inserts = {}
    replacements = {}
    for site in sites:
        if not site.get('groundable'):
            continue
        line_no = site.get('line')
        fpath = site.get('file', '?')
        if not isinstance(line_no, int):
            stats['skipped_moved'] += 1
            continue
        idx = line_no - 1
        if not (0 <= idx < len(lines)):
            stats['skipped_moved'] += 1
            print(f"warning: {fpath}:{line_no} is past end of file; skipped",
                  file=sys.stderr)
            continue
        indent = leading_ws(lines[idx])
        for key in dict.fromkeys(site.get('keys') or []):  # de-dupe, keep order
            result = quotes.get(key)
            if not isinstance(result, dict):
                stats['no_quote'] += 1  # absent key or malformed (non-object) value
                continue
            if not line_has_key(lines[idx], key):
                stats['skipped_moved'] += 1
                print(f"warning: {fpath}:{line_no} no longer cites "
                      f"{key!r}; skipped (source changed since extraction)",
                      file=sys.stderr)
                continue
            if already_grounded(lines, idx, key):
                stats['skipped_existing'] += 1
                continue
            body, kind = comment_for(key, result)
            stub_idx = find_todo_stub(lines, idx, key)
            if stub_idx is not None:
                new_line = leading_ws(lines[stub_idx]) + body
                if lines[stub_idx] == new_line:
                    stats['skipped_existing'] += 1  # stub already says exactly this
                    continue
                replacements[stub_idx] = new_line
                stats['replaced'] += 1
            else:
                inserts.setdefault(idx, []).append(indent + body)
            stats['inserted'] += 1
            if kind == 'quote':
                stats['quotes'] += 1
            else:
                stats['todos'] += 1
                stats['reasons'][kind] = stats['reasons'].get(kind, 0) + 1
    return inserts, replacements


def apply_changes(lines, inserts, replacements):
    """Apply replacements (index-stable) first, then insertions bottom-up so
    earlier insertions do not shift later indices."""
    for j, new_line in replacements.items():
        lines[j] = new_line
    for idx in sorted(inserts, reverse=True):
        for comment in reversed(inserts[idx]):
            lines.insert(idx + 1, comment)


def main(argv):
    p = argparse.ArgumentParser(description="Insert % GROUNDING comments from a grounding workflow's quotes.")
    p.add_argument('extract', help="JSON from extract_cites.py")
    p.add_argument('quotes', help="JSON mapping each key to {quote: ...} or {todo: <reason>}")
    p.add_argument('--dry-run', action='store_true',
                   help="print what would change without writing")
    args = p.parse_args(argv[1:])

    extract = load_json(args.extract, 'extract JSON')
    quotes = load_json(args.quotes, 'quotes JSON')
    if not isinstance(extract, dict):
        print(f"error: extract JSON {args.extract!r} is not a JSON object", file=sys.stderr)
        return 2
    if not isinstance(quotes, dict):
        print(f"error: quotes JSON {args.quotes!r} is not a JSON object", file=sys.stderr)
        return 2
    sites = extract.get('sites', [])

    by_file = {}
    for site in sites:
        fpath = site.get('file')
        if fpath is None:
            continue
        by_file.setdefault(fpath, []).append(site)

    stats = {'inserted': 0, 'quotes': 0, 'todos': 0, 'replaced': 0,
             'skipped_existing': 0, 'skipped_moved': 0, 'no_quote': 0,
             'files_changed': 0, 'reasons': {}}

    for fpath, fsites in by_file.items():
        try:
            # newline='' disables universal-newline translation so the file's own
            # line terminator survives the round-trip (a CRLF .tex is not rewritten
            # to LF, keeping the diff to the inserted comments only).
            with open(fpath, encoding='utf-8', errors='replace', newline='') as fh:
                text = fh.read()
        except OSError as e:
            print(f"warning: cannot read {fpath!r}: {e.strerror or e}; skipped", file=sys.stderr)
            continue
        newline = '\r\n' if '\r\n' in text else ('\r' if '\r' in text else '\n')
        had_final_newline = text.endswith(('\n', '\r'))
        lines = text.split(newline)
        if had_final_newline and lines and lines[-1] == '':
            lines.pop()  # trailing terminator yields an empty final element
        inserts, replacements = plan_file(lines, fsites, quotes, stats)
        if not inserts and not replacements:
            continue
        if args.dry_run:
            for idx in sorted(inserts):
                for comment in inserts[idx]:
                    print(f"{fpath}:{idx + 1}\t+{comment.strip()}")
            for j in sorted(replacements):
                print(f"{fpath}:{j + 1}\t~{replacements[j].strip()}")
            continue
        apply_changes(lines, inserts, replacements)
        out = newline.join(lines) + (newline if had_final_newline else '')
        with open(fpath, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)
        stats['files_changed'] += 1

    verb = 'would insert' if args.dry_run else 'inserted'
    summary = (
        f"{verb} {stats['inserted']} grounding comment(s) "
        f"({stats['quotes']} quote(s), {stats['todos']} TODO(s)); "
        f"{stats['skipped_existing']} already grounded, "
        f"{stats['skipped_moved']} skipped (moved/missing), "
        f"{stats['no_quote']} key(s) with no result"
    )
    if stats['replaced']:
        summary += f"; {stats['replaced']} TODO stub(s) replaced"
    if not args.dry_run:
        summary += f"; {stats['files_changed']} file(s) changed"
    print(summary, file=sys.stderr)
    if stats['reasons']:
        breakdown = ', '.join(f"{r}: {n}" for r, n in sorted(stats['reasons'].items()))
        print(f"TODO reasons -- {breakdown}", file=sys.stderr)
        if 'source-does-not-support' in stats['reasons']:
            print("note: 'source-does-not-support' TODOs flag likely miscitations; "
                  "review these keys before grounding them.", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
