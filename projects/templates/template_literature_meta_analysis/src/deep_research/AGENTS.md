# Deep Research Adapter — Agent Directives

## Overview

A single thin adapter (`deep_research_adapter.py`) over the shared
`infrastructure.search.deep_research` package — the provider-neutral dispatch
surface for OpenAI / Gemini deep-research agents. This exemplar exercises that
capability **offline and deterministically** via recorded-report replay; it
never performs a live (paid, non-deterministic) call. The orchestrator is
`scripts/08_deep_research_dispatch.py`.

## Invariants Agents Must Preserve

- **Offline by default**: `replay_recorded_report()` reads a recorded JSON
  fixture and rebuilds the real `DeepResearchResult`. No network call, no API
  key. Do not add a live dispatch to the default path.
- **Fail closed**: replay raises `FileNotFoundError` when the fixture is
  missing — it never fabricates a passing run. Mirrors `template_sia`'s
  fixture-replay/live separation.
- **Real infrastructure symbols only**: import `DeepResearchConfig`,
  `DeepResearchRequest`, `DeepResearchResult`, `DeepResearchClient`,
  `DeepResearchCitation`, `DEFAULT_OPENAI_MODEL`, `DEFAULT_GEMINI_AGENT` from
  `infrastructure.search.deep_research` (see its `__all__`). Never re-implement
  the models.
- **Layer-contract exception**: this is the one src subpackage allowed to import
  `infrastructure` — it is listed in `manuscript/layer_contract.yaml`
  (`allow_infrastructure_imports`). Keep that entry in sync if files move.
- **No mocks**: tests in `tests/test_deep_research_adapter.py` run the real
  adapter over the real shipped fixture and `tmp_path` files.

## Live Dispatch (not in CI)

`build_offline_request()` returns the genuine provider-neutral request a live
`DeepResearchClient.submit()` would dispatch. A fork enables real providers by
setting `OPENAI_API_KEY` / `GEMINI_API_KEY`; this exemplar still replays for
determinism.

## Files

- `deep_research_adapter.py` — provider profile, request builder, replay.
- `fixtures/recorded_report.json` — synthetic recorded deep-research report.
