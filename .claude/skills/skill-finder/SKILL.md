---
name: skill-finder
description: Find the repeated manual work in this vault that is worth turning into a skill. Reads what is already visible (recent dailies, the conversation, project notes) for tasks the owner has done by hand more than once, tests each against four criteria, and presents the two or three strongest candidates with evidence. Use when the owner asks "what should I automate", "what skill should I build", "what am I doing by hand", or when a wrap-up notices the same manual sequence for the third time. Hands the chosen candidate to skill-maker.
---

# Find a skill worth building

Surface repeated manual work from evidence, not from an interview. The owner's own dailies and notes already record what they do by hand; read those first and lead with findings.

## Steps

1. **Read what is already there.** The last two weeks of `Daily/`, the current conversation, and any project `notes/` that describe a process. Look for the same multi-step sequence done by hand on separate occasions.
2. **Test each pattern against four criteria.** A real candidate passes all four:
   - **Recurring:** three or more separate occasions.
   - **Multi-step:** several steps or decisions, not a single command.
   - **Manual:** done by hand each time, not already automated by a hook or a script.
   - **Uncovered:** no existing skill in `.claude/skills/` does this job. Match by the job, not by keywords; two skills can share words and do different work.
3. **Present at most three candidates**, each with the evidence that it recurs (which dailies, which dates) and the phrase that should trigger it. Then ask one question: which, if any, to build. On a pick, hand off to `skill-maker`.
4. **Do not force it.** If nothing passes all four tests, say so. Finding nothing is a healthy result; a padded list is worse than an empty one.
5. **Cold start only:** if there is nothing to read yet (a fresh vault), ask the owner to name a few tasks they repeat, or to describe last week, and run the same test on that.

## Hard rules

- Evidence first. Never open with "what do you do repeatedly?" when the dailies can answer it.
- Never build in this skill; that is `skill-maker`'s job.

## Self-improvement

When the owner rejects a candidate, note why in one line under the criteria here if it reveals a missing test. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| Build the chosen candidate | `skill-maker` |
| Review the skills that already exist | `skill-health` |
