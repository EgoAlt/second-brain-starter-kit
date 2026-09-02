Dated records and the archive. Everything here is a snapshot: written once, corrected only by an appended dated note, never rewritten.

## Routing

| Content | Goes to |
|---|---|
| A decision and its reasoning | `decisions/YYYY-MM-DD-{slug}.md` |
| The origin story of a numbered rule | `decisions/rule-provenance.md`, keyed by rule number |
| A finished project | `archive/{project-slug}/`, moved whole |
| Meeting notes | `meetings/YYYY-MM-DD-{slug}.md` |

<!-- FILL: add rows for the record types you keep. -->

## Decision records

A decision record answers four questions: what was decided, what the options were, why this one, and what would make it worth revisiting. Frontmatter carries `type: decision`, `date`, `status: decided | superseded`, and `project` when it applies to one. A superseded decision is not deleted; it gets `status: superseded` and a callout pointing at the record that replaced it.

## Rules

- Append-only. To correct a record, add a dated callout; do not edit the original claim.
- Archiving a project is a whole-folder move plus an inbound-link repair in the same pass. An archived README gets `status: archived` and a one-line callout stating when and why it closed.
- The archive is the permanent record and the active queue lists only open work. Nothing finished stays in `Projects/`.
