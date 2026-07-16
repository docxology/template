# Deep Research Replay — Agent Directives

Stage 08 demonstrates the shared provider-neutral deep-research models without
submitting a paid or non-deterministic job. `dispatch.py` builds the genuine
`DeepResearchRequest`, normalizes the tracked fixture through
`DeepResearchResult`, and writes `deep_research_replay.json`.

## Invariants

- The default path is offline and deterministic. Never call `submit()` here.
- Replay fails closed when its fixture is absent or malformed.
- Fixture citations must identify real primary sources. Prefer metadata-only
  citations rather than invented excerpts or offsets.
- Keep network/provider SDK imports lazy in shared infrastructure; this package
  only uses the exported provider-neutral models and client configuration.
- `scripts/08_deep_research_dispatch.py` is a thin CLI boundary. Keep replay,
  normalization, and artifact persistence in `dispatch.py`.
- Exercise behavior with real files and dataclasses; do not use mocks.

The infrastructure import is intentional and declared in
`manuscript/layer_contract.yaml`.
