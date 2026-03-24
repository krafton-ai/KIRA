---
name: skill-creator
description: >
  Create or refine KiraClaw/Codex skills as concise SKILL.md packages. Trigger on:
  "make a skill", "create a skill", "update this skill", "seed skill", "default skill",
  or when the user wants reusable agent workflow instructions instead of one-off prompt text.
---

# Skill Creator

Use this skill when the task is to create or refine a reusable skill package.

## Goals

- keep the skill short enough to load cheaply
- encode workflow, not generic model intelligence
- use references or scripts only when they clearly reduce risk or repetition
- fit KiraClaw's seeded-skill layout under `Filesystem Base Dir/skills`

## Workflow

1. Define the trigger clearly:
   - what user requests should activate this skill?
   - what should not activate it?
2. Decide the scope:
   - one focused workflow per skill
   - avoid combining unrelated jobs into one package
3. Write the frontmatter carefully:
   - `name`
   - `description`
   - include trigger examples in the description
4. Write the body as operational guidance:
   - workflow steps
   - failure modes
   - decision rules
   - exit criteria
5. Add references or scripts only if they reduce repeated work or improve reliability.

## Rules

- Prefer one strong skill over one huge omnibus skill.
- Do not explain concepts the base model already knows unless the local workflow is special.
- Do not turn the skill into a README or changelog.
- If the skill depends on local tools, directories, or conventions, say so directly.
- Keep examples short and realistic.

## Good Skill Shape

Most good skills have:
- a narrow trigger
- a short workflow
- a few rules that prevent common mistakes
- one or two high-value examples

## When to Split

Split the skill if:
- it has multiple unrelated trigger families
- it needs different rules for different domains
- the body is becoming reference material instead of workflow guidance

## Seed Skill Guidance

For seeded default skills:
- optimize for broad usefulness
- avoid org-private assumptions
- keep the body compact so new workspaces do not inherit unnecessary prompt weight

## Validation

Before finishing a new skill, check:
- is the trigger description specific enough?
- does the body contain real workflow guidance?
- can at least one realistic task use it without extra explanation?
