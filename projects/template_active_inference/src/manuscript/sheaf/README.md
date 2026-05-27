# Sheaf composition package

Implementation of the sheaf manuscript composition.

- `models.py` — data models for tracks, sections, and the sheaf manifest.
- `manifest.py` — load/validate the `manuscript/sheaf/` manifest and tracks.
- `registry.py` — track/fragment registry.
- `renderers.py` — per-track fragment renderers.
- `compose.py` — glue fragments into composed manuscript sections.
- `coverage.py` — verify every declared track/section fragment is present.
