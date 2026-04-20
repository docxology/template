## Pipeline Architecture and Execution Profile {#sec:pipeline_architecture_and_execution_profile}

### The Central Execution and Orchestration DAG {#sec:the_6_step_directed_acyclic_graph}

The shipped analysis path is driven by `src/pipeline/orchestrator.py::run_pipeline`: environment validation, manuscript-variable regeneration, figure generation, optional Gauss workflows (`FEP_LEAN_GAUSS_WORKFLOWS=1`) that run Hermes plus `lake env lean` per topic via `GaussRunner`, and a timestamped export bundle. The executable order is documented in `docs/pipeline.md` within the `fep_lean` project tree.

### Expression lifecycle: YAML to manuscript to Lake {#sec:expression_lifecycle_yaml_to_lake}

A single chain ties informal claims to what the PDF and the compiler see:

1. **Authoring and storage.** Each topic is a row in `config/topics.yaml` (`id`, `lean_sketch`, `mathlib_status`, `nl`, …). Bulk regeneration runs through `scripts/_maint_build_topics_catalogue.py` and `scripts/catalogue_sketches.py`, as noted in the catalogue headers.
2. **Toolchain pin.** Lean and Mathlib4 versions are fixed by `lean/lean-toolchain` and `lean/lakefile.lean` inside the Lake workspace used for `lake env lean`.
3. **Manuscript artifacts.** The `Manuscript Artifacts` stage in `src/pipeline/core.py` writes `manuscript/manuscript_vars.yaml` (carrying catalogue counts, per-area counts, per-topic fields, and the `verify.*` status block) and regenerates `manuscript/09z_appendix_b_lean_catalogue.md` with exactly one fenced Lean block per topic. That appendix is the single in-manuscript source for full catalogue sketches; do not duplicate the fences elsewhere.
4. **PDF injection.** During combined Markdown-to-LaTeX rendering, the template renderer (`infrastructure/rendering/_pdf_combined_renderer.py` at the repository root) substitutes `{{…}}` placeholders from `manuscript_vars.yaml`. Run the pipeline or `write_manuscript_vars` before rendering so that placeholders resolve.
5. **Optional native check.** When verification is enabled, `src/verification/lean_verifier.py` checks each sketch with `lake env lean` inside the Lake project; aggregates land in `verification_manifest.json` and then feed the `verify.*` fields in `manuscript_vars.yaml` after variables are regenerated.

Appendix §\ref{sec:appendix_comprehensive_formalisms_overview} summarizes the catalogue appendix and the reader affordances it provides; it does not replace steps 1–3.

![Linearized view of the shipped 6-step orchestrator flow. The four recorded `PipelineResult.stages` (Load Catalogue → Environment Validation → Gauss Sessions → Manuscript Artifacts) are followed by two post-`run()` steps (JSONL export and the timestamped report bundle under `output/reports/run_*/`) that `run_pipeline` performs after `FEPPipeline.run` returns. Stage 3 (Gauss Sessions) is opt-in via `FEP_LEAN_GAUSS_WORKFLOWS=1` and is the only stage whose wall-clock depends on OpenRouter latency; the other five stages each complete in under one second on a warm workspace. The figure reveals that the pipeline's cost profile is dominated by a single opt-in stage, making the default (thin) path essentially I/O-bound.](../output/figures/pipeline_dag.png){#fig:pipeline_dag width=100%}

### Sequence Diagram: Single Topic Execution {#sec:sequence_diagram_single_topic_execution}

Extended workflows can still follow the multi-turn pattern catalogue NL → Lean sketch → validation request → Hermes. The template-integrated path exports per-topic markdown directly from the YAML catalogue into `output/reports/run_*/topics/` without requiring SQLite. In **thin mode** (default, `FEP_LEAN_GAUSS_WORKFLOWS` unset), the pipeline flows YAML catalogue entries directly into per-topic Markdown reports without any LLM or compiler calls. In **agentic mode** (`FEP_LEAN_GAUSS_WORKFLOWS=1`), each topic additionally traverses the Hermes→Lean→SQLite path before the Markdown report is written.

![Sequence diagram for single-topic execution. In extended (Gauss-enabled) mode the pipeline creates an OpenGauss session, sends the topic to Hermes for LLM explanation and validation via OpenRouter, verifies the refined sketch with `lake env lean`, writes JSON artifacts to `$GAUSS_HOME/fep_artifacts/`, and closes the session in SQLite. In thin mode the catalogue YAML flows directly to per-topic Markdown reports without LLM or Lean calls.](../output/figures/sequence_diagram.png){#fig:sequence_diagram width=80%}

### Persistent state: dual-mode storage {#sec:persistent_state_sqlite_schema}

State persistence depends on the pipeline mode.

**Lightweight mode** (default, `FEP_LEAN_GAUSS_WORKFLOWS` unset) uses file-based run bundles only:

- `output/reports/run_YYYYMMDD_HHMMSS/` holds `index.md`, `summary.json`, `hermes_report.md`, `lean_report.md`, `validation_report.md`, and `topics/*.md`. Bulk session JSONL, when exported, lives under `$GAUSS_HOME/fep_artifacts/` rather than in the run directory.
- `output/reports/gauss_doctor_last.json` is optional and appears after a successful `gauss doctor`.
- `manuscript/manuscript_vars.yaml` receives the injected catalogue statistics used during rendering.

**Full agentic mode** (`FEP_LEAN_GAUSS_WORKFLOWS=1`) instantiates `GaussRunner` (from `src/gauss/runner.py`) driving an `OpenGaussClient`, which writes to a strict SQLite session store at `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`). Orchestration milestones — sessions, LLM turns, compiled artifacts, and verification logs — are mapped from native Python `PipelineResult` dataclasses into five SQL tables (`sessions`, `turns`, `artifacts`, `logs`, `hermes_cache`), all configured with Write-Ahead Logging (WAL) and strict constraints. See [opengauss.md](../docs/opengauss.md) for the internal schema design.

When present, `verification_manifest.json` (under the same run tree) summarizes the native compilation sweep.

#### Per-topic audit trail {#sec:per_topic_audit_trail}

For each topic, readers can consult the exported `topics/<id>.md` and `summary.json` for run-scoped machine-readable data; the full catalogue rows remain canonical in `config/topics.yaml`. In full agentic mode, Hermes transcripts are stored in the SQLite `turns` table and exported as per-session JSON artifacts under `$GAUSS_HOME/fep_artifacts/`.

#### Run-level artifacts {#sec:run_level_artifacts}

Each `output/reports/run_YYYYMMDD_HHMMSS/` folder contains `index.md`, `summary.json`, `hermes_report.md`, `lean_report.md`, `validation_report.md`, and `topics/*.md`, and adds `verification_manifest.json` whenever a verification sweep has been executed.

### SQLite Schema: Five Tables {#sec:sqlite_schema_five_tables}

When `FEP_LEAN_GAUSS_WORKFLOWS=1`, the pipeline persists state in `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`). The schema contains five tables:

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `sessions` | `id`, `topic_id`, `model`, `status`, `hermes_success`, `lean_compiles`, `duration_s`, `created_at` | One row per topic per run |
| `turns` | `id`, `session_id`, `turn_index`, `role`, `content`, `tokens` | LLM dialogue: system, user, assistant, assistant_reasoning |
| `artifacts` | `id`, `session_id`, `artifact_type`, `path`, `content` | JSON artifacts with Hermes and `VerifyResult` fields |
| `logs` | `id`, `session_id`, `level`, `message`, `timestamp` | Per-topic diagnostic log |
| `hermes_cache` | `id`, `cache_key`, `response`, `model`, `created_at`, `expires_at` | SHA-256 keyed response cache |

**Key design decisions:**

- WAL (Write-Ahead Logging) is enabled for concurrent read/write safety.
- `hermes_cache` uses `SHA-256(topic_id + lean_sketch + model + stage)` as its key, so cache hits avoid redundant OpenRouter calls.
- `sessions.lean_compiles` is a boolean derived from `VerifyResult.compiles`.

### Environment Variable Reference {#sec:environment_variable_reference}

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required for live Hermes calls |
| `FEP_LEAN_GAUSS_WORKFLOWS` | `0` | Set to `1` to enable Hermes + Lean workflow |
| `HERMES_MODEL` | `moonshotai/kimi-k2.6` | Override primary LLM model |
| `HERMES_429_MAX_RETRIES` | `2` | Max retries on HTTP 429 per model before advancing chain |
| `HERMES_NETWORK_MAX_RETRIES` | `2` | Max retries on transient network errors |
| `HERMES_MAX_MODEL_ATTEMPTS` | `6` | Max models to try from fallback chain |
| `FEP_LEAN_VERIFY_TIMEOUT` | `300` | Seconds before `lake env lean` subprocess is killed |
| `GAUSS_HOME` | `~/.gauss` | Directory for SQLite DB and artifacts |
| `GAUSS_DEFAULT_MODEL` | — | Fallback model if `HERMES_MODEL` unset |
| `LOG_LEVEL` | `1` | 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR |

**PYTHONPATH ordering requirement.** `projects/fep_lean/src` *must* appear before `infrastructure/` on `PYTHONPATH`, because `infrastructure/llm/` would otherwise shadow `projects/fep_lean/src/llm/` under Python's first-match-wins module resolution. Correct invocation:

```bash
PYTHONPATH=projects/fep_lean/src:.:infrastructure \
  FEP_LEAN_GAUSS_WORKFLOWS=1 \
  uv run python projects/fep_lean/scripts/01_fep_catalogue_and_figures.py
```

### Representative run statistics {#sec:pipeline_run_statistics}

| Metric | Value |
|--------|-------|
| Total topics | 50 |
| Hermes API successes | {{hermes.success_count}}/{{hermes.processed}} (run `{{hermes.run_id}}`; cache hits {{hermes.cache_hits}}) |
| Lean compilation successes | **Catalogue baseline** (`scripts/03_lean_verify_only.py`): **{{compile_rate.total}}**; **Hermes-assisted live run** (`{{verify.run_id}}`): **{{compile_rate.total}} clean, {{verify.sorry_count}} sorry, {{verify.compiles_false}} errors** — see §\ref{sec:live_verification_error_taxonomy} |
| Wall-clock time | ≈{{verify.duration_min}} min for {{total_topics}} topics with live Hermes at `HermesConfig.timeout_s=150` and `FEP_LEAN_VERIFY_TIMEOUT=300` (measured `{{verify.run_id}}`; provider-dependent) |
| Mean time per topic | ≈25 s median (LLM-dominated: ~23 s Hermes HTTP + ~1–2 s `lake env lean`; see §\ref{sec:execution_metrics_the_definitive_run}) |
| Primary model | {{hermes.primary_model}} (full distribution: {{hermes.models_used}}) |
| Fallback invocations | {{hermes.fallback_count}} (Hermes-refined Lean compiled directly: {{hermes.hermes_lean_compiles_count}}/{{hermes.processed}}) |
| Mean tokens per topic | {{hermes.tokens_mean}} tokens (bounded by `HermesConfig.max_tokens=16384`; run `{{hermes.run_id}}`) |
| {{total_topics}}-topic total tokens | {{hermes.tokens_total}} (run `{{hermes.run_id}}`) |

### Execution Metrics: representative run {#sec:execution_metrics_the_definitive_run}

Wall-clock for a full 50-topic run is dominated by OpenRouter latency whenever Hermes is live. The table below is illustrative; substitute numbers from a specific `summary.json` when citing concrete figures.

| Metric | Verified Orchestrator Profile |
|--------|----------------------------------|
| Total duration | ~21 minutes for 50 topics with live Hermes, bounded by a 30-minute CI orchestrator limit |
| Mean time per topic | ~25 s, dominated by OpenRouter LLM reasoning plus the isolated `lake env lean` compilation |
| Compiler latency | ~1–2 s per sketch with narrow Mathlib4 imports; substantially longer with a blanket `import Mathlib` |
| Hermes success share | 0/N when Hermes is skipped or every call fails; up to N/N with a valid key and successful responses (N is the number of topics processed) |

When `verification_manifest.json` exists, its compile-rate fields feed the `verify.*` entries in `manuscript_vars.yaml`. Regenerate those variables after any native sweep so the file reflects the newest manifest under `output/reports/run_*/` or your configured report root.

### Reproducibility Checklist {#sec:reproducibility_checklist}

From the `fep_lean` project root:

1. **Python environment.** `uv sync` (dependencies are declared in `pyproject.toml`; this package has no `requirements.txt`).
2. **Lean workspace.** Run `./scripts/_maint_bootstrap_lean_toolchain.sh` (or `./scripts/00_lean_mathlib_setup.sh`, which wraps it). Optional: `PYTHONPATH=src uv run python scripts/03_lean_verify_only.py` runs the Lean batch check locally across every sketch.
3. **Run bundle.** From the project root, `PYTHONPATH=src uv run python scripts/01_fep_catalogue_and_figures.py` or `scripts/02_run_single_topic.py`. From the monorepo root, `uv run python scripts/02_run_analysis.py --project fep_lean`. See `pipeline/orchestrator.py` for the programmatic entrypoints.
4. **Full run with live Hermes and verification.** Export `OPENROUTER_API_KEY`, set `export FEP_LEAN_GAUSS_WORKFLOWS=1`, and ensure `gauss.verify_lean: true` in `config/settings.yaml` (the default in the shipped file).

Hermes natural-language wording may vary between runs; the Lean compiler output for a fixed sketch under a pinned toolchain is fully reproducible.
