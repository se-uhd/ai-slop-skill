#!/usr/bin/env python3
"""check_fixture_recall.py REPORT [REPORT ...]

Compare the report of a real review of a TL;DR fixture with the findings that
the fixture planted. The fixtures under `fixtures/tldr/` are synthetic reviews
of invented papers. Each `<name>.txt` has a `<name>.report.md` with the planted
findings, and `expected.json` holds the number of patterns that affect
readability that the planted findings give, or null when the case must have no
findings. The smoke suite checks those with the
planted reports. This script checks the review itself, which the smoke suite
cannot run because the review is a model reading the text.

To use it, review each fixture text with `/ai-slop:tldr` (or `/ai-slop:review`)
and pass the reports that the runs wrote. A report is matched to its fixture by
the file name in its `**Paper:**` header. A planted finding counts as found when
the report has a finding on the same line that names the same catalog trope,
or one that EQUIVALENT lists with it, such as "Content duplication" and
"Self-echo", which a review may give the same repeated text. Running the reviews twice and comparing the two outputs
shows how stable the review is.

Output (stdout), tab-separated:

    fixture\\t<name>\\t<found>/<planted>\\t<extra>\\t<patterns>/<expected patterns>
    missed\\t<name>\\t<line>\\t<rule>
    extra\\t<name>\\t<line>\\t<rule>

An extra finding is not necessarily wrong, since the fixtures plant only the
patterns that each case is about. The number of patterns is computed by
count_findings.py from the report under review. A one-line summary is printed
to stderr:

    9 report(s): 38/41 planted findings found, 6 extra, 8/9 pattern counts as expected

Exit codes:
    0  every report was read and matched to a fixture
    2  usage error, or a report cannot be read or names no known fixture
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import count_findings  # noqa: E402
from scan_io import report_unreadable  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'tldr'
KEY_RE = re.compile(r'\(\s*([GSLT]\.[a-z0-9-]+)')

# Catalog tropes (normalized names) that a review may give the same text. Each
# group is reported under its first name.
EQUIVALENT = [
    ('content duplication', 'one-point dilution', 'self-echo'),
    ('delve and friends', 'tapestry and landscape'),
    ('signposted conclusion', 'never-ending conclusion', 'the tie-back'),
    ('negative parallelism', 'not x. not y. just z.'),
]
CANON = {rule: group[0] for group in EQUIVALENT for rule in group}


def rule_id(rule):
    """Return a catalog trope's normalized name, mapped to the first member of
    its EQUIVALENT group, or a layer rule's key, or the rule as written."""
    found = count_findings.trope(rule)
    if found:
        return CANON.get(found[0], found[0])
    m = KEY_RE.search(rule)
    return m.group(1) if m else rule.strip().lower()


def located(text):
    """Return the set of (line, rule id) pairs that a report's findings name."""
    paper, findings = count_findings.parse_report(text)
    pairs = set()
    for field, location, _ in findings:
        _, line = count_findings.place(location, paper)
        for rule in count_findings.split_rules(field):
            pairs.add((line, rule_id(rule)))
    return paper, pairs


def patterns(report):
    """Return the number of patterns that count_findings.py gives a report, or
    None when the report has no findings."""
    text = report.read_text(encoding='utf-8')
    paper, findings = count_findings.parse_report(text)
    entries = [(rule, count_findings.place(loc, paper)[1], quote)
               for rule, loc, quote in findings]
    if not entries:
        return None
    name = Path(paper or '').name
    return int(count_findings.summarize(name, entries, FIXTURES, {})[0].split('\t')[7])


def main(argv):
    reports = [Path(a) for a in argv[1:]]
    if not reports or any(str(r).startswith('-') for r in reports):
        print('check_fixture_recall: usage: check_fixture_recall.py REPORT [REPORT ...]',
              file=sys.stderr)
        return 2
    expected = json.loads((FIXTURES / 'expected.json').read_text(encoding='utf-8'))
    out, found_total, planted_total, extra_total, matches = [], 0, 0, 0, 0
    for report in reports:
        try:
            text = report.read_text(encoding='utf-8')
        except OSError as e:
            report_unreadable(str(report), e)
            return 2
        paper, got = located(text)
        name = Path(paper or '').stem
        if name not in expected:
            print(f'check_fixture_recall: {report} names no known fixture ({paper!r})',
                  file=sys.stderr)
            return 2
        _, planted = located((FIXTURES / f'{name}.report.md').read_text(encoding='utf-8'))
        hit = planted & got
        extra = got - planted
        count = patterns(report)
        want = expected[name]
        found_total += len(hit)
        planted_total += len(planted)
        extra_total += len(extra)
        matches += count == want['patterns']
        out.append(f"fixture\t{name}\t{len(hit)}/{len(planted)}\t{len(extra)}\t"
                   f"{count}/{want['patterns']}")
        out += [f'missed\t{name}\t{line}\t{rule}' for line, rule in sorted(planted - got)]
        out += [f'extra\t{name}\t{line}\t{rule}' for line, rule in sorted(extra, key=str)]
    sys.stdout.write('\n'.join(out) + '\n')
    print(f'{len(reports)} report(s): {found_total}/{planted_total} planted findings found, '
          f'{extra_total} extra, {matches}/{len(reports)} pattern counts as expected', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
