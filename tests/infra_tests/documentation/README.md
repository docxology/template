# Documentation Infrastructure Tests

Tests exercise figure metadata persistence, generated-file registries,
source-derived documentation, publication records, and measured-fact producers.

## Commands

```bash
uv run pytest tests/infra_tests/documentation/ -v
uv run pytest tests/infra_tests/documentation/test_figure_manager.py tests/infra_tests/documentation/test_generated_figure_registry.py -v
uv run pytest tests/infra_tests/documentation/ --cov=infrastructure.documentation --cov-report=term
```

## Test map

| Modules | Verified behavior |
| --- | --- |
| `test_figure_manager.py` | Real registration, labels, metadata serialization, JSON reload, Markdown inventories, and corrupt-registry recovery. |
| `test_generated_figure_registry.py` | Missing/deleted outputs, duplicate labels or filenames, invalid specifications, deterministic writes, and refusal before partial publication. |
| `test_glossary_gen.py`, `test_generate_glossary_cli.py` | Source AST extraction, API tables, marker replacement, and actual CLI execution. |
| `test_api_reference_gen.py`, `test_stage_table.py` | Declared export resolution and YAML-derived documentation. |
| `test_counts_*.py`, `test_coverage_snapshot_output.py` | Measured counts, coverage-input provenance, isolated measurement, and exact independent snapshot handling. |
| `test_active_projects_doc.py`, `test_architecture_overview.py` | Canonical public roster and architecture generation. |
| `test_publication_records*.py` | Publication identities, source records, workflow inputs, and rendered tables. |
| `test_backlog.py`, `test_security_policy.py`, `test_maintenance_doc_reachability.py` | Future-work contracts, documented policies, and maintenance documentation reachability. |

## Real metadata test pattern

Use a unique temporary registry and assert its persisted behavior:

```python
from infrastructure.documentation import FigureManager


def test_registry_round_trip(tmp_path):
    path = tmp_path / "registry.json"
    manager = FigureManager(str(path))
    original = manager.register_figure(
        filename="figure.png", caption="Measured result.", label="fig:result"
    )
    restored = FigureManager(str(path)).get_figure("fig:result")
    assert restored == original
```

Generated-registry tests additionally create actual output files, remove or
corrupt required inputs, and assert publication refusal. Keep filesystem and
Source DATA mutations confined to each test's owned temporary paths.

## See Also

- [Agent test contract](AGENTS.md)
- [Documentation module](../../../infrastructure/documentation/README.md)
- [Infrastructure tests](../README.md)
