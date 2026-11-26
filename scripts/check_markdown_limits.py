#!/usr/bin/env python3
"""check_markdown_limits.py [--root <dir>] [--config <file>] [<file> ...]

Check the Markdown files of the repository against the length and structure
limits in scripts/markdown_limits.toml. Each [[limit]] entry names its files
with `paths` globs, relative to the repository root, and the source of its
limits, which each violation repeats. An entry sets one or more of these
limits:

    max_lines              the lines of the files of the entry together
    max_section_lines      the lines from a heading to the next heading of
                           any level, without the heading line
    max_body_tokens        the tokens of the body of a SKILL.md, after the
                           front matter, counted as characters divided by
                           chars_per_token and rounded up
    changelog_headings     the structure of the changelog (see below)
    max_bullet_sentences   the sentences of a changelog bullet in
                           [Unreleased] and in each release after
                           `after_release`

The changelog starts with '# Changelog'. Each version heading is
'## [Unreleased]', only at the top, or '## [YYYY-MM_revN] - YYYY-MM-DD', with
the versions newest first and the date in the month of the version. A version
holds only the headings of changelog_headings, in this order and each once,
and each heading holds only bullets ('- ') and their continuation lines. A
released version has at least one heading. The sentence count reuses the
sentence split of plugins/ai-slop/scripts/scan_sentences.py, so a quotation,
a code span, or an abbreviation such as "e.g." does not end a sentence.

Without a file, the script checks every entry. With files, it checks the
entries that name one of them, so an edit of CLAUDE.md checks AGENTS.md and
CLAUDE.md together. A file that no entry names has no limits.

Exits 0 when every limit holds, 1 with each violation on stderr when a limit
breaks, and 2 on a usage error or an invalid configuration.
"""
import argparse
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'plugins' / 'ai-slop' / 'scripts'))
import scan_sentences  # noqa: E402  (stdlib-only bundle helper)

LIMIT_KEYS = {'paths', 'source', 'max_lines', 'max_section_lines', 'max_body_tokens',
              'changelog_headings', 'max_bullet_sentences', 'after_release'}
VERSION = re.compile(r'## \[(?P<name>Unreleased|(?P<month>\d{4}-\d{2})(?:_rev(?P<rev>[1-9]\d*))?)\]'
                     r'(?: - (?P<date>\d{4}-\d{2}-\d{2}))?')
RELEASE = re.compile(r'(\d{4})-(\d{2})(?:_rev([1-9]\d*))?')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')
HEADING = re.compile(r'^ {0,3}#{1,6}(?:\s|$)')


class ConfigError(Exception):
    pass


def load_config(path):
    try:
        config = tomllib.loads(path.read_text(encoding='utf-8'))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f'{path}: {error}') from None
    limits = config.get('limit')
    if not isinstance(limits, list) or not limits:
        raise ConfigError(f'{path}: no [[limit]] entry')
    for number, limit in enumerate(limits, 1):
        unknown = set(limit) - LIMIT_KEYS
        if unknown:
            raise ConfigError(f'{path}: limit {number} has the unknown keys {sorted(unknown)}')
        if not limit.get('paths') or not limit.get('source'):
            raise ConfigError(f'{path}: limit {number} needs paths and a source')
        if 'max_bullet_sentences' in limit and not RELEASE.fullmatch(limit.get('after_release', '')):
            raise ConfigError(f'{path}: limit {number} needs after_release = "YYYY-MM_revN"')
    if any('max_body_tokens' in limit for limit in limits) and not (
            config.get('chars_per_token') and config.get('chars_per_token_source')):
        raise ConfigError(f'{path}: max_body_tokens needs chars_per_token and its source')
    return config


def release_key(name):
    """Return a sortable key of a release name, with [Unreleased] newest."""
    match = RELEASE.fullmatch(name)
    if not match:
        return (math.inf,)
    year, month, rev = match.groups()
    return (int(year), int(month), int(rev or 0))


def read_lines(path):
    lines = path.read_text(encoding='utf-8').split('\n')
    if lines[-1] == '':
        lines.pop()
    return lines or ['']


def prose_lines(lines):
    """Yield (index, line) for the lines outside fenced code blocks."""
    fence = None
    for index, line in enumerate(lines):
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)[0] * len(match.group(1))
        elif fence is not None and line.strip().startswith(fence) and not line.strip(fence[0]).strip():
            fence = None
        elif fence is None:
            yield index, line


def check_sections(name, lines, limit):
    headings = [index for index, line in prose_lines(lines) if HEADING.match(line)]
    ends = headings[1:] + [len(lines)]
    return [f'{name}:{start + 1}: the section has {end - start - 1} lines, more than '
            f"{limit['max_section_lines']} ({limit['source']})"
            for start, end in zip(headings, ends) if end - start - 1 > limit['max_section_lines']]


def body_of(text):
    """Return the text after the YAML front matter."""
    if text.startswith('---\n'):
        end = text.find('\n---\n', 3)
        if end >= 0:
            return text[end + 5:]
    return text


def sentence_count(text):
    norm = scan_sentences.normalize(text, False)
    return sum(1 for start, end in scan_sentences.split_sentences(norm)
               if scan_sentences.count_words(norm[start:end]))


def changelog_bullets(lines):
    """Yield (index, version, text) for each bullet, with its continuation
    lines joined."""
    version, bullet = None, None
    for index, line in enumerate(lines + ['']):
        match = VERSION.fullmatch(line)
        if bullet and not line.startswith('  '):
            yield bullet[0], bullet[1], ' '.join(bullet[2])
            bullet = None
        if match:
            version = match.group('name')
        elif version and line.startswith('- '):
            bullet = (index, version, [line[2:]])
        elif bullet:
            bullet[2].append(line.strip())


def check_bullet_sentences(name, lines, limit):
    after = release_key(limit['after_release'])
    violations = []
    for index, version, text in changelog_bullets(lines):
        count = sentence_count(text)
        if release_key(version) > after and count > limit['max_bullet_sentences']:
            violations.append(f'{name}:{index + 1}: the bullet has {count} sentences, more than '
                              f"{limit['max_bullet_sentences']} ({limit['source']})")
    return violations


def check_changelog(name, lines, limit):
    headings, source = limit['changelog_headings'], limit['source']
    violations = []

    def fail(index, message):
        violations.append(f'{name}:{index + 1}: {message} ({source})')

    if lines[0] != '# Changelog':
        fail(0, "the file starts with the heading '# Changelog'")
    # The current version as (index, match), the match of the last valid
    # version, the position of the current heading in `headings`, the index of
    # that heading, and the number of its bullets.
    version, previous, position, heading_line, bullets, in_bullet = None, None, -1, 0, 0, False

    def end_heading():
        if position >= 0 and not bullets:
            fail(heading_line, f'the heading {headings[position]} has no bullet')

    def end_version():
        end_heading()
        if version and version[1].group('name') != 'Unreleased' and position < 0:
            fail(version[0], f"the version {version[1].group('name')} has no heading")

    for index, line in enumerate(lines[1:], 1):
        if not line.strip():
            in_bullet = False
        elif line.startswith('## '):
            end_version()
            match = VERSION.fullmatch(line)
            if not match or (match.group('name') == 'Unreleased') != (match.group('date') is None):
                fail(index, "a version heading is '## [Unreleased]' or '## [YYYY-MM_revN] - YYYY-MM-DD'")
                match = None
            elif match.group('date') and not match.group('date').startswith(match.group('month')):
                fail(index, f"the date {match.group('date')} is not in the month of the version")
            if match and previous:
                above = previous.group
                if release_key(match.group('name')) >= release_key(above('name')):
                    fail(index, f"the version {match.group('name')} is not older than the version above it")
                elif match.group('date') and above('date') and match.group('date') > above('date'):
                    fail(index, f"the date {match.group('date')} is later than the date above it")
            version = (index, match) if match else None
            previous = match or previous
            position, bullets, in_bullet = -1, 0, False
        elif line.startswith('### '):
            end_heading()
            heading = line[4:].strip()
            following = headings.index(heading) if heading in headings else -1
            if version is None or following <= position:
                fail(index, f"the headings of a version are {', '.join(headings)}, "
                            'in this order, each once')
            position, heading_line, bullets, in_bullet = max(position, following), index, 0, False
        elif version is None and position < 0:
            continue
        elif line.startswith('- ') and position >= 0:
            bullets += 1
            in_bullet = True
        elif not (line.startswith('  ') and in_bullet):
            fail(index, "a heading of a version holds only bullets ('- ') and their "
                        'continuation lines (two spaces)')
    end_version()
    return violations


def check_limit(limit, files, root, config):
    names = [str(path.relative_to(root)) for path in files]
    violations = []
    if 'max_lines' in limit:
        total = sum(len(read_lines(path)) for path in files)
        if total > limit['max_lines']:
            violations.append(f"{' and '.join(names)}: {total} lines, more than "
                              f"{limit['max_lines']} ({limit['source']})")
    for name, path in zip(names, files):
        lines = read_lines(path)
        if 'max_section_lines' in limit:
            violations += check_sections(name, lines, limit)
        if 'max_body_tokens' in limit:
            tokens = math.ceil(len(body_of(path.read_text(encoding='utf-8'))) / config['chars_per_token'])
            if tokens > limit['max_body_tokens']:
                violations.append(
                    f"{name}: the body has about {tokens} tokens, more than {limit['max_body_tokens']} "
                    f"({limit['source']}). Move reference material into files that the SKILL.md "
                    'names at the step that needs them')
        if 'changelog_headings' in limit:
            violations += check_changelog(name, lines, limit)
        if 'max_bullet_sentences' in limit:
            violations += check_bullet_sentences(name, lines, limit)
    return violations


def main(argv):
    parser = argparse.ArgumentParser(prog='check_markdown_limits.py')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--config', type=Path)
    parser.add_argument('files', nargs='*', type=Path)
    args = parser.parse_args(argv[1:])
    root = args.root.resolve()
    try:
        config = load_config(args.config or root / 'scripts' / 'markdown_limits.toml')
    except ConfigError as error:
        print(f'check_markdown_limits.py: {error}', file=sys.stderr)
        return 2
    wanted = {path.resolve() for path in args.files}

    violations = []
    for limit in config['limit']:
        files = sorted({path.resolve() for pattern in limit['paths'] for path in root.glob(pattern)
                        if path.is_file()})
        if files and (not wanted or wanted & set(files)):
            violations += check_limit(limit, files, root, config)
    for violation in violations:
        print(violation, file=sys.stderr)
    return 1 if violations else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
