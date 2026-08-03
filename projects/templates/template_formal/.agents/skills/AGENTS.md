# .agents/skills — AGENTS.md

Per-folder technical reference for the project-local skill catalog.
One folder per skill. Each ships `AGENTS.md`, `README.md`, `SKILL.md`.

| Skill | Purpose |
| --- | --- |
| [`template-formal/`](template-formal/AGENTS.md) | Drive this exemplar end-to-end (types → storage → protocol/network → agent → colony → manuscript). |

## Skill contract

Every skill folder under `.agents/skills/<name>/` must ship:

- `SKILL.md` — YAML frontmatter (`name`, `description`, `version`,
  `tags`, …) + a body markdown describing **when to use**, **quick
  reference**, **pitfalls**, **cross-refs**.
- `AGENTS.md` — short technical reference for the skill folder.
- `README.md` — purpose + pointer.

All relative cross-references within these files must resolve against the
folder they live in.
