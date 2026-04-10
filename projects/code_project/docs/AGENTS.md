# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `projects/code_project/docs/` — the operational rulebook for AI agents and developers working inside the `code_project` exemplar.

## Files

| File | Purpose |
| --- | --- |
| `README.md` | Quick navigation and table of contents |
| `AGENTS.md` | This index (technical overview of `docs/`) |
| `agent_instructions.md` | Behavioral constraints for AI agents (read-first priority) |
| `architecture.md` | Thin orchestrator flow: `src/` → `scripts/` → `infrastructure/` |
| `testing_philosophy.md` | Zero-mock policy; **39** collected tests; ≥90% coverage gate on `src/` |
| `rendering_pipeline.md` | Manuscript-to-PDF flow via `infrastructure.rendering` |
| `style_guide.md` | Core programming principles (Zero-Mock, documentation links) |
| `syntax_guide.md` | Manuscript markdown syntax (Madlibs, Pandoc format, labels) |

## Key Conventions

- **Read-first protocol**: AI agents must read `agent_instructions.md` before modifying any project file
- **Architecture isolation**: `src/` is pure logic, `scripts/` is orchestration, `infrastructure/` is operations
- **Zero-mock enforcement**: No `unittest.mock`, `MagicMock`, or `@patch` anywhere in the project
- **Show-not-tell**: Manuscript references must use explicit file paths, not vague descriptions

## Reading Order

1. `agent_instructions.md` — Operational constraints (start here)
2. `architecture.md` — Modular boundaries
3. `testing_philosophy.md` — Test requirements before writing code
4. `rendering_pipeline.md` — How manuscript becomes PDF
5. `style_guide.md` / `syntax_guide.md` — Code and manuscript conventions

## See Also

- [README.md](README.md) — Quick reference (mirrors file list with audience hints)
- [../AGENTS.md](../AGENTS.md) — Project-level technical documentation
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript directory: variables, SYNTAX, workflow
- [../../AGENTS.md](../../AGENTS.md) — Root template documentation
