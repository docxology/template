# infrastructure/validation/rendered_snapshot/ - Rendered-Input Snapshot

Current rendered-input snapshot and validation-report commitments, split from
the former single `rendered_snapshot.py` module for the line-count gate.

## Files

- `__init__.py` - public snapshot models and builders
- `_scan.py` - repository-boundary scan (`FileRecord`, `Fingerprint`, `cached_records`, `iter_tree_files`, symlink confinement)
- `_records.py` - record-set builders (`_stage_records`, `_project_records`, `_fingerprint`, `_is_config_path`) and implementation-root selection

## Public API

Import from the package root only:

```python
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
```

Focused implementation controls import scanning helpers from `_scan.py`.

## See Also

- [`../AGENTS.md`](../AGENTS.md) - rendered-snapshot role in validation
- [`../../../tests/infra_tests/validation/`](../../../tests/infra_tests/validation/) - rendered-provenance tests (`test_rendered_provenance_*` cluster)
