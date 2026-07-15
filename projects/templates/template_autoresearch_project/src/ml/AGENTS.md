# ML package

| Module | Role |
| --- | --- |
| `data.py` | MNIST task config, fixture loading, provenance |
| `models.py` | Baseline/candidate evaluation and robustness |
| `training.py` | Softmax MLP, SGD, metrics |
| `selection.py` | Candidate ranking, tie-break, error examples |
| `task.py` | `run_bounded_ml_task` orchestration |
| `mnist_fixture.py` | Offline fixture download/verify |

The flat→package migration is complete: no root-level `ml_task.py`, `ml_data.py`,
`ml_models.py`, `ml_selection.py`, or `ml_training.py` stub files exist (see
`../AGENTS.md`). Import directly from this package, e.g. `from src.ml import task`.
