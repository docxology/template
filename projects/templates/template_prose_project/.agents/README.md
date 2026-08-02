# `.agents/`

Agent-facing orientation for the `template_prose_project` exemplar's local
skill scaffolding.

## What lives here

| Path | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Technical reference: what this directory holds and when to update it. |
| [`skills/`](skills/README.md) | Project-local skill catalog (one folder per skill). |

## For agents

The substantive guidance for working inside this exemplar lives in the
project root files — start with [`README.md`](../README.md) and
[`AGENTS.md`](../AGENTS.md) — and the project-scoped skill at
[`skills/template-prose-project/SKILL.md`](skills/template-prose-project/SKILL.md),
which is the Hermes/agentskills.io-compatible operating walkthrough for
driving this exemplar end-to-end.

## When to update

- A new skill specific to this template lands → add a folder under
  `skills/<name>/` with `SKILL.md`, `AGENTS.md`, `README.md` (see
  [`skills/AGENTS.md`](skills/AGENTS.md)).
