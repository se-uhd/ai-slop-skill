#!/usr/bin/env python3
"""build_writing.py OUTPUT [--scientific] [--latex] [--economist] [--ste] [--tropes=PATH ...] [--force]

Write the WRITING.md of a project to OUTPUT: a header for the contributors of
the project, the rule layers that the project calls for, and the AI trope
catalog. The writing skill selects the layers and handles AGENTS.md and
CLAUDE.md. This helper only writes OUTPUT, so the rules reach the file without
being retyped.

The general layer is always included. `--scientific` adds the scientific
layer, `--latex` adds the scientific and LaTeX layers (a LaTeX paper is a
research article), `--economist` adds the Economist layer, and `--ste` adds the
STE layer. Each layer contributes everything from its first `## ` heading
onward, self-check included, in the order general, scientific, LaTeX,
Economist, STE. The H1 title and intro paragraph of a layer, which describe
the file and the skills that load it, are left out. A heading that repeats one
of an earlier layer, such as the `## Voice` of the scientific layer, gets the
name of its layer in parentheses, as the self-check headings do.

The catalog comes from fetch_tropes.py, the only source, through the loader of
export_rules.py. `--tropes=PATH` (repeatable) reads local files instead,
concatenated in the order given. The catalog loses its title and preamble
(everything before the first `## ` heading), and its headings move one level
down, so the whole catalog is nested under one `## AI Writing Tropes to Avoid`
section. Each `**Avoid patterns like:**` label is followed by a blank line
before its list, which the Markdown linter requires. The status line of each
entry stays, since it carries the frequency rating and category of the catalog.

An existing OUTPUT is never replaced without `--force`, because the user may
have edited it. The skill asks first and passes `--force` on yes.

A one-line summary goes to stderr: whether OUTPUT was created or replaced, the
layers, the content hash of the catalog, and the size of the file.

Exit codes
----------
  0  OUTPUT written.
  1  no catalog: the fetch failed, or a --tropes file has no `## ` heading.
  2  usage error, or a --tropes file or a rule layer could not be read.
  3  OUTPUT exists and --force was not passed.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import export_rules  # noqa: E402

# (flag that selects the layer, file, label), in the order the layers stack.
# The general layer has no flag, and `--latex` also selects the scientific
# layer. The label, as in the self-check headings of the layers, tells apart a
# heading that repeats one of an earlier layer, such as `## Voice`.
LAYERS = (
    (None, 'rules-general.md', 'general'),
    ('scientific', 'rules-scientific.md', 'scientific'),
    ('latex', 'rules-latex.md', 'LaTeX'),
    ('economist', 'rules-economist.md', 'Economist'),
    ('ste', 'rules-ste.md', 'STE'),
)
FLAGS = ('scientific', 'latex', 'economist', 'ste')
AVOID_LINE = export_rules.AVOID_LINE


def usage():
    print(__doc__.splitlines()[0].replace('build_writing.py', 'usage: build_writing.py', 1),
          file=sys.stderr)
    return 2


def parse_args(argv):
    """Return (output, flags, tropes, force), or None on a usage error."""
    output, flags, tropes, force = None, set(), [], False
    for arg in argv[1:]:
        if arg.startswith('--') and arg[2:] in FLAGS:
            flags.add(arg[2:])
        elif arg == '--force':
            force = True
        elif arg.startswith('--tropes='):
            path = arg[len('--tropes='):]
            if not path:
                return None
            tropes.append(path)
        elif arg.startswith('-') or output is not None:
            return None
        else:
            output = arg
    if output is None:
        return None
    if 'latex' in flags:
        flags.add('scientific')
    return output, flags, tropes, force


def label_repeated_headings(text, label, seen):
    """Append ` (<label>)` to an ATX heading outside a fenced block when an
    earlier heading already used its text, and record the headings in seen.
    The Markdown linter rejects two headings with the same text."""
    out, fence = [], None
    for line in text.splitlines():
        match = export_rules.FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker[0] * len(marker)
            elif marker.startswith(fence):
                fence = None
        elif fence is None and export_rules.HEADING_RE.match(line):
            hashes, title = line.split(' ', 1)
            if title.strip() in seen:
                title = f'{title.strip()} ({label})'
                line = f'{hashes} {title}'
            seen.add(title.strip())
        out.append(line)
    return '\n'.join(out)


def space_avoid_lists(text):
    """Put a blank line between each `**Avoid patterns like:**` label and the
    list that follows it."""
    out = []
    for line in text.splitlines():
        if out and out[-1].strip() == AVOID_LINE and line.strip():
            out.append('')
        out.append(line)
    return '\n'.join(out)


def normalize_catalog(text):
    body = export_rules.from_first_h2(text)
    if not body:
        return ''
    return space_avoid_lists(export_rules.demote_headings(body)).strip()


def build(bodies, catalog, version):
    """Assemble WRITING.md from the layer bodies and the normalized catalog."""
    parts = [
        '# Writing rules for this project',
        'These rules apply to all prose in this repository. They were generated '
        'by `/ai-slop:writing` from the '
        '[ai-slop-skill](https://github.com/se-uhd/ai-slop-skill) '
        f'(skill version {version}) and combine the writing rules maintained by '
        'the [Software Engineering Group at Heidelberg University]'
        '(https://github.com/se-uhd) with a general AI trope catalog from '
        '[tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is).',
        'Edit this file freely to add project-specific conventions. The '
        'sections below are a starting point. Once you edit them, this file is '
        'yours.',
        'To audit a draft against everything below, use the `ai-slop:review` '
        'skill (or `ai-slop:review-diff` to scope the audit to git-modified '
        'lines). In Claude Code, invoke `/ai-slop:review`. In Codex, select the '
        'skill through `/skills` or a `$` mention. In pi, invoke `/skill:review`.',
    ]
    parts += [body.strip() for body in bodies]
    parts += [
        '---',
        '## AI Writing Tropes to Avoid',
        'The catalog below is sourced from [tropes.fyi](https://tropes.fyi) by '
        '[ossama.is](https://ossama.is) and inlined here so co-authors and '
        'offline tooling can read it without re-fetching. The skill fetches the '
        'live catalog on every run. This inlined copy is for reading by humans '
        'and other Agent Skills clients.',
        catalog,
    ]
    return '\n\n'.join(parts) + '\n'


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        return usage()
    output, flags, trope_paths, force = parsed
    out_path = Path(output).expanduser()
    existed = out_path.exists()
    if existed and not force:
        print(f"error: {output} exists; pass --force to replace it", file=sys.stderr)
        return 3

    bodies, names, seen = [], [], set()
    for flag, name, label in LAYERS:
        if flag is not None and flag not in flags:
            continue
        try:
            text = (export_rules.SHARED / name).read_text(encoding='utf-8')
        except OSError as exc:
            print(f"error: cannot read rule layer {name}: {exc}", file=sys.stderr)
            return 2
        body = export_rules.from_first_h2(text)
        bodies.append(label_repeated_headings(body, label, seen))
        names.append(name)

    try:
        raw, source = export_rules.load_catalog(trope_paths)
    except OSError as exc:
        print(f"error: cannot read --tropes file: {exc}", file=sys.stderr)
        return 2
    if raw is None:
        print(f"error: {source}", file=sys.stderr)
        return 1
    catalog = normalize_catalog(raw)
    if not catalog:
        print(f"error: the catalog from {source} has no `## ` trope heading",
              file=sys.stderr)
        return 1

    catalog_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]
    content = build(bodies, catalog, export_rules.skill_version())
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding='utf-8')
    except OSError as exc:
        print(f"error: cannot write {output}: {exc}", file=sys.stderr)
        return 2
    size = len(content.encode('utf-8'))
    print(f"{'replaced' if existed else 'created'} {out_path}: {', '.join(names)} "
          f"+ catalog sha256 {catalog_hash}; {size} bytes, about {size // 4} tokens",
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
