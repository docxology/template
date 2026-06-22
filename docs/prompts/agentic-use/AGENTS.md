# Agentic use skill

## Overview

Agent skill `template-agentic-use` - skill discovery, routing hardening, optional external-skill review, and external agentic operating-model reference adoption for the Research Project Template.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## External references

Route Steward OS-style, AutoResearch CLI-style, and LEANN-style requests here when the user asks to review an external agentic maintenance system, measurement-loop tool, semantic-retrieval system, or other outside reference. Keep the default implementation template-native: paraphrase and attribute useful patterns, update routing/evals, add optional local guides when appropriate, and do not vendor external `SKILL.md` files, install MCP servers, or add public-write automation without an explicit separate request.

## Verification

```bash
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run pytest tests/infra_tests/skills -q
uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --fail-under 0.96
```

## See also

- [`../AGENTS.md`](../AGENTS.md) - prompts hub
- [`../SKILL.md`](../SKILL.md) - workflow router
- [`../../../infrastructure/skills/SKILL.md`](../../../infrastructure/skills/SKILL.md) - discovery API
