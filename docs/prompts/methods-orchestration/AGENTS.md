# Methods Orchestration Skill

Use `SKILL.md` for repo-wide methods orchestration work.

Primary infrastructure:

```bash
uv run python -m infrastructure.methods plan --project <project> --format json --check
```

Keep edits in source layers. Generated output is evidence, not the fix target.
