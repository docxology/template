# Multi-phase search

This package implements the advanced exemplar's project-specific search layer:
phase parsing, deterministic record filters, optional LLM relevance decisions,
iterative query refinement, and cross-phase deduplication with provenance.

`search.py` is the library surface used by `scripts/01_multi_phase_search.py`.
It writes per-phase records and metadata before producing the combined corpus;
the script only parses CLI options and reports results.

Retarget phases in `../../manuscript/config.yaml`, then run the focused tests in
`../../tests/test_multi_phase_search.py` before refreshing live evidence.
