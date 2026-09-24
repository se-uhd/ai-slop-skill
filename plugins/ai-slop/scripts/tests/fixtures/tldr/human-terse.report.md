# AI Slop Review

**Paper:** `human-terse.txt`

## Summary

Synthetic fixture. A terse human review with grammar slips and a few mechanical findings.

## Findings by file

### human-terse.txt

#### Finding 1

- **Rule:** Semicolons (G.semicolons)
- **Location:** `human-terse.txt:25`
- **Quote:** `The baseline is weak; the comparison only uses`
- **Suggested revision:** `The baseline is weak. The comparison only uses`

#### Finding 2

- **Rule:** Anchor sentence-initial pronouns (G.anchor-pronouns)
- **Location:** `human-terse.txt:25`
- **Quote:** `This makes the results hard to judge.`
- **Suggested revision:** `The weak baseline makes the results hard to judge.`

#### Finding 3

- **Rule:** Oxford comma (G.oxford-comma)
- **Location:** `human-terse.txt:29`
- **Quote:** `in CI minutes, time and money`
- **Suggested revision:** `in CI minutes, time, and money`

## Items requiring author judgment

None.

## Signs of unassisted writing

- `human-terse.txt:17` grammar slip: `The paper propose`
- `human-terse.txt:17` missing article: `Authors evaluate`
- `human-terse.txt:21` missing article: `Problem is relevant`
- `human-terse.txt:25` grammar slip: `The threats section do not discuss`
- `human-terse.txt:29` grammar slip: `what is the cost`
