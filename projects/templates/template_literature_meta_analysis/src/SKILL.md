---
name: Meta-Analysis Source API
description: Core orchestration guidelines and MCP interactions for the src/ library.
---

# Instructions

You are interfacing with the `src/` directory of the literature meta-analysis project. This directory contains 45+ public APIs spread across 5 submodules.

## Agentic Interface (MCP Strategy)

When operating within this workspace, adhere to the following interaction protocols:

1. **No-Mock Constraint**: If you write tests for these modules, you MUST use `pytest-httpserver` or local data objects. Do not use `mocker.patch` or `MagicMock`.
2. **Execution Context**: Execute modules using the thin orchestrators located in `scripts/`, or by running `uv run pytest` in the `tests/` directory. Do not write temporary execution blocks inside `src/`.
3. **Data Immutability**: The code here processes JSONL and TriG outputs. Ensure you have parsed `manuscript/config.yaml` using your file reading tools to understand runtime constraints.

## Architecture Guidelines for AI Agents

- **Modularity**: Business logic never resides in `scripts/`. It belongs here.
- **Reproducibility**: When adding new NLP or analytical functions, ensure RNG seeds are hardcoded (typically `seed=42`) to guarantee deterministic analysis.
- **Documentation Parity**: If you modify any file here, you must run `python3 -m infrastructure.validation.cli markdown` to verify nothing was broken.

Refer to the specific `SKILL.md` in each subdirectory for granular file-level guidance.
