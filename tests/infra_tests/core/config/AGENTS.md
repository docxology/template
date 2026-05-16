# core/config/ - Agent Guide

## Purpose

This directory covers `infrastructure.core.config` extension points: registered
project config blocks, strict unknown-key handling, and generated schema output.

## Local Rules

- Reset the schema-extension registry before and after each test that mutates it.
- Use real YAML files in `tmp_path`; do not mock loader I/O.
- Cover both warning mode and strict failure mode when adding config keys.
- Keep project-specific extension tests isolated by project name.

## Validation

```bash
uv run pytest tests/infra_tests/core/config/ -q
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
