The daily journal. One note per day, always writable, edited in place.

## Two files per day

| File | Holds | Auto-loaded? |
|---|---|---|
| `Daily/YYYY-MM-DD.md` | State: `## Priorities`, `## Focus`, `## Completed` (one or two lines each), `## Open Loops` | Yes, the most recent one, at every session start |
| `Daily/log/YYYY-MM-DD-log.md` | The full narrative of the day's sessions, written only when the daily's stubs stop being enough | No |

A Completed entry states the outcome and the resulting state, with a `[[wikilink]]` to where the detail lives. If a reader has to follow the link to learn anything, the entry has failed.

## Rules

- **Create once, then edit.** A daily is written with a full-file write only when it does not exist yet. After that it is edited in place, section by section. A wholesale overwrite clobbers whatever another session wrote into it, and the daily is uncommitted for the length of a session, so git has no copy. The guard `.claude/scripts/guard-daily-overwrite.py` blocks the overwrite.
- **Every daily carries the full section skeleton**, in order: `## Priorities`, `## Focus`, `## Completed`, `## Open Loops`, even when a section is a placeholder line. Tooling that embeds a section by heading breaks when the heading is missing.
- **The `-log` suffix is mandatory** on the narrative file. Wikilinks resolve by basename, so `log/2026-01-15.md` would collide with `2026-01-15.md`.
- **Crossing midnight:** a session that runs past midnight logs its work in the daily for the date the work happened and leaves a one-line pointer in the new date's daily. Never duplicate the narrative. Never re-date earlier entries.
- **Focus is state.** `## Focus` summarizes everything that has happened today, not just the current session. Update it whenever you update Completed.
- **Scannability over size.** There is no byte limit. The trigger for moving narrative to `log/` is composition: when a load-bearing fact is buried mid-paragraph, move the paragraph.

## Frontmatter

```yaml
---
type: daily-note
date: YYYY-MM-DD
status: active
tags: [two, or-more]
---
```

The log file uses `type: daily-log` with the same `date` and links back to its daily.

<!-- FILL: any extra sections you want in every daily (a calendar line, a habit tracker), added to the skeleton above. -->
