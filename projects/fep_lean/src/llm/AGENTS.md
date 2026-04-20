# fep_lean/src/llm/ — LLM Integration (Hermes Explainer)

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

## Purpose

LLM-side of the FEP formalisation pipeline. Uses the OpenRouter / Anthropic HTTP API (via stdlib `urllib`, no third-party SDK) to send a structured system+user message pair that explains proof strategies and refines Lean 4 sketches for catalogue topics. The conceptual flow is a 4-phase process (explain → refine → check → finalise) but the wire format is a single API completion request with 2 chat messages.

## Files

- `hermes.py` — the entire client surface (`HermesConfig`, `HermesExplainer`, `HermesResult`, `HermesAPIError`)
- `__init__.py` — re-exports the public API

## Public API

| Symbol | Kind | Description |
| --- | --- | --- |
| `HermesConfig` | dataclass | Configuration (env vars + `settings.yaml`): model, base URL, API key |
| `HermesExplainer` | class | Sends system+user prompt via `explain_topic(topic)` → `HermesResult`; `build_messages(topic)` constructs the 2-message payload |
| `HermesResult` | dataclass | Structured result with the explanation text and refined Lean sketch |
| `HermesAPIError` | exception | Raised on HTTP / network errors so callers can decide to retry or skip |

## Imports

```python
from llm.hermes import HermesConfig, HermesExplainer, HermesResult, HermesAPIError
```

## Notes

- No external SDK — uses `urllib` so the package has zero runtime LLM dependencies beyond the standard library.
- Config sources are layered: `HermesConfig.from_settings()` reads `OPENROUTER_API_KEY` / `HERMES_MODEL` / `HERMES_API_BASE`, then merges defaults from `config/settings.yaml` if present.
- HTTP **429** responses retry the same model with exponential backoff (bounded); env `HERMES_429_MAX_RETRIES` (default 2). Optional `HERMES_MAX_MODEL_ATTEMPTS` caps how many models from the OpenRouter fallback chain are tried per topic.
- `_make_request` enforces `timeout_s` / `reasoning_timeout_s` as a **wall-clock** deadline via a worker thread + `join(timeout=…)`. `urllib`'s native `timeout=` only bounds individual socket ops, so streaming responses that drip bytes for minutes still trip this hard deadline and raise a transient `HermesAPIError("Wall-clock timeout after Ns …")`, letting `explain_topic` advance to the next model in the chain.
- Default primary model is `moonshotai/kimi-k2.6` (member of `_REASONING_MODELS`); `_FREE_MODEL_CHAIN` keeps `z-ai/glm-5.1` as a demoted fallback after a prior cold-restart regression.
- Consumed by `gauss/runner.py::GaussRunner` as the LLM half of the per-topic loop.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../gauss/AGENTS.md`](../gauss/AGENTS.md) — orchestrator that calls `HermesExplainer`
