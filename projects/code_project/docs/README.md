# docs/ — Project Documentation

> **Operational rulebook** for the code_project exemplar

**Quick Reference:** [Agent Instructions](agent_instructions.md) | [Architecture](architecture.md) | [Testing](testing_philosophy.md) | [Rendering](rendering_pipeline.md) | [Style](style_guide.md) | [Syntax](syntax_guide.md) | [Index](AGENTS.md)

## Purpose

The `docs/` directory contains the behavioral and architectural rules that govern modifications to the `code_project` exemplar. Every document here is a hard constraint — not a suggestion. The authoritative file index (including this `README.md` and `AGENTS.md`) lives in [`AGENTS.md`](AGENTS.md).

## Contents

| File | Purpose | Lines | Audience |
|---|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | 7 hard rules for AI agents; verification checklist | ~152 | AI agents, all developers |
| [`architecture.md`](architecture.md) | Layer table, dependency direction, forbidden patterns, how-to-add-algorithm | ~78 | Developers |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, 42-test class inventory, coverage mechanics | ~106 | Developers, testers |
| [`rendering_pipeline.md`](rendering_pipeline.md) | 4-phase manuscript→PDF pipeline; config.yaml controls; troubleshooting | ~159 | Content authors, developers |
| [`style_guide.md`](style_guide.md) | 7 rules: Zero-Mock, Infrastructure Delegation, Thin Orchestrator, Show-Not-Tell, Explicit Paths, Type Hints, Error Messages | ~185 | Developers |
| [`syntax_guide.md`](syntax_guide.md) | Markdown links, LaTeX refs, all 28 `{{VARIABLE}}` tokens, figure label registry | ~194 | Content authors |
| [`AGENTS.md`](AGENTS.md) | Technical index of this `docs/` folder; verification commands | ~67 | Developers, agents |

## Quick Navigation

### Before Modifying Any Code

1. Read **[Agent Instructions](agent_instructions.md)** — 7 rules and the verification checklist
2. Read **[Architecture](architecture.md)** — understand layer boundaries before touching file structure
3. Read **[Testing Philosophy](testing_philosophy.md)** — understand zero-mock constraint before writing tests

### Before Editing Manuscript Files

1. Read **[Rendering Pipeline](rendering_pipeline.md)** — understand the 4-phase pipeline
2. Read **[Syntax Guide](syntax_guide.md)** — complete `{{VARIABLE}}` token list and figure label registry

### Before Writing Source Code

1. Read **[Style Guide](style_guide.md)** — 7 rules covering mocks, imports, error messages, type hints

## Verification Commands

```bash
# Tests pass + coverage ≥90%
uv run pytest projects/code_project/tests/ \
    --cov=projects/code_project/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch" projects/code_project/tests/ || echo "Clean"

# src/ has no infrastructure imports
grep -r "from infrastructure\|import infrastructure" projects/code_project/src/ || echo "Clean"
```

## See Also

- [../AGENTS.md](../AGENTS.md) — Full project documentation (API reference, known issues, complete directory map)
- [../README.md](../README.md) — Project quick start
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript directory rules and `{{VARIABLE}}` protocol
- [../output/AGENTS.md](../output/AGENTS.md) — Disposable-directory contract and regeneration sequence
- [../../docs/](../../docs/) — Repository-level documentation hub (127 files, 14 subdirectories)
