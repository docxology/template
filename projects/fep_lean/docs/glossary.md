# Glossary — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

Definitions for the FEP / Active Inference / Bayesian mechanics / information geometry / thermodynamics terminology that appears in the 50-topic catalogue, the manuscript, and the Lean 4 sketches. Cross-linked to [`topics-reference.md`](topics-reference.md) where each term has a corresponding theorem.

---

## A

### Active Inference
An extension of the Free Energy Principle in which agents select **policies** (action sequences) that minimize **expected free energy** over future trajectories. Combines belief updating (perception) with action selection under a single variational objective. See the ActiveInference area topics (fep-003, fep-007, fep-008, and others; 11 entries total). Related: [FEP](#free-energy-principle-fep), [ELBO](#elbo-evidence-lower-bound), [expected free energy](#expected-free-energy).

### Ambient state
The full world-state before any Markov blanket decomposition — includes both internal and external states before conditioning. Rarely used alone; the useful objects are internal, external, sensory, and active states (see [Markov blanket](#markov-blanket)).

---

## B

### Bayesian mechanics
A research program that reformulates statistical mechanics in terms of self-organizing systems whose dynamics can be read off from a variational free energy functional. The BayesianMechanics area covers 10 topics including generative model likelihoods, Markov blanket partitions, hierarchical generative models, and empirical Bayes coupling. NESS solenoidal flow is treated as a Thermodynamics topic (fep-025).

### Belief (in AI / Active Inference)
The agent's current variational distribution `q(ψ|s)` over hidden states given sensory observations. Updated by gradient descent on free energy (perception) or by message passing (discrete Active Inference).

### Belief propagation
Message-passing algorithm for computing marginal distributions on factor graphs. Discrete-time Active Inference uses a sum-product variant for policy inference. See fep-007.

---

## C

### Conditional independence
Two random variables `X` and `Y` are conditionally independent given `Z` (written `X ⊥ Y | Z`) iff `p(x, y | z) = p(x | z) · p(y | z)` for all values. Conditional independence of internal and external states **given** the Markov blanket is the formal mathematical content of the FEP's "statistical separation" claim.

### Curl (solenoidal) flow
See [solenoidal](#solenoidal-flow).

---

## D

### DKL (Kullback–Leibler divergence)
`DKL[q ∥ p] = ∫ q(x) log(q(x)/p(x)) dx`. A non-symmetric measure of how "different" distribution `q` is from reference distribution `p`. Non-negative, zero iff `q = p` almost everywhere. The central quantity in variational free energy; see fep-001, fep-002 (ELBO decomposition). KL non-negativity is fep-014 (InfoGeometry area).

### Diffeomorphism (in information geometry)
A smooth, invertible reparametrization of a statistical manifold. The Fisher information metric is **invariant** under diffeomorphisms — a defining property that motivates its use as the natural Riemannian metric on probability spaces. See fep-004.

### Diffusion (in NESS flow)
The D term in the flow decomposition `J = −D·∇F + Q·∇F`. Represents symmetric, dissipative noise that drives the system toward a free-energy minimum. Contrasts with [solenoidal](#solenoidal-flow).

---

## E

### ELBO (Evidence Lower Bound)
`ELBO(q) = E_q[log p(s, ψ)] − E_q[log q(ψ)]`, equivalently `log p(s) − DKL[q ∥ p(·|s)]`. A lower bound on the log marginal likelihood `log p(s)` (the "evidence"). Maximizing ELBO = minimizing variational free energy (they differ by sign). See fep-002.

### ELBO–free-energy duality
`F[q, p] = −ELBO(q)`. Maximizing ELBO ↔ minimizing free energy. The two objectives are mathematically identical up to sign; which one is written depends on community convention (Bayesian ML vs theoretical neuroscience).

### Entropy
`H[p] = −∫ p(x) log p(x) dx` (continuous) or `H[p] = −Σ p(x) log p(x)` (discrete). Measures the uncertainty / spread of a distribution. Maximized by the uniform distribution on a bounded support. Central to thermodynamic free energy (`F = U − T·H`).

### Epistemic value
The expected information gain component of expected free energy — encourages actions that reduce uncertainty about hidden states. Contrasts with [pragmatic value](#pragmatic-value). `Epistemic = E_q[log p(s|o) − log p(s)]`. See fep-021.

### Expected free energy
`G(π) = E_{q(o,s|π)}[log q(s|π) − log p(o, s|π)]`. The analogue of variational free energy for *future* trajectories under policy `π`. Minimizing G over policies selects actions that balance exploration (epistemic value) and exploitation (pragmatic value).

### External state
Hidden world variables outside the Markov blanket that the agent cannot directly observe, only infer through sensory states. Denoted `η` in the FEP literature. See [Markov blanket](#markov-blanket).

---

## F

### Fisher information metric
The Riemannian metric on a statistical manifold induced by `g_ij(θ) = E_p[∂_i log p · ∂_j log p]`. Uniquely characterized (Chentsov's theorem) as the only Riemannian metric invariant under sufficient statistics. Defines natural gradients and geodesics between probability distributions. See fep-004, fep-017.

### Free Energy Principle (FEP)
The hypothesis that self-organizing biological systems persist over time by minimizing **variational free energy** — a tractable upper bound on surprise (negative log evidence). Formalized by Friston (2010). The FEP area of `fep_lean` covers 14 topics including the bound itself (fep-001), the ELBO decomposition (fep-002), predictive coding (fep-006), and surprise minimization as entropy minimization (fep-024). KL non-negativity is covered in the InfoGeometry area (fep-014).

### Free energy (variational)
`F[q, p] = DKL[q ∥ p(·|s)] − log p(s)`, which equals `E_q[log q − log p(s, ψ)]`. Non-negative difference between the log marginal likelihood and the ELBO. Minimizing F makes `q` approximate the true posterior (perception) while simultaneously minimizing surprise (adaptation). See fep-001.

---

## G

### Generative model
The joint `p(s, ψ)` that an agent uses to relate hidden states `ψ` to sensory observations `s`. Together with the variational density `q(ψ|s)` and the choice of what to minimize (F, ELBO, expected free energy), it fully specifies a Bayesian mechanics or Active Inference setup.

### Geodesic
Shortest path between two points on a Riemannian manifold. On a statistical manifold equipped with the Fisher metric, geodesics capture the "natural" way to interpolate between probability distributions — preserving entropy in an information-geometric sense.

---

## H

### Helmholtz free energy
Thermodynamic quantity `F_thermo = U − T·S` (internal energy minus temperature × entropy). Connected to variational free energy via `F_variational = E_q[U(ψ)] − H[q]` when a Boltzmann prior is used. See fep-013, fep-044 through the Thermodynamics area.

### Hidden state
A latent variable `ψ` that the agent infers but does not observe directly. Contrast with [sensory state](#sensory-state).

---

## I

### Information geometry
The differential-geometric study of statistical manifolds — spaces of probability distributions equipped with natural metrics (Fisher), connections (α-connections), and divergences. The InfoGeometry area covers 8 topics including Fisher metric, natural gradient, and dual affine structure. See Amari (2016) for the standard reference.

### Internal state
State variable inside the Markov blanket — roughly, the "agent" or "system" itself. Denoted `μ`. Conditionally independent of the external state `η` given the blanket `B = (s, a)`.

---

## J

### Jensen's inequality
For a convex function `φ` and a random variable `X`: `φ(E[X]) ≤ E[φ(X)]`. Used repeatedly in variational-inference derivations, notably to prove ELBO ≤ log evidence (fep-002) and DKL ≥ 0 (fep-014).

---

## K

### KL divergence
See [DKL](#dkl-kullbackleibler-divergence).

### Kernel (in Bayesian mechanics)
In stochastic dynamics, a Markov kernel `K(x, A)` gives the probability of transitioning from state `x` into measurable set `A`. Used in the BayesianMechanics area to formalize the noise structure of NESS systems.

---

## M

### Markov blanket
A partition of the state space into internal (`μ`), external (`η`), sensory (`s`: external → blanket), and active (`a`: internal → blanket) states, such that `μ ⊥ η | (s, a)`. The formal mathematical structure that makes "agent" distinguishable from "world" under the FEP. See fep-005.

### Markov process
A stochastic process for which future states depend only on the present (conditional on the present, future and past are independent). NESS dynamics and Bayesian mechanics typically work in continuous-time Markov settings with stochastic differential equations.

### Mathlib4
The community-maintained library of formalized mathematics for Lean 4. Contains the measure-theory, probability, analysis, and linear-algebra lemmas that `fep_lean` catalogue sketches depend on. Pinned to **v4.29.0** in `lean/lakefile.lean`. See [`lean4.md`](lean4.md).

### Maturity (in topics.yaml)
A per-topic tag (`mathlib_status`) with values `real` / `partial` / `aspirational`. In v0.7.0 **all 50 topics are `real`** — they compile cleanly with no `sorry` on Lean v4.29.0 + Mathlib v4.29.0.

---

## N

### Natural gradient
Gradient descent preconditioned by the inverse Fisher information matrix: `θ_{t+1} = θ_t − η · F⁻¹ · ∇L`. Invariant under reparametrization of the parameter space; converges faster than standard gradient descent on statistical-manifold objectives. See fep-017.

### NESS (Non-Equilibrium Steady State)
A stationary probability distribution reached by a dissipative system subject to external driving — the invariant density of a Markov process whose flow has a nonzero solenoidal component. Central to Bayesian mechanics: living systems maintain NESS rather than thermal equilibrium. See fep-025.

---

## O

### OpenGauss / `gauss`
The [math-inc/OpenGauss](https://github.com/math-inc/OpenGauss) command-line tool (`gauss`) that `fep_lean` integrates with for session state and LLM routing. Writes SQLite to `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`). See [`opengauss.md`](opengauss.md).

---

## P

### Policy (π)
A probability distribution over action sequences in Active Inference. Policies are inferred (not chosen) by computing the posterior `q(π) ∝ exp(−G(π))`, where G is the expected free energy.

### Posterior
The conditional distribution `p(ψ | s)` of hidden states given observations. In variational inference, the posterior is approximated by a simpler variational density `q(ψ)` chosen to minimize DKL. The "true" posterior is the intractable object that `q` is meant to approach.

### Pragmatic value
The expected utility component of expected free energy — encourages actions that bring observations into alignment with prior preferences `p(o|C)`. Contrasts with [epistemic value](#epistemic-value). `Pragmatic = E_q[log p(o|C)]`. See fep-021.

### Precision
The inverse of variance (`Π = Σ⁻¹`). In predictive coding, prediction errors are weighted by the precision of the relevant likelihood: high-precision (certain) observations drive strong belief updates, low-precision (uncertain) observations barely nudge beliefs.

### Predictive coding
Neural-computation scheme in which top-down predictions are compared to bottom-up sensory input, and the (precision-weighted) residual ("prediction error") drives belief updates. The FEP derivation of predictive coding is fep-006.

---

## R

### Random variable (in Lean / Mathlib)
Formalized in Mathlib as a **measurable function** `X : Ω → ℝ` from a probability space `(Ω, ℙ)` to the real line with the Borel σ-algebra. The Lean catalogue sketches work directly with `MeasureTheory.Measure` rather than named random variables, following Mathlib conventions.

---

## S

### Sensory state
Observations flowing from external variables through the Markov blanket into the agent — the "s" in `q(ψ|s)`. The only information the agent has about `η`.

### `sorry` (Lean)
The Lean 4 tactic that closes any goal but leaves a compile-time warning. A proof containing `sorry` is an **incomplete** proof — the statement type-checks but is not mathematically verified. The fep_lean catalogue enforces **zero `sorry`** in the canonical YAML (`mathlib_status: real`).

### Solenoidal flow
The curl-like (antisymmetric) component `Q·∇F` in the decomposition of a NESS probability flow. Orthogonal to the gradient component `−D·∇F`, meaning it does not decrease free energy on average but prevents the system from equilibrating. Essential to characterizing living / self-organizing systems as non-equilibrium.

### Surprise
`−log p(s)`, the negative log marginal likelihood of observing `s`. Upper-bounded by variational free energy; minimizing F therefore minimizes long-run average surprise (and, by ergodic equivalence, sensory entropy). See fep-024.

---

## T

### Thermodynamic free energy
See [Helmholtz free energy](#helmholtz-free-energy).

### Time-average surprise
`E_τ[−log p(s_τ)]`, the expectation of surprise over a trajectory. By ergodicity equals `H[p(s)]`, the entropy of the sensory marginal. Minimizing time-averaged surprise = minimizing sensory entropy = self-organization. See fep-024.

### Topic (fep-NNN)
One of the 50 entries in `config/topics.yaml`. Each topic bundles (id, title, area, `mathlib` hint, `mathlib_status`, natural-language statement, Lean 4 sketch). The canonical list is in the YAML; illustrative pedagogical versions appear in `topics-reference.md`.

---

## V

### Variational density
The parametric distribution `q(ψ; θ)` used to approximate the true posterior `p(ψ|s)` in variational inference. Optimized by minimizing DKL over parameters `θ`.

### Variational free energy
See [free energy (variational)](#free-energy-variational).

### Variational inference
The general Bayesian inference technique of approximating an intractable posterior `p(ψ|s)` with a tractable family `q(ψ; θ)` by minimizing DKL (equivalently, maximizing ELBO). The FEP is a specific application with additional commitments about which probabilities an agent "is" (generative model) and which it "computes" (q).

---

## Pipeline and tooling

### Stage 02 (repository root)

The template **analysis** stage that runs `scripts/02_run_analysis.py` from the monorepo root. It discovers `projects/<name>/scripts/*.py`, skips `_*.py` maintenance scripts, and wraps each script in a subprocess with a configurable timeout (`ANALYSIS_SCRIPT_TIMEOUT_SEC`; default **7200** s). See [pipeline.md](pipeline.md#stage-02-repository-root-analysis) and [configuration.md](configuration.md#monorepo-stage-02-repository-root).

### Gauss workflows (env-gated)

When `FEP_LEAN_GAUSS_WORKFLOWS` is **truthy** (or `FEP_LEAN_LIVE_TESTS=1`), `01_fep_catalogue_and_figures.py` runs Hermes + Lean batch work inside `GaussRunner`. When unset or **falsy**, those workflows are skipped unless explicitly enabled. See [configuration.md](configuration.md#fep-lean-stage-01-catalogue-and-figures).

---

## Code-level components (SSOT: `src/`)

Runtime objects the pipeline, tests, and docs all reference by name.

### `HermesConfig`
Configuration dataclass for the Hermes LLM explainer. Defined in [`src/llm/hermes.py:173`](../src/llm/hermes.py#L173). Fields include `model` (primary model slug, defaults to `moonshotai/kimi-k2.6`), `base_url` (`https://openrouter.ai/api/v1`), `api_key`, `max_tokens` (16384), `timeout_s` (150, **wall-clock** — see `_make_request`), `reasoning_max_tokens` (65536), `reasoning_timeout_s` (300, wall-clock), `enabled`, `cache_ttl_hours` (24.0), and `fallback_models`. Loaded via `HermesConfig.from_settings(project_root)` which reads `config/settings.yaml` and environment variables (including `OPENROUTER_API_KEY` from `~/.gauss/.env`).

### `HermesExplainer`
Main LLM client class that wraps OpenRouter chat-completions calls using `urllib` (no `requests` dependency). Defined in [`src/llm/hermes.py:389`](../src/llm/hermes.py#L389). Sends a 2-message prompt (system persona + user task) and parses response into an explanation plus refined Lean 4 sketch (extracted from the first fenced ``lean`` code block). On 4xx/5xx or transient failure, walks the [fallback chain](#fallback-chain).

### `HermesResult`
Dataclass for a Hermes LLM response. Defined in [`src/llm/hermes.py:360`](../src/llm/hermes.py#L360). Fields: `success`, `model_used`, `explanation`, `refined_lean_sketch`, `reasoning`, `tokens_used`, `duration_s`, `error`, `topic_id`, `cache_hit`. `.as_dict()` serializes with reasoning truncated to 2000 chars for storage.

### `GaussRunner`
Orchestrates per-topic Hermes + `LeanVerifier` + SQLite workflow. Defined in [`src/gauss/runner.py:98`](../src/gauss/runner.py#L98). Constructs one OpenGauss session per topic, invokes Hermes for explanation and sketch refinement, calls `LeanVerifier` to compile the refined sketch, and persists artifacts via `OpenGaussClient`.

### `VerifyResult`
Dataclass describing the result of one `lake env lean` compilation. Defined in [`src/verification/lean_verifier.py`](../src/verification/lean_verifier.py). Fields include `topic_id`, `compiles`, `has_sorry`, `failure_kind`, `errors`, `warnings`, `stdout`, `stderr`, `duration_s`, `lean_version`, `lean_file`, `skip_reason`. Derived `.status` returns one of `skipped (...)`, `compile_error`, `compiles_with_sorry`, or `compiles_clean`.

### `LeanVerifier`
Runs `lake env lean` subprocess for sketch verification against the pinned Lean + Mathlib toolchain (`lean/lean-toolchain`, `lean/lakefile.lean`). Defined in [`src/verification/lean_verifier.py`](../src/verification/lean_verifier.py). Wraps a sketch body in a temporary `.lean` file, prepending `import Mathlib` and the standard `open` preamble before shelling out into the `lean/` workspace.

### `OpenGaussClient`
Python SQLite persistence layer with a 5-table schema (sessions, turns, artifacts, events, jsonl_events). Defined in [`src/gauss/client.py:132`](../src/gauss/client.py#L132). Writes to `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`). Uses `check_same_thread=False` for cross-thread reads; writes serialized by the pipeline's `max_workers=1` execution model.

### `TopicEntry`
FEP topic dataclass. Fields: `id` (e.g. `fep-001`), `title`, `area` (one of FEP / ActiveInference / BayesianMechanics / InfoGeometry / Thermodynamics), `mathlib` (navigation hint), `mathlib_status` (`real` / `partial` / `aspirational`), `nl` (natural-language anchor), `lean_sketch` (body text copied from `SKETCHES[id]` in `scripts/catalogue_sketches.py`).

### `FEPTopicCatalogue`
Container for all 50 `TopicEntry` records. Defined in `src/catalogue/topics.py`. Loads `config/topics.yaml` at runtime; exposes per-area filters and is consumed by `FEPPipeline`, tests, and Hermes prompts.

### `PipelineResult`
Dataclass returned by `FEPPipeline.run()`. Contains a `stages` dict keyed by stage name (the 4-stage DAG: setup, catalogue, verification, report), each value a `StepResult`.

### `StepResult`
Per-stage result dataclass. Fields: `status` (`ok` / `skipped` / `error`), `duration_s`, `error` (empty on success). Aggregated by `Reporter` into the final report bundle.

### `OpenRouter`
LLM API aggregator used by `HermesExplainer`. Base URL: `https://openrouter.ai/api/v1`. Accepts multiple model providers behind a single OpenAI-compatible chat-completions surface. Requires `OPENROUTER_API_KEY`; optional `HTTP-Referer` and `X-Title` headers identify the project.

### fallback chain
An 8-model ordered list (primary first, then 7 fallbacks) tried in sequence when the active model fails with 429 or transient error on OpenRouter. Configurable via `HermesConfig.fallback_models` (which lists the 7 fallbacks only — the primary `HermesConfig.model` is prepended automatically); empty list falls back to the built-in `_FREE_MODEL_CHAIN`. Anthropic `base_url` ignores the chain.

### `moonshotai/kimi-k2.6`
Primary Hermes model slug in the default configuration (default `HermesConfig.model`). Moonshot Kimi K2.6, 262K context, member of `_REASONING_MODELS` (so it gets `reasoning_max_tokens` instead of the 16K instruct budget). Overridable via `HERMES_MODEL` env var or `config/settings.yaml`.

### `z-ai/glm-5.1`
ZhipuAI GLM-5.1, 128K context. Demoted from primary to a fallback-chain entry after a cold-run regression where it returned empty content past the 150 s budget; retained in the chain because it is otherwise capable. Now also a member of `_REASONING_MODELS`.

### stub mode
Hermes operating with empty `api_key` or `enabled=False`. In this mode, `HermesExplainer.explain_topic()` returns a `HermesResult(success=False)` immediately, with no network call. Used throughout the test suite for deterministic offline behavior.

### `lake`
The Lean 4 build tool. Two commands matter for `fep_lean`: `lake build` (compiles the `FepSketches` library and its Mathlib dependency) and `lake env lean <file>` (type-checks a single file against the built environment, used by `LeanVerifier`).

### `.olean` cache
Precompiled Mathlib binary files stored under `lean/.lake/`. Populated once by `lake exe cache get` (~3 GB download). Without these, every `lake env lean` call would have to rebuild Mathlib from source.

### tactic mode
The Lean 4 proof-construction mode introduced by `by`. Within a tactic block, goals are closed using tactics such as `simp`, `exact`, `apply`, `ring`, `norm_num`, `rw`, `nlinarith`, `positivity`, `have`, `calc`, `intro`, and `constructor`. The fep_lean sketches mix term-mode proofs (direct Mathlib lemma references) with tactic blocks where convenient.

---

## References

1. **Friston, K.** (2010). "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience* **11**, 127–138. DOI: [10.1038/nrn2787](https://doi.org/10.1038/nrn2787).
2. **Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., Pezzulo, G.** (2016). "Active inference: a process theory." *Neural Computation* **29** (1).
3. **Parr, T., Pezzulo, G., Friston, K.** (2022). *Active Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press. ISBN 978-0-262-04535-3.
4. **Ramstead, M., Sakthivadivel, D., Friston, K.** (2023). "On Bayesian mechanics: a physics of and by beliefs." *Interface Focus* **13** (3).
5. **Amari, S.** (2016). *Information Geometry and Its Applications*. Applied Mathematical Sciences **194**. Springer. DOI: [10.1007/978-4-431-55978-8](https://doi.org/10.1007/978-4-431-55978-8).
6. **The mathlib Community** (2024). *The Lean Mathematical Library*. <https://leanprover-community.github.io/mathlib4_docs/>.

---

## Navigation

- [← FEP Background](fep-background.md)
- [Topics reference →](topics-reference.md)
- [Lean 4 notes →](lean4.md)
- [← docs/README.md](README.md)
