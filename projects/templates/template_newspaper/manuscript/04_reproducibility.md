# Reproducibility

The artifact is produced by a deterministic, three-step chain that the
repository pipeline runs as Stage-02 analysis scripts, in lexicographic order:
`00_preflight.py` confirms the dependencies import and the edition loads and
validates; `10_generate_figures.py` writes the halftone scenes and charts to
`output/figures/`; and `20_render_newspaper.py` renders the twelve pages to
`output/pdf/the-triplicate.pdf` and emits a machine-readable render report
(`output/data/render_report.json`) plus a human summary. The render is
deterministic — the canvas is opened in ReportLab's `invariant` mode and the
figures are drawn from fixed procedural recipes — so the same content yields the
same bytes.

Correctness is established two ways. A `pytest` suite exercises the pure logic
(geometry, configuration, content loaders, typography, figure generation) and
renders the real edition end-to-end, asserting that the output is a valid PDF of
exactly twelve pages at the correct trim with no over-set page. Because the
remaining correctness of a *layout* is visual, the development loop rasterizes
each page and inspects it; the project's agent guidance makes that visual check
mandatory after any layout change. The engine is type-checked with mypy and
linted with ruff, and the test suite reports roughly ninety-five percent line
coverage.

Every quantitative claim in this project — the page count, the trim dimensions,
the figure count — is recorded in `data/claim_ledger.yaml` against the artifact
that substantiates it, so a reviewer can trace each number to its source.
