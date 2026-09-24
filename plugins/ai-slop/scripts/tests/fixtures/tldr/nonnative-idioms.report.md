# AI Slop Review

**Paper:** `nonnative-idioms.txt`

## Summary

Synthetic fixture. A human review by a non-native writer, with idioms and padding phrases next to grammar slips.

## Findings by file

### nonnative-idioms.txt

#### Finding 1

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `nonnative-idioms.txt:21`
- **Quote:** `It can be noticed that the approach repairs`
- **Suggested revision:** `The approach repairs`

#### Finding 2

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `nonnative-idioms.txt:25`
- **Quote:** `It is worth to mention that the agent`
- **Suggested revision:** `The agent`

#### Finding 3

- **Rule:** No figurative language (G.no-figurative-language)
- **Location:** `nonnative-idioms.txt:25`
- **Quote:** `the agent is the brain of the whole pipeline`
- **Suggested revision:** `the agent makes every decision in the pipeline`

#### Finding 4

- **Rule:** Vague attributions (tropes.fyi, consistent)
- **Location:** `nonnative-idioms.txt:25`
- **Quote:** `Many researchers agree that prompts matter a lot`
- **Suggested revision:** `Prompt design affects the results`

#### Finding 5

- **Rule:** No figurative language (G.no-figurative-language)
- **Location:** `nonnative-idioms.txt:25`
- **Quote:** `a big hole in the paper`
- **Suggested revision:** `a serious gap in the paper`

#### Finding 6

- **Rule:** Cut padding at the sentence level (G.sentence-padding)
- **Location:** `nonnative-idioms.txt:31`
- **Quote:** `As a suggestion, the authors could`
- **Suggested revision:** `The authors could`

#### Finding 7

- **Rule:** No figurative language (G.no-figurative-language)
- **Location:** `nonnative-idioms.txt:31`
- **Quote:** `open the black box of the agent`
- **Suggested revision:** `show what the agent does`

## Items requiring author judgment

None.

## Signs of unassisted writing

- `nonnative-idioms.txt:21` grammar slip: `the scripts runs`
- `nonnative-idioms.txt:25` grammar slip: `It is worth to mention`
- `nonnative-idioms.txt:27` grammar slip: `Evaluation use only`
- `nonnative-idioms.txt:31` grammar slip: `It would be also nice`
