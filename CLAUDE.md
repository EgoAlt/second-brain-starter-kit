# Vault Guide

<!-- FILL: one paragraph on what this vault is for and who owns it. Example: "Personal knowledge base and operating system for <your name>. All state lives in markdown files the agent reads, writes, and maintains." -->

This vault is an Obsidian knowledge base and a working environment for an AI agent. All state lives in markdown files. The agent reads them, writes them, and keeps them current. Nothing that matters lives only in a chat.

## Orientation

<!-- FILL: two to four sentences pointing at the areas of the vault that matter most right now, with `[[wikilinks]]` to their README pages. This is the first thing the agent reads, so name the active projects and where their state lives. -->

## Session Startup

On the first response of every session:

1. Silently read the most recent `Daily/YYYY-MM-DD.md` (the lexically greatest filename matching the date pattern; never `Daily/CLAUDE.md`, never a file in `Daily/log/`).
2. Silently read `Context/me.md`.
3. Check `Inbox/`. If anything is there, mention it and offer to ingest it. Never ingest silently.
4. If `Context/me.md` still contains a `FILL:` marker, this vault has not been set up yet. Say so in one line and offer to run the `setup-vault` skill before anything else. Do not start it unasked.

Do not announce that you loaded anything. Read it, then respond.

## Rules

Rule numbers are permanent IDs. They are never renumbered and never reused, so a hook, a decision record, or a daily note can cite a rule by number and the reference stays valid forever. Rules are grouped by theme, which is why numbering runs non-sequential within a section. A new rule takes the next unused number and files into the section it belongs to. When a rule is retired, its number stays in the file as a one-line tombstone stating when and why.

Each rule's origin story (the incident, the reasoning, the date) lives in `Intelligence/decisions/rule-provenance.md`, keyed by number, not inline here. That keeps this file scannable.

<!-- FILL: the ten rules below are generic examples that show the shape. Keep the ones that fit, delete the ones that do not, add your own with the next unused number. -->

### Session lifecycle

1. The Session Startup section above governs the first response of every session.
2. When meaningful work happens (not casual chat), write a session log entry to `Daily/YYYY-MM-DD.md`. An entry states what is true now in one or two lines (the outcome and resulting state, not the story of getting there) plus a wikilink to where the detail lives. When narrative starts burying state, move the full account verbatim to `Daily/log/YYYY-MM-DD-log.md` and link it from the daily. The Stop hook (`.claude/scripts/check-daily-log.sh`) blocks ending a session that changed vault content without touching today's daily.
3. Before the final response of a session, persist anything meaningful still only in the conversation to its home per the Knowledge Routing table. Skip casual chat.

### Writing standard

4. Every note gets full frontmatter (`type`, `status`, two or more specific `tags`) and a one-line `**Summary**` as its first body line. A note stands alone: a reader who opens it cold should not need a parent note to understand it. Post-action detector: `.claude/scripts/check-note-standard.py`.
5. Use `[[wikilinks]]` for every entity that has a page, woven into sentences. Never link to a page that does not exist: an entity without a page is written as plain text until it earns one. Zero ghost nodes. Non-blocking nudge: `.claude/scripts/nudge-wikilinks.py`.
6. Use callouts (`> [!type]`) for visual structure, sparingly, one to three per note.

### Write gates

7. Corrections from the owner about how the agent works get saved permanently without asking: a durable invariant becomes a rule here, a fact about the owner updates `Context/me.md`. Session output (logs, notes, corrections) auto-saves and is reported. New source material is the exception: it always goes through `Inbox/`'s discuss-first gate before anything is written from it.
8. A daily note is created once and then edited in place. Never overwrite one wholesale, and never use a destructive git or shell command (a restore, a checkout of a path, a hard reset, an `rm`) to discard uncommitted vault work; reverse your own edits with targeted edits instead. Blocking guard: `.claude/scripts/guard-daily-overwrite.py`.

### Operations

9. Never create files or folders in the vault root. Every file lives in an existing top-level folder. A new top-level area is the owner's structural call, raised first. Blocking guard: `.claude/scripts/guard-vault-root.py`.
10. A page move, rename, or archival repairs its own broken inbound links before the task is done. After any `mv` or `rm` of a page, grep the vault for the old slug and repoint every hit. Non-blocking nudge: `.claude/scripts/nudge-move-linkcheck.py`.

## Knowledge Routing

Every piece of information has one home. No catch-all.

| Type | Route to |
|------|----------|
| New source material awaiting ingest | `Inbox/` (see `Inbox/CLAUDE.md`) |
| Who the owner is, preferences, working style | `Context/me.md` |
| Goals and strategy | `Context/strategy.md` |
| Tool stack, integrations, where external code lives | `Context/infrastructure.md` |
| Active project state (status, next steps, specs, research) | `Projects/{name}/` (see `Projects/CLAUDE.md`) |
| Reusable reference material (frameworks, prompts, templates) | `Resources/` (see `Resources/CLAUDE.md`) |
| Decisions, records, meeting notes, completed projects | `Intelligence/` (see `Intelligence/CLAUDE.md`) |
| Rule origin stories | `Intelligence/decisions/rule-provenance.md` |
| Daily journal | `Daily/YYYY-MM-DD.md` (see `Daily/CLAUDE.md`) |
| Operator health findings (autonomous, not the human's queue) | `Resources/operator/health-backlog.md` |
| Rules for agent behavior | this file, Rules section |

<!-- FILL: add rows for the areas you use (a glossary, a people index, a hobbies area). Delete rows you do not. -->

## Query

When answering a question, search the vault first (grep, or the editor's search) before researching externally, and cite the vault pages you used with `[[wikilinks]]`.

## Document Voice

Vault notes sound like a teammate, not a report. Specific names, specific context, specific consequences.

- Bad: "The project is progressing well. Key milestones are being tracked."
- Good: "Kite frame built, bridle not yet tuned. Next checkpoint: first flight test on a calm day. Blocked on sourcing 2mm line."

## Frontmatter

```yaml
---
type: note | project | reference | decision | daily-note
date: YYYY-MM-DD
project: project-slug        # when the note belongs to a project
status: active | draft | done | archived
tags: [two, or-more, specific, tags]
---
```

Always include `status` and two or more `tags`. Tags are lowercase, hyphenated, singular by default.

## Anti-patterns

Do not:

- Put a `# Title` heading that duplicates the filename.
- Create orphan notes. Every note is linked from at least one existing note.
- Update vault files on casual chat.
- Cram all project detail into a README; route it to the project's subfolders.
- Write an entity as plain text when it has a page, or link an entity that has no page.
- Use `[markdown](links)` for internal notes. Wikilinks only.
- Reference tooling files with a wikilink. `.claude/` is a dot-folder that Obsidian does not index, so `[[.claude/...]]` is always a broken link. Use a backtick path instead.
