# .agents - AGENTS.md

Per-folder technical reference for the project-local agent scaffolding.

| Subdirectory | Purpose |
| --- | --- |
| [`skills/`](skills/AGENTS.md) | Project-local skills. Each ships `SKILL.md` with YAML frontmatter. |

## When to update

- A new skill specific to this template lands → add a folder under
  `skills/<name>/` with `SKILL.md`, `AGENTS.md`, `README.md`.
- The release-safety boundary, canonical Stage 02 entrypoint, or render
  workflow changes → refresh `skills/template-redacted-report/SKILL.md` and
  this catalog.
