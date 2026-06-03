# Writers package

| Module | Role |
| --- | --- |
| `io.py` | `write_json`, `write_text`, `relative_path` |
| `loop_artifacts.py` | Core loop JSON/CSV/report writers |
| `ml_artifacts.py` | ML task output tree |
| `figure_artifacts.py` | Figure render context and loop-bound figures |
| `payloads.py` | `refresh_loop_payloads` (+ legacy aliases) |
| `manifests.py` | Artifact manifest, schema manifest, phase ledger |
| `benchmark.py`, `figure_dispatch.py` | Benchmark grading and figure batch dispatch |
| `constants.py` | Manifest exclusion sets |

Public API: `writers/__init__.py` (same symbols previously imported from monolithic `writers.py`).
