# registered_report - AGENTS.md

Keep validation deterministic. Do not read result files inside the core validators unless callers pass the data explicitly.

`figures.py` owns immutable label/filename/caption/generator specs alongside
the deterministic renderers; the thin script owns output mirroring and JSON I/O.
