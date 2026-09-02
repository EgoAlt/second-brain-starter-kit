Reusable reference material, organized by topic. Pages here are written to the page standard and cross-linked densely: a knowledge page with no links in and out is a filing error.

## Structure

- `library/{topic}/`: knowledge pages for one topic, plus an `index.md` that links every page in the folder and gives a one-line summary of each.
- `operator/`: operator-owned state. `health-backlog.md` is the scheduled agent's list of content-health findings. The owner reads it; the operator works it.

<!-- FILL: add subfolders you use (prompts/, templates/, frameworks/) with a one-line description of each. -->

## The page standard

Every knowledge page has:

- Frontmatter: `type: reference`, `status`, two or more specific `tags`, `updated`; `project` when it belongs to one.
- A one-line `**Summary**` as the first body line.
- A `**Sources**` line naming where the content came from. Only material from a real source becomes content; nothing is written from general knowledge as if it were fact.
- Body under `##` headings, with every entity that has a page `[[wikilinked]]` on first mention in each section.
- A `## Related pages` section listing every real neighbor. Links are bidirectional: if A lists B, B lists A.
- No `# Title` heading duplicating the filename.

## Rules

- Zero ghost nodes: every `[[wikilink]]` resolves to a real file. An entity without a page stays plain text until it earns one.
- No orphans: every page is reachable from its topic `index.md` and from at least one other content page.
- Splitting: a page that covers two distinct things becomes two pages, cross-linked, when either half is cited on its own.
- After any batch of page work, run `python3 .claude/scripts/vault-health.py` and clear what it reports.
