# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `projects/code_project/docs/` — the operational rulebook for AI agents and developers working inside the `code_project` exemplar.

## Files

| File | Purpose |
|------|---------|
| `agent_instructions.md` | Behavioral constraints for AI agents (read-first priority) |
| `architecture.md` | Thin orchestrator flow: `src/` → `scripts/` → `infrastructure/` |
| `testing_philosophy.md` | Zero-mock standard and 34-test validation strategy |
| `rendering_pipeline.md` | Manuscript-to-PDF flow via `infrastructure.rendering` |

## Key Conventions

- **Read-first protocol**: AI agents must read `agent_instructions.md` before modifying any project file
- **Architecture isolation**: `src/` is pure logic, `scripts/` is orchestration, `infrastructure/` is operations
- **Zero-mock enforcement**: No `unittest.mock`, `MagicMock`, or `@patch` anywhere in the project
- **Show-not-tell**: Manuscript references must use explicit file paths, not vague descriptions

## Reading Order

1. `agent_instructions.md` — Operational constraints (start here)
2. `architecture.md` — Understand modular boundaries
3. `testing_philosophy.md` — Understand test requirements before writing code
4. `rendering_pipeline.md` — Understand how manuscript becomes PDF

## See Also

- [../AGENTS.md](../AGENTS.md) — Project-level technical documentation
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — RASP protocol for manuscript editing
- [../../AGENTS.md](../../AGENTS.md) — Root template documentation
