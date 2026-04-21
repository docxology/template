# Introduction {#sec:introduction}

## The Verification Gap in Mathematical Physics {#sec:the_verification_gap_in_mathematical_physics}

The Free Energy Principle (FEP) offers a unified account of perception, action, and learning [@friston2010free], positing that all self-organizing systems minimize a variational free energy functional to resist entropic dissolution. Over the past two decades, the FEP has generated a rich theoretical ecosystem spanning Active Inference [@parr2022active], Information Geometry [@amari2016information], and Bayesian Mechanics [@dacosta2024bayesian]. Yet the mathematical foundations of this ecosystem—drawing simultaneously on measure theory, stochastic differential equations, differential geometry, and category theory—remain difficult to parse, verify, and extend. A working researcher reconstructing a derivation from a flagship paper must typically cross-reference textbooks in four distinct subfields, reconcile inconsistent notation, and silently patch over assumptions the author judged too obvious to state.

This difficulty is not merely pedagogical. Recent critiques [@biehl2021critique; @aguilera2022particular; @andrews2021math] raise substantive concerns about the mathematical status of key FEP claims: the uniqueness of Markov blanket decompositions, the conditions under which steady-state densities exist, and the extent to which variational bounds apply beyond specific model classes. Such debates expose a **verification gap** in mathematical physics: informal review alone cannot machine-check every inference step at scale. The quantitative shape of this gap is itself instructive. The FEP literature has accumulated on the order of two thousand papers over the past fifteen years, and many of them build on prior results without re-verifying the mathematical premises those results rest on. In any rapidly expanding field the risk of *accumulated error* — valid-seeming but subtly incorrect mathematical claims propagating through citations until they are treated as background facts — is real, and it grows superlinearly with the citation graph. Formal verification provides a *checksum* on the mathematical claims: a theorem that compiles in a kernel-checked proof assistant is guaranteed to be internally consistent with the definitions it invokes and with every lemma it cites, though it is not thereby guaranteed to be correct about the world. A catalogue of checksummed theorems gives the community a layer against which new claims can be audited at the speed of a compile, rather than at the speed of editorial review. When the free energy $F$ is claimed to upper-bound surprise, the argument hinges on a chain of measure-theoretic manipulations:

$$F[q, p] = \KL[q(\psi \mid m) \,\|\, p(\psi \mid s, m)] - \log p(s \mid m) \geq -\log p(s \mid m),$$

where the inequality holds because Kullback–Leibler divergence is non-negative by Gibbs' inequality. Each of those symbols—$q$, $p$, $\KL$, $\log p(s \mid m)$—carries type-theoretic weight: $q$ is a probability measure absolutely continuous with respect to $p$, $\KL$ is the Radon–Nikodym-derivative integral $\int \log \frac{dq}{dp}\, dq$, and $\log p(s \mid m)$ is a real-valued random variable. In a journal proof these conditions are implicit; in a theorem prover they must be declared, and the compiler rejects the proof if they are not.

## Why Formal Verification of FEP Matters for Cognitive Science {#sec:why_formal_verification_matters}

The stakes are concrete. Active Inference is now used to model cortical processing, motor control, psychiatric conditions, and the behavior of multi-agent biological systems. When a clinical claim rests on the "free energy minimization" rationale, the underlying inequality should be correct by construction rather than by editorial consensus. Three specific benefits follow from machine-checked FEP mathematics:

1. **Unambiguous statements.** Each theorem forces explicit declaration of the measurable space, the dominating measure, and the policy type, eliminating the category errors that [@andrews2021math] identify as pervasive in the literature.
2. **Compositional reasoning at scale.** Once a lemma (for example, KL non-negativity) is verified, it composes into larger results without re-verification. A community library of FEP theorems would give each new manuscript a springboard rather than a restart.
3. **Automated differentiation of hype from theorem.** When Lean refuses to close a goal, the author sees precisely which hypothesis is missing. This provides a principled interface between informal intuition and formally defensible claim.

## Interactive Theorem Provers as Resolution Mechanism {#sec:interactive_theorem_provers_as_resolution_mechanism}

Interactive Theorem Provers (ITPs) such as Lean 4 [@moura2021lean] address this challenge directly. Lean 4's dependent type system implements the Calculus of Inductive Constructions, so accepted theorems are checked against the kernel. A theorem proven in Lean produces a *proof object*—a certificate that an independent verifier can re-check. Its standard library, Mathlib4 [@mathlib2020], is one of the largest actively maintained formal mathematics libraries in use today, with over 60,000 declarations—contributed by a global community—covering topology, measure theory, algebra, and geometry. Notable successes include the formalization of Terence Tao's polynomial Freiman–Ruzsa conjecture [@tao2023lean] and the Liquid Tensor Experiment [@scholze2022liquid]. Stochastic process foundations—critical for FEP path integrals—remain uneven in Mathlib4 at large; the shipped catalogue rows are nonetheless `sorry`-free under this project's maturity policy, while broader SDE and continuous-time stochastic infrastructure remains aspirational where Mathlib4 does not yet supply it (see §\ref{sec:gap_analysis}).

We selected Lean 4 over alternative proof assistants (Coq, Isabelle/HOL, Agda) based on the analysis presented below:

| Criterion | Lean 4 | Coq | Isabelle/HOL | Agda |
|-----------|--------|-----|--------------|------|
| Library size | 60K+ declarations (Mathlib4) | ~70K (Stdlib + MathComp) | ~40K (AFP) | ~20K |
| Measure theory | Full (Bochner, Radon-Nikodym) | Partial (Coquelicot) | Partial | Minimal |
| LLM ecosystem | LeanDojo, Copilot, LEGO-Prover | Limited | Limited | None |
| Programming model | Functional + metaprogramming | Gallina + Ltac2 | Isar + SML | Dependent types |
| Proof automation | `grind` (SMT), `omega`, `positivity` | Ltac2 | sledgehammer | Agda auto |

The combination of Mathlib4's measure-theoretic infrastructure and a rapidly maturing LLM-ITP integration ecosystem makes Lean 4 the natural target for formalizing probabilistic physics.

## Origins and Context: FEP and Lean 4 / Mathlib4 Maturity {#sec:context_fep_lean_mathlib}

The FEP was formally introduced by Karl Friston in a sequence of papers between 2005 and 2010 [@friston2005theory; @friston2006free; @friston2010free], generalizing the Helmholtz machine and predictive coding frameworks of the 1990s. By 2017, Active Inference [@friston2017active] had matured into a full perception–action theory; between 2021 and 2024, Bayesian Mechanics [@dacosta2024bayesian; @friston2024path] supplied a rigorous path-integral treatment that placed the FEP in direct contact with non-equilibrium statistical mechanics. The core variational identity—minimization of

$$F = \mathbb{E}_{q}[\log q(s) - \log p(o, s)]$$

—originates jointly in the evidence lower bound (ELBO) literature of variational Bayesian methods and in the Helmholtz free energy of statistical mechanics.

Lean 4 reached a comparable inflection point in parallel. Lean 4.0.0 was released in 2023, Mathlib4 completed its migration from Lean 3 in the same year, and the pinned toolchain used in this work (**`{{lean_toolchain}}`**, Mathlib4 **`{{mathlib_tag}}`**) brings tactic automation (`grind`, `positivity`, `nlinarith`) to a level sufficient for routine measure-theoretic manipulations. The Statistical Learning Theory project [@lean_slt2026] is actively upstreaming KL divergence and related information-theoretic infrastructure. These converging trajectories—the FEP maturing into a physics-grade theory and Lean 4 maturing into a mathematics-grade prover—make the present project timely.

## LLM-ITP Integration: Beyond Problem Solving {#sec:llm_itp_integration_beyond_problem_solving}

The integration of Large Language Models with ITPs has produced strong results in parallel. Systems such as LeanDojo and ReProver [@yang2024leandojo], LEGO-Prover [@xin2024lego], DeepSeek-Prover [@deepseek2024prover], and the more recent DeepSeek-Prover-V2 [@deepseek2025proverv2] demonstrate that LLMs can effectively navigate proof search spaces, while AlphaProof [@alphaproof2024] solved International Mathematical Olympiad problems at a silver-medal level. Lean Copilot [@song2025copilot] brings LLM-assisted tactic suggestion directly into the developer workflow. The pinned Lean 4 **`{{lean_version}}`** toolchain (`lean/lean-toolchain`) and Mathlib4 **`{{mathlib_tag}}`** supply automation including `grind` (SMT-style), `positivity`, and related tactics, expanding the proof capabilities available to our pipeline.

Our work targets the **axiomatization of a physical theory** in a proof assistant: turning informal FEP statements into well-typed Lean specifications. Related formalization efforts exist nearby (e.g., categorical ontology definitions or classical simulation boundaries; see [@namjoshi2026fundamentals]); this catalogue is a systematic, template-integrated slice focused on FEP-facing rows. The task demands domain knowledge spanning neuroscience, statistical mechanics, and measure theory—material that must be *translated* from informal mathematical physics into formal specifications, not merely retrieved from Mathlib4.

## The FEP Lean Pipeline {#sec:the_fep_lean_pipeline}

The pipeline curates 50 Lean 4 theorem sketches spanning the FEP theoretical landscape (bodies in `SKETCHES`, materialized in `config/topics.yaml`; §\ref{sec:methodology_and_system_architecture}), compiling each against a native Mathlib4 environment via the `lake env lean` toolchain. Organized as a four-stage DAG within the template orchestration engine, it validates the environment, runs optional Hermes LLM commentary sessions per topic, generates manuscript artifacts, and records timestamped run bundles under `output/reports/`. When extended Gauss workflows are enabled, the pipeline performs a `gauss doctor` preflight and persists session state—LLM turns, compiled artifacts, and verification logs—into a SQLite database at `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`), providing structured provenance well beyond file-based logging.

In a representative end-to-end run with the primary model `{{hermes.primary_model}}` served via OpenRouter, the pipeline produced **50/50 (100%) successful Hermes commentary sessions**. Catalogue-baseline native compilation — original `topics.yaml` sketches run via `scripts/03_lean_verify_only.py` — achieves **`50/50`** against the pinned `lean/lean-toolchain` (`leanprover/lean4:v4.29.0`) and Mathlib4 v4.29.0; the latest measured counts live in `manuscript_vars.yaml::verify.compiles_true / verify.failed_topic_ids`. Hermes-assisted Gauss run `{{verify.run_id}}` (~{{verify.duration_min}} min) achieved **{{compile_rate.total}} clean compiles, {{verify.sorry_count}} sorry, {{verify.compiles_false}} errors** — see §\ref{sec:live_verification_error_taxonomy} (injector and verifier detail in §\ref{sec:formalisms_and_results}). The LLM side is the dominant bottleneck: average LLM latency is on the order of seconds per call, while `lake env lean` verification averages roughly 1.5 seconds per topic thanks to pre-warmed Mathlib `.olean` caches under `lean/`.

The pipeline operates through the structured LLM interaction protocol in §\ref{sec:the_hermes_ai_agent_and_llm_assisted_formalization}, native `lake env lean` feedback where workflows and caches allow (§\ref{sec:native_lean_4_compilation_and_zero_mock_verification}), and the orchestration architecture in §\ref{sec:pipeline_architecture_and_execution_profile}, bridging file-based asset generation with optional SQLite persistence under `$GAUSS_HOME`.

## Research Contributions {#sec:contributions}

This manuscript makes five principal contributions:

- **(C1) Catalogue-scale FEP formalization.** We deliver 50 curated Lean 4 theorem sketches across 5 theoretical areas (FEP foundations, Active Inference, Information Geometry, Bayesian Mechanics, Thermodynamics), each compiling against a native Mathlib4 environment. The catalogue is materialized in `config/topics.yaml` with one-to-one provenance to `SKETCHES` in `scripts/catalogue_sketches.py`.
- **(C2) Maturity taxonomy for formal FEP work.** We introduce a three-level `sorry`-aware classification (`real` / `partial` / `aspirational`) that makes incomplete formalization honest and auditable. The current catalogue is entirely `real`, with zero `sorry` in shipped bodies.
- **(C3) Zero-mock verification methodology.** Every reported compilation result is produced by a real `lake env lean` invocation against the pinned Lean 4 **`{{lean_version}}`** toolchain and Mathlib4 **`{{mathlib_tag}}`**. There are no mocked compilers, no stubbed parsers, and no synthetic success signals anywhere in the pipeline.
- **(C4) End-to-end LLM-assisted pipeline.** We integrate OpenRouter-served LLMs (primary: `moonshotai/kimi-k2.6`; fallback chain retains `z-ai/glm-5.1`) with native Lean verification, SQLite session persistence, and manuscript regeneration in a single reproducible pipeline. A representative run with workflows enabled yielded 50/50 Hermes successes; catalogue-baseline native compilation is 50/50 (confirmed by `scripts/03_lean_verify_only.py`). Hermes-refined variants from full Gauss runs are tracked separately.
- **(C5) Reproducible run bundles.** Each pipeline run emits a timestamped bundle under `output/reports/run_*/` containing session transcripts, verification manifests, compiled sketches, and summary statistics, providing structured provenance well beyond file-based logging.

The corresponding evidence and cross-references are summarized below:

| # | Contribution | Evidence | Section |
|--|---------------|------------|-----|
| C1 | **Catalogue-scale FEP formalization** | One compiling sketch per topic in Appendix B (§\ref{sec:appendix_b_full_topic_lean_catalogue}); short appendix overview in §\ref{sec:appendix_comprehensive_formalisms_overview} | §\ref{sec:formalisms_and_results}, §\ref{sec:appendix_comprehensive_formalisms_overview} |
| C2 | **Maturity taxonomy** | 50 topics (= 50 under current policy); 0 / 0 are zero until YAML reintroduces those rows | §\ref{sec:the_sorry_mechanism_and_formalization_maturity} |
| C3 | **Zero-mock methodology** | Native `lake env lean` compilation, 0 syntax errors; catalogue compiles at Lean **`{{lean_version}}`** + Mathlib **`{{mathlib_tag}}`** when verified | §\ref{sec:native_lean_4_compilation_and_zero_mock_verification} |
| C4 | **End-to-end LLM-assisted pipeline** | 50/50 Hermes successes; {{compile_rate.total}} Lean on catalogue baseline (`scripts/03_lean_verify_only.py`); Hermes-assisted Gauss run `{{verify.run_id}}`: {{verify.compiles_true}}/{{total_topics}} clean, {{verify.sorry_count}} sorry, {{verify.compiles_false}} errors (§\ref{sec:live_verification_error_taxonomy}) | §\ref{sec:the_hermes_ai_agent_and_llm_assisted_formalization} |
| C5 | **Reproducible pipeline** | Pytest suite (no mocks), modular output subfolder, timestamped run bundles | §\ref{sec:pipeline_architecture_and_execution_profile} |

**What this contribution is, and is not.** It is worth situating the *type* of claim these five contributions make. This is **not** a proof that the FEP is true — neither in the empirical sense (that it matches neural or behavioural data) nor in the causal sense (that it is the right model of self-organisation). It is a demonstration that the mathematical *language* of the FEP is well-typed. Just as type-checking a program in a statically typed language does not guarantee the program is correct — it guarantees only that the program will not crash on a type mismatch — type-checking a catalogue of FEP theorems does not prove that the FEP correctly models cognition. What it *does* establish is that the mathematical objects referenced by FEP practitioners — variational free energy $F$, Markov blankets $(\mu, s, a, \eta)$, expected free energy $\EFE$, Fisher information $g_{ij}$, solenoidal flows $Q\nabla F$ with $Q = -Q^\top$, Landauer-style entropy bounds — are well-defined, mutually consistent, and carry the algebraic properties routinely claimed for them. This is a *necessary* condition for any empirical or causal claim the theory makes; it is not a *sufficient* condition. The contribution is a formal-language artefact that sits upstream of empirical test, not a replacement for it.

## Paper Organization {#sec:paper_organization}

The remainder of this paper is organized as follows. **§\ref{sec:background_and_related_work}** reviews FEP and Active Inference background and surveys prior formalization attempts (Lean 4 / Mathlib4 maturity, the Statistical Learning Theory project, and adjacent ITP efforts in Isabelle/HOL and Coq). **§\ref{sec:methodology_and_system_architecture}** details the Lean 4 / Mathlib4 methodology and pipeline architecture, with six deep-dive subsections (§\ref{sec:lean_4_a_primer_for_active_inference_researchers}–§\ref{sec:pipeline_architecture_and_execution_profile}) covering Lean 4 fundamentals, Mathlib4 coverage, the `sorry` maturity taxonomy, the Hermes AI agent, native `lake env lean` compilation, and the orchestration DAG. **§\ref{sec:formalisms_and_results}** presents results for the 50-topic catalogue across the 5 theoretical areas (FEP foundations, Active Inference, Information Geometry, Bayesian Mechanics, Thermodynamics), reporting **injected `compile_rate` metrics** (from `manuscript_vars.yaml`) alongside **Hermes and native verification** statistics in the reference configuration (§\ref{sec:quantitative_execution_metrics}). **§\ref{sec:discussion}** examines Mathlib4 coverage gaps, the zero-mock standard, and implications for the FEP debate. **§\ref{sec:conclusion_and_future_work}** concludes with an engineering-outcomes analysis and future directions. **Appendix \ref{sec:appendix_comprehensive_formalisms_overview}** orients readers to the catalogue appendix, anchors, and injection path; **Appendix \ref{sec:appendix_b_full_topic_lean_catalogue}** contains the full 50-topic Lean catalogue (one code fence per row).

## Notation {#sec:notation}

The following notation is used throughout this paper:

| Symbol | Definition | First use |
|--------|-----------|-----------|
| $\FE[q,p]$ | Variational free energy functional | §\ref{sec:formal_definition_variational_free_energy}, Eq. \ref{eq:eq_1} |
| $\EFE(\pi)$ | Expected free energy under policy $\pi$ | §\ref{sec:the_theoretical_landscape}, Eq. \ref{eq:eq_4} |
| $\KL[q \| p]$ | Kullback-Leibler divergence from $q$ to $p$ | §\ref{sec:formal_definition_variational_free_energy}, Eq. \ref{eq:eq_1} |
| $\Ent[q]$ | Shannon entropy of distribution $q$ | §\ref{sec:the_theoretical_landscape} |
| $\E_q[\cdot]$ | Expectation under distribution $q$ | §\ref{sec:formal_definition_variational_free_energy}, Eq. \ref{eq:eq_1} |
| $\Omega, \mathcal{F}, P$ | Sample space, sigma-algebra, and probability measure | §\ref{sec:lean_4_a_primer_for_active_inference_researchers} |
| $q \ll p$ | Absolute continuity ($q$ is abs. continuous w.r.t. $p$) | §\ref{sec:lean_4_a_primer_for_active_inference_researchers} |
| $\frac{dq}{dp}$ | Radon-Nikodym derivative | §\ref{sec:mathlib4_and_measure_theoretic_probability} |
| `sorry` | Lean 4 tactic admitting a goal without proof | §\ref{sec:the_sorry_mechanism_and_formalization_maturity} |
| $\nabla$ | Gradient operator (on statistical manifold or $\R^n$) | §\ref{sec:the_theoretical_landscape} |
| $\Gamma$ | Solenoidal flow operator | §\ref{sec:the_theoretical_landscape} |
| $Q = -Q^\top$ | Skew-symmetric (solenoidal) matrix | §\ref{sec:the_theoretical_landscape}, Eq. \ref{eq:eq_25} |
| $F, U, T, S$ | Helmholtz free energy, internal energy, temperature, entropy | §\ref{sec:thermodynamics_results} |
