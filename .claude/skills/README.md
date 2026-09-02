# How skills work here

A skill is a repeatable workflow written as a markdown instruction file. Claude Code discovers every `.claude/skills/{name}/SKILL.md` at session start, reads its frontmatter (`name`, `description`) into the agent's available-skills list, and runs it when the agent judges the description matches the situation or when you type `/{name}`.

Nothing about a skill is tool-specific beyond that discovery convention. The file is plain markdown: a description of when to use it, numbered steps, hard rules, and a routing table for the jobs it hands to other skills. Another agent framework would read the same file with a different loader.

## The shape

```
.claude/skills/{name}/
  SKILL.md          <- frontmatter + the procedure
  references/       <- optional: longer material loaded on demand
```

`SKILL.md` frontmatter:

```yaml
---
name: {name}
description: One paragraph. What the skill does, when to use it, and the phrases that should trigger it. This is the only text the agent sees before deciding to invoke, so make the trigger conditions concrete.
---
```

Add `disable-model-invocation: true` to the frontmatter for a skill the agent should never start on its own (one that publishes, deletes, or spends money). The owner runs it with `/{name}`.

## The shipped skills

| Skill | Job | Shows |
|---|---|---|
| `setup-vault` | Turn the blank kit into your vault, and customize it later | An interview-then-build flow driven by the `FILL:` markers in the templates; user-invoked only |
| `ingest` | Move a file from `Inbox/` to its home | The discuss-first gate: read everything, propose destinations, wait for a go, then write |
| `author-page` | Write or rewrite a knowledge page | The page standard applied step by step, with the health check as the exit gate |
| `wrap-up` | Close a session cleanly | Persisting conversation-only facts, the daily log, and delegating to another skill |
| `skill-finder` | Find repeated manual work worth a skill | Evidence-first: reads the dailies, tests candidates against four criteria, never pads the list |
| `skill-maker` | Turn a finished task into a single-job skill | Reconstruct from what happened, hunt exceptions, mark checkpoints, prune, play back |
| `skill-health` | Keep the skill set small and clear | Same-job versus different-job overlap, propose-only |

The four vault-lifecycle skills are generic and complete; run them as they are, then edit them as your conventions diverge. The three skill-building skills form a loop: finder mines your own dailies for what to build, maker builds it, health keeps the set clean and points back to finder.

## When to write a skill

A task recurs, it has steps worth pinning down, and getting a step wrong costs something. If the task is one line, a rule in `CLAUDE.md` is enough. If it is a one-off, just do it.

Prefer a skill over a subagent. A skill runs in the current session with its context already loaded; a subagent starts cold and pays the full context cost again. Reach for a subagent only for parallel work, for isolating a large read from the main session, or when an independent perspective is the point (a reviewer who did not write the code).

## Keeping skills small

Every skill in this kit ends with a self-improvement section that says the same thing: when the owner corrects a step, fix it in the skill so the correction sticks; when they say a run was well done, save the output as an example; and after adding anything, run the deletion test and cut what no longer changes behavior.

A structural change to a skill changes how it behaves on every future run. Propose it and get an explicit go before applying. A typo fix or a clearer sentence can be applied directly.
