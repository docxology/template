# infrastructure/validation/rendered_snapshot/ - Rendered-Input Snapshot Documentation

## Purpose

The `rendered_snapshot` package commits the current rendered-input and
validation-report fingerprints used by the strict
`check_rendered_provenance` snapshot surface. It was split from the former
single-module `rendered_snapshot.py` (800 lines) to satisfy the line-count
gate; the public import path is unchanged.

## Contracts

- Public API stays at the package root (`__init__.py`); companion modules are
  private (`_scan`, `_records`). Do not import companions from outside.
- Every historical name must keep importing from
  `infrastructure.validation.rendered_snapshot`; the doc-pair lint and the
  provenance tests pin this.
- Constants shared across builders (`_IMPLEMENTATION_ROOTS`, `_CACHE_PARTS`)
  live beside their consumers in `_records.py`.

## Verification

```bash
uv run pytest tests/infra_tests/validation/test_rendered_provenance.py -q
uv run python scripts/gates/module_line_count_check.py
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
