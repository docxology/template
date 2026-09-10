# `template_code_project/src/figures/` - agent guide

## Purpose

Importable figure-generation package for the code exemplar.

## Rules

- Keep scripts as thin wrappers; figure assembly belongs in this package.
- Do not move optimizer math into figure modules.
- Use real project outputs or typed config inputs in tests; avoid mocks.
- Write generated files only from explicit orchestration paths.

## See Also

- [`README.md`](README.md) - quick reference
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
