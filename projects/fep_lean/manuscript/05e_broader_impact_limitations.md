## Broader Impact: Reproducible Science and the Digital Mathematics Programme {#sec:broader_impact_reproducible_science_and_the_digital_mathematics_programme}

The FEP Lean pipeline contributes to a broader programme of digitising scientific knowledge into machine-verifiable form. Seven implications follow:

1. **Reproducibility**: Re-run `orchestrator.run_pipeline` with the same commit, keys, and verification flags. `output/reports/run_*/` bundles provide an audit trail; Hermes wording may still vary between runs when enabled. The zero-mock standard ensures that what is reproduced is the *actual* computational trace — real compiler output, real API bytes on the wire, real SQLite rows — rather than a frozen, mocked facsimile of it.

2. **Living formalization**: Unlike a static journal paper, the formalization catalogue can be *updated* as Mathlib4 grows. As Lean SLT's native `klDiv` formalization nears completion, catalogue topics that currently define KL divergence via custom Radon-Nikodym constructions will become candidates for upgrade to the native infrastructure—a form of automatic scientific progress requiring no change to the pipeline itself. The same pattern applies as Itô integrals, Fokker–Planck operators, and Riemannian manifold infrastructure land in Mathlib4: each upgrade is a one-sketch edit with no restructuring of the surrounding pipeline.

3. **AI-readable mathematics**: The 50 theorem sketches constitute a machine-readable description of the FEP's mathematical structure. Future AI systems can use these specifications as training data, building on verified foundations rather than potentially inconsistent natural-language descriptions. This feedback loop — formalised mathematics training better formalisation assistants [@yang2024leandojo; @song2025copilot; @deepseek2025proverv2] — is a distinguishing feature of machine-verifiable artefacts relative to informal PDFs.

4. **Safety implications**: As AI systems increasingly operate under Active Inference-like frameworks, formal verification of the underlying mathematics provides assurance that the theoretical foundations are sound—a contribution to AI safety through mathematical rigor. The sorry-free, compiler-verified sketches for softmax normalization (fep-028), belief update nonnegativity (fep-034), and optimal policy existence (fep-008) are directly relevant to safety-critical Active Inference deployments; these sketches establish machine-checked type consistency and internal arithmetic validity, a distinction from complete end-to-end formal proofs discussed in §\ref{sec:limitations_and_threats_to_validity}.

5. **Community bridge**: The FEP Lean catalogue bridges two historically disjoint communities — the Active Inference / theoretical neuroscience community and the formal verification / proof assistant community. The Lean 4 primer (§\ref{sec:lean_4_a_primer_for_active_inference_researchers}) is designed as an onboarding resource for Active Inference researchers who have not previously encountered interactive theorem provers, while the FEP-specific content provides formal verification researchers with a substantive application domain in mathematical physics.

6. **Cognitive science's relationship to formal methods**: Much of the cognitive-science literature has treated mathematics as an *expository* tool (to communicate models) rather than as a *verification* tool (to certify derivations). The catalogue is a small step toward reframing that relationship. If successful, the broader programme of formalised cognitive theory would allow journals to require (or at least welcome) machine-verifiable proof artefacts alongside narrative derivations, analogous to the gradual normalisation of open data and open code in empirical science.

7. **Machine-auditable FEP claims**: The catalogue makes FEP claims *machine-auditable* in a sharp sense — a peer reviewer can **check the theorems computationally** by running `lake env lean` against the shipped sketches, rather than relying on the reviewer's ability to follow informal derivations in a PDF. This matters most for the subset of FEP constructs that have been disputed in the literature (e.g., the precise form of the Markov blanket partition, the legitimacy of specific steady-state assumptions, the conditions under which variational free energy upper-bounds surprise). For each such construct, the catalogue provides a typed Lean statement that pins down *exactly* which mathematical object is meant; this **reduces informal mathematical ambiguity in disputed FEP constructs** to a level where disagreements become either (a) disagreements about the informal-to-formal translation (which the catalogue makes explicit and reviewable) or (b) disagreements about the underlying mathematics (which are then resolvable at the level of Lean definitions rather than at the level of prose).

## Limitations and Threats to Validity {#sec:limitations_and_threats_to_validity}

Several limitations qualify the conclusions drawn from this work.

| # | Threat | Severity | Mitigation |
|---|--------|----------|------------|
| 1 | **Semantic vs. proof depth**: Sketches demonstrate stateability, not provability | High | Maturity taxonomy makes distinction explicit |
| 2 | **LLM non-determinism**: Output quality varies across runs | Medium | Compilation as hard validation gate; Hermes assessment |
| 3 | **Single-model evaluation**: Definitive run uses GLM-5.1 as primary | Medium | Fallback chain tests 5 additional models beyond the primary (6 total in `_FREE_MODEL_CHAIN`) |
| 4 | **Mathlib4 version sensitivity**: Maturity assessments reflect March 2026 state | Low | Version pinned; upgradeable as Mathlib grows |
| 5 | **Domain specificity**: FEP-domain prompt may not generalize | Medium | Architecture is domain-agnostic; prompt is pluggable |
| 6 | **`sorry` inflation**: LLM may over-use `sorry` when proofs are available | Medium | Hermes assessment identifies unnecessary `sorry` usage; zero-`sorry` policy enforced across all 50 current catalogue rows |
| 7 | **Hermes self-assessment bias**: LLM evaluating its own output | Medium | Native compilation provides independent check |
| 8 | **Primary-model quality ceiling**: `moonshotai/kimi-k2.6` is a strong free-tier model but not frontier-SOTA | Medium | Chain falls back to 7 additional models (including `z-ai/glm-5.1`, `kimi-k2-thinking`, GPT-OSS-120B); commentary is reviewable; sketches are curated, not LLM-authored |
| 9 | **Mathlib cache / workspace drift** | Low | Use `scripts/_maint_bootstrap_lean_toolchain.sh` or `scripts/00_setup_environment.py --project fep_lean`; preflight fails fast if `.olean` cache is incomplete |
| 10 | **Catalogue scope**: 50 topics out of a potentially much larger FEP literature | High | Maturity taxonomy is explicit about coverage; catalogue is extensible per-topic without restructuring |
| 11 | **Authorship ambiguity for AI-assisted proofs** | Medium | Curated sketches remain researcher-authored; Hermes contributes commentary; attribution is logged per run |
| 12 | **Snapshot-in-time maturity assessments** | Low | Roadmap (§\ref{sec:maturity_roadmap}) ties maturity to forthcoming Mathlib milestones |

*Threats to validity and mitigations.*

The most fundamental limitation is the distinction between *stateability* and *provability*. In general ITP formalisation, a `sorry`-laden sketch demonstrates that constructs can be *expressed* in Lean 4's type system without proving them — the FEP catalogue goes further with zero `sorry` across all 50 rows, but the compiled sketches are anchored lemmas and definitions rather than complete end-to-end formalisations of every theorem title. The stateability contribution is itself significant: it establishes the *form* of the proof obligations, a necessary precondition for any future complete verification effort.

Beyond this headline caveat, five concrete limitations deserve explicit attention:

1. **Definitional lemmas and structural identities, not full dynamical theorems.** The current catalogue covers *definitional* lemmas (e.g., softmax normalisation, entropy non-negativity, Radon–Nikodym well-definedness on finite supports) and *structural* identities (e.g., algebraic rearrangements of KL bounds, finset-level Jensen inequalities). It does **not** cover the full dynamical theorems that FEP practitioners sometimes invoke — e.g., the existence-and-uniqueness of non-equilibrium steady states for the full non-linear Fokker–Planck operator, or the convergence-in-distribution claims for continuous-time active-inference agents. Those theorems are out of scope for the shipped catalogue precisely because Mathlib4's SDE layer is not yet mature enough to host them (§\ref{sec:identified_mathlib_gaps}).
2. **Namespace isolation prevents cross-topic lemma reuse.** Every topic is scoped under its own `namespace FEPNNN … end FEPNNN` block (where `NNN` is the zero-padded topic number). This is a deliberate design choice that keeps each sketch self-contained for independent compilation and review, but it also means that a lemma proved in, say, `FEP028` cannot be invoked from `FEP034` without re-exporting it or re-proving it. A future revision may refactor shared primitives into a common namespace, but until that refactor lands, the catalogue should be read as a **set of 50 disjoint specification fragments** rather than as a single integrated theory.
3. **Mathlib pin requires forward maintenance.** The toolchain and Mathlib tag are pinned (Lean **v4.29.0**, Mathlib **v4.29.0**). Future releases will rename lemmas, tighten hypotheses, deprecate tactics, and change default `simp` sets — each bump needs a **maintenance sweep** (`03_lean_verify_only.py`, CI). The pipeline keeps sweeps tractable (small per-topic sketches), but they are not free.
4. **Hermes commentary is advisory, not authoritative.** The LLM (Hermes, via the OpenRouter chain rooted at `moonshotai/kimi-k2.6`) produces natural-language commentary and, on request, a refined sketch suggestion. This output is **advisory**: it does not overwrite `config/topics.yaml`, it does not overwrite the `SKETCHES` dictionary, and it does not guarantee proof correctness. The compiler — not the LLM — is the authority on whether a sketch typechecks. Readers should treat Hermes's prose the way they treat a knowledgeable but fallible collaborator's whiteboard commentary: useful for orienting a reader, insufficient as a verification claim.
5. **Headline compilation is measured, not assumed.** Native success rates are reported via **`50/50`** and verifier artefacts in §\ref{sec:quantitative_execution_metrics}.

### Model-quality ceiling {#sec:model_quality_compile_gap}

The default Hermes primary model is not the current state of the art in LLM-ITP benchmarks; SOTA results on miniF2F are held by specialised provers (DeepSeek-Prover-V2 [@deepseek2025proverv2], AlphaProof [@alphaproof2024]). Hermes’s role is *commentary* and *review*, not authority over compilation: **`lake env lean`** and catalogue curation decide correctness.

### Scope Limitations: 50 Topics of Many {#sec:scope_limitations}

The FEP literature contains far more than 50 distinguishable theorems. A fuller catalogue might cover:

- **Continuous-time formulations** of variational free energy (not yet tractable due to SDE gap).
- **Hierarchical predictive coding** beyond the two-layer structure of fep-027.
- **Geometric mechanics** extensions (symplectic structures, Lagrangian formulations).
- **Non-equilibrium thermodynamics** beyond the fluctuation-theorem sketches.
- **Neurobiological specialisations** (e.g., specific circuit-level instantiations).

Each omission is a principled choice: either the Mathlib4 infrastructure is not ready (SDE, Riemannian, PDE), or the topic is sufficiently specialised that its inclusion would bloat the catalogue without proportional pedagogical benefit. The 50-topic scope is pragmatic, not definitive; the extension pattern is documented in `scripts/_maint_build_topics_catalogue.py`.

### Ethical Considerations: Authorship and AI-Assisted Proof {#sec:authorship_ethics}

The catalogue is authored by human researchers; Hermes contributes commentary. However, as LLM-ITP systems grow more capable — potentially authoring full proofs rather than commentary — the authorship question will sharpen. We adopt three practices in anticipation:

1. **Per-run attribution logs**: The model identifier, run timestamp, and commit hash are recorded for every Hermes turn in `output/reports/run_*/`. Any claim of formal verification is paired with an artefact bundle that names the assistant.
2. **Curated sketches remain researcher-authored**: The Lean 4 code itself is not generated by the LLM in this pipeline. Authorship of the *mathematical content* is unambiguous.
3. **Reviewer responsibility**: Hermes commentary is treated as draft text that must be reviewed by a human before publication. The pipeline does not elevate LLM output to authoritative status.

The broader ethical question — *"if an LLM proves a theorem in Lean, who is the author?"* — remains unsettled. The position adopted here is that the author is whoever takes responsibility for the statement, the proof, and the review. The LLM is an instrument; attribution attaches to the researchers who wield it and vouch for the result.

### Future Work: From Sketches to End-to-End Proofs {#sec:future_sketch_to_proof}

Three concrete directions would deepen the catalogue:

1. **Close `sorry`-free end-to-end proofs** for a chosen subset of topics (starting with fep-002, fep-028, fep-034). This is already partially achieved at the *sketch* level; the work remaining is to extend each sketch into the full theorem that its informal statement claims.
2. **Expand Mathlib4 coverage**: contribute upstream the primitives identified in §\ref{sec:identified_mathlib_gaps} (native `klDiv`, conditional entropy, Itô integrals, Fokker–Planck operators).
3. **Broaden scope**: add topics as Mathlib infrastructure permits — continuous-time dynamics, Riemannian geometry, hierarchical models with more than two layers, and specific neurobiological instantiations.

These are not idle aspirations; each is keyed to a specific Mathlib4 milestone (§\ref{sec:maturity_roadmap}) and can be planned on a 6–12 month horizon.
