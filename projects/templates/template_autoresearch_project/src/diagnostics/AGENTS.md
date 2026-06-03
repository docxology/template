# Diagnostics package

| Module | Role |
| --- | --- |
| `records.py` | Prediction records and row validators |
| `metrics.py` | Class metrics, calibration, robustness, training dynamics |
| `intervals.py` | Wilson/bootstrap intervals, rank stability, paired stats |
| `reports.py` | Bundle assembly, selection audit, JSON writers |
| `__init__.py` | Public facade (`diagnostic_bundle`, writers re-exported to tests) |

No root `diagnostics.py` — the package name is canonical.
