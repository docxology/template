# Multi-phase search

This package implements the advanced exemplar's project-specific search layer:
phase parsing, deterministic record filters, optional LLM relevance decisions,
iterative query refinement, and cross-phase deduplication with provenance.

`search.py` is the public orchestration façade used by
`scripts/01_multi_phase_search.py`. `models.py` owns the phase/paper records and
`llm_filter.py` owns the optional relevance engine; keeping those contracts
separate prevents the façade from becoming a second monolith. The façade writes
per-phase records and metadata before producing the combined corpus, plus
`cross_phase_analysis.json` with deterministic membership/overlap and configured
citation-sufficiency evidence. That artifact distinguishes structural provenance
from hypothesis scoring; claim-level scores are attached later by the
knowledge-graph stage when assertions exist. The script only parses CLI options
and reports results.

Retarget phases in `../../manuscript/config.yaml`, then run the focused tests in
`../../tests/test_multi_phase_search.py` before refreshing live evidence.
