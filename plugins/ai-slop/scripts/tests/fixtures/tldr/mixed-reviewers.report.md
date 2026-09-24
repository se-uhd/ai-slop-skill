# AI Slop Review

**Paper:** `mixed-reviewers.txt`

## Summary

Synthetic fixture. One submission with three reviews: a human review with slips, an AI-written review, and a clean human review.

## Findings by file

### mixed-reviewers.txt

#### Finding 1

- **Rule:** No formulaic section openings (G.no-formulaic-openings)
- **Location:** `mixed-reviewers.txt:36`
- **Quote:** `In an era where software systems are increasingly complex, incident response has never been more critical.`
- **Suggested revision:** `Incidents cost on-call engineers time.`

#### Finding 2

- **Rule:** Promotional language (tropes.fyi, new)
- **Location:** `mixed-reviewers.txt:36`
- **Quote:** `a groundbreaking approach to log summarization`
- **Suggested revision:** `an approach to log summarization`

#### Finding 3

- **Rule:** Negative parallelism (tropes.fyi, consistent)
- **Location:** `mixed-reviewers.txt:40`
- **Quote:** `The approach is not merely a summarizer. It is a paradigm shift`
- **Suggested revision:** `The approach summarizes logs`

#### Finding 4

- **Rule:** No rule-of-three defaults (G.no-rule-of-three)
- **Location:** `mixed-reviewers.txt:40`
- **Quote:** `clear, concise, and compelling`
- **Suggested revision:** `clear`

#### Finding 5

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `mixed-reviewers.txt:44`
- **Quote:** `As noted earlier,`
- **Suggested revision:** ``

#### Finding 6

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `mixed-reviewers.txt:44`
- **Quote:** `It is worth noting that`
- **Suggested revision:** ``

## Items requiring author judgment

None.

## Signs of unassisted writing

- `mixed-reviewers.txt:17` missing article: `Paper present`
- `mixed-reviewers.txt:17` grammar slip: `a tool that summarize`
- `mixed-reviewers.txt:21` missing article: `all from same company`
