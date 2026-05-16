# core/telemetry/ - Agent Guide

## Purpose

This directory covers retention behavior for infrastructure telemetry reports.

## Local Rules

- Use real files under `tmp_path`; do not mock filesystem state.
- Keep timestamps deterministic so lexicographic order matches chronology.
- Assert both counts and actual surviving filenames after rotation.
- Cover live-file archival and pruning behavior together.

## Validation

```bash
uv run pytest tests/infra_tests/core/telemetry/ -q
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
