# `.agents/skills/`

Project-local skill catalog for the `template_prose_project` exemplar.

## Skills

| Skill | Purpose | Load when |
| --- | --- | --- |
| [`template-prose-project/`](template-prose-project/SKILL.md) | Drive this exemplar end-to-end. | Working inside `projects/templates/template_prose_project/`, forking it as a scaffold, or validating its contracts. |

## Folder contract

Every skill folder under `.agents/skills/<name>/` ships three files:

- `SKILL.md` — YAML frontmatter (`name`, `description`, `version`, `tags`)
  plus the operating walkthrough (when to use, quick reference, pitfalls,
  cross-refs).
- `AGENTS.md` — short technical reference and claim-traceability for the
  skill folder.
- `README.md` — purpose + pointer for humans browsing the tree.

See [`AGENTS.md`](AGENTS.md) for the full contract.
