# Manuscript composition

Composes the multi-track section sources into the manuscript and hydrates
run-derived values.

- `sheaf/` — sheaf composition package: glues per-track section fragments
  (`../../manuscript/sections/`) into coherent sections per the sheaf manifest;
  `coverage.py` builds the B/W/G matrix and heatmap inputs.
- `variables.py` — hydrate run-derived numbers into manuscript variable tokens
  so prose values trace to generated artifacts.
