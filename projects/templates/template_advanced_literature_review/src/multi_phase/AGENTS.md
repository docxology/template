# Multi-Phase Search — Agent Directives

`search.py` owns phase-aware retrieval, deterministic and optional LLM filtering,
deduplication, cross-phase citation checks, and provenance output. Keep
`scripts/01_multi_phase_search.py` as a thin CLI entrypoint.

## Contracts

- Every retained paper records its discovery phase and every later phase where it reappeared.
- Missing year, citation, or venue metadata is retained rather than silently treated as a failing measurement.
- LLM filters are optional, fail closed with the `error` label, and use a configurable base URL and timeout.
- Tests exercise HTTP through a real local server; do not introduce mock frameworks or network dependence.
- Output paths are injected into `MultiPhaseSearchRunner`; never write relative to the caller's current working directory.
- Keep live retrieval separate from deterministic downstream analysis. A corpus refresh is an intentional network operation.
