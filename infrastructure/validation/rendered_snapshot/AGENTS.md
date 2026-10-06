# infrastructure/validation/rendered_snapshot/ - Rendered-Input Snapshot Documentation

## Purpose

The `rendered_snapshot` package commits the current rendered-input and
validation-report fingerprints used by the strict
`check_rendered_provenance` snapshot surface. It was split from the former
single-module `rendered_snapshot.py` (800 lines) to satisfy the line-count
gate; the public import path is unchanged.

## Contracts

- Public snapshot models and builders are exposed from the package root.
- Scan and record implementation helpers live in `_scan` and `_records`;
  focused controls import these helpers directly.
- Scan cache policy is declared once as `CACHE_PARTS` in `_scan.py`.

## Verification

```bash
uv run pytest tests/infra_tests/validation/test_rendered_provenance.py -q
uv run python scripts/gates/module_line_count_check.py
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
