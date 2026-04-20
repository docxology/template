# Conclusion and Future Work {#sec:conclusion_and_future_work}

This work delivers the first machine-checked catalogue of the Free Energy Principle in a modern proof assistant: **50 curated Lean 4 sketches, all `sorry`-free, all tagged `mathlib_status: real`, compiling at a `{{compile_rate.total}}` native `lake env lean` rate** (confirmed via `scripts/03_lean_verify_only.py`) against the pinned Mathlib4 `{{mathlib_tag}}` / Lean `{{lean_version}}` toolchain (`{{lean_toolchain}}`), and spanning five distinct areas (FEP core, Active Inference, Information Geometry, Bayesian Mechanics, Thermodynamics). The catalogue is produced by a catalogue-driven workflow — curated sketches in `topics.yaml`, Hermes commentary via OpenRouter, native `lake env lean` verification, and SQLite persistence under the OpenGauss codename — that organises FEP / Active Inference formalisation at a scale no prior proof-assistant effort has matched. The `{{compile_rate.total}}` compile rate applies to both original catalogue sketches and the Hermes-assisted Gauss run `{{verify.run_id}}` ({{verify.compiles_true}}/{{total_topics}} clean, {{verify.sorry_count}} sorry, {{verify.compiles_false}} errors), achieved via `restore_lean_structure` post-processing and a GaussRunner baseline fallback (§\ref{sec:live_verification_error_taxonomy}). A `{{compile_rate.total}}` catalogue verification rate, a zero-`sorry` policy applied uniformly across all rows, and a five-area coverage footprint together constitute a scientific contribution distinct from proof-search systems that close individual theorems: this is a type-disciplined, machine-auditable **axiomatisation** of a contested physical theory.

The zero-mock stance applies uniformly to the **compiler and HTTP paths**: every success claim is underwritten by a real `lake env lean` invocation or a real OpenRouter round-trip, never by a stubbed return value. With `hermes.enabled: true`, Hermes uses a single configured OpenRouter model and `OPENROUTER_API_KEY`; failures surface as errors rather than synthetic replies. Setting `hermes.enabled: false` omits the Hermes assistant turn for offline runs. The three-level maturity taxonomy (`real` / `partial` / `aspirational`) is reserved for future staging work; today all 50 catalogue rows carry `mathlib_status: real`, so the taxonomy degenerates to the compile-gated subset it was designed to distinguish. When publishing machine-checked claims, align the `verify.*` fields in `manuscript_vars.yaml` with a fresh native run.

## Theoretical Synthesis: What Machine-Checked FEP Establishes {#sec:theoretical_synthesis}

The catalogue is a finite, auditable artefact — 50 theorems, one compile gate, one pinned toolchain. Its theoretical significance, however, is not exhausted by these counts. We frame the contribution along four axes: the notion of *formal adequacy* relative to empirical and causal adequacy; the typology of results the catalogue establishes; the role of the Lean type system in enforcing *definitional commitment*; and the status of the catalogue as a piece of *formal review infrastructure* for the FEP community.

### Formal adequacy is a distinct dimension of theory evaluation {#sec:formal_adequacy}

What does it mean for a theory to be "formally adequate"? The 50 `sorry`-free theorems establish that the *algebraic and measure-theoretic substrate* of the FEP is formally adequate — the definitions compile, the properties hold, the internal consistency is machine-verified. This is distinct from two other standard dimensions of theory evaluation:

- **Empirical adequacy**: does the FEP match neural, behavioural, or physiological data? This is an empirical-science question and is not addressed by the catalogue.
- **Causal adequacy**: is the FEP the *right* causal model of self-organisation, as opposed to merely one that fits observed trajectories? This is a metaphysical and modelling question and is likewise outside the catalogue's remit.

The contribution is to the *formal* dimension: the mathematical objects the FEP literature references (variational free energy $F$, expected free energy $\EFE$, Markov blankets, Fisher information, solenoidal flows) are well-typed, mutually consistent, and carry the algebraic properties routinely claimed for them. A theory can be formally adequate while being empirically or causally inadequate — indeed, this is the default state for any mathematical framework prior to its empirical test. Conversely, empirical success cannot substitute for formal adequacy: a theory whose definitions do not type-check is not yet a theory in the logical sense. Machine-checked formal adequacy is, therefore, a *precondition* for — not a substitute for — empirical evaluation.

### Typology of results: definitional, structural, quantitative {#sec:typology_of_results}

The current catalogue establishes three types of results, each corresponding to a distinct epistemic role.

1. **Definitional results** — e.g., **fep-001** (variational free energy as a Radon–Nikodym integral), **fep-002** (KL divergence non-negativity), **fep-015** (joint distribution factorisation). These establish that the mathematical objects used in the FEP (measures, KL, joint distributions, entropy) are *well-formed*: the types exist, the integrals converge under stated conditions, and the operations compose. A theory cannot proceed without this layer, and it is precisely the layer most often left implicit in informal FEP papers.
2. **Structural results** — e.g., **fep-005** (Markov blanket as an exhaustive, disjoint four-part partition of states), **fep-025** (solenoidal / dissipative decomposition of NESS flows), **fep-027** (hierarchical factorisation of generative models). These establish that the key structural claims are *internally consistent*: the partitions are genuine partitions, the decompositions preserve the claimed symmetries, the hierarchies compose. Structural results carry more weight than definitional ones because they encode the *architectural* commitments of the theory — the claims that distinguish the FEP from generic variational inference.
3. **Quantitative results** — e.g., **fep-012** (softmax normalisation $\sum_i \exp(-\gamma G_i)/Z = 1$), **fep-028** (Boltzmann factor positivity $\exp(-\gamma G) > 0$), **fep-031** (policy-probability non-negativity), **fep-050** (Landauer bound $\Delta S \geq k_B \log 2$). These establish that the numerical claims hold with *explicit precision*: the bounds are tight, the constants are named, the inequalities are strict where the theory demands strictness. Quantitative results are the layer that an empirical test ultimately touches.

Each of these three classes has a different failure mode: definitional failure is a type error, structural failure is a counterexample, quantitative failure is a numerical discrepancy. A catalogue that checks all three simultaneously thus provides a stronger guarantee than any one class alone.

### Definitional commitment via the type system {#sec:definitional_commitment}

The Lean type system enforces what we call **definitional commitment**: once a theorem compiles, the shape of its conclusion is fixed by the kernel, not by editorial convention. Consider **fep-005**, the Markov-blanket partition. In informal FEP papers, the partition of a state space $\mathcal{X}$ into internal $\mu$, sensory $s$, active $a$, and external $\eta$ states is typically introduced as a conceptual framing — "assume states partition into blanket and non-blanket parts" — with the disjointness and exhaustiveness conditions left unstated and the precise algebraic structure of the partition deferred to the reader. The formal version makes these commitments explicit:
$$\mathcal{X} \;=\; \mu \,\sqcup\, s \,\sqcup\, a \,\sqcup\, \eta, \qquad \mu \cap s = \mu \cap a = \mu \cap \eta = s \cap a = s \cap \eta = a \cap \eta = \varnothing.$$
Once `fep005_markov_blanket_partition` type-checks, all four parts are disjoint and exhaustive *by machine proof*, not by convention. Any downstream theorem that uses the partition inherits these properties — and, crucially, cannot silently weaken them.

This is a general pattern. The formal version shows exactly where the algebraic structure ends and the *dynamical* assumption begins: disjointness and exhaustiveness are algebraic (they are about the set structure of the state space); the conditional independence $\mu \perp\!\!\!\perp \eta \mid (s, a)$ that the FEP additionally posits under the stationary distribution is a separate, stronger claim that must be stated over a measure. The type system makes this boundary visible. In informal presentations the two live in the same sentence and the reader is expected to supply the distinction; in the formal version, the algebraic partition compiles from `Set` operations while the independence claim requires a `Measure` argument. The formalisation therefore clarifies not only *what* is claimed but *what class of claim* each piece belongs to.

### The catalogue as formal review infrastructure {#sec:catalogue_as_infrastructure}

A final synthesis: the catalogue is not merely a static artefact enumerating 50 theorems. It is a piece of *formal review infrastructure* for the FEP community. Any new FEP theorem — whether from a journal paper, a preprint, or a conference talk — can now be *submitted* to the catalogue in the form of a Lean sketch. The pipeline (Hermes commentary + `lake env lean` verification) provides a 24-hour review cycle at the level of machine-checked specifications, complementing rather than replacing the multi-month cycle of conventional peer review.

This reframes the catalogue's role. Rather than a one-time census of the FEP literature at a particular moment, it is a *living formal specification* that grows as new theorems are contributed and as Mathlib4 infrastructure matures (cf. the roadmap in §\ref{sec:maturity_roadmap}). The zero-`sorry` discipline, the pinned toolchain, and the reproducible run-bundle format together mean that any contributed sketch is either admitted on objective criteria (it compiles) or returned with a precise, actionable compiler trace (it does not, and here is exactly where). The catalogue is, in this sense, a *formal review infrastructure* for the theory — not just a snapshot of the current formalisation frontier.

## Summary of Contributions {#sec:summary_of_contributions}

1. **FEP catalogue in Lean 4**: 50 compiling, `sorry`-free sketches paired with natural-language statements across five areas — 14 FEP core rows, 11 Active Inference rows, 10 Bayesian Mechanics rows, 8 Information Geometry rows, and 7 Thermodynamics rows — constituting a systematic Lean-facing axiomatisation of the Free Energy Principle.
2. **50/50 native compilation**: Every catalogue sketch compiles under `lake env lean` against the pinned Mathlib4 **v4.29.0** / Lean **4.29.0** toolchain (confirmed 2026-04-18 via `scripts/03_lean_verify_only.py`), recorded in `verification_manifest.json` and surfaced as `verify.compiles_true: 50` in `manuscript_vars.yaml`. Hermes-refined sketch variants are tracked separately; see §\ref{sec:live_verification_error_taxonomy}.
3. **Maturity census**: All 50 rows carry `mathlib_status: real`; the `partial` and `aspirational` tiers remain reserved staging states, so every shipped row is machine-checked rather than aspirational.
4. **Zero-mock methodology**: SQLite persistence, HTTP requests to OpenRouter, and `lake env lean` invocations run against real dependencies; Hermes-off and skipped Lean are explicit configuration states, never mocked successes.
5. **Error taxonomy**: Systematic classification of LLM failure modes in physical-theory formalisation, informing prompt engineering for future LLM-ITP pipelines.
6. **Formalization roadmap**: Concrete upgrade pathways keyed to forthcoming Mathlib4 milestones — native `klDiv`, Itô integrals, Fokker–Planck operators, Wasserstein distance, and Riemannian metric infrastructure.

## Implications for the Active Inference Community {#sec:implications_for_active_inference_community}

The FEP Lean catalogue has immediate relevance for Active Inference researchers and practitioners:

1. **Verified reference implementations**: The 11 Active Inference sketches (fep-003, fep-007, fep-008, fep-020, fep-021, fep-023, fep-028, fep-033, fep-034, fep-041, fep-047) provide machine-checked *specifications* that can be compared to numerical implementations in pymdp, SPM, and other toolkits. When code and the formal sketch disagree, the Lean row documents the intended semantics; the numerical code may still be wrong.

2. **Precision for debated constructs**: The EFE decomposition (fep-003, fep-021) and policy selection (fep-008, fep-028) are among the most actively debated constructs in the Active Inference literature. Our Lean sketches make the mathematical assumptions explicit — e.g., fep-028 defines softmax policy selection and proves both non-negativity and normalization, leaving no ambiguity about the intended semantics.

3. **Teaching resource**: The Lean 4 primer (§\ref{sec:lean_4_a_primer_for_active_inference_researchers}) and the full catalogue in Appendix B provide a structured pathway from informal Active Inference mathematics to formal type theory. The `sorry` mechanism shows students exactly where mathematical gaps exist, rather than hiding them behind "by standard arguments."

4. **Foundation for POMDP verification**: As Active Inference moves toward real-world POMDP deployments, formal verification of the underlying mathematics becomes a safety requirement. The catalogue's discrete belief update (fep-034), message passing (fep-047), and affordance characterization (fep-023) are direct building blocks for verified POMDP planning.

## Engineering Outcomes and Lessons {#sec:engineering_outcomes_and_lessons}

### Compilation headline

Native compilation is summarized by **`50/50`** in `manuscript_vars.yaml` (from the latest `verification_manifest.json` when a verify-enabled run exists). The shipped catalogue targets **Lean 4.29.0** and **Mathlib v4.29.0** (`lean/lean-toolchain`, `lean/lakefile.lean`).

### Mathlib integration lessons

Patterns observed while maintaining the catalogue at the pinned release:

- **`MeasureTheory.Measure.rnDeriv`** underpins KL-style rows where densities are stated via Radon–Nikodym derivatives and integrals.
- **Information geometry** still leans on inner-product and metric infrastructure; a full Fisher–Riemannian metric story remains future work.
- **Thermodynamics** topics stress `Analysis.SpecialFunctions` and real arithmetic — typically stable modules.
- **Version pinning** is load-bearing: any Mathlib bump should be followed by a catalogue sweep (`uv run python scripts/03_lean_verify_only.py` or CI).

### LLM-ITP Synergy

The Hermes LLM layer (primary model `moonshotai/kimi-k2.6` via OpenRouter, with `z-ai/glm-5.1` retained in the fallback chain) achieved a **100% API success rate** (50/50) in a representative full batch, with token counts on the order of 10³ per topic (exact totals are in `summary.json` and provider logs). Hermes-refined sketches consistently improved tactic clarity over baseline `SKETCHES` bodies, particularly for:

- **Measure-theoretic topics**: Hermes correctly identifies which `MeasureTheory` open namespace to use and suggests `exact?` / `apply?` alternatives when the primary tactic fails.
- **Algebraic identity topics**: Hermes prefers `ring` and `norm_num` over manual arithmetic rewrites, reducing proof length.
- **Conditional topics**: Hermes uses `obtain ⟨..., ...⟩ := ...` destructuring rather than verbose `rcases`, improving readability.

The four workflow stages (verify → draft → prove → review) enable iterative formalisation without human-in-loop intervention for routine tactics. The `verify` workflow (default) assesses the existing sketch and proposes refinements; `prove` targets `sorry`-elimination by gap-filling. Neither workflow overwrites the canonical `SKETCHES` automatically — Hermes output is advisory, and the human curator decides which refinements to promote to the catalogue.

## Future Work {#sec:future_work}

Six directions for future development stand out:

1. **Iterative proof repair**: A **second Hermes pass** (or loop) driven by compiler stderr is not implemented in the current orchestrator; adding this would extend the Draft-Sketch-Prove paradigm [@first2023draft] from competition math to physical theory.

2. **Axiom expansion**: Extending the catalogue with stronger statements (and new rows) that may require foundational lemmas for Riemannian manifolds [@amari2016information], Itô stochastic integrals [@pavliotis2014stochastic], and Fokker-Planck evolution operators. A collaborative effort with the Mathlib4 SDE formalization community could accelerate this substantially.

3. **Real-time proof assistance**: Integrating fast **`lake env lean`** feedback (after Mathlib cache warm-up) into collaborative workflows, along the lines of Lean Copilot [@song2025copilot], using the FEP-domain Hermes prompt as a starting point.

4. **Upstream Mathlib contribution**: Contributing verified formalizations to Mathlib4 where real maturity has been demonstrated, particularly for information-theoretic primitives (KL bounds, Fisher information definitions, conditional entropy). The affordance formalization (fep-023) is an immediate candidate.

5. **Cross-framework comparison**: Evaluating the pipeline's LLM-generated formalisms against alternative proof assistants (Coq, Isabelle/HOL, Agda) to assess the generalizability of the axiomatization approach and identify framework-specific advantages for physical theory formalization. Coq's Coquelicot library for real analysis and Isabelle's AFP measure theory modules offer complementary infrastructure.

6. **POMDP EFE Mathematical Constraints**: Utilizing the likelihood constraints for Expected Free Energy (where POMDP observation risks rigorously restrict prior preferences to perfectly align with generative models) [@champion2026reframing], enforcing these exact likelihood mappings at compile-time to guarantee valid policy planning.

## Reproducibility Statement {#sec:reproducibility_statement}

Runs are reproducible **given** pinned toolchain artifacts, the same environment variables, and (when Hermes is on) API access. Reported timings and throughput are **environment-dependent**; see a concrete `output/reports/run_*/summary.json` for a given machine, not fixed global numbers.

| Component | Version / Requirement |
|-----------|-----------------------|
| Lean 4 | v4.29.0 (pinned in `lean-toolchain`) |
| Mathlib4 | v4.29.0 tag (pinned in `lean/lakefile.lean`) |
| Python | $\geq$ 3.10 (managed via `uv`) |
| OpenRouter API key | Required when `hermes.enabled: true`; omit or disable Hermes for offline catalogue runs |
| Disk space | ~2 GB for Mathlib4 `.olean` cache |
| Pipeline duration | Order-of-magnitude: tens of minutes for full batches when Hermes + Lean workflows run; use `hermes.enabled: false` and `FEP_LEAN_GAUSS_WORKFLOWS=0` for catalogue-only paths |
| Operating system | macOS, Linux (tested); Windows via WSL2 |

**To replicate a full run**:

```bash
cd projects/fep_lean   # if `fep_lean` is under `projects/` (see `docs/_generated/active_projects.md`)
uv sync
bash scripts/_maint_bootstrap_lean_toolchain.sh   # or: cd lean && lake exe cache get && lake build
export OPENROUTER_API_KEY=...       # required if hermes.enabled; else set hermes.enabled: false in settings
uv run python scripts/02_run_single_topic.py --topic fep-003   # smoke test
# or full pipeline using standard 02_run_analysis.py when ready
```

Per-run Markdown and `verification_manifest.json` live under `output/reports/run_YYYYMMDD_HHMMSS/`. Session data: `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`; SQLite; project codename OpenGauss).

## Data Availability {#sec:data_availability}

All data generated by this work is available in the following locations:

- **Source code**: `src/` (pipeline, Gauss client, Hermes, verifier, injector, ...)
- **Test suite**: `tests/` (`uv run pytest tests/`)
- **Topic catalogue**: `config/topics.yaml` (50 topics)
- **Execution artifacts**: `output/reports/` (per-run subdirectories)
- **Database**: `$GAUSS_HOME/fep_lean_state.db` (default `~/.gauss/`; SQLite, sessions + turns tables)
- **JSONL export**: `$GAUSS_HOME/fep_artifacts/` (bulk session exports)

## Closing Remark {#sec:closing_remark}

The FEP Lean pipeline demonstrates that a contested physical theory can be lifted into a proof assistant without mocks, without `sorry`, and without sacrificing breadth: 50 theorems, five areas, one compile gate, and one reproducible toolchain. The resulting artefact is not a complete formalisation of the FEP — full dynamical theorems await Mathlib4's SDE and Riemannian infrastructure — but it is a machine-checked axiomatisation whose every row is auditable by rerunning `lake env lean`. As Mathlib4 and LLM-ITP tooling mature [@yang2024leandojo], the same harness will host stronger per-topic statements without changing its workflow shape. The catalogue turns informal debate about what the FEP *says* into a question that a proof assistant can answer.

