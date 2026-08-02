# `.agents/skills/` — Skill catalog

Project-local skills for the `template_eda_notebook` exemplar. One folder per
skill; each ships `SKILL.md`, `AGENTS.md`, and `README.md`.

| Skill | Purpose |
| --- | --- |
| [`template-eda-notebook/`](template-eda-notebook/README.md) | Drive the exemplar end-to-end: quick reference, pitfalls, cross-refs. |

## Contract

Every skill folder under `.agents/skills/<name>/` must ship:

- `SKILL.md` — YAML frontmatter (`name`, `description`, `version`, `tags`, …)
  + a body describing **when to use**, **quick reference**, **pitfalls**,
  **cross-refs**.
- `AGENTS.md` — short technical reference for the skill folder.
- `README.md` — purpose + pointer.

See [`AGENTS.md`](AGENTS.md) for the full folder contract.
