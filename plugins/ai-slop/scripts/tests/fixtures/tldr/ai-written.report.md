# AI Slop Review

**Paper:** `ai-written.txt`

## Summary

Synthetic fixture. A review written with an AI tool: a formulaic opening, negative parallelism, restatement, and a formulaic closing.

## Findings by file

### ai-written.txt

#### Finding 1

- **Rule:** No formulaic section openings (G.no-formulaic-openings)
- **Location:** `ai-written.txt:17`
- **Quote:** `In today's rapidly evolving software landscape, continuous integration has become more important than ever.`
- **Suggested revision:** `Misconfigured CI pipelines waste build time.`

#### Finding 2

- **Rule:** Announce a count only when the reader tracks it (G.no-announced-counts)
- **Location:** `ai-written.txt:17`
- **Quote:** `The paper makes three key contributions.`
- **Suggested revision:** `The paper contributes the analysis and an evaluation.`

#### Finding 3

- **Rule:** Restricted words (G.restricted-words)
- **Location:** `ai-written.txt:17`
- **Quote:** `software landscape`
- **Suggested revision:** `software development`

#### Finding 4

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `ai-written.txt:25`
- **Quote:** `that developers actually make in practice`
- **Suggested revision:** `that developers make`

#### Finding 5

- **Rule:** Negative parallelism (tropes.fyi, consistent)
- **Location:** `ai-written.txt:21`
- **Quote:** `The approach is not just a linter. It is a comprehensive framework`
- **Suggested revision:** `The approach checks pipeline reliability`

#### Finding 6

- **Rule:** No rule-of-three defaults (G.no-rule-of-three)
- **Location:** `ai-written.txt:21`
- **Quote:** `thorough, rigorous, and well executed`
- **Suggested revision:** `thorough`

#### Finding 7

- **Rule:** Refer back instead of repeating (G.refer-back)
- **Location:** `ai-written.txt:29`
- **Quote:** `The evaluation does not report false positives, which is a significant limitation.`
- **Suggested revision:** `As noted under the weaknesses, false positives are missing.`

#### Finding 8

- **Rule:** Refer back instead of repeating (G.refer-back)
- **Location:** `ai-written.txt:29`
- **Quote:** `the comparison with actionlint covers only 50 workflows`
- **Suggested revision:** `the small comparison noted above`

#### Finding 9

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `ai-written.txt:29`
- **Quote:** `It is important to note that`
- **Suggested revision:** ``

#### Finding 10

- **Rule:** No formulaic closings (G.no-formulaic-closings)
- **Location:** `ai-written.txt:33`
- **Quote:** `Overall, PipeGuard represents a promising step toward more reliable CI pipelines`
- **Suggested revision:** `PipeGuard could make CI pipelines more reliable`

#### Finding 11

- **Rule:** The "Serves As" dodge (tropes.fyi, fading)
- **Location:** `ai-written.txt:33`
- **Quote:** `PipeGuard represents a promising step`
- **Suggested revision:** `PipeGuard is a step`

## Items requiring author judgment

None.
