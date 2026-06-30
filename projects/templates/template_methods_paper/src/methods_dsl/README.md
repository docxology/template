# `template_methods_paper/src/methods_dsl/`

Tested controlled-method specification library for the methods-paper exemplar.

The analysis script (`scripts/methods_analysis.py`) and the manuscript
variable generator (`src/manuscript_variables.py`) call these functions
instead of burying logic in either place, so the methodology the paper
describes is reproducible and unit-tested.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Public DSL exports re-exported from `src/__init__.py`. |
| `vocabulary.py` | Controlled-vocabulary `StepKind` and `Target` enums; `target_accepts`. |
| `units.py` | Dimensional-safety unit system: `Dimension`, `DimensionError`, `Quantity`. |
| `model.py` | `Method`, `Step`, `Resource`, `Parameter` frozen dataclasses with shape validation. |
| `validation.py` | Four staged gates (`structural_gate`, `semantic_gate`, `plan_gate`, `target_gate`) and `run_all_gates`. |
| `compiler.py` | `topological_order` (Kahn's algorithm) and `compile_method` — deterministic `Method` → `Plan`. |
| `export.py` | Worklist markdown, CSV, Mermaid graph, and canonical JSON renderers for a `Plan`. |
| `trust.py` | `ProvenanceTier` and a hash-chained `StateRecord` history (`append_record`, `verify_chain`). |
| `examples_methods.py` | Two worked example methods (`pbs_preparation_method`, `sensor_calibration_method`) used by the script, tests, and manuscript. |
| `_logging.py` | The one sanctioned `infrastructure.*` import (logging adapter; falls back to stdlib `logging` when forked standalone). |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
- [`AGENTS.md`](AGENTS.md) - subpackage-level rules
