---
name: ingest
description: Process files sitting in the vault-wide Inbox/ staging folder. Read each one in full, discuss the key takeaways and the right destination with the owner before writing anything, then route it into the correct place per that destination's own CLAUDE.md conventions, and archive substantial source material to the destination project's raw/ folder. Use whenever the owner mentions dropping something in the inbox, asks to process or ingest or look at what is in the inbox, or replies "go ahead" right after being told the inbox is non-empty. Also check Inbox/ proactively at the start of a session.
---

# Ingest

Process everything currently in `Inbox/`. This skill does not invent a process; it makes the one documented in `Inbox/CLAUDE.md` and every destination folder's `CLAUDE.md` explicit and consistent from run to run.

## Operating principles

1. **Read everything in full before forming an opinion.** A file in `Inbox/` is never "already processed" because it has been there a while.
2. **Discuss before writing.** The owner sees what the material says and where it is proposed to go before anything is created or edited. Never rewrite the vault from a new source silently.
3. **The destination's `CLAUDE.md` is the routing authority, not this skill.** Read the live file every time; conventions change.
4. **Ambiguity is normal, guessing is not.** When a destination is unclear, ask, with a recommendation and the trade-off. Several rounds on one drop is expected.
5. **Never drop in-scope content as "off-topic".** Every section the source treats as distinct gets captured somewhere. If content does not fit the page being written, ask where it goes or build it its own page. Deferring part of a source is the owner's decision, surfaced in chat, never a silent omission.
6. **Pull recurring concepts out.** If something mentioned in passing matters across several pages, give it a page and link to it.
7. **Done means `Inbox/` is empty again**, apart from its own `README.md` and `CLAUDE.md`.

## Steps

Track progress:

```
- [ ] 1. See what is there
- [ ] 2. Read everything in full
- [ ] 3. Propose destinations (and a coverage manifest for a multi-page build)
- [ ] 4. Discuss, wait for the go
- [ ] 5. Write
- [ ] 6. Archive or clear
- [ ] 7. Confirm
```

### 1. See what is there
List `Inbox/`. Name every file to the owner with its type and size. Nothing is written yet.

### 2. Read everything in full
Read each file completely. For a PDF, extract the text; for a web clipping, follow its outbound links one hop if they are load-bearing for the content. Note the source's own structure (chapters, sections, tables) as you go; it drives step 3.

### 3. Propose destinations
For each file, propose: the destination folder (per the root `CLAUDE.md` Knowledge Routing table), the page or pages to create or update, and the frontmatter tags (reusing the vault's existing tag vocabulary before coining a new one). For any source that will become more than one page, build a **coverage manifest**: every section the source treats as distinct, assigned to a target page. An item you cannot assign is a question for the owner, never a silent omission.

### 4. Discuss, wait for the go
Present the proposal and the manifest. Answer questions. Adjust. Do not write until the owner says go. If they defer part of a source, record the deferral where they will see it again (a project's open questions, or a note in the daily's Open Loops) and say so in chat.

### 5. Write
Write as one sequential author, working the manifest top to bottom, following the destination folder's `CLAUDE.md` and the page standard (`author-page` skill). After writing a multi-page build, diff the manifest against the pages by reading or grepping them: every item ends Present or Deferred, and a Missing item blocks "done". Then run `python3 .claude/scripts/vault-health.py` and clear what it reports.

### 6. Archive or clear
Substantial source material worth citing later moves into the destination project's `raw/` folder and is never edited again. A one-off note fully absorbed in step 5 is deleted. Either way `Inbox/` returns to empty.

### 7. Confirm
Report what was written where, what was archived, what was deferred (by name, each one), and that `Inbox/` is empty. Add a one-line Completed entry to today's daily.

## Hard rules

- No write before the go in step 4.
- No deferral without the owner's decision and a visible record of it.
- Source material only. Nothing from general knowledge is written as if the source said it.
- `raw/` is immutable once a file is placed there.

## Self-improvement

When the owner corrects how a step was done, fix it here so the correction sticks. When a run was well done, save the proposal and manifest to `references/examples/` as a model. Keep the skill small: after adding anything, cut what no longer changes behavior.

## Routing

| Concern | Route to |
|---|---|
| Writing a page to the standard | `author-page` skill |
| Closing the session after the ingest | `wrap-up` skill |
| Destination format inside a folder | that folder's `CLAUDE.md` |
