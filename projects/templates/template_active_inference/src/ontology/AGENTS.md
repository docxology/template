# Ontology Track Notes

Naming and binding contract shared by manuscript sections, GNN annotations,
formal interop artifacts, and generated method inventories.

## Where To Look

| Task | Location |
| --- | --- |
| Load and flatten section ontology | `bindings.py` |
| Public exports | `__init__.py` |
| Canonical terms in use | `../../domain_profile.yaml`, `../../manuscript/sheaf/*.yaml` |

## Contracts

- Add or rename a term once in the source ontology/binding data; do not hard-code
  substitute labels in analytical, simulation, manuscript, or GNN lanes.
- `load_section_ontology()` flattens nested `terms:` blocks. Preserve that
  behavior because generated inventories and semantic gluing depend on it.
- Alias changes are cross-track changes: regenerate formal interop/integration
  audit artifacts before updating claims.
- Missing or ambiguous ontology terms should fail validation rather than silently
  dropping evidence bindings.

## Commands

```bash
uv run pytest tests/test_method_inventory.py tests/test_semantic_sheaf.py tests/test_documentation_contracts.py
uv run python scripts/generate_formal_interop_tracks.py
```
