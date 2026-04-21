# Methodology and System Architecture {#sec:methodology_and_system_architecture}

The methodology rests on a modular technical stack built around the FEP Lean architecture and enforces a strict zero-mock policy: every compiler invocation, database transaction, and HTTP request is executed against the real subsystem rather than a stub. This section gives the high-level view; six detailed sub-sections (§\ref{sec:lean_4_a_primer_for_active_inference_researchers}–§\ref{sec:pipeline_architecture_and_execution_profile}) each expand a single pipeline component — Lean 4 primer, Mathlib4 coverage map, `sorry` maturity taxonomy, Hermes LLM, native compilation, and the 4-stage DAG — with reproducibility-grade detail.

> **Readers unfamiliar with Lean 4 or interactive theorem proving** should begin with §\ref{sec:lean_4_a_primer_for_active_inference_researchers}, which introduces the core concepts from the perspective of Active Inference research.

## System Architecture Overview {#sec:system_architecture_overview}

The pipeline's core DAG executes **four recorded stages** — Load Catalogue, Environment Validation, Gauss Sessions, and Manuscript Artifacts. The orchestrator wraps these into a **6-step end-to-end flow** that additionally performs JSONL export, statistics aggregation, and timestamped run-bundle reporting. The table below documents the full orchestrator flow.

**Data flow per topic**:

| Stage | Input | Process | Output | Duration |
|-------|-------|---------|--------|----------|
| 1. Load | `topics.yaml` | Parse 50 catalogue rows (`FEPTopic`) | Typed catalogue | <1s |
| 2. Validate | Environment | 13 environment checks (Gauss CLI, Lean/Lake workspace, Mathlib4 cache, YAML, layout, Python stack, catalogue load, …) | Pass/fail report | <1s |
| 3. Run topic | NL + Lean sketch (`topics.yaml`, sourced from `SKETCHES` in `scripts/catalogue_sketches.py`) | OpenGauss session when `FEP_LEAN_GAUSS_WORKFLOWS=1`: one Hermes HTTP call (2 chat messages), up to 4 persisted SQLite turn rows; then `lake env lean` verification; compiler output in JSON artifacts | Session + turns + artifact JSON in SQLite | ≈28 s (representative GLM-5.1-primary median; see §\ref{sec:execution_metrics_the_definitive_run}) |
| 4. Export | DB sessions | JSONL serialization | Bulk artifact file | <1s |
| 5. Stats | DB queries | Aggregate metrics | Summary JSON | <1s |
| 6. Report | All session data | Markdown generation | Modular run subfolder | <1s |

## The Command-Line Toolchain {#sec:the_command_line_toolchain}

Researchers interact with the FEP Lean infrastructure through a suite of specialized Python scripts under `scripts/`. Each script exposes granular control over a specific pipeline stage:

- **Catalogue and Figures** (`01_fep_catalogue_and_figures.py`) validates `config/topics.yaml` and regenerates procedural figures. After editing catalogue bodies in `scripts/catalogue_sketches.py` (`SKETCHES`), run `scripts/_maint_build_topics_catalogue.py` to keep the YAML aligned (see the SSOT test `tests/test_catalogue_sketches_ssot.py`).
- **Single Topic Formalization** (`02_run_single_topic.py <id>`) runs the per-topic Hermes + Lean verification workflow for one topic, which is the primary loop for iterative refinement of theorem sketches.
- **Batch Lean Verification** (`03_lean_verify_only.py`) bypasses the LLM layer and drives a native Lean 4 compilation check across every sketch in the catalogue, applying the zero-mock mandate at scale.
- **Report Generation** (`04_generate_reports.py`) aggregates the latest pipeline outputs into the human-readable documentation hub.

## The Hermes Agent and LLM Integration {#sec:the_hermes_agent_and_llm_integration}

The reasoning engine is the `HermesExplainer` class defined in `src/llm/hermes.py`.

- **Hermes agent infrastructure.** The agent framework routes queries to OpenRouter, manages request context, and enforces a rigid structural template through a dedicated FEP-domain system prompt that constrains the LLM to valid Lean 4 output.
- **Model backbone.** To handle the reasoning load of mapping high-level physics into strict dependent types, the primary model is **Moonshot Kimi K2.6** (`moonshotai/kimi-k2.6`), served via the OpenRouter API. Kimi K2.6 was selected for its 262K context window and consistently fast time-to-first-token; it sits in `_REASONING_MODELS` so it receives the larger `reasoning_max_tokens` budget. **ZhipuAI GLM-5.1** (`z-ai/glm-5.1`, 128K context) is retained in the fallback chain after it returned empty content past the standard 150 s budget on a prior cold-restart run; the wall-clock-deadline guard in `_make_request` now ensures any slow streaming model is abandoned at its budget so the chain can advance.
- **Prompt engineering.** The system prompt requires a 2–4 sentence explanation followed by a refined Lean 4 sketch in a fenced code block, with honest reporting of Mathlib4 module paths. Committed theorem bodies are authored in `scripts/catalogue_sketches.py` (`SKETCHES`) and regenerated into `config/topics.yaml`; Hermes never overwrites the catalogue in the default pipeline — it reviews the sketch that the YAML supplies.
- **Fallback chain** (see `_FREE_MODEL_CHAIN` in `src/llm/hermes.py`). The chain has six entries, starting with the primary GLM-5.1 and followed by five free OpenRouter models: **Nemotron 120B** (`nvidia/nemotron-3-super-120b-a12b:free`), **Qwen3-Next 80B** (`qwen/qwen3-next-80b-a3b-instruct:free`), **GPT-OSS 120B** (`openai/gpt-oss-120b:free`), **Hermes 3 Llama 405B** (`nousresearch/hermes-3-llama-3.1-405b:free`), and **Trinity Large** (`arcee-ai/trinity-large-preview:free`). The helper `_build_model_chain` deduplicates the configured primary against the chain so that overriding `HERMES_MODEL` does not produce a duplicate entry. Premium paid models (for example `anthropic/claude-sonnet-4` or `deepseek/deepseek-r1`) can be configured manually via `HERMES_MODEL` or `config/settings.yaml` but are not part of the shipped default chain.

See §\ref{sec:the_hermes_ai_agent_and_llm_assisted_formalization} for the full Gauss session protocol, model fallback chain, and post-processing pipeline.

## The Native Lean Compilation Engine {#sec:the_native_lean_compilation_engine}

Simulated compilation offers no guarantee of mathematical coherence. To validate the syntax and type-correctness of every generated formalism, the pipeline uses a native compiler bridge:

- **Native shell orchestration.** [`src/verification/lean_verifier.py`](../src/verification/lean_verifier.py) defines `LeanVerifier`, which wraps each catalogue body with a standard preamble (`import Mathlib` plus shared `open` lines, applied via `_wrap_lean_code` — the `mathlib` field in YAML is a navigation hint, not a per-snippet import list), writes a temporary `.lean` file under `lean/FepSketches/`, and invokes `lake env lean <file>` as a subprocess. This is a per-file typecheck, not a full `lake build` of the workspace.
- **Aggressive caching.** Mathlib4 `.olean` artifacts live in the repository Lake workspace under [`lean/`](../lean/), populated by `lake exe cache get` followed by `lake build`. The verifier reuses that environment directly; there is no separate `~/.gauss/` Lean tree for compilation.
- **Sub-second feedback.** With a primed workspace, the verifier typechecks Lean 4 expressions and parses raw `stdout`/`stderr` from the compiler in about **1.5 seconds per query**. The subprocess is capped by `FEP_LEAN_VERIFY_TIMEOUT` (default **300 s**); any longer run is classified as `timeout` by `classify_failure_kind` and surfaced as a skip in `VerifyResult`.

See §\ref{sec:native_lean_4_compilation_and_zero_mock_verification} for the full compilation architecture, caching strategy, and zero-mock standard.

## OpenGauss Workflow and State Integration {#sec:opengauss_database_integration}

Persistence and orchestration rely on **OpenGauss**, a project-scoped Lean workflow orchestrator developed by Math, Inc. ([OpenGauss repository](https://github.com/math-inc/OpenGauss)). OpenGauss provides a multi-agent frontend for `lean4-skills` workflows (prove, draft, review, autoformalize) and handles project detection, managed backend setup, swarm tracking, and recovery. This framework is entirely distinct from the Huawei OpenGauss relational database product.

- **SQLite persistence.** Multi-agent sessions and Hermes/Lean results are written to `fep_lean_state.db` under `GAUSS_HOME` (default `~/.gauss`). When `FEP_LEAN_GAUSS_WORKFLOWS=1` and `gauss.verify_lean: true` in `config/settings.yaml`, `GaussRunner` invokes `LeanVerifier` per topic; raw compiler diagnostics are stored in the per-topic JSON artifact (Hermes output plus `VerifyResult` fields), not as additional chat turns in the SQLite `turns` table.
- **Session identifiers.** One session is created per topic id (for example `fep-001`), optionally suffixed with a run tag to disambiguate parallel runs.
- **Operations log.** All database operations are appended to `operations.jsonl` with UTC timestamps for post-hoc audit.

See §\ref{sec:pipeline_architecture_and_execution_profile} for the full database schema, operations log, and execution metrics.

## The Unified Execution Pipeline {#sec:the_unified_execution_pipeline}

The `orchestrator.py` and `pipeline.py` entry points stitch these layers together. A representative full run — a live OpenRouter key, all 50 topics, `FEP_LEAN_GAUSS_WORKFLOWS=1`, and `gauss.verify_lean: true` — completes in **roughly {{verify.duration_min}} minutes** (run `{{verify.run_id}}` with primary model `{{hermes.primary_model}}`, a reasoning model whose extended-thinking trace is the dominant wall-clock contributor; non-reasoning chat models such as the prior `z-ai/glm-5.1` historically landed near 21 minutes). Exact durations vary by provider and rate limits. For Lean-only checks without Hermes, use `scripts/03_lean_verify_only.py` or the compile test suite. The pipeline integrates cleanly into the template's multi-project CI orchestrator (`run.sh` and `execute_pipeline.py`); CI and local runs often use stub Hermes (`sk-test-*` or no key) and may set `FEP_LEAN_GAUSS_WORKFLOWS=0` for speed. See `config/settings.yaml` and the environment variable reference for the full set of toggles.

See §\ref{sec:pipeline_architecture_and_execution_profile} for the full 6-step DAG architecture, CLI interface, and detailed execution breakdown.

## Standard Reproducibility Workflow {#sec:standard_reproducibility_workflow}

To reproduce the results presented in this paper, follow the environment-driven workflow below:

1. **Environment priming.** Export `OPENROUTER_API_KEY` for LLM access.
2. **Workflow opt-in.** Set `FEP_LEAN_GAUSS_WORKFLOWS=1` to enable the high-latency Hermes and Lean stages. Without this flag, the pipeline runs in lightweight mode and skips active formalization.
3. **Health check.** Run `gauss doctor` via the `gauss` CLI to confirm that the local SQLite state, Mathlib4 cache, and OpenRouter connectivity are in order.
4. **Execution.** Invoke the pipeline via the template's root orchestrator: `uv run python scripts/02_run_analysis.py --project fep_lean`.
5. **Validation.** Inspect the latest `output/reports/run_*/` bundle (`index.md`, and `verification_manifest.json` when present) for the zero-mock verification summary.

## Area-Specific Methodological Constraints {#sec:area_specific_methodological_constraints}

To prompt the LLM into producing mechanically sound abstractions across diverse mathematical topologies, the methodology partitions the conceptual space into five discrete areas. Each area carries a dedicated set of namespace constraints that bound the type-safe envelope available to both the Hermes agent and the committed sketches. The namespace constraints below reflect the Mathlib4 modules actually imported by the compiled catalogue sketches (see §\ref{sec:coverage_map_and_dependency_graph} for the full coverage map); aspirational targets such as Riemannian manifold modules or SDE infrastructure were explored during development but cannot be used yet because the required Mathlib4 formalization does not exist.

### FEP Methodology (14 topics) {#sec:fep_methodology}

The core Free Energy Principle concepts sit at the probabilistic foundation. The methodology restricts the accessible Mathlib envelope to measure-theoretic primitives and log/exp special functions; KL divergence is constructed via Radon-Nikodym derivatives (`rnDeriv`) rather than a native `klDiv` (which is not yet in Mathlib4). The agent is instructed to avoid stochastic integrals and to constrain proofs to discrete or continuous measure combinations built from elementary Lebesgue bounds. Throughout, we adopt the convention that free energy $F$ is convex in prediction errors, so that the precision matrix $\Pi = -\nabla^2 F$ is positive definite at the minimum; this convention propagates consistently through all FEP topics.

**Namespace constraints**: `MeasureTheory.Measure.rnDeriv`, `MeasureTheory.Integral.Bochner`, `Analysis.SpecialFunctions.Log.Basic`

### Active Inference Methodology (11 topics) {#sec:active_inference_methodology}

Active inference models temporal policies, building on the graphical brain framework that connects belief propagation to active inference [@friston2018deep]. Prompt engineering targets discrete policy types and finite-type summations; the compiled sketches use finite-set operations and ordered-comparison infrastructure to formalize policy selection and cost aggregation.

**Namespace constraints**: `Algebra.BigOperators.Group.Finset`, `Data.Fin`, `Data.Finset`, `Order.Basic`

### Information Geometry Methodology (8 topics) {#sec:information_geometry_methodology}

For Fisher information and statistical distances, the methodology steers the LLM toward Mathlib4's inner-product-space and metric-space infrastructure. The compiled sketches anchor the Fisher metric via `EuclideanSpace` inner products, and statistical-manifold geodesics via metric-space triangle inequalities — the algebraic building blocks currently available for Riemannian metric tensors. The `Geometry.Manifold.*` modules were explored but the connection to score-function second moments requires measure-theoretic integration that is not yet composable in Mathlib4.

**Namespace constraints**: `Analysis.InnerProductSpace.Basic`, `Topology.MetricSpace.Basic`, `Analysis.SpecialFunctions.Pow.Real`

### Bayesian Mechanics Methodology (10 topics) {#sec:bayesian_mechanics_methodology}

As the most advanced area, Bayesian Mechanics instructs the Hermes agent to target solenoidal flows and non-equilibrium steady states (NESS). The compiled sketches encode skew-symmetry via matrix transposition (`Matrix.transpose_neg`) and Markov blanket partitions via finite-set operations. Full vector calculus infrastructure (divergence theorems, SDE operators) remains aspirational pending Mathlib4 formalization.

**Namespace constraints**: `LinearAlgebra.Matrix.Transpose`, `Data.Finset.Basic`, `MeasureTheory.Measure.MeasureSpace`

### Thermodynamics Methodology (7 topics) {#sec:thermodynamics_methodology}

The thermodynamics pipeline bridges back to classical physics by isolating state variables (entropy, internal energy) and cross-validating them against the informational KL divergences that appear in the FEP bounds, using standard real-number operations from `Analysis.SpecialFunctions.Log`.

**Namespace constraints**: `Analysis.SpecialFunctions.Log.Basic`, `MeasureTheory.Integral.Bochner`

See §\ref{sec:mathlib4_and_measure_theoretic_probability} for the complete Mathlib4 coverage map across all five areas, and §\ref{sec:the_sorry_mechanism_and_formalization_maturity} for the maturity assessment of each formalization.

## Catalogue Authorship Pipeline {#sec:catalogue_authorship_pipeline}

The catalogue's Lean bodies follow a strict single-source-of-truth (SSOT) chain to prevent drift between authored sketches, the YAML config, and the compiled Lean files:

```
scripts/catalogue_sketches.py (SKETCHES dict)
    ↓  uv run python scripts/_maint_build_topics_catalogue.py
config/topics.yaml  (lean_sketch field per row)
    ↓  LeanVerifier._wrap_lean_code()
lean/FepSketches/fepNNN.lean  (import Mathlib + shared opens prepended)
    ↓  lake env lean <file>
VerifyResult (compiles: bool, has_sorry: bool, errors: list[str])
```

`SKETCHES["fep-NNN"]` stores the raw theorem body **without** the leading `import Mathlib` line — that preamble (plus `open MeasureTheory ProbabilityTheory Real Nat Finset Set` and `open scoped BigOperators`) is injected by `LeanVerifier._wrap_lean_code()` at verification time. `tests/test_catalogue_sketches_ssot.py` asserts that every `topics.yaml` `lean_sketch` matches the corresponding `SKETCHES` entry string-for-string; CI fails if they diverge.

After editing `SKETCHES`, always regenerate with:
```bash
cd projects/fep_lean
uv run python scripts/_maint_build_topics_catalogue.py
uv run pytest tests/test_catalogue_sketches_ssot.py -v
```

## Verification Workflow and Cache Strategy {#sec:verification_workflow_cache_strategy}

`LeanVerifier` invokes `lake env lean <tempfile>` (not `lake build`) per topic. This hits the pre-built Mathlib4 `.olean` artifacts without triggering a full rebuild. Cache states and their performance implications are:

| Cache state | Time per topic | Precondition |
|-------------|----------------|--------------|
| Cold (fresh clone, no cache) | 45+ min total (once) | `lake build` from scratch |
| Warm (`.olean` present, stamps match) | 3–7 min total (50 topics) | `lake exe cache get && lake build` done once |
| Cached (Lean compiler cache hot) | 1–2 s per topic | Steady-state: `.olean` hot in OS page cache |

**Warm-up procedure** (one-time per clone):
```bash
cd projects/fep_lean/lean
lake exe cache get     # Download Mathlib4 .olean CDN artifacts (~2 GB)
lake build             # Build fep_lean's own files (~30 s)
```

`LeanVerifier.check_mathlib_built()` runs as a preflight before every batch verification. It checks for `Mathlib.olean` under `lean/.lake/packages/mathlib/.lake/build/lib/` and exits with an actionable message if the cache is absent or partial.

## Zero-Mock Testing Policy {#sec:zero_mock_testing_policy}

The test suite enforces a strict zero-mock standard: no `MagicMock`, no `mocker.patch`, no `unittest.mock`. Every test path that touches a stateful subsystem exercises the real implementation:

- **SQLite.** The `tmp_path` fixture creates a throwaway database per test; `OpenGaussClient` transacts against it directly.
- **HTTP.** Tests that require OpenRouter make real `urllib.request` calls guarded by `pytest.mark.skipif(not OPENROUTER_API_KEY, ...)` so that offline CI skips them cleanly.
- **Lean compilation.** `test_lean_verifier.py` (22 tests) and `test_lean_verifier_sad_paths.py` (15 tests) drive `LeanVerifier.verify_sketch` and `verify_batch` through real `lake env lean` subprocesses on representative sketches and toolchain-path edge cases. Per-row results for the full 50-topic sweep come from `scripts/03_lean_verify_only.py` (stdout) and, when `FEP_LEAN_GAUSS_WORKFLOWS=1`, from the Gauss Sessions stage, with aggregates written to `output/reports/run_*/verification_manifest.json` by the `Reporter`.
- **Figures.** `write_all_catalogue_figures` uses real `matplotlib` with `MPLBACKEND=Agg` for headless rendering, and exercises `ProcessPoolExecutor` unless `FEP_LEAN_FIGURES_MP=0`.

This policy means the test suite doubles as an integration harness: a passing run guarantees that the real compiler, database, and HTTP stack behave as expected, not just that mock objects return the right values.

## Namespace Convention and Topic Isolation {#sec:namespace_convention}

All 50 committed Lean bodies include a `namespace FEPNNN … end FEPNNN` wrapper and use `fepNNN_<descriptor>` theorem name prefixes, providing two layers of collision isolation when the full catalogue is compiled as a single Lake aggregate target. A representative body (as stored in `SKETCHES["fep-001"]`) looks like:

```lean
import Mathlib.MeasureTheory.Measure.MeasureSpace

namespace FEP001

variable {α : Type*} [MeasurableSpace α]

open MeasureTheory

/-- Measure subadditivity: μ(A ∪ B) ≤ μ(A) + μ(B), fundamental for variational bounds. -/
theorem fep001_measure_union_le (μ : Measure α) (s t : Set α) :
    μ (s ∪ t) ≤ μ s + μ t :=
  measure_union_le s t

end FEP001
```

Each body begins with a topic-specific `import Mathlib.XYZ` statement. Because `LeanVerifier._wrap_lean_code()` detects a leading `import` and passes the body through unchanged (skipping the shared preamble injection), each topic compiles with precisely its declared Mathlib dependency rather than the full shared `open` set. `tests/test_catalogue_sketches_ssot.py` enforces that `topics.yaml lean_sketch` matches `SKETCHES` byte-for-byte; the namespace wrapper is part of the stored body, not injected at runtime.

## PYTHONPATH Isolation {#sec:pythonpath_isolation}

The monorepo has two `llm/` packages: `infrastructure/llm/` (generic Ollama client) and `projects/fep_lean/src/llm/` (Hermes OpenRouter client). Python resolves the first match in `sys.path`. If `infrastructure/` appears before `projects/fep_lean/src/` in `PYTHONPATH`, imports of `llm.hermes` fail with `ModuleNotFoundError`.

**Required PYTHONPATH order**:
```bash
export PYTHONPATH="projects/fep_lean/src:.:infrastructure"
```

This ordering is enforced in `pyproject.toml` for `uv run` contexts and in CI. For ad-hoc script runs from the monorepo root, always set `PYTHONPATH` explicitly or use `uv run` from the project directory.

## Parallelism Model {#sec:parallelism_model}

Stage 4 (Manuscript Artifacts) exploits two levels of parallelism.

**Outer level — `ThreadPoolExecutor(max_workers=2)`.** `pipeline/core.py` submits `write_manuscript_vars` + `write_full_topic_lean_catalogue_markdown` concurrently with `write_all_catalogue_figures`. Both futures must complete before `PipelineResult.stages["Manuscript Artifacts"]` is recorded.

**Inner level — `ProcessPoolExecutor` (spawn context).** `output/figures.py:write_all_catalogue_figures` dispatches the seven per-area PNG charts across a process pool created with `multiprocessing.get_context("spawn")`. Spawn (rather than fork) prevents worker processes from inheriting open SQLite connections or matplotlib state. Coverage is traced across processes via `concurrency = ["multiprocessing"]` in `pyproject.toml`.

**Serial escape hatch.** Set `FEP_LEAN_FIGURES_MP=0` to force all figure rendering onto the main process — required when the host OS blocks subprocess spawn (some container environments) or when debugging figure generation interactively.

**Optional prefetch** (`FEP_LEAN_PREFETCH=1`). `GaussRunner._run_topics_batch_prefetch` overlaps Hermes for topic $N+1$ with `lake env lean` verification on topic $N$ using a `ThreadPoolExecutor`. This optimization applies only to `workflow="verify"` with at least two topics.

---

## Detailed Methodology Sub-Sections {#sec:detailed_methodology_sub_sections}

The following sub-sections provide comprehensive technical exposition for readers requiring deeper understanding of each pipeline component:

- **§\ref{sec:lean_4_a_primer_for_active_inference_researchers}** — [Lean 4: A Primer for Active Inference Researchers](03a_lean4_primer.md): Type theory, Curry-Howard correspondence, dependent types, tactics, and a concrete informal-vs-formal KL proof comparison
- **§\ref{sec:mathlib4_and_measure_theoretic_probability}** — [Mathlib4 and Measure-Theoretic Probability](03b_mathlib4_measure_theory.md): Full coverage map of what Mathlib4 provides for each FEP area, with specific module paths
- **§\ref{sec:the_sorry_mechanism_and_formalization_maturity}** — [The `sorry` Mechanism and Formalization Maturity](03c_sorry_maturity.md): How to read incomplete proofs, the real/partial/aspirational taxonomy, and the maturity distribution across all 50 topics
- **§\ref{sec:the_hermes_ai_agent_and_llm_assisted_formalization}** — [The Hermes AI Agent and LLM-Assisted Formalization](03d_hermes_llm_pipeline.md): Gauss session protocol, FEP-domain system prompt, model fallback chain, graceful degradation, and honest limitations
- **§\ref{sec:native_lean_4_compilation_and_zero_mock_verification}** — [Native Lean 4 Compilation and Zero-Mock Verification](03e_lean_compilation.md): Compiler bridge architecture, Mathlib4 caching, sub-second feedback, and the zero-mock mandate
- **§\ref{sec:pipeline_architecture_and_execution_profile}** — [Pipeline Architecture and Execution Profile](03f_pipeline_architecture.md): 6-step DAG, SQLite session tables, `verification_manifest.json`, operations log, and CLI notes
