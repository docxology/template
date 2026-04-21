# Pipeline — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

> **Representative reference run (`moonshotai/kimi-k2.6`)**
>
> - **Hermes API**: **50 / 50** topics succeeded (100%) — order of 10³ tokens/topic (copy from `summary.json` for audit-grade figures)
> - **Lean compilation**: **50 / 50** on the shipped catalogue when the verify sweep is green (`scripts/03_lean_verify_only.py`); pins in `lean/lean-toolchain` and `lean/lakefile.lean`
> - **Total wall time**: order of tens of minutes end-to-end with live Hermes (varies by machine and API)
> - **Primary model**: `moonshotai/kimi-k2.6` (Moonshot Kimi K2.6, 262K context) with an 8-model fallback chain (primary + 7 fallbacks in `_FREE_MODEL_CHAIN`) that includes `z-ai/glm-5.1` as a demoted entry
>
> Reproduce aggregates from `output/reports/run_*/summary.json` and `verification_manifest.json`. Runs without an API key still produce manuscript artefacts; Hermes rows show `hermes_success=0`.

## Top-Level Pipeline Orchestration (`run.sh`)

`fep_lean` is selected by template discovery (`--project fep_lean`) when it appears under `projects/` (see [`docs/_generated/active_projects.md`](../../../docs/_generated/active_projects.md)). It integrates into the global template DAG executed by the repository root [`run.sh`](../../../run.sh). The integration sequence is as follows:

1. **Discovery & Setup**: The orchestrator automatically discovers `fep_lean` and verifies the environment via `00_setup_environment.py`.
2. **Project Testing**: `01_run_tests.py` executes the `tests/` directory natively, relying on the project's zero-mock testing policy to validate the environment.
3. **Project Analysis**: repo-root [`scripts/02_run_analysis.py`](../../../scripts/02_run_analysis.py) runs **every** `scripts/*.py` in this project except names starting with `_` (so `_maint_*.py` maintenance scripts are **not** auto-run). The template discovers them as `projects/<name>/scripts/*.py` for the active project name. Each script is executed in its own subprocess with a timeout from [`infrastructure/core/analysis_timeout.py`](../../../infrastructure/core/analysis_timeout.py): default **`ANALYSIS_SCRIPT_TIMEOUT_SEC=7200`** (2 hours); `0` / `none` / `unlimited` disables the per-script timeout. The first script is typically `01_fep_catalogue_and_figures.py` (lightweight or full `FEPPipeline` per env below).
4. **PDF Rendering**: `03_render_pdf.py` compiles the manuscript PDF utilizing Pandoc and xelatex.
5. **Output Validation**: Final verification sweeps logic via `04_validate_output.py`.

This integration ensures the project benefits from global executive reporting, automated steganography (if using `secure_run.sh`), and consistent artifact formatting.

---

## Stage 02 (repository root analysis)

Repo-root [`scripts/02_run_analysis.py`](../../../scripts/02_run_analysis.py) runs each discovered project script in its own subprocess. The per-script limit is **`ANALYSIS_SCRIPT_TIMEOUT_SEC`** (default **7200** s); see [`infrastructure/core/analysis_timeout.py`](../../../infrastructure/core/analysis_timeout.py). This is the same mechanism summarized under **Top-Level Pipeline Orchestration** (step 3) above.

---

## Entry Points

| Entry | Role |
| ----- | ---- |
| `scripts/01_fep_catalogue_and_figures.py` | Called by template `02_run_analysis.py`; sets `MPLBACKEND=Agg`, calls `orchestrator.run_pipeline` |
| `pipeline/orchestrator.py::run_pipeline` | Full pipeline + reporting; optional `FEP_LEAN_GAUSS_WORKFLOWS=1` enables `FEPPipeline` Gauss stage |
| `scripts/02_run_single_topic.py` | CLI for `run_single_topic(topic_id)` |

---

## Two Modes (workflows on vs off)

`workflows_enabled()` in `gauss/cli.py` is true only when `FEP_LEAN_GAUSS_WORKFLOWS` is `1` / `true` / `yes` / `on`.

### Lightweight (default for `01_fep_*` without exports)

[`scripts/01_fep_catalogue_and_figures.py`](../scripts/01_fep_catalogue_and_figures.py) sets `FEP_LEAN_GAUSS_WORKFLOWS=0` when that variable was **not** already set in the parent environment, unless `FEP_LEAN_LIVE_TESTS` is truthy. So a bare `uv run python scripts/01_fep_*.py` runs **catalogue + validation + skipped Gauss + manuscript artifacts** without Hermes/OpenRouter.

**Interactive** use via repo [`run.sh`](../../../run.sh) is different: the shell exports `FEP_LEAN_GAUSS_WORKFLOWS="${FEP_LEAN_GAUSS_WORKFLOWS:-1}"`, so workflows default **on** unless you export `0`.

Executable order after `run_pipeline`:

1. **`FEPPipeline.run()`** — Load Catalogue → Environment Validation → Gauss Sessions (**skipped** if workflows falsy) → Manuscript Artifacts (`write_manuscript_vars`, `09z` markdown, `write_all_catalogue_figures` → `output/figures/`). Optional env **`FEP_LEAN_MAX_TOPICS`** caps how many topics enter Gauss Sessions after filters.
2. **`Reporter.generate()`** — invoked from `orchestrator.run_pipeline` **after** `FEPPipeline.run()` returns. Writes `output/reports/run_*/` with `index.md`, `summary.json`, `hermes_report.md`, `lean_report.md`, `validation_report.md`, and `topics/fep-NNN.md` for each catalogue row. **Reporter is not a 5th entry in `PipelineResult.stages`** — the `stages` list only records the four DAG stages inside `run()`.

There is no `catalogue_bulk.jsonl` under the run directory; bulk JSONL exports live under `{GAUSS_HOME}/fep_artifacts/` when using `OpenGaussClient.write_bulk_jsonl`.

### Full agentic (`FEP_LEAN_GAUSS_WORKFLOWS=1`)

`run_pipeline` always constructs `FEPPipeline`; with the flag truthy, **Gauss Sessions** runs (`GaussRunner` per topic). When falsy, that stage is **skipped** and the rest (including **Manuscript Artifacts**) still runs.

#### Concrete example — full batch with Gauss enabled

```bash
# Live Hermes + Lean over all 50 topics (OpenRouter free tier)
export OPENROUTER_API_KEY=sk-or-...
export FEP_LEAN_GAUSS_WORKFLOWS=1
export HERMES_MODEL=moonshotai/kimi-k2.6   # primary (matches baseline)
export FEP_LEAN_PREFETCH=1                  # overlap next-topic Hermes with current-topic Lean
export FEP_LEAN_VERIFY_TIMEOUT=300          # per-topic `lake env lean` budget (seconds)

uv run python scripts/01_fep_catalogue_and_figures.py
# → end-to-end wall-clock dominated by Hermes when enabled
# → 50/50 Hermes OK, 50/50 Lean clean when verify stage green
# → output/reports/run_YYYYMMDD_HHMMSS/summary.json
```

Without the API key you still get catalogue validation, figures, manuscript artifacts, and a report
bundle marked `hermes_success=0` for every row — useful for quick CI sanity runs.

---

## `FEPPipeline` — staged DAG

```python
FEPPipeline(project_root).run(topic_filter=None, area_filter=None) -> PipelineResult
```

The DAG has **exactly four** stages appended to `PipelineResult.stages`:

| Stage | `StepResult.name` | Description |
|-------|-------------------|-------------|
| 1 | Load Catalogue | `FEPTopicCatalogue.from_yaml(config/topics.yaml)` — 50 topics (after filters) |
| 2 | Environment Validation | `run_validation_checks` — 13 checks |
| 3 | Gauss Sessions | `GaussRunner.run_topics_batch` — Hermes + `LeanVerifier` + SQLite per topic (skipped unless workflows enabled) |
| 4 | Manuscript Artifacts | `write_manuscript_vars` + `write_full_topic_lean_catalogue_markdown` (`manuscript/09z_appendix_b_lean_catalogue.md`) + `write_all_catalogue_figures` |

`Reporter.generate()` runs **after** `FEPPipeline.run()` returns, from inside
`orchestrator.run_pipeline`. It is **not** a 5th stage in the `stages` dict and does not produce a
`StepResult`. Downstream code that iterates `PipelineResult.stages` will always see these four rows
(Gauss may be `skipped`).

**Parallelism (safe defaults) — Stage 4 Manuscript Artifacts:**

`pipeline/core.py` uses a `ThreadPoolExecutor(max_workers=2)` inside `_stage_artifacts`:

- **Thread 1** runs `_manuscript_block`, which writes `manuscript_variables.json` via
  `write_manuscript_vars` **and** `manuscript/09z_appendix_b_lean_catalogue.md` via
  `write_full_topic_lean_catalogue_markdown`. These two writes are pinned to the same thread so
  they share the same catalogue object and don't race each other.
- **Thread 2** runs `write_all_catalogue_figures(self._catalogue, self.project_root)` to render
  the nine PNGs under `output/figures/`.

The executor blocks on `f_ms.result()` and `f_fig.result()` before the stage completes, so any
exception from either branch surfaces as a normal stage failure. Inside
`write_all_catalogue_figures`, figure generation additionally uses a `ProcessPoolExecutor` with
**spawn** (one matplotlib state per process); on failure it falls back to serial. Set
`FEP_LEAN_FIGURES_MP=0` to skip the process pool and render serially.

**Parallelism — Stage 3 Gauss Sessions:** set `FEP_LEAN_PREFETCH=1` to overlap Hermes HTTP for the
**next** catalogue row with `lake env lean` on the **current** row (`gauss/runner.py`
`_run_topics_batch_prefetch`; `verify` workflow only, ≥2 topics). `LeanVerifier.verify_batch` stays
**serial** (`max_workers=1`) to avoid `.olean` races. **Tests:** optional `pytest-xdist` is listed
under `dev` dependencies; the default pytest command remains single-process because multiple
workers can contend on the shared `lean/.lake` workspace — see [`tests/AGENTS.md`](../tests/AGENTS.md).

Stage 3 is **skipped** when `FEP_LEAN_GAUSS_WORKFLOWS` is falsy (unset counts as falsy in
`workflows_enabled()`).

Note — **four vs six**: `PipelineResult.stages` always has **four** named entries (Gauss may be
`skipped`). The six-step DAG figure in `manuscript/03f_pipeline_architecture.md` is an end-to-end
narrative (including the post-`run()` report bundle), not an extra two rows in `stages`.

Per-topic Lean skips (no `lake`, sandbox, and so on) are recorded on each `TopicRunResult`, not as
a separate pipeline stage.

### `StepResult` / `PipelineResult`

`pipeline/core.py` defines `StepResult` (`status` may be `ok`, `error`, `skipped`, or `warning`)
and `PipelineResult` (`stages`, `lean_stats`, topic metrics via properties). The orchestrator
attaches `run_dir` and may enrich the object before `Reporter.generate`.

---

## Stage 2: Validation Detail

`run_validation_checks(project_root)` runs **13** named checks (see [AGENTS.md](../AGENTS.md)):

- Tooling: `gauss`, `lake`, `GAUSS_HOME` / `.gauss`, `lean/` workspace, `mathlib_built` (Mathlib `.olean` probe)
- Project: `topics.yaml`, layout, Python stack, `output/` writable, manuscript config, scripts/tests layout, catalogue import, `references.bib`

All checks complete regardless of failure; aggregate `status` is `ok` only if all pass.

---

## Stage 3: Gauss Sessions (`GaussRunner`)

Before the per-topic loop, `_stage_gauss` calls `HermesExplainer.preflight()` once — a
`max_tokens=1` live probe at the current model/endpoint. On **401 / 403** it disables
Hermes globally and logs actionable remediation (OpenRouter key page, Anthropic-direct
env vars). On 5xx / transport it logs and continues (real topics retry with backoff).

Per topic:

```text
create_session(topic_id, area, lean_sketch)
HermesExplainer.explain_topic(topic)  → HermesResult  [2-message HTTP call]
_record_hermes_turns:
  update_session(0, "system",    system_prompt)
  update_session(1, "user",      theorem_block)
  update_session(2, "assistant", explanation + refined lean sketch)
  [optional] update_session(3, "assistant_reasoning", reasoning)
set_refined_sketch(session_id, refined_sketch)
LeanVerifier.verify_sketch(...)  → VerifyResult
write_artifact(session_id, payload)
close_session(session_id, hermes_success, lean_compiles=...)
```

Hermes returns `HermesResult(success=False)` immediately (no network) when `api_key=''` **or**
`enabled=False`.

---

## Lean verification (inside `GaussRunner`)

Per topic with a `refined_lean_sketch` (or falls back to original `lean_sketch`):

```text
LeanVerifier.verify_sketch(topic_id, lean_code) → VerifyResult
  → executes sequentially (max_workers=1) to prevent ELAN sandbox import masking
  → writes temp file to lean/FepSketches/
  → subprocess: lake env lean <file>  (timeout: FEP_LEAN_VERIFY_TIMEOUT, default 300s)
  → removes temp file
  → VerifyResult(compiles, has_sorry, errors, warnings, status)
```

`VerifyResult.status` values:

| Value | Meaning |
|-------|---------|
| `compiles_clean` | `lake env lean` exits 0, no `sorry` |
| `compiles_with_sorry` | exits 0 but sketch contains `sorry` |
| `compile_error` | non-zero exit code |
| `skipped(...)` | lake absent, sandbox error, or lakefile not found |

---

## Reports (`Reporter`, after `FEPPipeline.run`)

```text
output/reports/run_YYYYMMDD_HHMMSS/
├── index.md                 ← Pipeline summary + stage table + topic stats
├── summary.json             ← Full PipelineResult (JSON)
├── hermes_report.md         ← Per-topic Hermes status and explanations
├── lean_report.md           ← Per-topic VerifyResult table
├── validation_report.md     ← 13 check results
└── topics/                  ← Per-topic markdown reports
```

---

## Filters

| Parameter | Effect |
|-----------|--------|
| `area_filter` | Only process topics from this area (one of 5) |
| `topic_filter` | Process only these topic IDs (`["fep-001", "fep-002"]`) |
| `FEP_LEAN_MAX_TOPICS` (env) | After filters, keep only the first *N* topics for Gauss Sessions (`pipeline/core.py`) |

Validation (stage 2) always runs against the resolved project tree; the catalogue is loaded in stage 1 (50 topics before filters).

---

## Timing

Dominated by:

- **Stage 02 subprocess** (each analysis script): default wall-clock cap **`ANALYSIS_SCRIPT_TIMEOUT_SEC=7200`** (2 h) per script unless overridden or disabled — see [configuration.md](configuration.md#monorepo-stage-02-repository-root).
- Gauss stage (Hermes + Lean per topic): highly variable. Hermes retries HTTP **429** and **transient** transport errors (e.g. chunked `IncompleteRead`) with backoff (`HERMES_429_MAX_RETRIES`, `HERMES_NETWORK_MAX_RETRIES`). Lean runs **serially** (`max_workers=1`) to prevent macOS ELAN sandbox proxy lock contention; total time scales with topic count and API rate limits.
- Validation: usually seconds; slower if `gauss doctor` or Mathlib checks are cold
- Catalogue load: negligible

**Baseline** — measured macOS run with pinned Mathlib tag, `moonshotai/kimi-k2.6` primary model (a reasoning model — see [hermes.md §"Reasoning models and tokens"](hermes.md#reasoning-models-and-tokens)), `FEP_LEAN_PREFETCH=1`:

| Phase | Observed (order-of-magnitude) |
|-------|-------------------------------|
| Full `01_fep_catalogue_and_figures.py` end-to-end | **~30–60 min** (provider/queue-dependent for the reasoning model; prior `z-ai/glm-5.1` runs landed ~21 min — current measured value lives in `manuscript_vars.yaml::verify.duration_min`) |
| 50-topic Hermes HTTP (avg ~1500 prompt tok/topic + reasoning trace) | dominant share of total, prefetch-overlapped with Lean |
| 50-topic Lean pass (serial `lake env lean`) | ~262 s (avg 5.2 s/topic) |
| Manuscript Artifacts (2-thread pool, 9 figures) | < 30 s |
| Validation (13 checks) | single-digit seconds when warm |

Per-test timeout is **900 s** (`pyproject.toml [tool.pytest.ini_options] timeout`). Plan GitHub
Actions job timeouts accordingly.

---

## See also

- [configuration.md](configuration.md) — every env var and YAML knob
- [opengauss.md](opengauss.md) — session store schema and CLI glue
- [hermes.md](hermes.md) — LLM explainer details
- [api.md](api.md) — public APIs for every `src/` module
- [cli-reference.md](cli-reference.md) — CLI surface of the analysis scripts
- [troubleshooting.md](troubleshooting.md) — pipeline failure modes with fixes
