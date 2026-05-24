# tests/infra_tests/skills/

Tests for `infrastructure.skills`: YAML frontmatter parsing, recursive `SKILL.md` discovery under configurable roots, manifest write/check, and CLI entry points.

## Files

- `test_skill_discovery.py` — unit tests with `tmp_path` fixtures; integration checks against the real template repo and `.cursor/skill_manifest.json`
- `test_skill_eval_grader.py` — table-driven expectations for `docs/prompts/_skill-eval/scripts/grade_eval_output.py`
- `test_skill_eval_report.py` — harness ASCII report formatter (`skill_eval/report.py`)
- `test_skill_eval_workspace.py` — persisted run loader (`skill_eval/workspace.py`)
- `test_skill_eval_runner_offline.py` — offline CLI modes (`--save-baseline-only`, `--compare-only`)

## Running

```bash
uv run pytest tests/infra_tests/skills/ -v
uv run pytest tests/infra_tests/skills/ --cov=infrastructure.skills --cov-report=term-missing
```

## See also

- [`../../../infrastructure/skills/AGENTS.md`](../../../infrastructure/skills/AGENTS.md)
