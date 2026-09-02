---
name: skill-health
description: Review the vault's skills as a set and keep it small and clear. Lists every skill in .claude/skills/, checks each one for use and for single-job scope, checks pairs for overlap by job rather than by wording, and proposes keep, merge, split, retire, or build. Use when the owner says "check my skills", "review my skills", "do I have too many skills", "these two overlap", or roughly every couple of months. Proposes only; never deletes or rewrites without an explicit go.
---

# Review the skill set

Keep the set small enough that every skill is used and clear enough that none is confused with another.

## Steps

1. **List every skill** in `.claude/skills/` with its one-line job from the `description`.
2. **Check each on its own.** Is it still used (look for its trigger phrases in recent dailies and the skills README)? Does it do one job, or has it grown a second? Flag unused skills and split candidates.
3. **Check the set as a whole.** For any two that look overlapping, decide: do they do the **same job** in different ways, or **different jobs** that resemble each other? Same job means one clear winner and the rest marked as optional second opinions. Different jobs stay separate; force-merging them builds one bloated do-everything skill.
4. **Look for gaps.** A task the owner repeats with no skill for it goes to `skill-finder`.
5. **Propose, do not act.** Present a short list: keep, merge, split, retire, build, each with a one-line reason. Wait for the owner's go before changing any file. Retiring a skill means moving its folder out of `.claude/skills/`, updating the skills README, and noting the retirement in the daily; never a silent delete.

## Hard rules

- No deletion, merge, or rewrite without an explicit go.
- Same-job versus different-job is decided by reading what each skill does, not by comparing names.

## Self-improvement

When the owner overrules a merge or split proposal, record the reasoning in one line here so the next review does not re-propose it. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| A gap that needs a new skill | `skill-finder`, then `skill-maker` |
| Executing an approved rewrite | `skill-maker` (improve mode) |
