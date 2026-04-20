# Hermes AI Explainer — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

## Overview

The **Hermes AI Explainer** (`src/llm/hermes.py`) makes OpenRouter HTTP calls to produce:

1. **Explanation**: Plain-English proof strategy explanation
2. **Refined Lean 4 sketch**: Improved sketch with Mathlib4 declarations (when the model returns one)

Both are stored in the OpenGauss SQLite session and in the per-topic artifact JSON.

**Canonical Lean for the paper** remains **`config/topics.yaml`** and the regenerated **`manuscript/09z_appendix_b_lean_catalogue.md`**. Hermes output is **session / audit** material unless you merge changes back into YAML.

> **Representative production-style run (`moonshotai/kimi-k2.6`)**
>
> - **50 / 50 topics succeeded** (100% Hermes HTTP success) on the primary model.
> - **Average token usage**: order of **10³ tokens / topic** (prompt + completion; `HermesResult.tokens_used`).
> - **Retries were rare** — the 6-model fallback chain was exercised on < 2 % of topics across
>   sample end-to-end runs; `HERMES_429_MAX_RETRIES=2` was sufficient.
> - **Lean downstream**: **50 / 50** on the shipped catalogue when the verifier sweep is green — see [`pipeline.md`](pipeline.md#timing) for end-to-end timing.

> [!NOTE]
> **Agentic Settings**: OpenRouter API calls via Hermes execute entirely asynchronously underneath Python. However, because mathematical validation relies on the strict, thread-sensitive macOS ELAN proxy sandbox (`LeanVerifier`), Hermes outputs are verified completely **sequentially**. Do not design orchestrators that pipe multiple Hermes outputs into `lake env lean` concurrently.

---

## Architecture

```text
HermesExplainer.explain_topic(topic) → HermesResult
    │
    ├── Guard: enabled=False or api_key='' → return immediately (no network)
    │
    ├── build_messages(topic)
    │       system: _FEP_SYSTEM_PROMPT (Hermes + Lean4 + Mathlib4 specialist)
    │       user:   "**Theorem:** {title}\n**NL:** {nl}\n**Sketch:**\n```lean\n...\n```"
    │
    ├── _build_model_chain()  (optional cap: env HERMES_MAX_MODEL_ATTEMPTS)
    │       [primary, fallback_1, ...]  (OpenRouter free models by default)
    │
    └── for model in chain:
            _try_fetch_raw(messages, model, topic_id)
                └── loop: _call_api(messages, model)
                        POST .../chat/completions
                    on HTTP 429 → sleep (bounded exponential backoff), retry on
                        **same** model up to HERMES_429_MAX_RETRIES (default 2)
                    on transient transport (IncompleteRead, URLError, HTTPException,
                        socket/timeout) → same backoff budget via
                        HERMES_NETWORK_MAX_RETRIES (default 2)
                    after retries exhausted → try **next** model in chain
                    on other HTTP 4xx (from response body) → may disable Hermes
                        for remainder of run (not applied to transport-only errors)
            _parse_response(raw, model, elapsed, topic_id)
                → _extract_lean_block(content)   → refined_lean_sketch
                → _extract_explanation(content)  → explanation
                → HermesResult(success=bool(content), ...)
            if success → return immediately
```

---

## FEP System Prompt

The system prompt (`_FEP_SYSTEM_PROMPT`) identifies Hermes as:

- Expert in Free Energy Principle, Active Inference, Bayesian Mechanics, Information Geometry, Thermodynamics
- Lean4 + Mathlib4 formal mathematics specialist

It instructs the model to:

1. Explain the proof strategy in 2–4 sentences
2. Provide a refined `\`\`\`lean` block using Mathlib4 declarations
3. Minimize `sorry` to genuinely open sub-goals
4. Include a `-- [proof strategy: ...]` comment

---

## Model Fallback Chain (OpenRouter Free Tier)

The chain is defined verbatim in `src/llm/hermes.py` as the module-level constant
`_FREE_MODEL_CHAIN` (lines **88–95**):

```python
_FREE_MODEL_CHAIN = [
    "moonshotai/kimi-k2.6",
    "moonshotai/kimi-k2-thinking",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "z-ai/glm-5.1",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "arcee-ai/trinity-large-preview:free",
]
```

| Priority | Model | Notes |
|----------|-------|-------|
| 1 (primary) | `moonshotai/kimi-k2.6` | Moonshot Kimi K2.6, 262K context — default `HermesConfig.model` (member of `_REASONING_MODELS`) |
| 2 | `moonshotai/kimi-k2-thinking` | Kimi K2 with extended thinking trace |
| 3 | `qwen/qwen3-next-80b-a3b-instruct:free` | 80B fast instruct |
| 4 | `z-ai/glm-5.1` | ZhipuAI GLM-5.1; demoted from primary after returning empty content under the 150 s timeout |
| 5 | `openai/gpt-oss-120b:free` | OpenAI 120B distilled, free tier |
| 6 | `nvidia/nemotron-3-super-120b-a12b:free` | 120B MoE, reasoning model (extended `reasoning_max_tokens`) |
| 4 | `openai/gpt-oss-120b:free` | 120B |
| 5 | `nousresearch/hermes-3-llama-3.1-405b:free` | 405B |
| 6 | `arcee-ai/trinity-large-preview:free` | Preview |

`_build_model_chain` (line **640** of `hermes.py`) always starts with the configured primary model
(`self._cfg.model`), then appends `fallback_models` when non-empty, otherwise `_FREE_MODEL_CHAIN`.
Anthropic-direct endpoints (`api.anthropic.com` in `base_url`) skip the chain entirely — a single
model is tried.

**Reasoning models** (DeepSeek-R1, o1, o3, Nemotron) get extended `reasoning_max_tokens` (65536) and
`reasoning_timeout_s` (300s) automatically via `HermesConfig.is_reasoning_model()`.

---

## `HermesConfig`

```python
@dataclass
class HermesConfig:
    model: str = 'moonshotai/kimi-k2.6'
    base_url: str = 'https://openrouter.ai/api/v1'
    api_key: str = ''
    max_tokens: int = 16384
    timeout_s: int = 150
    reasoning_max_tokens: int = 65536
    reasoning_timeout_s: int = 300
    enabled: bool = True
    cache_ttl_hours: float = 24.0   # SQLite hermes_cache TTL; 0 disables result caching
    fallback_models: list[str] = []  # overrides _FREE_MODEL_CHAIN when non-empty

    http_referer: str = 'https://github.com/docxology/template'
    x_title: str = 'FEP-Lean Formalization'
```

### Field-by-field

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `model` | `str` | `"moonshotai/kimi-k2.6"` | Primary model ID; tried first in the chain. |
| `base_url` | `str` | `"https://openrouter.ai/api/v1"` | Chat-completions endpoint; OpenRouter by default. |
| `api_key` | `str` | `""` | Bearer token. Empty string ⇒ **stub mode** (no network). |
| `max_tokens` | `int` | `16384` | Max completion tokens for non-reasoning models. |
| `timeout_s` | `int` | `150` | Per-request **wall-clock** budget for non-reasoning models. Enforced by a worker-thread + `join(timeout=…)` guard in `_make_request`; `urllib`'s native `timeout=` only bounds individual socket ops, so streaming responses that drip bytes for ten minutes still trip this hard deadline and raise a transient `HermesAPIError` so the next model in the chain can take over. |
| `reasoning_max_tokens` | `int` | `65536` | Larger budget for reasoning models (Kimi K2.x, DeepSeek-R1, o1/o3, Nemotron, GLM-5.1). |
| `reasoning_timeout_s` | `int` | `300` | Longer wall-clock budget for reasoning models, enforced the same way as `timeout_s`. |
| `enabled` | `bool` | `True` | Master switch. `False` ⇒ `HermesResult(success=False)` with no network. |
| `cache_ttl_hours` | `float` | `24.0` | `hermes_cache` table TTL. `0.0` ⇒ caching disabled. |
| `fallback_models` | `list[str]` | `[]` | Ordered chain that **replaces** `_FREE_MODEL_CHAIN` when non-empty. Useful for pinning paid models or restricting to a single vendor. Loaded from `hermes.fallback_models` in `config/settings.yaml`. |
| `http_referer` | `str` | `"https://github.com/docxology/template"` | OpenRouter-only header (`HTTP-Referer`). |
| `x_title` | `str` | `"FEP-Lean Formalization"` | OpenRouter-only header (`X-Title`). |

### Class methods

```python
@classmethod
def from_settings(
    cls,
    project_root: Path | str | None = None,
    *,
    settings_path: Path | None = None,
) -> HermesConfig

def is_reasoning_model(self) -> bool
def effective_max_tokens(self) -> int
def effective_timeout(self) -> int
```

`cache_ttl_hours` may also be set in `config/settings.yaml` under `hermes: cache_ttl_hours:`.

- `project_root` — optional project root used to locate `config/settings.yaml`. Defaults to walking up from the caller.
- `settings_path` — keyword-only explicit path to an alternate `settings.yaml` (useful in tests).

**Config resolution order** (highest → lowest):

```text
1. Process environment variables
2. ~/.gauss/.env (auto-loaded by _load_gauss_dotenv)
3. config/settings.yaml  hermes: block
4. Code defaults
```

**Key environment variables**:

```text
OPENROUTER_API_KEY            → primary (for OpenRouter endpoint)
ANTHROPIC_API_KEY             → fallback (for Anthropic endpoint)
OPENAI_API_KEY                → fallback (for any OpenAI-compatible endpoint)
HERMES_MODEL                  → override the model ID
HERMES_API_BASE               → override the base URL
HERMES_429_MAX_RETRIES        → retries after HTTP 429 per model (default 2, clamped to 0–10)
HERMES_NETWORK_MAX_RETRIES    → retries after transient read/connection errors (default 2, clamped to 0–10)
HERMES_MAX_MODEL_ATTEMPTS     → cap on total models tried per call
GAUSS_DEFAULT_MODEL           → fallback model override
GAUSS_HOME                    → location of .env file (default: ~/.gauss)
```

The two retry budgets share the same attempt loop: `max_attempts = max(429_budget, network_budget) + 1`,
so **2 + 2 retries ⇒ 3 HTTP attempts per model** before moving on. Both values are parsed by
`_hermes_429_max_retries` / `_hermes_network_max_retries` (hermes.py) and **clamped to the range
`[0, 10]`** — i.e. `min(n, 10)` with a `max(0, …)` floor — to prevent runaway loops.

### Dotenv Auto-Loading

The `from_settings()` method automatically calls `_load_gauss_dotenv()` which reads
`$GAUSS_HOME/.env` (default `~/.gauss/.env`) and injects any `KEY=VALUE` pairs
that are not already present in `os.environ`. This ensures API keys stored by
the OpenGauss CLI are available to the Python process without manual `export`.

### Key ↔ Endpoint Affinity Validation

After resolving the API key, Hermes validates that the key prefix matches the
configured endpoint:

| Key prefix | Valid endpoint | Invalid endpoint |
|------------|---------------|------------------|
| `sk-or-*`  | `openrouter.ai` | `api.anthropic.com` |
| `sk-ant-*` | `api.anthropic.com` | `openrouter.ai` |

A mismatch **auto-disables** Hermes with an error log, preventing 401 errors.

---

## `HermesResult`

```python
@dataclass
class HermesResult:
    success: bool
    model_used: str
    explanation: str = ''          # Plain text (code blocks stripped)
    refined_lean_sketch: str = ''  # Extracted ```lean block (no fences)
    reasoning: str = ''            # From <think>...</think> or reasoning field
    tokens_used: int = 0
    duration_s: float = 0.0
    error: str = ''                # Empty on success
    topic_id: str = ''
    cache_hit: bool = False        # True when served from SQLite cache (no network call made)

    def as_dict(self) -> dict
```

When `cache_hit=True`, `tokens_used` reflects the originally recorded value (not 0) and `duration_s` reflects the original call duration — not the cache retrieval time.

---

## Stub Mode (No Network)

Hermes triggers **zero-network early return** when **either** of these conditions holds at call
time:

1. `HermesConfig.api_key` is empty (`""`) — no credential resolved from env, `~/.gauss/.env`, or
   `settings.yaml`, **or**
2. `HermesConfig.enabled` is `False` — either set explicitly or auto-disabled by the key ↔ endpoint
   affinity validator / a fatal 401/403 from an earlier topic.

In both cases `explain_topic()` returns **immediately** with no HTTP request:

```python
# enabled=False branch
HermesResult(
    success=False,
    model_used=cfg.model,
    error="hermes disabled in config",
    topic_id=topic.id,
)

# api_key="" branch
HermesResult(
    success=False,
    model_used=cfg.model,
    error="no API key (set OPENROUTER_API_KEY or ANTHROPIC_API_KEY)",
    topic_id=topic.id,
)
```

**No network call is made.** The pipeline continues with `hermes_success=False` for all topics.
Reports show `❌` for Hermes status. SQLite records the session with `hermes_success=0`.

Note — there is **no `sk-test-*` fast-path** in the current code: any non-empty `api_key` triggers a
real HTTP call. If you need a dry-run without hitting the network, leave `OPENROUTER_API_KEY` unset
(or explicitly export `OPENROUTER_API_KEY=""`).

To enable live calls:

```bash
export OPENROUTER_API_KEY=sk-or-...
export FEP_LEAN_GAUSS_WORKFLOWS=1
# From the project root:
uv run python scripts/01_fep_catalogue_and_figures.py
```

---

## HTTP transport, `HermesAPIError`, and retries

`_call_api` maps failures to **`HermesAPIError`** with optional **`status_code`** and
**`transient`**:

| Origin | `status_code` | `transient` | Notes |
|--------|---------------|-------------|--------|
| `urllib.error.HTTPError` | HTTP status | `False` | Body read with `HTTPError.read()` where applicable |
| `urllib.error.URLError` | `None` | `True` | Connection refused, DNS, etc. |
| `http.client.HTTPException` (e.g. `IncompleteRead`) | `None` | `True` | Chunked/streaming drops, truncated bodies |
| `TimeoutError` / `OSError` on read | `None` | `True` | Belt-and-suspenders for socket-level issues |

`_try_fetch_raw` retries **429** and **transient** errors on the **current** model with
`min(60s, 2**(attempt+1))` sleep, up to **`HERMES_429_MAX_RETRIES`** and
**`HERMES_NETWORK_MAX_RETRIES`** respectively (defaults **2** each, clamped to `min(n, 10)`; loop
length is `max(429_budget, network_budget) + 1` attempts). It does **not** disable Hermes when
`status_code is None` (transport-only). Client **4xx** from `HTTPError` (except 429) can still
disable Hermes for the rest of the run per existing logic.

---

## Error Handling

| Error | Behavior |
|-------|-----------|
| HTTP 429 (rate limit) | Retry **same** model with backoff (`HERMES_429_MAX_RETRIES`, default 2, clamped to ≤ 10), then next model in chain |
| Transient transport (`IncompleteRead`, `URLError`, …) | Retry **same** model (`HERMES_NETWORK_MAX_RETRIES`, default 2, clamped to ≤ 10), then next model |
| HTTP 5xx (server error) | Mapped to `HermesAPIError`; typically try next model after fetch failure |
| HTTP 401 (invalid key) | Stop chain, **disable Hermes globally** for remainder of run |
| HTTP 403 (forbidden) | Stop chain, **disable Hermes globally** for remainder of run |
| HTTP 400 (bad model ID) | Stop chain → `HermesResult(success=False)` |
| Timeout (`timeout_s`) | `HermesResult(success=False)`, pipeline continues |
| All models failed | `HermesResult(success=False, error=last_err)` |
| Key ↔ endpoint mismatch | Hermes disabled at config time (no network call) |

`explain_topic` returns a **`HermesResult`** for normal failure paths. Uncaught bugs or
future refactors could still surface as exceptions to `GaussRunner` (which logs and
records `status="error"` per topic); internal transport errors are converted to
`HermesAPIError` inside `_call_api` / `_try_fetch_raw` so **`IncompleteRead`** no longer
skips that handling.

### `HermesExplainer.preflight()` — fail-fast credential probe

Called once at the head of **Stage 3: Gauss Sessions** (`pipeline/core.py::_stage_gauss`)
before batching 50 topics. Issues a single `max_tokens=1` completion at the current model
and endpoint with a tight timeout (≤10 s). Outcomes:

| Probe result | Action |
|--------------|--------|
| HTTP 200 | Return `True`; pipeline proceeds |
| HTTP 401 / 403 | Disable Hermes globally, log actionable OpenRouter URL + Anthropic-direct hint, return `False` |
| HTTP 5xx / transport | Log and return `True` (tolerate flaky upstream — real topics will retry with backoff) |
| Hermes disabled / no key | No-op, return `True` |

This surfaces credential problems (rotated keys, exhausted quotas) in seconds rather than
after a full Lean pass. Covered by `tests/test_hermes_error_paths.py::test_preflight_*`.

### User-supplied `fallback_models`

`HermesConfig.fallback_models` (YAML `hermes.fallback_models`) takes precedence over
`_FREE_MODEL_CHAIN` when non-empty. Used for pinning paid models or constraining the chain
to a single vendor. Selected by `_build_model_chain`; covered by
`test_build_model_chain_prefers_user_fallbacks`.

---

## Response Parsing

The following helpers are **module-private** (leading underscore) and **not part of the public API**; they are referenced only by `HermesExplainer._parse_response`. They are documented here because the tests exercise them directly via the pattern `from llm.hermes import _extract_lean_block, _extract_explanation` (legitimate for test-only access, not for downstream consumers).

```python
def _extract_lean_block(content: str) -> str:
    """Extract first ```lean...``` fence block (no fences in output)."""

def _extract_explanation(content: str) -> str:
    """Remove code blocks; return first 3 non-header paragraphs."""
```

Reasoning content in `<think>...</think>` tags is extracted into `HermesResult.reasoning` and stripped from `content` before parsing.

---

## Workflow Preambles

`GaussRunner` injects a task directive into the Hermes system prompt via `_WORKFLOW_PREAMBLES`
(defined in `src/gauss/runner.py`). The preamble prefixes the standard `_FEP_SYSTEM_PROMPT`
for every non-verify workflow:

| Workflow | Preamble summary | Lean block expected? |
|----------|-----------------|----------------------|
| `verify` | *(empty)* — standard explain + refine | Yes |
| `draft`  | Draft a new Lean 4 skeleton; use `sorry` freely for all sub-goals | Yes |
| `prove`  | Attempt full proof; prefer `exact`/`apply`/`simp`/`ring`/`linarith` over sorry | Yes |
| `review` | Review compiled sketch: correctness, Mathlib improvements, clarity — **no new lean block** | No |

The `review` workflow triggers a **second Hermes call** after successful compilation of the first
response. The second call receives the `review` preamble and the compiled sketch. Its output is
stored in `TopicRunResult.stage_results` (key `"stage": "review_commentary"`).

Non-verify workflows silently downgrade to `"verify"` when `FEP_LEAN_GAUSS_WORKFLOWS` is not set or is `"0"`.

## Hermes Result Cache

Before every Hermes HTTP call, `GaussRunner` queries `OpenGaussClient.get_cached_hermes()` using a SHA-256 key derived from `topic_id:lean_sketch:model:stage`. On a cache hit:

- The stored `HermesResult.as_dict()` is deserialised and returned.
- `HermesResult.cache_hit` is set `True`.
- No network call is made.

On a cache miss the call proceeds normally, and `set_cached_hermes()` stores the result for
future runs. Entries older than `HermesConfig.cache_ttl_hours` (default 24 h) are pruned by
`prune_hermes_cache()`.

To disable caching entirely, set `cache_ttl_hours: 0` in `config/settings.yaml` (or pass `HermesConfig(cache_ttl_hours=0)` in tests).

---

## `restore_lean_structure` — Post-Processing Pipeline

After every Hermes HTTP response, `GaussRunner` calls `restore_lean_structure(refined, original)` (defined in `src/llm/hermes.py`) before handing the sketch to `lake env lean`. This 7-step pipeline corrects the structural drift introduced by LLM rewriting.

### Step 0 — Garbage Detection

If the refined sketch contains C++ `//` comment syntax or contains no `theorem` keyword at all, the original sketch is returned immediately. This guards against the rare case where Hermes returns prose or non-Lean content.

### Steps 1–3 — Original-Imports-Only

Hermes sometimes introduces extra `import Mathlib.*` or `import Init.*` lines absent from the original. Steps 1–3 strip all `import` lines from the refined output and replace them with the exact import block from `original`. This ensures the verifier sees only known-good imports.

### Step 5 — Namespace Restore

If `original` contains a `namespace fepNNN` block and the refined output dropped it, the namespace declaration (and matching `end`) is re-inserted around the theorem body.

### Step 5.5 — Open-Statement Restoration

`open MeasureTheory`, `open Finset`, `open Real`, and similar directives are occasionally stripped by Hermes. Step 5.5 collects all `open X` lines present in `original` and absent from `refined`, and re-inserts them immediately before the first `theorem` or `def` line. This is the critical fix for fep-001, fep-014, fep-027 (MeasureTheory namespace), and several Finset-dependent topics.

### Step 6 — `_strip_extra_theorems`

```python
def _strip_extra_theorems(sketch: str, allowed_names: set[str]) -> str:
```

A line-by-line state machine that removes theorem bodies **not** present in `original`. When Hermes adds helper lemmas or renames theorems, this step removes them, keeping only the theorems whose names appear in `allowed_names` (extracted from `original` before the pipeline runs). The state machine tracks indentation depth to correctly handle multi-line `by` tactic blocks.

### Step 7 — Completeness Check

After `_strip_extra_theorems`, if **none** of the original theorem names survive in the output (because Hermes renamed all of them), `restore_lean_structure` returns the `original` sketch unchanged. This is the correct fallback for topics where Hermes systematically renames theorems (observed in run_20260419_130508 for fep-005, fep-029, fep-031, fep-038, fep-039).

### Topics Triggering Each Mechanism (run_20260419_130508)

| Mechanism | Topics |
|-----------|--------|
| Open-statement restore (Step 5.5) | fep-001, fep-014, fep-027 + Finset topics |
| Completeness fallback (Step 7) | fep-005, fep-029, fep-031, fep-038, fep-039 |
| Garbage detection (Step 0) | none in run_20260419_130508 |

Covered by `tests/test_hermes_explainer.py` (38 tests including `test_restore_lean_structure_*`).

---

## GaussRunner Baseline Fallback

`GaussRunner` (in `src/gauss/runner.py`) implements a two-attempt compile strategy tracked via the `_hermes_lean_compiles` counter:

1. **Attempt 1**: Compile the `restore_lean_structure`-processed Hermes output via `lake env lean`.
2. **Attempt 2 (baseline fallback)**: If Attempt 1 fails, compile the **original YAML sketch** unchanged. If Attempt 2 succeeds, the topic is recorded as `compiled: True` with `source: "baseline_fallback"` in the run summary.

This fallback is why all 50 topics compiled in run_20260419_130508: topics where `restore_lean_structure` output could not be made to compile (e.g. Hermes introduced an unfixable tactic) still compiled via their known-good YAML sketch.

The fallback is transparent in the run JSON (`output/reports/run_*/summary.json`): the `hermes_lean_compiles` field counts Attempt-1 successes, while `compiled` counts total successes including baseline fallback.

---

## Navigation

- [← OpenGauss](opengauss.md)
- [Reporter →](reporter.md)
- [← docs/README.md](README.md)
