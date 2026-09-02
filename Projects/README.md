# Projects

Active work. One folder per project, each a living directory that grows subfolders as content arrives. The README inside each project is the entry point: overview, current status, next steps, and links to everything else in the folder.

A project belongs here while it has a build cadence: specs being written, next steps waiting on something, decisions pending. When it finishes, the whole folder moves to `Intelligence/archive/`.

Routing inside a project:

| Content | Goes to |
|---|---|
| Status, overview, next steps | `README.md` |
| Research findings | `research/{topic}.md` |
| Specs and requirements | `specs/{name}.md` |
| Drafts and written output | `drafts/{name}.md` |
| Ideas and brainstorms | `ideas/{name}.md` |
| Working notes | `notes/{name}.md` |
| Decisions specific to this project | `decisions/YYYY-MM-DD-{slug}.md` |
| Ingested source material (immutable once placed) | `raw/{file}` |

`example-project/` is a demo showing the README shape. Delete it when you have a real project.
