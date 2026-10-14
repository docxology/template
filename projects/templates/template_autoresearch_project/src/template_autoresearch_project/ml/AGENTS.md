# ML package

| Module | Role |
| --- | --- |
| `data.py` | MNIST task config, fixture loading, provenance |
| `models.py` | Baseline/candidate evaluation and robustness |
| `training.py` | Softmax MLP, SGD, metrics |
| `selection.py` | Candidate ranking, tie-break, error examples |
| `task.py` | `run_bounded_ml_task` orchestration |
| `mnist_fixture.py` | Offline fixture download/verify |

Import the public API from `template_autoresearch_project.ml`, or use a specific
implementation module such as `template_autoresearch_project.ml.selection`.
