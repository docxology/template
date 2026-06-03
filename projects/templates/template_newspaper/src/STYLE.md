# src/ Style

- `from __future__ import annotations`; full type hints; Python 3.10+.
- Dataclasses for the content model; `frozen=True` for value objects (geometry,
  config).
- Strict loaders raise `ValueError` quoting the bad value and the allowed set.
- Small, single-purpose functions; docstrings explain *why*.
- No font name outside `typography.py`; no copy/strings of edition content in
  any module.
- Defensive rendering: missing font → base-14; missing image → placeholder.
- Keep `geometry`/`content`/`config` free of ReportLab imports.
