# fep_lean/src/llm/

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

LLM integration for the FEP formalisation pipeline. `HermesExplainer` sends a
2-message prompt (system + user) to an OpenAI-compatible chat-completions
endpoint (OpenRouter by default, Anthropic as an alternate `base_url`) using
only `urllib` — no third-party SDK. The response is parsed into a plain-text
proof-strategy explanation plus a refined Lean 4 sketch extracted from the
first fenced `lean` code block.

## Public API

| Symbol | Role |
| ------ | ---- |
| `HermesConfig` | Configuration dataclass (model, base_url, api_key, timeouts, fallback chain). Construct via `HermesConfig.from_settings(project_root)`. Defined at `hermes.py:145`. |
| `HermesResult` | Result dataclass with `success`, `model_used`, `explanation`, `refined_lean_sketch`, `reasoning`, `tokens_used`, `duration_s`, `error`, `topic_id`, `cache_hit`. Defined at `hermes.py:332`. |
| `HermesExplainer` | Main explainer class (`hermes.py:361`). Methods: `explain_topic(topic)`, `preflight()`, property `is_live`. |
| `HermesAPIError` | Raised on non-retryable HTTP/transport failures. |

## Configuration

Resolution priority (highest → lowest):

1. Environment variables (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`,
   `HERMES_MODEL`, `HERMES_API_BASE`, `HERMES_429_MAX_RETRIES`,
   `HERMES_NETWORK_MAX_RETRIES`, `HERMES_MAX_MODEL_ATTEMPTS`).
2. `config/settings.yaml` under the `hermes:` block.
3. Shared `~/.gauss/.env` auto-loaded into `os.environ` for any key not
   already set (`$GAUSS_HOME/.env` honoured if set).
4. Built-in defaults (`moonshotai/kimi-k2.6` on `https://openrouter.ai/api/v1`).

An API-key / base-URL affinity check disables Hermes automatically if an
`sk-ant-*` key is about to be sent to OpenRouter, or an `sk-or-*` key to
Anthropic.

## Fallback chain

When the primary model returns a retryable failure, the client advances
through `fallback_models` from settings; if that list is empty and the
base_url is OpenRouter, the built-in **6-model free-tier chain** is tried in
order:

```
moonshotai/kimi-k2.6
moonshotai/kimi-k2-thinking
qwen/qwen3-next-80b-a3b-instruct:free
z-ai/glm-5.1
openai/gpt-oss-120b:free
nvidia/nemotron-3-super-120b-a12b:free
openai/gpt-oss-120b:free
nousresearch/hermes-3-llama-3.1-405b:free
arcee-ai/trinity-large-preview:free
```

Retry budgets:

- `HERMES_429_MAX_RETRIES` (default **2**) — retries on the *same* model
  after HTTP 429 before advancing to the next model.
- `HERMES_NETWORK_MAX_RETRIES` (default **2**) — retries on transient
  transport failures (`IncompleteRead`, dropped connections, `URLError`).

Reasoning-capable models (Nemotron, DeepSeek-R1 family, OpenAI o1/o3) get
larger token budgets (`reasoning_max_tokens=65536`, default 16384) and
longer timeouts (`reasoning_timeout_s=300`, default 150), selected by
`HermesConfig.effective_max_tokens()` / `effective_timeout()`.

## `preflight()`

`HermesExplainer.preflight()` probes the endpoint with a `max_tokens=1`
completion against the primary model. Any 4xx (except 429) flips the shared
`HermesConfig` to `enabled=False` with an actionable log line, so the
enclosing batch run skips Hermes entirely instead of degrading mid-run.

See [`AGENTS.md`](AGENTS.md) for the full import-contract notes and the
wiring into `gauss.runner.GaussRunner`.
