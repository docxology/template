# Startup skill

## Overview

Agent skill `template-startup` — full installation and validation for a fresh clone of the Research Project Template. Installs dependencies, runs pre-commit hooks, executes the core pipeline against `template_code_project`, validates outputs, and reports a structured PASS / FAIL.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
| [`README.md`](README.md) | Human-facing overview |

## Verification

```bash
# Confirm the skill produces a passing pipeline run:
./run.sh --pipeline --project templates/template_code_project --core-only
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
- [`../../../START_HERE.md`](../../../START_HERE.md) — repo entry point
- [`../../../docs/guides/startup-and-setup.md`](../../../docs/guides/startup-and-setup.md) — detailed guide
