# Source Module Notes

Keep all reusable logic in this directory. Scripts under `../scripts/` should
only parse arguments, resolve paths, and call these functions.

Preserve compatibility exports from `ml_task.py`, `figures.py`, and
`diagnostics.py` when moving implementation details into the split modules.
