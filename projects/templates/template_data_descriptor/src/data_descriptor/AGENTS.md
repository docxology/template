# data_descriptor - AGENTS.md

Public API lives in `__init__.py`; behavior lives in `descriptor.py` (validation,
fingerprint, readiness, release manifest), `verification.py` (byte-level
descriptor↔file reconciliation), and `figures.py` (plot-ready data preparers, no
matplotlib). Keep validation deterministic and file-system independent; only
`verification.py` touches the filesystem, and only when a caller supplies a base
directory. Do not import matplotlib here — rendering is the scripts' job. Update
`__init__.__all__` when adding public functions.

`figures.py` also owns immutable figure provenance specs (labels, filenames,
captions, generator names); the script owns registry file I/O.
