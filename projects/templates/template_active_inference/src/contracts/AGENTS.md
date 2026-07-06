# Artifact contract SSOT

Single source of truth for artifact relative paths consumed by gates, variable
injection, and test fixtures.

## Module

| Symbol | Role |
| --- | --- |
| `PROMOTED_ARTIFACTS` | Map of logical name → `output/...` path for promoted roadmap artifacts |
| `VARIABLE_ARTIFACTS` | Subset read by `manuscript/variables.py` during token hydration |
| `REQUIRED_GATE_ARTIFACTS` | Minimal artifact tree for gate regression tests (`tests/gate_support.py`) |
| `EXPERIMENT_PLAN_METRIC_KEYS` | Keys aggregated into `experiment_plan_metrics` gate boolean |

## Consumers

- `gates/output_checks_promoted.py` — schema checks against promoted paths
- `manuscript/variables.py` — loads JSON from `VARIABLE_ARTIFACTS`
- `tests/gate_support.py` — bootstraps stable artifact tree for regression tests

Do not duplicate these path maps in gate or variable modules; import from
`contracts.artifact_contract`.
