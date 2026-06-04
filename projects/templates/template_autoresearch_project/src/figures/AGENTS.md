# Figures package

| Module | Role |
| --- | --- |
| `figure_specs.py` | Labels, dispatch table, `FigureRenderContext` helpers |
| `figure_registry*.py` | Captions, records, contract checks |
| `figure_style.py`, `figure_quality.py` | Style + quality report |
| `figures_core.py` | Shared chart primitives |
| `figures_ml*.py` | ML calibration, matrices, MNIST panels |
| `figures_process.py`, `figures_security.py` | Stage matrix, security charts |
| `__init__.py` | Public figure writer barrel |

Register new figures in `figure_specs.py` before adding a writer module.
