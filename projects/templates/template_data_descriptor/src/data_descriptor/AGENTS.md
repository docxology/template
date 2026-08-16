# data_descriptor - AGENTS.md

Public API lives in `__init__.py`; behavior lives in `descriptor.py` (validation,
fingerprint, readiness, release manifest), `verification.py` (byte-level
descriptor↔file reconciliation), `figures.py` (plot-ready data and truthful
figure descriptions), `figure_pipeline.py` (typed rendering and publication),
and `registry.py` (fail-closed figure-registry persistence). Keep validation
deterministic and file-system independent. Filesystem effects belong only to
explicitly called producer APIs: `verification.py` checks supplied paths,
`figure_pipeline.py` writes the requested figure run, and `registry.py`
mirrors/writes its complete registry. Matplotlib must remain lazy and select
the non-interactive backend before importing `pyplot`, so importing validators
does not trigger rendering. Update `__init__.__all__` when adding public APIs.

`figures.py` also owns immutable figure provenance specs (labels, filenames,
captions, generator names). `figure_pipeline.py` binds one descriptor and
verification snapshot to both the pixels and data-derived alternate text, then
publishes through the byte-compatible local `registry.py` contract. The script
must never reconstruct or publish that evidence independently.
