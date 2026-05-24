---
name: template-test-creation
description: |
  Create pytest suites under the no-mocks policy — real data, temp files, subprocess,
  pytest-httpserver. USE WHEN adding tests, raising coverage, testing new src/ module,
  or user forbids mocks.
---

# Test creation

## Natural invoke

- "Add tests for projects/template_code_project/src/optimization.py"
- "Raise coverage on infrastructure/validation to pass 60% gate"
- "Test this CLI with subprocess, no mocks"

## Inputs to confirm

- **Code under test** — module/path.
- **Layer** — infrastructure (60%) vs project (90%).

## Workflow

1. **No mocks** — never `unittest.mock`, `MagicMock`, or patch the unit under test. Use real computation, `tmp_path`, local HTTP servers, subprocess for CLIs.

2. **Structure** — `test_*.py` mirroring src modules; parametrize variants; fixed RNG seeds.

3. **Coverage** — run pytest-cov; meet floor for layer.

4. **Integration** — wire into `projects/<n>/tests/` or `tests/infra_tests/` following existing layout.

## Deliverables

- Test file(s) with passing run and coverage report excerpt
- Note any opt-in markers (`requires_latex`, `requires_ollama`)

## Verification commands

```bash
uv run pytest path/to/test_file.py -v
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90
uv run pytest tests/infra_tests/path/ --cov=infrastructure --cov-fail-under=60
```

## When NOT to use

- **Implement feature + tests together** → [feature-addition](../feature-addition/SKILL.md) or [code-development](../code-development/SKILL.md)

## References

- [`docs/rules/testing_standards.md`](../../rules/testing_standards.md)
- Patterns: [references/patterns.md](references/patterns.md)
