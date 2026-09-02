---
type: operator-state
status: active
tags: [operator, health, backlog]
---

**Summary**: The scheduled operator's own list of content-health findings (dead links, orphans, frontmatter drift). The operator writes it and works it; the owner reads it. Not the owner's task queue.

Last run: never

> [!important] Operator-owned, autonomous
> The operator fixes what is mechanical within its per-run cap and parks the rest here for a later run. A finding escalates to the owner only when it needs a human decision (for example, whether a recurring plain-text term should become a page). A finding whose root cause is a script bug is fixed in the script, not parked here.

## Open findings

_None yet. The first operator run populates this section._

## Fixed

_Each fix is a one-line bullet with a `fixed YYYY-MM-DD` prefix. The operator prunes this section on its next run after the owner has had a chance to see it._
