# PAI — fep_lean

**Version**: v0.7.0 | **Type**: Project | **Status**: Active | **Last Updated**: April 2026

## AI Context Summary

`fep_lean` formalizes 50 FEP / Active Inference / Bayesian Mechanics topics via a 4-stage agentic pipeline (Load Catalogue → Environment Validation → Gauss Sessions → Manuscript Artifacts). Each topic yields one OpenGauss session: the pipeline records system, user, and assistant turns. The Hermes API call itself is a single HTTP request with 2 chat messages (system + user); the session structure records the full context including catalogue sketch and LLM response. Sessions are persisted in SQLite (`{GAUSS_HOME}/fep_lean_state.db`), Lean sketches are compiled via `lake env lean`, and reports are written to `output/reports/run_*/`.

**Catalogue**: 50 topics (`fep-001`…`fep-050`), 5 areas, in `config/topics.yaml`.

**Maturity**: All **50** topics are `mathlib_status: real` with compiling Lean sketches in `config/topics.yaml` (source: `scripts/catalogue_sketches.py`). Sketches are short Mathlib-backed lemmas keyed to each topic, not placeholders.

---

## Entry Points

| Task | Command |
| ---- | ------- |
| Install deps (canonical) | From **project root**: `uv sync --extra dev`. From **repository root**: `uv sync --directory <path-to-this-project> --extra dev` |
| Toolchain preflight (gauss / lean / Mathlib) | From **project root**: `uv run fep-lean-preflight` |
| Catalogue + figures (from project root) | `uv run python scripts/01_fep_catalogue_and_figures.py` |
| Single topic (orchestrator) | From **project root**: `uv run python scripts/02_run_single_topic.py fep-001` |
| Full pipeline (programmatic) | From **project root**: `PYTHONPATH=src python3 -c "from pipeline.orchestrator import run_pipeline; run_pipeline()"` |
| Template analysis stage (repo root) | `uv run python scripts/02_run_analysis.py --project fep_lean` |
| Regenerate 50-topic YAML | From **project root**: `uv run python scripts/_maint_build_topics_catalogue.py` |
| Lean verify only (50 sketches) | From **project root**: `uv run python scripts/03_lean_verify_only.py` |
| Tests | From **project root**: `uv run pytest tests/ -q --timeout=900 --cov=src --cov-fail-under=89` |

---

## Key Modules

| Module | Class/Function | Role |
| ------ | -------------- | ---- |
| `catalogue/topics.py` | `FEPTopicCatalogue`, `TopicEntry` | Load 50 topics from `config/topics.yaml` |
| `gauss/client.py` | `OpenGaussClient` | SQLite session store — sessions, turns, artifacts, logs |
| `verification/lean_verifier.py` | `LeanVerifier`, `VerifyResult` | `lake env lean` compilation, sorry detection |
| `llm/hermes.py` | `HermesExplainer`, `HermesConfig`, `HermesResult` | OpenRouter LLM HTTP client, FEP system prompt |
| `gauss/runner.py` | `GaussRunner`, `TopicRunResult` | Per-topic orchestration (Hermes + Lean + SQLite) |
| `pipeline/core.py` | `FEPPipeline`, `PipelineResult`, `StepResult` | Staged DAG |
| `output/reporter.py` | `Reporter`, `ReportPaths` | Markdown + JSON report generation |
| `pipeline/orchestrator.py` | `run_pipeline`, `run_single_topic` | Template integration entrypoints |
| `config/topics.yaml` | — | 50 topics (id, area, mathlib, mathlib_status, nl, lean_sketch) |

---

## Config Priority

```
OPENROUTER_API_KEY / ANTHROPIC_API_KEY (env, highest)
HERMES_MODEL / HERMES_API_BASE (env)
GAUSS_HOME (env)
config/settings.yaml  hermes: / gauss: blocks
Code defaults (model: moonshotai/kimi-k2.6)
```

---

## API Signatures

### `OpenGaussClient`

```python
OpenGaussClient(gauss_home: str | Path | None = None)
  .create_session(topic_id, area, lean_sketch_original='', *, source='fep_lean') -> str
  .update_session(session_id, turn_index, role, content, tokens=0)
  .close_session(session_id, status='success', hermes_success=False, lean_compiles=-1)
  .set_refined_sketch(session_id, refined_sketch)
  .export_session(session_id) -> dict
  .export_all_sessions(source='fep_lean') -> list[dict]
  .write_artifact(session_id, payload, *, label='result') -> Path
  .write_bulk_jsonl(sessions, out_path) -> Path
  .log_event(event, *, session_id=None, **kwargs)
  .get_stats() -> dict
```

### `HermesConfig` / `HermesExplainer` / `HermesResult`

```python
HermesConfig(
    model='moonshotai/kimi-k2.6',
    base_url='https://openrouter.ai/api/v1',
    api_key='',
    max_tokens=16384, timeout_s=150,
    reasoning_max_tokens=65536, reasoning_timeout_s=300,
    enabled=True
)
  .from_settings(project_root=None) -> HermesConfig
  .is_reasoning_model() -> bool
  .effective_max_tokens() -> int

HermesExplainer(config: HermesConfig | None = None)
  .explain_topic(topic: TopicEntry) -> HermesResult

HermesResult(success, model_used, explanation='', refined_lean_sketch='',
             reasoning='', tokens_used=0, duration_s=0.0, error='',
             topic_id='', cache_hit=False)
  .as_dict() -> dict
```

### `LeanVerifier` / `VerifyResult`

```python
LeanVerifier(lean_dir=None, project_root=None)
  .check_lake_available() -> bool
  .lean_version() -> str | None
  .verify_sketch(topic_id, lean_code) -> VerifyResult
  .verify_batch(items: list[tuple[str,str]]) -> list[VerifyResult]

VerifyResult(topic_id, compiles, has_sorry, errors=[], warnings=[],
             stdout='', stderr='', duration_s=0.0, lean_version='unknown',
             lean_file=None, skip_reason='', failure_kind=FailureKind.NONE)
  .status: str  # 'compiles_clean' | 'compiles_with_sorry' | 'compile_error' | 'skipped(...)'
  .as_dict() -> dict
# failure_kind: 'none' | 'missing_import' | 'renamed_identifier' | 'tactic_failure'
#               | 'arity_mismatch' | 'timeout' | 'other'
```

### `GaussRunner` / `TopicRunResult`

```python
# Typical entry point — use the factory, not __init__ directly
GaussRunner.create_default(project_root, require_cli=False) -> GaussRunner

# Direct constructor (requires pre-built components)
GaussRunner(lean_verifier: LeanVerifier, hermes: HermesExplainer,
            client: OpenGaussClient, project_root: Path)
  .run_topic(topic: TopicEntry, *, workflow: str = 'verify') -> TopicRunResult
  .run_topics_batch(topics, *, max_topics=None, workflow='verify') -> list[TopicRunResult]
# Run-level aggregates (success/Hermes/Lean counts, durations) live on
# ``PipelineResult.lean_stats`` and ``PipelineResult.topic_results``; there is no
# ``GaussRunner.get_summary()`` method.

TopicRunResult(topic_id, session_id, success, status,
               hermes_success=False, lean_compiles=False,
               lean_has_sorry=False, duration_s=0.0, error='',
               workflow='verify', stage_results=[],
               explanation='', refined_lean_sketch='',
               tokens_used=0, hermes_model='',
               cache_hit=False, hermes_lean_compiles=False)
  .as_dict() -> dict
```

### `FEPPipeline` / `PipelineResult`

```python
FEPPipeline(project_root)
  .run(topic_filter=None, area_filter=None) -> PipelineResult

PipelineResult(status, total_duration=0.0, run_dir='', stages=[],
               lean_stats={})
  # Computed properties (from topic_results populated post-run):
  .steps -> list[StepResult]          # alias for stages
  .topic_results -> list[TopicRunResult]
  .hermes_count -> int
  .lean_verified_count -> int
  .lean_compile_ok -> int
  .topics_ok -> int
  .as_dict() -> dict

StepResult(name, status='ok', message='', duration_s=0.0, payload=None, error=None)
```

### `Reporter` / `ReportPaths`

```python
Reporter(project_root: Path | str)
  .generate(pipeline_result, run_dir=None) -> ReportPaths

ReportPaths(index_md, summary_json, hermes_md, lean_md, validation_md, topics_dir)
  .as_dict() -> dict[str, str]
```

---

## OpenGauss Writes

| Path | Contents |
|------|----------|
| `{GAUSS_HOME}/fep_lean_state.db` | SQLite: 5 tables (sessions, turns, artifacts, logs, hermes_cache) |
| `{GAUSS_HOME}/fep_artifacts/session_*.json` | Per-topic artifact |
| `{GAUSS_HOME}/fep_artifacts/sessions_fep_lean_*.jsonl` | Bulk JSONL export |
| `{GAUSS_HOME}/fep_logs/operations.jsonl` | Structured event log |

---

## 5-Area Taxonomy (50 topics)

| Area | Count | Examples |
|------|-------|---------|
| **FEP** | 14 | Variational FE, ELBO, Predictive Coding, Precision Weighting, Sentient Behavior |
| **ActiveInference** | 11 | Expected FE G(π), Optimal Policy, Belief Propagation, Langevin, Epistemic/Pragmatic |
| **BayesianMechanics** | 10 | Markov Blanket, Generative Model Likelihood, Empirical Bayes, Stick-Breaking Priors |
| **InfoGeometry** | 8 | Fisher Metric, KL Properties, Natural Gradient, Geodesics/Transport |
| **Thermodynamics** | 7 | Helmholtz Free Energy, NESS Solenoidal Flow, Entropy Production, Landauer Bound |

---

## Navigation

- [README.md](README.md) — Human docs
- [AGENTS.md](AGENTS.md) — Agent coordination
- [SPEC.md](SPEC.md) — Functional spec
- [../PAI.md](../PAI.md) — Parent PAI
