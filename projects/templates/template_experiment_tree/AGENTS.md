# AGENTS.md — template_experiment_tree

Technical reference for the living-record exemplar. Companion to
[README.md](README.md). All business logic lives in `src/template_experiment_tree/`;
`scripts/` are thin orchestrators.

## Module map (`src/`)

| Module | Responsibility |
| --- | --- |
| `tree.py` | `ExperimentNode`, `ExperimentTree`, `NodeStatus` (provisional/frozen/answered), run_command contract, frozen-node immutability. |
| `store.py` | Deterministic JSON persistence (`output/data/experiment_tree.json`), schema-checked round-trip. |
| `report.py` | `summarize`, `render_markdown`, `render_variables`, `flatten_sections`, fail-closed token resolution. |
| `manuscript_variables.py` | `generate_variables` — the canonical hydration entrypoint backing `scripts/z_generate_manuscript_variables.py`. |

## Invariants (each locked by a negative-control test)

1. Answering a frozen node raises `ExperimentTreeError` (preregistration invariant).
2. One run_command per tree — a conflicting declaration raises.
3. A manuscript token without tree-derived backing raises (`KeyError` / `ManuscriptVariablesError`).

## Conventions

- Deterministic, offline, no mocks; 90% coverage floor on `src/`.
- Scripts are thin orchestrators importing from `src/`.
- Qualified pipeline name: `templates/template_experiment_tree`.


## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Tree structure and node statuses | `output/data/experiment_tree.json` (committed) — frozen nodes are immutable |
| Run command contract | identical across every node in one tree; validated by `src/template_experiment_tree/tree.py` |
| Manuscript values | generated `{{EXP_*}}` variables from `manuscript_variables.json`; a token with no tree backing fails |
| Configuration | `manuscript/config.yaml` |

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md):
record every experiment as an answered tree node with its evidence path, and
never edit answered nodes (regenerate the manuscript from the tree instead).
