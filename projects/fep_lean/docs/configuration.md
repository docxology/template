# Configuration Reference — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

This page is the **hub** for environment variables: monorepo (template) knobs first, then `fep_lean`-specific pipeline vars, then the grepped-from-`src/` complete list.

## Monorepo Stage 02 (repository root)

The template invokes [`scripts/02_run_analysis.py`](../../../scripts/02_run_analysis.py) from the **repository root** (not from this project's tree). It discovers `projects/<project>/scripts/*.py` in sorted order, **excluding** filenames starting with `_` (maintenance scripts such as [`_maint_build_topics_catalogue.py`](../scripts/_maint_build_topics_catalogue.py) are manual-only).

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `ANALYSIS_SCRIPT_TIMEOUT_SEC` | **7200** (2 hours) | Per-script `subprocess.run` timeout. Set a higher value for very long batches, or `0` / `none` / `unlimited` / `inf` for **no** timeout. Implemented in [`infrastructure/core/analysis_timeout.py`](../../../infrastructure/core/analysis_timeout.py). |

Each analysis script runs in a **separate** subprocess with this limit (not one timeout for the whole Stage 02).

---

## Quick environment variable summary

All env vars honoured by `fep_lean` code (grepped from `src/`). Full descriptions follow in later sections.

| Variable | Default | Domain | One-line effect |
| -------- | ------- | ------ | --------------- |
| `OPENROUTER_API_KEY` | — | Hermes (primary) | OpenRouter auth; Hermes stays enabled when present |
| `FEP_LEAN_GAUSS_WORKFLOWS` | `0` (off) | Pipeline | `1` enables full Gauss Sessions (Hermes + Lean + SQLite) |
| `HERMES_MODEL` | from settings.yaml | Hermes | Override primary model ID (e.g. `qwen/qwen3-next-80b-a3b-instruct:free`) |
| `HERMES_429_MAX_RETRIES` | `2` | Hermes | Retries after HTTP 429 on current model (0–10) |
| `HERMES_NETWORK_MAX_RETRIES` | `2` | Hermes | Retries after transient transport errors on current model (0–10) |
| `HERMES_MAX_MODEL_ATTEMPTS` | unset (all) | Hermes | Cap models tried per topic from fallback chain |
| `FEP_LEAN_VERIFY_TIMEOUT` | `300` | Lean | Per-sketch `lake env lean` timeout (seconds) |
| `GAUSS_HOME` | `~/.gauss` | Gauss | Session / SQLite root directory |
| `FEP_LEAN_MAX_TOPICS` | unset (all) | Pipeline | Cap Gauss batch size to first N catalogue rows |
| `FEP_LEAN_FIGURES_MP` | unset (parallel) | Figures | `0`/`false` renders PNGs serially, skipping `ProcessPoolExecutor` |
| `FEP_LEAN_PREFETCH` | unset (off) | Gauss | `1` overlaps Hermes for topic N+1 with Lean verify for N (verify workflow, ≥2 topics) |

See the full **Environment Variables Complete List** below for all other knobs (ANTHROPIC, lake/lean paths, preflight, etc.).

---

## Python pipeline environment

### fep_lean Stage 01 (catalogue and figures)

Behaviour of [`scripts/01_fep_catalogue_and_figures.py`](../scripts/01_fep_catalogue_and_figures.py) depends on the workflow flags in the table below (Gauss / Hermes batch vs catalogue-only).

These variables are read by `gauss/cli.py`, `pipeline/core.py`, `pipeline/orchestrator.py`, and `llm/hermes.py` (via `config/settings.yaml`):

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `FEP_LEAN_REQUIRE_GAUSS` | unset | If `1`/`true`/`yes`/`on`, missing `gauss` or failing `gauss doctor` fails validation |
| `FEP_LEAN_GAUSS_WORKFLOWS` | falsy unless set | If truthy, `FEPPipeline` runs **Gauss Sessions**: `GaussRunner.run_topics_batch` (Hermes + per-topic `lake env lean` via `LeanVerifier` + SQLite). `gauss/cli.workflows_enabled()` treats unset as off. [`scripts/01_fep_catalogue_and_figures.py`](../scripts/01_fep_catalogue_and_figures.py) sets the process env to `0` when unset unless `FEP_LEAN_LIVE_TESTS` is truthy. **Interactive** [`run.sh`](../../../run.sh) at the repo root still defaults `FEP_LEAN_GAUSS_WORKFLOWS` to `1` when the variable is unset — contrast with bare Stage 02. |
| `FEP_LEAN_LIVE_TESTS` | unset | When `FEP_LEAN_GAUSS_WORKFLOWS` is not already set, `1`/`true`/`yes`/`on` enables workflows from `01_fep_*`. |
| `FEP_LEAN_MAX_TOPICS` | unset | If set to a positive integer, only the first *N* catalogue rows run in Gauss Sessions (after `topic_filter` / `area_filter`). See `pipeline/core.py` (`_max_topics_from_env`). |
| `GAUSS_HOME` | `~/.gauss` | Writable config directory check |
| `PROJECT_DIR` | (from `src/` parent) | Override project root (tests, template analysis) |

## Priority Order (highest → lowest) — YAML / Hermes

```text
┌─────────────────────────────────────────────────────────┐
│  1. Environment variables (OPENROUTER_API_KEY, GAUSS_HOME)│
│  2. ~/.gauss/.env  (auto-loaded by HermesConfig._load_gauss_dotenv) │
│  3. config/settings.yaml  (project-level defaults)       │
│  4. Code defaults  (gauss/runner.py, llm/hermes.py)       │
└─────────────────────────────────────────────────────────┘
```

The `~/.gauss/.env` loader lives in `HermesConfig._load_gauss_dotenv` (see `src/llm/hermes.py`); it runs once on first use of `HermesConfig.from_settings`. `OpenGaussClient` does not parse this file — it consumes only environment variables that the loader has already populated.

Always use env vars or `~/.gauss/.env` to override API keys — never commit secrets to `config/settings.yaml`.

---

## settings.yaml — Complete Reference

Values below match the shipped [`config/settings.yaml`](../config/settings.yaml); if the file drifts, treat the YAML as source of truth.

### `[project]`

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `name` | str | `fep_lean` | Project identifier (used as GAUSS source tag) |
| `version` | str | `0.7.0` | Semantic version |
| `description` | str | — | Human-readable description |

### `[gauss]`

| Key | Type | Default | Env Override | Description |
|-----|------|---------|--------------|-------------|
| `home` | path | `~/.gauss` | `GAUSS_HOME` | Root directory for all GAUSS state |
| `default_model` | str | `moonshotai/kimi-k2.6` | `GAUSS_DEFAULT_MODEL` | Default model id for sessions |
| `log_level` | str | `INFO` | `GAUSS_LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `source` | str | `fep_lean` | — | Source tag applied to all sessions |
| `verify_lean` | bool | `true` | — | When Gauss workflows run, drive native `lake env lean` checks per topic (see `LeanVerifier`) |

### `[gauss.throttle]` (optional / reserved)

The shipped [`config/settings.yaml`](../config/settings.yaml) does **not** define an active `gauss.throttle` block (a commented-out `inter_topic_s` stub exists for documentation only). A documented `inter_topic_s`-style throttle is **reserved**: it is not present in the baseline YAML and is **not read** by the current Python sources (rate limiting is handled via Hermes retries and env vars such as `HERMES_*_MAX_RETRIES`). You may add a `throttle` subtree for local notes or future tooling, but do not assume the pipeline consumes it unless a release note says otherwise.

### `[orchestration]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `batch_size` | int | `5` | Topics per log-progress batch |
| `export_artifacts` | bool | `true` | Export per-topic JSON artifacts |
| `generate_report` | bool | `true` | Generate Markdown run directory |
| `report_dir` | path | `output/reports` | Base directory for run subdirectories |

### `[hermes]`

Matches the shipped [`config/settings.yaml`](../config/settings.yaml) `hermes:` block:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Enable Hermes OpenRouter calls when workflows run |
| `model` | str | `moonshotai/kimi-k2.6` | Primary OpenRouter model ID (Moonshot Kimi K2.6, 262K ctx, fast instruct) |
| `fallback_models` | `list[str]` | (5 entries, see below) | Fallback chain, tried in order when primary fails |
| `max_tokens` | int | `16384` | Max tokens (non-reasoning path) |
| `timeout_s` | int | `150` | HTTP request timeout (non-reasoning path) |
| `reasoning_max_tokens` | int | `65536` | Budget for reasoning-style models (R1, o1, o3) |
| `reasoning_timeout_s` | int | `300` | Timeout for reasoning-style models (seconds) |

**Default fallback chain** (matches `config/settings.yaml::hermes.fallback_models` and the in-code `_FREE_MODEL_CHAIN` in `src/llm/hermes.py`; the primary `hermes.model` is **not** repeated in `fallback_models`):

```yaml
hermes:
  model: "moonshotai/kimi-k2.6"
  fallback_models:
    - "moonshotai/kimi-k2-thinking"
    - "qwen/qwen3-next-80b-a3b-instruct:free"
    - "z-ai/glm-5.1"
    - "openai/gpt-oss-120b:free"
    - "nvidia/nemotron-3-super-120b-a12b:free"
    - "nousresearch/hermes-3-llama-3.1-405b:free"
    - "arcee-ai/trinity-large-preview:free"
  max_tokens: 16384
  timeout_s: 150
  reasoning_max_tokens: 65536
  reasoning_timeout_s: 300
```

---

## manuscript/config.yaml — Paper metadata

Ships at [`manuscript/config.yaml`](../manuscript/config.yaml); consumed by `infrastructure/core/config_loader.py` and `infrastructure/rendering/pdf_renderer.py`.

### `[paper]`

| Key | Type | Value | Description |
|-----|------|-------|-------------|
| `title` | str | `Towards Lean 4 Formalization of the Free Energy Principle` | Main title |
| `subtitle` | str | `AI-Driven Theorem Sketching and Verification for Active Inference and Bayesian Mechanics` | — |
| `version` | str | `0.7.0` | Manuscript semantic version (tracks project version) |
| `date` | str | `""` | Auto-generated by infrastructure at render time |

### `[authors]`

Single corresponding author:

| Field | Value |
|-------|-------|
| `name` | Daniel Ari Friedman |
| `orcid` | `0000-0001-6232-9096` |
| `email` | `daniel@activeinference.institute` |
| `affiliation` | Active Inference Institute |
| `corresponding` | `true` |

### `[keywords]` (15 entries)

Authoritative keyword list used by PDF metadata and HTML `<meta>` tags:

```yaml
keywords:
  - free energy principle
  - active inference
  - bayesian mechanics
  - lean 4
  - formal verification
  - theorem proving
  - mathlib4
  - reproducible research
  - interactive theorem proving
  - variational inference
  - information geometry
  - LLM-ITP integration
  - zero-mock pipeline
  - stochastic differential equations
  - measure theory formalization
```

### `[metadata]`

| Key | Value | Description |
|-----|-------|-------------|
| `license` | `Apache-2.0` | SPDX identifier; included in PDF cover and citation metadata |
| `language` | `en` | Primary language code |

### `[llm]` — Manuscript reviews and translations

| Key | Value | Description |
|-----|-------|-------------|
| `reviews.enabled` | `true` | Stage 8 (LLM scientific review) runs; produces executive summary |
| `reviews.types` | `[executive_summary]` | Review types to generate |
| `translations.enabled` | `true` | Stage 9 translations run |
| `translations.languages` | `[zh, de, fr]` | Chinese, German, French technical abstracts |

### `[testing]`

| Key | Value | Description |
|-----|-------|-------------|
| `max_test_failures` | `0` | Strict: any failure halts pipeline |
| `max_infra_test_failures` | `0` | Strict for monorepo infra tests |
| `max_project_test_failures` | `0` | Strict for `projects/fep_lean/tests/` |

---

## Hermes model options (OpenRouter)

Default **runtime fallback order** matches `src/llm/hermes.py` (`_FREE_MODEL_CHAIN`) and `config/settings.yaml` (`hermes.model` plus `hermes.fallback_models`). When the primary model fails, the client tries the next IDs in this chain (OpenRouter free tier unless you override).

| Priority | Model ID | Context | Notes |
|----------|----------|---------|-------|
| 1 (primary) | `moonshotai/kimi-k2.6` | 262K | Moonshot Kimi K2.6, fast instruct (reasoning-style budget) |
| 2 | `moonshotai/kimi-k2-thinking` | 262K | Kimi K2 with extended thinking trace |
| 3 | `qwen/qwen3-next-80b-a3b-instruct:free` | 262K | Strong reasoning fallback |
| 4 | `z-ai/glm-5.1` | 128K | ZhipuAI GLM-5.1 (demoted after empty-content stalls under 150 s timeout) |
| 5 | `openai/gpt-oss-120b:free` | 131K | OpenAI 120B distilled, free tier |
| 6 | `nvidia/nemotron-3-super-120b-a12b:free` | 262K | 120B MoE, reasoning model |
| 4 | `openai/gpt-oss-120b:free` | 131K | OpenAI 120B MoE |
| 5 | `nousresearch/hermes-3-llama-3.1-405b:free` | 131K | 8 req/min limit on free tier |
| 6 | `arcee-ai/trinity-large-preview:free` | 131K | Preview |

See also [`hermes.md`](hermes.md) and [`api.md`](api.md) (`HermesExplainer`).

### Premium / manual overrides

Paid or non-default models are **not** in the default chain. Set `hermes.model` (and optionally `hermes.fallback_models`) to use them explicitly, for example:

| Model ID | Context | Notes |
|----------|---------|-------|
| `anthropic/claude-sonnet-4` | 200K | Paid; high quality |
| `openai/gpt-4o` | 128K | Paid |

To change the primary model:

```yaml
# config/settings.yaml
hermes:
  model: "qwen/qwen3-next-80b-a3b-instruct:free"
```

### User-supplied fallback chain

`hermes.fallback_models` (loaded by `HermesConfig.from_settings`) is first-class
and, when non-empty, fully replaces the built-in `_FREE_MODEL_CHAIN` for
OpenRouter endpoints.  On 429 or transient errors the client advances to the
next entry in order; a 4xx that is not 429 still disables Hermes for the
remainder of the run (see [troubleshooting.md § Hermes HTTP 403](troubleshooting.md#hermes-http-403)).

```yaml
# config/settings.yaml
hermes:
  model: "moonshotai/kimi-k2.6"
  fallback_models:
    - "moonshotai/kimi-k2-thinking"
    - "openai/gpt-oss-120b:free"
    - "qwen/qwen3-next-80b-a3b-instruct:free"
```

### Anthropic-direct fallback (no OpenRouter)

When the OpenRouter key is exhausted, point Hermes straight at Anthropic:

```bash
export HERMES_API_BASE=https://api.anthropic.com/v1
export ANTHROPIC_API_KEY=sk-ant-...
```

`HermesConfig.from_settings` sniffs the key/endpoint pair and disables Hermes
if they mismatch (e.g. `sk-or-…` against Anthropic).

---

## topics.yaml — Topic Record Schema

Every entry in `topics:` must include:

| Field | Required | Type | Constraints | Example |
|-------|----------|------|-------------|---------|
| `id` | ✅ | str | `fep-NNN` format, unique | `fep-001` |
| `title` | ✅ | str | Non-empty, ≤80 chars | `Variational Free Energy Bound` |
| `area` | ✅ | str | One of 5 valid areas (see below) | `FEP` |
| `mathlib` | ✅ | str | Comma-separated Mathlib4 module names | `MeasureTheory, Probability.KL` |
| `mathlib_status` | Optional | str | `real`, `partial`, or `aspirational` (loader default if omitted: `partial`) | `real` |
| `nl` | ✅ | str | 1–3 sentence mathematical statement | — |
| `lean_sketch` | ✅ | str (multiline) | Lean 4 fragment; **current catalogue** is `sorry`-free `real` | — |

### Valid `area` Values

Counts match the 50-topic catalogue (see [quickref.md](quickref.md)):

| Area | Count | Mathlib focus (typical) |
|------|-------|-------------------------|
| `FEP` | 14 | `MeasureTheory`, divergence-style bounds, integration |
| `ActiveInference` | 11 | Policies, finsets, conditional expectations |
| `BayesianMechanics` | 10 | Generative model likelihoods, Markov blankets, hierarchical models |
| `InfoGeometry` | 8 | Manifolds, metrics, information quantities |
| `Thermodynamics` | 7 | Entropy, thermodynamic potentials, production |

---

## Environment Variables Complete List

Every env var actually read by code in `src/`. Grepped from `llm/hermes.py`, `gauss/{cli,client,runner}.py`, `verification/{environment,lean_verifier,preflight}.py`, `pipeline/orchestrator.py`.

### Hermes / LLM

| Variable | Used By | Default | Example |
|----------|---------|---------|---------|
| `OPENROUTER_API_KEY` | `HermesExplainer` (primary) | — | `sk-or-v1-...` |
| `ANTHROPIC_API_KEY` | `HermesExplainer` (fallback; sets `api_base` to `api.anthropic.com`) | — | `sk-ant-v3-...` |
| `OPENAI_API_KEY` | `HermesExplainer` (lowest-priority fallback) | — | `sk-...` |
| `HERMES_MODEL` | `HermesConfig.from_settings` | — | `qwen/qwen3-next-80b-a3b-instruct:free` |
| `HERMES_API_BASE` | `HermesConfig.from_settings` | `https://openrouter.ai/api/v1` | `https://api.anthropic.com/v1` |
| `GAUSS_DEFAULT_MODEL` | `HermesConfig.from_settings` (shared fallback) | (from settings) | — |
| `OPENAI_BASE_URL` | `HermesConfig.from_settings` (shared fallback) | — | — |
| `HERMES_429_MAX_RETRIES` | `llm/hermes.py` (`_hermes_429_max_retries`) | `2` | Retries after HTTP 429 on the **current** model before advancing the chain (capped 0–10) |
| `HERMES_NETWORK_MAX_RETRIES` | `llm/hermes.py` (`_hermes_network_max_retries`) | `2` | Retries after transient transport errors (`IncompleteRead`, `URLError`, etc.) on the **current** model (capped 0–10) |
| `HERMES_MAX_MODEL_ATTEMPTS` | `llm/hermes.py` (`_env_positive_int`) | unset (full chain) | Max models from the OpenRouter fallback chain per topic |

### Gauss / OpenGauss

| Variable | Used By | Default | Example |
|----------|---------|---------|---------|
| `GAUSS_HOME` | `GaussRunner`, `OpenGaussClient`, `check_gauss_cli` | `~/.gauss` | `/data/gauss` |
| `GAUSS_LOG_LEVEL` | `OpenGaussClient` | `INFO` | `DEBUG` |
| `FEP_LEAN_REQUIRE_GAUSS` | `gauss/cli.py`, `pipeline.orchestrator`, `preflight.main` | unset | `1` / `true` / `yes` / `on` |
| `FEP_LEAN_GAUSS_WORKFLOWS` | `FEPPipeline.run`, `gauss/cli.workflows_enabled` | unset → falsy (**defaults to `0`**) | `1` / `true` / `yes` / `on` to enable Gauss sessions |
| `FEP_LEAN_MAX_TOPICS` | `pipeline/core.py` | unset (all rows after filters) | Positive int: cap batch size |
| `FEP_LEAN_TEST_GAUSS_DOCTOR` | `tests/test_gauss_cli.py` | unset | `1` to enable live `gauss doctor` test |

### Lean / Lake

| Variable | Used By | Default | Example |
|----------|---------|---------|---------|
| `FEP_LEAN_VERIFY_TIMEOUT` | `LeanVerifier._get_timeout` (per-sketch timeout, seconds) | `300` | `600` |
| `FEP_LEAN_LAKE_EXE` | `LeanVerifier._resolve_lake_exe` | auto-resolved via elan | `/usr/local/bin/lake` |
| `FEP_LEAN_LEAN_EXE` | `LeanVerifier.lean_version` | auto-resolved via elan | `/usr/local/bin/lean` |
| `ELAN_HOME` | `LeanVerifier._subprocess_env` (sandboxed override) | `$HOME/.elan` | temp dir |

### Pipeline / orchestration

| Variable | Used By | Default | Example |
|----------|---------|---------|---------|
| `PROJECT_DIR` | `pipeline.orchestrator.project_root` | (walks up from `src/`) | `/tmp/fep_lean_copy` |
| `FEP_LEAN_LIVE_TESTS` | legacy alias for `FEP_LEAN_GAUSS_WORKFLOWS` in `scripts/01_fep_catalogue_and_figures.py` | unset | `1` |
| `FEP_LEAN_PREFETCH` | `gauss/runner.py` (`_prefetch_enabled`) | unset → off | `1` / `true` — overlap Hermes for the next topic with Lean verify on the current topic (`verify` workflow, ≥2 topics) |
| `FEP_LEAN_FIGURES_MP` | `output/figures.py` (`_figures_mp_enabled`) | unset → parallel pool | `0` / `false` — render catalogue PNGs serially in-process (skip `ProcessPoolExecutor`) |
| `MPLBACKEND` | scripts set `Agg` for headless figure generation | `Agg` (set by script) | `Agg` |
| `PYTHONPATH` | Python import resolver (direct script/pytest use outside `uv run --directory`) | — | `projects/fep_lean/src:.:infrastructure` (project `src` first — see [troubleshooting.md](troubleshooting.md#pythonpath-shadowing)) |

---

## `.env` File Format

```bash
# ~/.gauss/.env — auto-loaded by OpenGaussClient
OPENROUTER_API_KEY=sk-or-v1-...
GAUSS_HOME=/path/to/gauss    # optional override
GAUSS_LOG_LEVEL=INFO          # optional
```

---

## pytest options (pyproject.toml)

| Setting | Value | Description |
|---------|-------|-------------|
| `testpaths` | `tests` | Discover tests under `tests/` |
| `python_files` | `test_*.py` | Test file naming |
| `python_functions` | `test_*` | Test function naming |
| `addopts` | `-v --tb=short --strict-markers` | Verbose, short tracebacks, strict markers |
| `timeout` | `900` | Per-test timeout (seconds) |
| Coverage (`tool.coverage.run`) | `source = ["src"]`, `concurrency = ["multiprocessing"]` | Measure `src/`; include figure worker processes |

---

## pyproject.toml Summary

Authoritative file: [`../pyproject.toml`](../pyproject.toml). At a glance:

- **version**: `0.7.0`
- **requires-python**: `>=3.10`
- **dependencies**: `numpy`, `matplotlib`, `pyyaml` (see file for pins)
- **optional dev**: `pytest`, `pytest-cov`, `pytest-timeout`, `pytest-xdist`
- **console script**: `fep-lean-preflight` → `verification.preflight:main`

---

## Navigation

- [← Architecture](architecture.md)
- [← docs/README.md](README.md)
- [Getting Started →](getting-started.md)
