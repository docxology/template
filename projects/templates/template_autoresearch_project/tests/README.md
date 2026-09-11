# template_autoresearch_project tests

Tests for the deterministic bounded AutoResearch public exemplar.

The suite runs against a session sandbox with a copied baseline output tree and
real source/infrastructure paths, so full loop and subprocess tests cannot dirty
tracked artifacts. Tests are mirrored one-to-one with the source subpackage
layout under `tests/<cluster>/` (SUBMODULAR-2).

## Quick Start

```bash
uv run pytest projects/templates/template_autoresearch_project/tests/ -q
```

Pipeline parity:

```bash
uv run python scripts/pipeline/stage_01_test.py --project template_autoresearch_project --project-only
```

## Coverage

| Cluster | Files | Focus |
| --- | --- | --- |
| `loop/` | `test_adapters.py`, `test_config.py`, `test_edge_config.py`, `test_edge_loop.py`, `test_gate_negative_controls.py`, `test_loop.py`, `test_models.py`, `test_scripts.py` | Loop orchestration, configuration parsing, adapters, models, gate negative controls, script smoke coverage |
| `manuscript/` | `test_format_helpers.py`, `test_manuscript_tables.py`, `test_manuscript_variables.py` | Manuscript token coverage, formatters, table builders, and resolved manuscript output |
| `writers/` | `test_artifact_schemas.py`, `test_edge_gates.py`, `test_gate_improvements.py`, `test_reports.py`, `test_writers.py` | Artifact writers, schema conformance, gate improvements, report rendering |
| `diagnostics/` | `test_edge_ledger.py`, `test_source_ledger.py` | Source-ledger contract and edge cases |
| `figures/` | `test_figures.py` | Figure registry and figure writers |
| `ml/` | `test_ml_task.py` | Fixed-seed ML dataset, candidate evaluation, selection, and budget behavior |
| `security/` | `test_security.py` | Local security profile and attestation artifacts |

See [AGENTS.md](AGENTS.md) for local editing guidance.
