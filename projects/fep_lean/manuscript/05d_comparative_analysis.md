## Comparative Analysis with Existing LLM-ITP Systems {#sec:comparative_analysis_with_existing_llm_itp_systems}

The FEP Lean pipeline differs from existing LLM-ITP systems along several dimensions:

| Dimension | LeanDojo / LEGO-Prover | DeepSeek-Prover-V2 | PhysLean | FEP Lean Pipeline |
|-----------|----------------------|---------------------|----------|-------------------|
| **Task** | Prove existing theorems | Prove competition problems | Digitalize physics | Axiomatize physical theory |
| **Input** | Formal theorem statement | Informal problem text | Physics textbooks | Informal physics + equations |
| **Output** | Proof term | Proof term | Formalized definitions | Compiled Lean sketch (zero `sorry` in shipped catalogue) |
| **Success metric** | Proof found (Y/N) | miniF2F pass rate | Coverage of physics | `sorry`-free compile + maturity tier (`real`/`partial`/`aspirational`; 50/50 at `real`) |
| **Domain** | General mathematics | Competition math | High-energy physics [@toobysmith2024] | FEP / Active Inference |
| **Mathlib usage** | Premise retrieval | Training signal | Building on top | Target namespace |
| **Human-in-loop** | None (automated) | None (automated) | Human-guided | Hermes assessment + researcher review |

*Comparison of the FEP Lean pipeline with existing LLM-ITP and physics formalization systems.*

The key architectural difference is that the FEP Lean pipeline uses the LLM as a *formalisation translator* rather than a *proof finder*. This shifts the success criterion from "did the LLM find a proof?" to "did the LLM produce a well-typed specification of the informal claim?" — a different task with different failure modes and evaluation criteria.

### Manual vs Hermes-Assisted Formalisation {#sec:manual_vs_hermes_assisted}

A central design question for any LLM-ITP pipeline is: *what does the LLM add on top of a careful human formalisation?* The table below reports a side-by-side comparison calibrated against a reference full run (50 topics, 50/50 Hermes commentary turns, **`50/50`** native compilation on the shipped catalogue under **Lean 4 4.29.0** / **Mathlib4 v4.29.0**, primary model `moonshotai/kimi-k2.6`).

| Phase | Manual (researcher-only) | Hermes-assisted (this pipeline) |
|-------|---------------------------|-----------------------------------|
| Per-topic skeleton drafting | 30–90 min (statement + imports + first sketch) | 2–5 min (curated `topics.yaml` entry + generated commentary) |
| Per-topic LLM commentary | N/A | tens of seconds (single OpenRouter call, `moonshotai/kimi-k2.6`; per-topic mean is logged in `summary.json` for each run) |
| Per-topic `lake env lean` check | 20–60 s (after cache warm-up) | 20–60 s (identical; zero-mock, same toolchain) |
| Error diagnosis on compile failure | Manual read of stderr, ~10–30 min | Manual read + Hermes commentary contextualises the error |
| 50-topic total wall time | Weeks of scholarly effort | Hours of pipeline wall-clock, tens-of-minutes for the LLM phase |
| Error rate (first pass) | Highly variable; depends on researcher expertise | 50/50 on curated sketches at current pin when CI / verifier is green |
| Completeness of narrative prose | Depends on researcher discipline | Structured by prompt; uniform depth across all topics |
| Correctness guarantee | Relies on researcher's care | Relies on `lake env lean` + zero-mock verifier |
| Scope | Typically 1–5 topics in a paper | 50 topics in a single catalogue |

The comparison is not meant to suggest that Hermes replaces the researcher: the researcher still curates `topics.yaml`, writes the catalogue sketches, reviews Hermes output, and makes the substantive mathematical choices. What the pipeline adds is *uniformity at scale*: all 50 topics receive structured narrative commentary, compile against the same toolchain, and appear in a consistent artefact bundle under `output/reports/run_*/`.

### Comparison to Similar Projects {#sec:comparison_similar_projects}

Situating our work among adjacent formalisation efforts clarifies both what is novel and what is borrowed:

- **PhysLean / HEPLean** [@toobysmith2024] formalises high-energy physics index notation in Lean 4. It is a *human-led* effort that builds directly on Mathlib4's tensor infrastructure. Our work shares the "build a physics catalogue on top of Mathlib4" structure but differs in (a) using an LLM for commentary, (b) targeting FEP/Active Inference rather than HEP, and (c) adopting a maturity taxonomy that prices the gap between "stateable" and "provable".
- **Lean 4 thermodynamics**: no standalone thermodynamics formalisation project exists in Mathlib4 to our knowledge as of March 2026. Statistical-mechanics content is scattered across Mathlib4's special-functions, probability, and measure-theory modules. The 7-topic Thermodynamics area of our catalogue (fep-010, fep-013, fep-025, fep-030, fep-031, fep-037, fep-049, fep-050) therefore represents one of the first unified Lean 4 thermodynamics sketch corpora, however modest in depth.
- **Coq FEP attempts**: we are aware of no published end-to-end Coq formalisation of the FEP. The most relevant Coq infrastructure is Coquelicot (real analysis) and the MathComp analysis library, each of which has partial SDE content but no FEP-specific layer. Our work is therefore, to the best of our knowledge, the first attempt at a sketch catalogue for the FEP in any proof assistant.
- **Isabelle/HOL measure theory and AFP probability**: the Archive of Formal Proofs contains mature measure-theory and probability entries. A port of our catalogue to Isabelle would likely succeed for the measure-theoretic and discrete rows; it would face the same SDE/Riemannian gap we do.
- **LeanDojo / LEGO-Prover / DeepSeek-Prover** [@yang2024leandojo; @xin2024lego; @deepseek2024prover; @deepseek2025proverv2]: these systems are *proof finders* rather than *formalisation translators*. They attempt to close a proof given a statement. Our system does the complementary, upstream task of *producing the statement* in the first place. In principle, a future pipeline could chain these systems: our Hermes-assisted formalisation produces the statement, and a LeanDojo-style prover then attempts to discharge the residual proof obligations.
- **Lean Copilot** [@song2025copilot]: an in-editor tactic-suggestion assistant that integrates LLM completions with Lean's elaboration feedback. Like LeanDojo, it is a *proof-search* layer; it does not curate a domain-specific catalogue, and it operates at the level of a single tactic block rather than a whole-theory corpus. Our pipeline is orthogonal: Lean Copilot could reasonably be deployed *inside* our curation loop to speed the researcher's drafting of catalogue sketches, but it would not replace the catalogue-driven axiomatisation that distinguishes our approach.
- **AlphaProof** [@alphaproof2024]: a DeepMind system that reached silver-medal performance on IMO 2024 geometry and number-theory problems by combining reinforcement learning with Lean. AlphaProof targets *competition-style problems with known-provable answers*; our catalogue targets *frontier physics theory where the correct statement is itself contested*. The two systems solve disjoint tasks: AlphaProof closes proofs of sharp competition claims, while our pipeline axiomatises the defining equations of a still-evolving scientific research programme.
- **Draft, Sketch, Prove (DSP)** [@jiang2023draft]: an LLM workflow that autoformalises informal proof text into Lean/Isabelle by drafting a natural-language proof, sketching the formal outline, and then discharging subgoals with `sledgehammer`-style automation. DSP operates end-to-end on *individual proofs*; our pipeline operates at the *catalogue* level, with curation, zero-mock integration, and a pinned toolchain as explicit pipeline phases. DSP could plausibly run *inside* our per-topic cycle to attempt proof closure on a catalogue sketch, but its autoformalisation layer is not a substitute for the researcher-curated axiomatisation we ship.

**What distinguishes this work from the LLM-ITP literature as a whole** is not the LLM component — a standard OpenRouter client — but three pipeline commitments: (i) **catalogue-driven axiomatisation** rather than proof search (the LLM explains curated sketches, it does not search for proofs); (ii) **domain specificity** (the catalogue, prompt, and maturity taxonomy are calibrated to FEP / Active Inference physics, not to general-purpose mathematics or competition problems); and (iii) **zero-mock end-to-end integration** (every claim is underwritten by a real Lean compile and a real HTTP round-trip, not a simulated dependency). Systems that share any one of these commitments are rare; systems that share all three, to our knowledge, do not yet exist.

**Comparison to Coq and Isabelle/HOL infrastructure.** Coq's Coquelicot library for real analysis and Isabelle's AFP measure theory modules offer complementary infrastructure — each has strong classical real analysis content and, in Coquelicot's case, partial stochastic-calculus coverage — but both lack the Mathlib4 coverage of `MeasureTheory.Measure.rnDeriv` that the FEP core depends on. The Radon–Nikodym derivative is the anchor for KL-divergence-style constructions used throughout the catalogue (fep-014, fep-024, fep-035, fep-044), and porting the catalogue to either system would require first reconstructing that infrastructure in the target library. This is not an abstract concern: the measure-theoretic rows of our catalogue would need non-trivial library work to reproduce elsewhere, which is itself evidence that Mathlib4 is currently the most tractable target for FEP formalisation.

### Our Approach vs GPT-4-Class Direct Lean Generation {#sec:gpt4_direct_comparison}

A natural baseline is to ask GPT-4 (or a comparable frontier model) directly for a Lean 4 sketch given an informal FEP statement, without any pipeline scaffolding. Prior anecdotal and controlled evaluations in the proof-engineering literature indicate the following qualitative differences:

- **Compile rate**: Direct GPT-4 Lean generation, without curation or a test gate, typically compiles a minority of outputs on first pass. The FEP catalogue compiles **50/50** at the pinned release because the sketches are *curated* by `scripts/catalogue_sketches.py`, not because the LLM is the author of the compiling code. The LLM's contribution is *commentary*, not code generation.
- **Hallucinated lemmas**: Direct LLM Lean generation is prone to invoking Mathlib lemma names that do not exist in the pinned Mathlib commit. The pipeline sidesteps this: the sketch is curated, and Hermes is asked to *explain*, not to *invoke*.
- **Type-theoretic subtlety**: Direct LLM generation occasionally conflates `ℝ`, `ℝ≥0∞`, and `ENNReal`, producing code that looks right but mixes types the compiler rejects. The curated sketches are written against the type system explicitly.
- **Reproducibility**: Direct LLM generation is non-deterministic and its output shape is sensitive to prompt wording. The catalogue sketches are deterministic (they live in `topics.yaml`); only the Hermes commentary varies run-to-run, and that variance is documented in the `output/reports/run_*/` bundle.

The pipeline therefore trades *autonomy* (the LLM does not author Lean code from scratch) for *reliability* (what the LLM does contribute is reviewable and cross-checked by the compiler on a known-good sketch).

### Quality Metrics {#sec:comparative_quality_metrics}

For the definitive run:

| Metric | Value |
|--------|-------|
| Topics attempted | 50 |
| Hermes turns successfully produced | 50/50 (100%) |
| Sketches compiled via `lake env lean` | **`50/50`** |
| Non-compiling sketches | 0 in a green CI sweep at **`v4.29.0`**; diagnostics in §\ref{sec:hermes_vs_native_lean_diagnostics} / §\ref{sec:quantitative_execution_metrics} |
| Sketches containing `sorry` | 0/50 (shipped policy) |
| Topics with `mathlib_status: real` | 50/50 (100%) |
| Primary model | `moonshotai/kimi-k2.6` (Moonshot Kimi K2.6, 262K context) |
| Fallback chain length | 7 additional models (8 total in `_FREE_MODEL_CHAIN`, including `z-ai/glm-5.1` as a demoted entry) |
| Toolchain | Lean 4 **4.29.0**, Mathlib4 **v4.29.0** (`lean/lean-toolchain`, `lean/lakefile.lean`) |

Residual compile failures in exploratory branches are environmental (cache, pin drift) or authoring bugs — **not** Hermes sketch authorship, because Hermes does not own `SKETCHES`.

### Time Comparison {#sec:time_comparison}

A careful manual formalisation of 50 FEP topics at the depth of sketch shipped here would conservatively take a mathematically trained researcher several weeks — roughly half a day per topic for drafting, compiling, and writing commentary, before accounting for literature review. The Hermes-assisted pipeline reduces the *commentary* phase to minutes per topic and the *compilation* phase to seconds. The *sketch-curation* phase still requires researcher effort but is a one-time cost, amortised across all subsequent runs. The net effect is an order-of-magnitude reduction in scholarly hours per catalogue refresh, at the cost of a new review responsibility (cross-checking Hermes commentary for accuracy).

### Implications for Active Inference Practitioners {#sec:implications_for_active_inference_practitioners}

For the Active Inference research community, this comparative positioning has practical significance. Existing computational tools (pymdp [@heins2022pymdp], SPM/MATLAB) provide *numerical implementations* of Active Inference agents — they compute expected free energy, select policies, and update beliefs. They cannot, however, formally guarantee that their implementations satisfy the mathematical properties assumed by the theory (e.g., that softmax probabilities sum to one, that belief updates preserve non-negativity, or that policy selection is optimal over the policy space).

The catalogue provides machine-checkable formalisation of these properties for 11 Active Inference topics. The fep-028 sketch defines softmax and includes compiler-verified proofs of both non-negativity and normalisation (`fep028_softmax_probs_sum_one`); fep-034 provides a verified belief-update non-negativity lemma; fep-008 encodes optimal-policy existence and minimum-value agreement via `Finset.exists_min_image`. All three compile without `sorry` — the compiler certifies internal type and arithmetic consistency. These are not numerical approximations but machine-checked formal specifications; the distinction from complete end-to-end proofs is treated in §\ref{sec:limitations_and_threats_to_validity}.

The bridge from informal FEP physics to Lean 4 formal specifications is analogous to the bridge from pseudocode to verified software in the programming-languages community. Just as verified compilers (CompCert [@leroy2009compcert]) provide stronger guarantees than tested compilers, formally verified FEP specifications provide stronger guarantees than numerically validated implementations — guarantees that matter most when Active Inference systems are deployed in safety-critical contexts [@parr2022active].
