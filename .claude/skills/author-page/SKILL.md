---
name: author-page
description: Write a new knowledge page, or bring an existing one up to the page standard. Applies the standard step by step (frontmatter, Summary line, Sources line, wikilinks woven into prose, a Related pages section, bidirectional links, index entry) and finishes with the vault health check as the exit gate. Use when the owner asks to write up a topic, create a page for an entity, document something in Resources/, or fix a page the health check flagged. Not for daily notes or project READMEs, which have their own shapes.
---

# Author a knowledge page

Write one page to the standard in `Resources/CLAUDE.md`, connected on both sides. A page that reads well but has no links in or out is a filing error, so connectivity is a step here, not a bonus pass.

## Steps

```
- [ ] 1. Confirm the source and the scope
- [ ] 2. Check what exists
- [ ] 3. Draft
- [ ] 4. Connect
- [ ] 5. Health check
```

### 1. Confirm the source and the scope
A page is built from source material (a file in `raw/`, a URL read in full, a transcript), never from general knowledge written as fact. Name the source before writing. If there is none, say so and ask whether the owner wants a page anyway, marked as unsourced.

Decide the page's boundary in one sentence: what it covers and what it leaves to a neighbor. If that sentence needs an "and", it may be two pages.

### 2. Check what exists
Grep the vault for the page's subject and its obvious synonyms. Three outcomes:

- A page exists: update it rather than creating a duplicate.
- Pages mention the subject as plain text: those are the inbound links you will add in step 4.
- Nothing: proceed, and note that the new page will need at least one inbound link from an existing page or it is an orphan.

Check the folder's `index.md` (or create one if the topic folder is new) and the vault's tag vocabulary (`grep -rh '^tags:' --include='*.md' .` shows every tag in use) before choosing tags.

### 3. Draft
The shape, in order:

```markdown
---
type: reference
status: active
project: {slug}            # when the page belongs to a project
tags: [two, or-more, specific]
updated: YYYY-MM-DD
---

**Summary**: one or two sentences a reader can stop after.

**Sources**: where the content came from, specifically.

## First section

Prose, with every entity that has a page [[wikilinked]] on first mention in each section.

## Related pages

- [[neighbor]]: one line on the relationship.
```

Rules while drafting:

- No `# Title` heading. The filename is the title.
- Wikilink only entities that have a page. An entity without one stays plain text.
- Callouts (`> [!note]`, `> [!tip]`, `> [!warning]`) for the one to three things a reader must not miss.
- Match the source's depth. A terse source gives a short page; do not pad.
- Vault voice: specific names, specific consequences, no filler.

### 4. Connect
- Add the page to its folder's `index.md` with a one-line summary.
- For every page listed under Related pages, add the reciprocal link there. Links are bidirectional.
- Repoint the plain-text mentions found in step 2 to `[[wikilinks]]`.
- If this page replaces or splits an existing one, repair every inbound link to the old location in the same pass.

### 5. Health check
Run `python3 .claude/scripts/vault-health.py`. Zero broken links, zero orphans, zero frontmatter drift is the exit condition. Fix and rerun until clean. Then add a one-line Completed entry to today's daily naming the page.

## Hard rules

- Source first. Unsourced claims are marked, never smuggled in.
- Zero ghost nodes.
- Bidirectional links.
- The health check runs before "done".

## Self-improvement

When the owner corrects a page's shape or voice in a way that should apply to every page, fix it here (and in `Resources/CLAUDE.md` if it is a convention). When a page is praised as a model, save a copy to `references/examples/`. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| Material still sitting in `Inbox/` | `ingest` skill first |
| Closing the session | `wrap-up` skill |
| Whole-vault audit | `python3 .claude/scripts/vault-health.py` |
