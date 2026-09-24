#!/usr/bin/env python3
"""check_fixture_recall.py REPORT [REPORT ...]

Compare the report of a real review of a TL;DR fixture with the findings that
the fixture planted. The fixtures under `fixtures/tldr/` are synthetic reviews
of invented papers. Each `<name>.txt` has a `<name>.report.md` with the planted
findings and signs of unassisted writing, and `expected.json` holds the level
and verdict that the case must get. The smoke suite checks those with the
planted reports. This script checks the review itself, which the smoke suite
cannot run because the review is a model reading the text.

To use it, review each fixture text with `/ai-slop:tldr` (or `/ai-slop:review`)
and pass the reports that the runs wrote. A report is matched to its fixture by
the file name in its `**Paper:**` header. A planted finding counts as found when
the report has a finding on the same line that names the same rule key, or the
same catalog trope. Running the reviews twice and comparing the two outputs
shows how stable the review is.

Output (stdout), tab-separated:

    fixture\\t<name>\\t<found>/<planted>\\t<extra>\\t<level>/<expected level>\\t<verdict>/<expected verdict>
    missed\\t<name>\\t<line>\\t<rule>
    extra\\t<name>\\t<line>\\t<rule>

An extra finding is not necessarily wrong, since the fixtures plant only the
patterns that each case is about. The level and the verdict are computed by
count_findings.py from the report under review. A one-line summary is printed
to stderr:

    9 report(s): 41/47 planted findings found, 6 extra, 8/9 verdicts as expected

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


def rule_id(rule):
    """Return a rule's key, or the lowercase name of a catalog trope."""
    m = KEY_RE.search(rule)
    if m:
        return m.group(1)
    return rule[:rule.rfind('(')].strip().strip('"').lower() if '(' in rule else rule.lower()


def located(text):
    """Return the set of (line, rule id) pairs that a report's findings name."""
    paper, findings = count_findings.parse_report(text)
    pairs = set()
    for field, location in findings:
        _, line = count_findings.place(location, paper)
        for rule in count_findings.split_rules(field):
            pairs.add((line, rule_id(rule)))
    return paper, pairs


def level_and_verdict(report):
    """Return the level and verdict that count_findings.py gives a report."""
    text = report.read_text(encoding='utf-8')
    paper, findings = count_findings.parse_report(text)
    entries = [(rule, count_findings.place(loc, paper)[1]) for rule, loc in findings]
    signs = [count_findings.place(loc, paper)[1] for loc in count_findings.parse_signs(text)]
    name = Path(paper or '').name
    line = count_findings.summarize(name, entries, FIXTURES, {}, signs)[0].split('\t')
    return line[7], line[12]


def main(argv):
    reports = [Path(a) for a in argv[1:]]
    if not reports or any(str(r).startswith('-') for r in reports):
        print('check_fixture_recall: usage: check_fixture_recall.py REPORT [REPORT ...]',
              file=sys.stderr)
        return 2
    expected = json.loads((FIXTURES / 'expected.json').read_text(encoding='utf-8'))
    out, found_total, planted_total, extra_total, verdicts = [], 0, 0, 0, 0
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
        level, verdict = level_and_verdict(report)
        want = expected[name]
        found_total += len(hit)
        planted_total += len(planted)
        extra_total += len(extra)
        verdicts += verdict == want['verdict']
        out.append(f"fixture\t{name}\t{len(hit)}/{len(planted)}\t{len(extra)}\t"
                   f"{level}/{want['level']}\t{verdict}/{want['verdict']}")
        out += [f'missed\t{name}\t{line}\t{rule}' for line, rule in sorted(planted - got)]
        out += [f'extra\t{name}\t{line}\t{rule}' for line, rule in sorted(extra, key=str)]
    sys.stdout.write('\n'.join(out) + '\n')
    print(f'{len(reports)} report(s): {found_total}/{planted_total} planted findings found, '
          f'{extra_total} extra, {verdicts}/{len(reports)} verdicts as expected', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
