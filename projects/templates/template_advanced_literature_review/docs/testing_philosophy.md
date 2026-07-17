# Testing Philosophy

The suite enforces the repository **no-mocks** rule: real code runs on real
data, HTTP is served locally by `pytest-httpserver`, and file I/O uses real
temp files. `src/` coverage is gated at **≥ 90%** (`pyproject.toml` →
`fail_under = 90`). See [`../tests/AGENTS.md`](../tests/AGENTS.md) for the
concrete per-boundary patterns.

## Why no mocks

A mock asserts that you *called* something; this template asserts what the
code *computed*. Phase filtering, cross-phase overlap, provenance tracking,
and manuscript-token computation all have checkable outputs, so every test
binds to an independently derived expected value rather than a stubbed
return. A green suite therefore means the multi-phase logic is right, not
merely that the wiring was invoked.

## What each layer tests (this project's own `tests/`)

Symlinked modules (`src/analysis/`, `src/knowledge_graph/`,
`src/reproducibility/`, `src/visualization/`) are covered by
`template_literature_meta_analysis`'s own test suite, not duplicated here.
This project's `tests/` directory covers the project-specific surface:

| File | Representative classes / test count | Covers |
| --- | --- | --- |
| `test_advanced_template.py` | `TestConfigValidation`, `TestDeterministicFilters`, `TestPhaseMetadata`, `TestCorpusCoverage`, `TestPhaseOverlap`, `TestMultiPhaseConfig` (33 test methods total) | Multi-phase config validation, per-phase deterministic filtering, phase metadata generation, cross-phase corpus coverage, phase overlap (Jaccard) computation, and end-to-end multi-phase config shape |
| `test_multi_phase_search.py` | 17 test functions | Phase-aware search orchestration (`src/multi_phase/search.py`, `src/literature/multi_phase_search.py`) |
| `test_deep_research_dispatch.py` | 4 test functions | Deterministic offline deep-research replay (`src/deep_research/dispatch.py`) |
| `test_publication_extensions.py` | 18 test functions | Publication/config extensions specific to the advanced template |

## Determinism

All randomness is seeded (default seed `42`, matching the single-term
sibling). The tracked corpus snapshot, phase filtering, and downstream
analysis/embedding stages are reproducible, so re-running the offline
pipeline produces consistent artifacts — the property the drift and
coverage-floor gates rely on.

## Error paths

Network clients degrade gracefully: a failed engine, malformed payload, or
non-convergent phase (e.g. a phase whose `deterministic_filters` yield zero
papers) is caught at a justified safety-net handler and turned into an
empty/`skipped` result rather than an exception. Tests drive those paths with
real fixtures (HTTP errors, malformed JSON, empty per-phase corpora) rather
than injected mock exceptions.

## Coverage

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ \
  --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90 -q
```

Live pass/fail counts and the current coverage percentage belong in
[`../../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md)
— do not hardcode them here.
