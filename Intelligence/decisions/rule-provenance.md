---
type: decision
status: active
tags: [rules, provenance, meta]
updated: 2026-01-15
---

**Summary**: The origin story of every numbered rule in the root `CLAUDE.md`, keyed by rule number: what happened, what the root cause was, when the rule was written. The rule itself stays short; the why lives here.

> [!note] How to use this file
> When you add a rule, add an entry here with the same number. When you retire a rule, note the date and reason here and leave a one-line tombstone in `CLAUDE.md`. Never renumber.

## Entries

### Rule 1: Session Startup governs the first response
Origin: kit default. An agent that starts every session by reading yesterday's state and the owner's profile does not need to be told the same context twice.

### Rule 2: Meaningful work gets a session log entry
Origin: kit default. Without a hook-backed log, work done in a session exists only in that session's transcript. The Stop hook makes the log a precondition for ending.

### Rule 3: Persist before the final response
Origin: kit default. The last message of a session is the last chance to route a conversation-only fact to its home.

### Rule 4: Frontmatter and a Summary line on every note
Origin: kit default. A note without frontmatter cannot be queried; a note without a summary cannot be skimmed.

### Rule 5: Wikilink every entity that has a page; never link one that does not
Origin: kit default. Broken links (ghost nodes) make the graph lie about what exists. Plain text for an entity without a page keeps the graph honest and leaves the name findable for a later page.

### Rule 6: Callouts, sparingly
Origin: kit default. Callouts read as emphasis. More than three per note and none of them stand out.

### Rule 7: Corrections save permanently; new source material goes through the inbox gate
Origin: kit default. The two write modes have opposite defaults: the owner's corrections should never require permission to save, and a new source should never be written from without discussion.

### Rule 8: Edit a daily in place; never discard uncommitted work destructively
Origin: kit default. A daily note is uncommitted for the length of a session, so a wholesale overwrite or a `git restore` destroys it with no copy to recover from. The guard script closes both routes.

### Rule 9: Nothing new in the vault root
Origin: kit default. Every stray root file is a routing decision that was skipped. The guard makes skipping it impossible.

### Rule 10: A move repairs its own inbound links
Origin: kit default. Link checks run on the file being edited, not on the files that link to it, so a move silently breaks links elsewhere unless the mover greps for them.

<!-- FILL: your rules from 11 onward, as you add them. -->
