# docs/ — Agent-Facing Documentation Hub

## Overview

Technical guide for `projects/code_project/docs/` — the operational rulebook for AI agents and developers working inside the `code_project` exemplar. Every document in this directory is a hard constraint, not a suggestion.

## File Inventory

| File | Purpose | Lines | Status |
|---|---|---|---|
| `README.md` | Quick navigation and audience-targeted entry points | ~45 | Current |
| `AGENTS.md` | This index — technical overview of `docs/` | ~100 | Current |
| `agent_instructions.md` | Behavioral constraints for AI agents (read-first priority) | ~80 | Comprehensive |
| `architecture.md` | Thin orchestrator flow: layers, dependencies, forbidden patterns, how-to-add-algorithm | ~100 | Comprehensive |
| `testing_philosophy.md` | Zero-mock policy; 42 collected tests; coverage mechanics; class inventory | ~90 | Comprehensive |
| `rendering_pipeline.md` | 4-phase manuscript→PDF flow; config.yaml controls; troubleshooting | ~80 | Comprehensive |
| `style_guide.md` | 7 rules: Zero-Mock, Infrastructure Delegation, Thin Orchestrator, Show-Not-Tell, Explicit Paths, Type Hints, Error Messages | ~120 | Comprehensive |
| `syntax_guide.md` | Markdown links, LaTeX refs, all 28 `{{VARIABLE}}` tokens, figure label registry, adding variables/figures | ~130 | Comprehensive |

## Key Conventions

**Read-first protocol**: AI agents must read `agent_instructions.md` before modifying any project file. Skipping this document is the most common source of errors in this project — agents who skip it tend to: introduce mocks (violating Rule 1), write math in `scripts/` (violating Rule 3), or hardcode numbers in manuscript prose (violating Rule 4 of `style_guide.md`). The consequence of any one violation is a CI failure or a misleading exemplar for future users.

**Architecture isolation**: `src/` is pure logic (no `infrastructure.*` imports), `scripts/` is orchestration (no math), `infrastructure/` is operations (cross-cutting). The dependency arrow is strictly one-directional: `scripts/` → `src/`; `scripts/` → `infrastructure/`; `tests/` → `src/`. Nothing imports upward. Violating isolation breaks the reproducibility guarantee: `src/` can be used in any Python environment without the pipeline installed.

**Zero-mock enforcement**: No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in `tests/`. CI enforces this via `scripts/verify_no_mocks.py` before the test stage runs. The enforcement exists because mock tests can pass even when the actual mathematical logic is wrong — they test call signatures, not convergence.

**Show-not-tell**: Manuscript references must use explicit file paths and function names, not vague descriptions. A reader of `02_methodology.md` should be able to open `src/optimizer.py` and find the exact function being discussed within 10 seconds. Vague descriptions like "the test suite validates accuracy" cannot be verified or linked.

## Reading Order

This sequence is intentional. Each document provides context that the next document assumes:

1. **`agent_instructions.md`** — Start here. 7 hard rules; consequence of violating each; verification checklist you run before submitting.
2. **`architecture.md`** — Understand layer boundaries before touching any file. Contains the forbidden-patterns table and the 5-step algorithm-addition protocol.
3. **`testing_philosophy.md`** — Understand the zero-mock constraint and test class inventory before writing or modifying any test. Contains the coverage run command.
4. **`rendering_pipeline.md`** — Understand the 4-phase pipeline before editing manuscript or output paths. Contains all config.yaml controls and troubleshooting steps.
5. **`style_guide.md`** — Understand the 7 style rules before writing any source code. Rules 1–3 govern code; Rules 4–5 govern documentation; Rules 6–7 govern type hints and error messages.
6. **`syntax_guide.md`** — Understand the complete `{{VARIABLE}}` token list and figure label registry before editing any manuscript `.md` file.

## Verification Commands

These three commands verify the most critical constraints. Run all three before submitting any change:

```bash
# Test suite passes + coverage ≥90%
uv run pytest projects/code_project/tests/ \
    --cov=projects/code_project/src \
    --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/code_project/tests/ || echo "Clean"

# src/ has no infrastructure imports
grep -r "from infrastructure\|import infrastructure" \
    projects/code_project/src/ || echo "Clean"
```

## Cross-References

- [`README.md`](README.md) — Quick reference with audience-targeted entry points
- [`../AGENTS.md`](../AGENTS.md) — Project-level documentation (API reference, known issues, full directory map)
- [`../pyproject.toml`](../pyproject.toml) — Coverage gate settings (`fail_under = 90`, `branch = true`)
- [`../tests/conftest.py`](../tests/conftest.py) — `sys.path` setup and `MPLBACKEND=Agg`
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory: `{{VARIABLE}}` protocol, figure list, workflow
- [`../../AGENTS.md`](../../AGENTS.md) — Root template documentation (infrastructure module reference)
