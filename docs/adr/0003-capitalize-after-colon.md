# ADR-0003: Capitalize after a colon when a complete sentence follows

- **Status:** Proposed
- **Date:** 2026-05-13
- **Decision-makers:** maintainers of `ai-slop-skill`
- **Related:** [ADR-0001](./0001-markdown-dialect.md), [ADR-0002](./0002-markdown-linter.md)

## Context

`rules.md` already pins the manuscript register to American English and to IEEE/ACM conventions where APA and IEEE/ACM diverge (statistics formatting, leading zeros). It did not, however, take a position on capitalization after a colon.

In practice, two conventions are in circulation:

- **Chicago / British style.** Lowercase after a colon unless what follows is a direct question, a quotation, or two or more sentences.
- **IEEE / ACM / AP / APA style.** Capitalize the first word after a colon when the colon introduces a complete sentence (an independent clause).

Without a stated rule, drafts under review drift between the two conventions and the model defaults to Chicago-style lowercase, which is inconsistent with the IEEE and ACM venues this skill targets. The user reported the inconsistency directly.

## Decision drivers

- The skill already declares itself IEEE/ACM-aligned and American-English-only. The post-colon capitalization rule should follow the same alignment.
- The rule must be checkable at review time, not just at draft time.
- Adding the rule must not require a new helper script — the existing review workflow handles it as a prose scan, the way it handles em-dash count, colon density, and the British-spelling audit.

## Decision

Capitalize the first word after a colon in running prose when what follows is a complete sentence. Keep the first word lowercase when the colon introduces a fragment, phrase, single word, or list. Headings and `figure:` / `table:` labels are exempt; the rule applies to running prose only.

This is the IEEE Editorial Style Manual position and matches ACM, AP, and APA practice.

The rule lives in `plugins/ai-slop/shared/rules.md` under "Punctuation," next to the existing colon-density rule, and as a numbered item in the self-check. The review skill adds a corresponding entry to its cross-cutting metrics section and to the report template, so violations are surfaced as individual findings rather than as a single aggregate count.

## Consequences

`rules.md` grows by one bullet under "Punctuation" and one self-check item. Numbering for the self-check shifts by one for the items that follow.

`plugins/ai-slop/skills/review/SKILL.md` gains one cross-cutting metric (lowercase-after-colon and uppercase-after-fragment cases) and one matching report-template section. The stale "19-item self-check" reference in the same file is corrected to 22 items in the same edit.

`/ai-slop:init` propagates the rule to user repositories on next invocation because WRITING.md is built by concatenating `rules.md` verbatim from `## Language` onward.

`/ai-slop:revise` is unaffected at the schema level; new findings flow through the existing `Quote` / `Suggested revision` pair.

The bundle version moves from `2026-05_rev9` to `2026-05_rev10` across the seven surfaces listed in the README's "Maintainer notes."

## Follow-up

- Bump the bundle version from `2026-05_rev9` to `2026-05_rev10` across `plugin.json`, `marketplace.json`, the four `SKILL.md` frontmatter blocks, the report template header in `review/SKILL.md`, and the WRITING.md header in `init/SKILL.md`.

## References

- IEEE Editorial Style Manual (capitalization after a colon when an independent clause follows).
- APA Publication Manual, 7th ed., §6.1 (capitalization after a colon).
- The Associated Press Stylebook (capitalize the first word of a complete sentence after a colon).
