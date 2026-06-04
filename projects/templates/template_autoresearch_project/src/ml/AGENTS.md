# ML package

| Module | Role |
| --- | --- |
| `data.py` | MNIST task config, fixture loading, provenance |
| `models.py` | Baseline/candidate evaluation and robustness |
| `training.py` | Softmax MLP, SGD, metrics |
| `selection.py` | Candidate ranking, tie-break, error examples |
| `task.py` | `run_bounded_ml_task` orchestration |
| `mnist_fixture.py` | Offline fixture download/verify |

Root stubs: `ml_task.py`, `ml_data.py`, `ml_models.py`, `ml_selection.py`, `ml_training.py` (`mnist_fixture.py` uses `sys.modules` alias for monkeypatch tests).
