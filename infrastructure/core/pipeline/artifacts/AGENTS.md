# infrastructure/core/pipeline/artifacts/ — Artifact Manifest Package

## Purpose

Stable output inventory scanning and stage artifact manifest I/O for pipeline
reproducibility controls. Split from the former single-module `artifacts.py`
(898 lines) to satisfy the line-count gate; the public import path is unchanged.

## Layout

| Module | Responsibility |
| --- | --- |
| [`__init__.py`](__init__.py) | Public re-exports; `_declared_output_paths` alias for incremental hashing |
| [`_inventory.py`](_inventory.py) | Git-ignore evaluation, stable shippable output inventory |
| [`_manifest.py`](_manifest.py) | Manifest schema, write/aggregate/validate, `declared_output_paths` |

## Contracts

- Callers import from `infrastructure.core.pipeline.artifacts` only.
- `declared_output_paths` is the public name; `_declared_output_paths` remains
  as a backward-compatible alias.
- `_git_ignore_matches` is exported for infra tests that pin git-ignore semantics.

## Verification

```bash
uv run pytest tests/infra_tests/core/test_artifact_manifest_semantics.py \
  tests/infra_tests/core/pipeline/test_artifact_finalization.py -q
uv run python scripts/gates/module_line_count_check.py
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
