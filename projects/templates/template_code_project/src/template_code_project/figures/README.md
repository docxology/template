# `template_code_project/src/figures/`

Figure builders for the code exemplar.

This package contains the importable Matplotlib figure workflows used by the
project scripts. Keep figure-specific data shaping here, keep optimization math
in `src/optimizer.py` and `src/invariants.py`, and keep CLI parsing in
`scripts/`.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Public figure-builder exports. |
| `_common.py` | Shared plotting helpers. |
| `convergence.py` | Convergence and rate-comparison figures. |
| `scientific.py` | Benchmark and stability figures. |
| `sensitivity.py` | Step-size sensitivity figures. |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
