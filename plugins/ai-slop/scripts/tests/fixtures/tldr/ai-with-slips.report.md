# AI Slop Review

**Paper:** `ai-with-slips.txt`

## Summary

Synthetic fixture. An AI-written review with two typos, whose AI-typical patterns outweigh the slips.

## Findings by file

### ai-with-slips.txt

#### Finding 1

- **Rule:** No formulaic section openings (G.no-formulaic-openings)
- **Location:** `ai-with-slips.txt:17`
- **Quote:** `In today's fast-paced world of continuous deployment, database migrations have become a critical bottleneck.`
- **Suggested revision:** `Failed migrations block deployments.`

#### Finding 2

- **Rule:** Promotional language (tropes.fyi, new)
- **Location:** `ai-with-slips.txt:17`
- **Quote:** `a groundbreaking tool`
- **Suggested revision:** `a tool`

#### Finding 3

- **Rule:** Negative parallelism (tropes.fyi, consistent)
- **Location:** `ai-with-slips.txt:21`
- **Quote:** `SchemaShift is not just a checker. It is a safety net`
- **Suggested revision:** `SchemaShift checks migrations`

#### Finding 4

- **Rule:** No rule-of-three defaults (G.no-rule-of-three)
- **Location:** `ai-with-slips.txt:21`
- **Quote:** `comprehensive, rigorous, and insightful`
- **Suggested revision:** `thorough`

#### Finding 5

- **Rule:** No figurative language (G.no-figurative-language)
- **Location:** `ai-with-slips.txt:21`
- **Quote:** `a safety net for the entire deployment pipeline`
- **Suggested revision:** `a check before deployment`

#### Finding 6

- **Rule:** Refer back instead of repeating (G.refer-back)
- **Location:** `ai-with-slips.txt:25`
- **Quote:** `As mentioned above, the tool is a safety net for deployments`
- **Suggested revision:** ``

#### Finding 7

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `ai-with-slips.txt:25`
- **Quote:** `it is important to note that`
- **Suggested revision:** ``

## Items requiring author judgment

None.

## Signs of unassisted writing

- `ai-with-slips.txt:17` typo: `producton`
- `ai-with-slips.txt:25` typo: `resuls`
