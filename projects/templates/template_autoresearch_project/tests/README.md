# template_autoresearch_project tests

Tests for the deterministic bounded AutoResearch public exemplar.

The suite runs against a session sandbox with copied project inputs and
real source/infrastructure paths, so full loop and subprocess tests cannot dirty
tracked artifacts. Output consumers explicitly request the actual deterministic
session loop; source-only exports do not need precomputed outputs. Tests are mirrored one-to-one with the source subpackage
layout under `tests/<cluster>/` (SUBMODULAR-2).

## Quick Start

```bash
uv run pytest projects/templates/template_autoresearch_project/tests/ -q
```

Pipeline parity:

```bash
uv run python scripts/pipeline/stage_01_test.py --project template_autoresearch_project --project-only
```

## Outside the monorepo

Source-integration cases consume the real platform DAG, analysis scripts,
build metadata, and canonical exemplar configuration. An installed platform
wheel supplies Python imports but does not supply that checkout. Outside the
canonical `projects/templates/template_autoresearch_project` layout, nominate
both `TEMPLATE_AUTORESEARCH_SOURCE_ROOT` (an absolute public platform checkout)
and `TEMPLATE_AUTORESEARCH_SOURCE_COMMIT` (its exact 40-character Git commit).
The checkout must declare `research-project-template` 4.0.2, remain clean, and
contain the actual committed input bytes. A nearby `infrastructure/` directory,
the current working directory, and abbreviated revisions confer no authority.

Use the prepared project interpreter and commands in
[`../STANDALONE.md`](../STANDALONE.md#full-suite-source-integration). These cases
are source integration; `loop/test_standalone_hydration.py` separately builds
and admits a genuine platform wheel, installs it independently, and checks its
installed import origin. Missing source/build tools or uncached dependencies
fail the required case rather than skipping it. Local real-Git provider controls
commit genuine current platform input bytes only in disposable fixtures; their
commits are not public release evidence.

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
