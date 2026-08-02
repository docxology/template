# `.agents/` — Agent-facing orientation

Project-local agent scaffolding for the `template_eda_notebook` exemplar.

| Path | Role |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Technical reference: directory layout + change discipline. |
| [`skills/`](skills/README.md) | Project-local skill catalog (one folder per skill). |

## Working inside this exemplar

Load the project skill at
[`skills/template-eda-notebook/SKILL.md`](skills/template-eda-notebook/SKILL.md)
for when-to-use guidance, quick-reference commands, and pitfalls. Read
[`../AGENTS.md`](../AGENTS.md) (the exemplar's layer contract) and
[`../docs/agent_instructions.md`](../docs/agent_instructions.md) before
modifying any project file.

## When to update

- A new project-specific skill lands → add a folder under
  `skills/<name>/` shipping `SKILL.md`, `AGENTS.md`, `README.md` (see
  [`skills/AGENTS.md`](skills/AGENTS.md)).
