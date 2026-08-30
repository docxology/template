# infrastructure/validation/rendered_snapshot/ - Rendered-Input Snapshot

Current rendered-input snapshot and validation-report commitments, split from
the former single `rendered_snapshot.py` module for the line-count gate.

## Files

- `__init__.py` - public API; every historical `infrastructure.validation.rendered_snapshot` name re-imported here
- `_scan.py` - repository-boundary scan (`FileRecord`, `Fingerprint`, `cached_records`, `iter_tree_files`, symlink confinement)
- `_records.py` - record-set builders (`_stage_records`, `_project_records`, `_output_records`, `_fingerprint`, `_is_config_path`) and the implementation-root/cache-part constants

## Public API

Import from the package root only:

```python
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
```

All historical names remain importable from
`infrastructure.validation.rendered_snapshot` (see `__init__.py` re-exports,
including legacy test aliases such as `_cached_records`).

## See Also

- [`../AGENTS.md`](../AGENTS.md) - rendered-snapshot role in validation
- [`../../../tests/infra_tests/validation/test_rendered_provenance.py`](../../../tests/infra_tests/validation/test_rendered_provenance.py)
