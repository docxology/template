# `template_experiment_tree/src/`

Domain engine for the living research record: pure, offline, deterministic
functions over the experiment tree. The thin `scripts/` orchestrators call
these on the filesystem's behalf.

## Modules

| Module | Public exports |
|---|---|
| `template_experiment_tree/tree.py` | `ExperimentNode`, `ExperimentTree`, `NodeStatus` (provisional/frozen/answered), `ExperimentTreeError`; run_command contract and frozen-node immutability. |
| `template_experiment_tree/store.py` | `save_tree`, `load_tree`, `tree_to_payload`, `tree_from_payload`, `default_store_path`, `ExperimentStoreError` — deterministic JSON at `output/data/experiment_tree.json` (`experiment-tree-v1`). |
| `template_experiment_tree/report.py` | `summarize`, `render_markdown`, `render_variables`, `flatten_sections`, `resolve_token_map` — fail-closed token resolution. |
| `template_experiment_tree/manuscript_variables.py` | `generate_variables`, `resolve_tokens`, `validate_tree`, `ManuscriptVariablesError` — the canonical hydration entrypoint behind `scripts/z_generate_manuscript_variables.py`. |

## Quick start

Programmatic use (`src/` must be importable; `tests/conftest.py` puts it
on the path):

```python
from template_experiment_tree import ExperimentTree, save_tree, render_markdown

tree = ExperimentTree()
tree.add_node("E001", "Baseline", "python scripts/run_baseline.py", round_number=1)
tree.record_answer("E001", "converged", "win")
save_tree(tree, "output/data/experiment_tree.json")
print(render_markdown(tree))
```

## Invariants

- **Frozen nodes are immutable.** Answering a frozen node raises `ExperimentTreeError` (preregistration invariant).
- **One `run_command` per tree.** A conflicting declaration raises.
- **Tokens fail closed.** A `{{TOKEN}}` with no tree-derived backing
  raises (`KeyError` / `ManuscriptVariablesError`).
- **No I/O outside `store.py` and `manuscript_variables.py`.** Tree and
  report logic run against in-memory `ExperimentTree` objects.

See [`AGENTS.md`](AGENTS.md) for module map, negative-control tests, and
ground truth; project-level policy is [`../AGENTS.md`](../AGENTS.md).