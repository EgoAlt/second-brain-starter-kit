---
name: wrap-up
description: Close out the current session before the owner ends or archives it. Persist anything meaningful still only in the conversation, write or refresh today's daily note (Completed entries and Focus), record any content-health finding fixed along the way, and make sure the Stop hook will pass. Fires on close-out language ("wrap up", "we're done", "anything left?", "log everything"), not on mid-task tidying. Not for starting a fresh session with context.
---

# Wrap up

Turn everything that happened this session into its correct persisted state, so nothing meaningful is lost and the Stop hook (`.claude/scripts/check-daily-log.sh`) passes without drama. The hook is the backstop; this skill is the complete version.

Runs autonomously and reports at the end. Session output auto-saves without asking (rule 7), so do not pester for permission on the logging. The only pauses are the propose-first cases in step 3.

## Steps

```
- [ ] 1. Read-only guard
- [ ] 2. Take stock
- [ ] 3. Persist what is still only in the conversation
- [ ] 4. Daily log and Focus
- [ ] 5. Health findings
- [ ] 6. Report
```

### 1. Read-only guard
If the owner declared this session read-only (an audit, a second opinion), make no vault writes at all. State in chat exactly what you would have logged, and stop. Skip the remaining steps.

### 2. Take stock
Before writing anything, work out what actually happened: which vault files changed (`git status --porcelain`), what decisions or findings arose, what was discussed but never saved. Look at what the session did, not at what the rules say a session should do.

### 3. Persist what is still only in the conversation
Anything meaningful still only in the conversation goes to its home per the root `CLAUDE.md` Knowledge Routing table: a preference to `Context/me.md`, a decision to `Intelligence/decisions/`, project state to the project README, a reusable insight to `Resources/`. Skip casual chat.

**Propose first** when the content is something the owner has marked as theirs to approve (see "Decisions I always want to make myself" in `Context/me.md`), or when it would change how a skill behaves. Propose the exact text and wait. Everything else auto-saves.

### 4. Daily log and Focus
- **Completed entries (rule 2):** one or two lines each stating what is true now, plus a `[[wikilink]]` to the detail. Not the story of getting there.
- **Focus:** rewrite `## Focus` so it summarizes everything that happened today, not just this session.
- **Open Loops:** add anything left unfinished; remove anything this session closed.
- If today's daily does not exist yet, create it with the full section skeleton from `Daily/CLAUDE.md`. If it exists, edit it in place; never overwrite it (rule 8).
- A session that crossed midnight logs under the date the work happened and leaves a one-line pointer in the new date's daily.

### 5. Health findings
Any content-health problem found and fixed this session (a broken link, a missing frontmatter field, an orphan) gets a one-line `fixed YYYY-MM-DD` bullet in `Resources/operator/health-backlog.md`, whether or not an audit was running. If the root cause was a script bug, fix the script or note it in the scripts README.

### 6. Report
Do not commit or push unless the owner asked; if you do commit, add files by explicit path. Report one short block: what was persisted and where, the daily entry written, anything backlogged, anything still waiting on the owner's go from step 3. Then say plainly that the session is wrapped, or name the one thing that blocks it.

## Self-improvement

When the owner corrects how a step was done, fix it here so it sticks. When they say a wrap-up was well done, save the report to `references/examples/`. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| Writing a page discovered to be missing | `author-page` skill (usually next session, noted in Open Loops) |
| Un-ingested material still in `Inbox/` | leave it; note it in Open Loops; `ingest` skill next session |
