Projects are living, structured directories, not flat README-only folders. Active work only.

## Rules

- **README as index.** `README.md` carries overview, current status, next steps, and links to subfolder content. It never duplicates what the subfolders hold.
- **Current Status and Next Steps are replaceable state.** Rewrite them to present-tense truth when things change. Do not stack dated corrections; move superseded reasoning to a `log.md` or a decision record if it still matters.
- **Subfolders on the fly.** Do not pre-create empty directories. When content arrives that needs one, create it, write the file, and link it from the README.
- **Vault versus codebase.** A project folder holds specs, research, and decisions, never runnable code. Before creating any code-shaped file, check `Context/infrastructure.md`'s External Codebases table for where that project's code lives, and write there instead.
- **Raw material arrives through `Inbox/`.** Once ingested, the original moves into this project's `raw/` and is never edited again.
- **Lifecycle.** A new project starts as a README alone. A finished project moves whole to `Intelligence/archive/{name}/`, and every inbound link is repointed in the same pass.
- Include `project: {slug}` in the frontmatter of every note that belongs to a project, wherever in the vault it lives.

## Frontmatter for a project README

```yaml
---
type: project
status: active | paused | done
project: {slug}
activity_mode: active-build | live-operation | scheduled | on-hold | paused | reference-ready
updated: YYYY-MM-DD
tags: [two, or-more]
---
```

`status` says whether the document is current. `activity_mode` says whether the project deserves attention now. Keep them separate.

## Current projects

<!-- FILL: one bullet per active project, `[[wikilinked]]` to its README, with a one-line description. The demo entry below shows the shape; delete it with the demo folder. -->

- [[example-project/README|example-project]]: a demo project (building a two-line stunt kite) that exists only to show the README shape.
