# infrastructure/validation/rendered_snapshot/ - Rendered-Input Snapshot

Current rendered-input snapshot and validation-report commitments, split from
the former single `rendered_snapshot.py` module for the line-count gate.

## Files

- `__init__.py` - public snapshot models and builders
- `_scan.py` - repository-boundary scan (`FileRecord`, `Fingerprint`, `cached_records`, `iter_tree_files`, symlink confinement)
- `_records.py` - record-set builders (`_stage_records`, `_project_records`, `_fingerprint`, `_is_config_path`) and implementation-root selection
- `_inputs.py` - fail-closed admission of explicit compiler-owned generated ordering

## Public API

Import from the package root only:

```python
from infrastructure.validation.rendered_snapshot import (
    build_current_rendered_snapshot,
    declared_generated_manuscript_inputs,
)
```

Focused implementation controls import scanning helpers from `_scan.py`.

The generated-input contract is documented in
[`../README.md`](../README.md#rendered-input-commitments).

For ignored working/external outputs,
`publication.rendered_provenance.validate_current_rendered_provenance` checks
the complete coherent derived snapshot. It does not grant native execution or
acceptance authority. `validate_rendered_provenance` additionally requires
byte-clean published Git evidence; current consistency cannot replace that
publication boundary.

## Verification

```bash
uv run pytest tests/infra_tests/validation/test_rendered_provenance_roles.py \
  tests/infra_tests/validation/test_rendered_provenance_stage_closures.py \
  tests/infra_tests/validation/test_rendered_validation_input_diagnostics.py -q
uv run python scripts/gates/module_line_count_check.py
```

## See Also

- [`../AGENTS.md`](../AGENTS.md) - rendered-snapshot role in validation
- [`../../../tests/infra_tests/validation/`](../../../tests/infra_tests/validation/) - rendered-provenance tests (`test_rendered_provenance_*` cluster)
