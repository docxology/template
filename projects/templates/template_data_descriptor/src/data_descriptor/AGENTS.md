# data_descriptor - AGENTS.md

Public API lives in `__init__.py`; behavior lives in `descriptor.py` (validation,
fingerprint, readiness, release manifest), `verification.py` (byte-level
descriptor↔file reconciliation), `figures.py` (plot-ready data preparers, no
matplotlib), and `registry.py` (fail-closed figure-registry publishing used by
standalone clones that lack the monorepo `infrastructure` package). Keep
validation deterministic and file-system independent; only `verification.py`
touches the filesystem for byte checks, and `registry.py` mirrors/writes figure
registry artifacts when called — both only when a caller supplies the paths. Do
not import matplotlib here — rendering is the scripts' job. Update
`__init__.__all__` when adding public functions.

`figures.py` also owns immutable figure provenance specs (labels, filenames,
captions, generator names); the script owns registry file I/O, preferring the
shared `infrastructure.documentation.generated_figure_registry` publisher in the
monorepo and falling back to the byte-compatible `registry.py` implementation on
standalone clones.
