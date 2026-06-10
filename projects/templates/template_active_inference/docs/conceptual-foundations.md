# Conceptual Foundations — Active Inference, Cellular Sheaves, and Verified Composition

> Why this template exists, in full. The [README](../README.md) gives the short
> version ("When to use this template" / "Why sheaf composition?"); this
> document gives the intellectual grounding. Adapted 2026-06-10 from an
> external research synthesis of the framework; all volatile numbers (grid
> values, row counts, entropies) are deliberately **not** reproduced here —
> they live in the generated artifacts under `output/data/` and are injected
> into the manuscript through `{{token}}` hydration, never hand-typed.

## The problem: semantic drift in multi-method research

Computational cognitive science increasingly couples prose, analytical
derivations, simulations, and formal proofs in one paper. Each surface evolves
on its own schedule, so the traditional manuscript — a manually assembled
projection of the underlying research — desynchronizes the moment any model,
dataset, or library changes. This template's answer is to treat publishing not
as authoring text but as the **strict gluing of typed, gated artifacts**: the
manuscript is an executable, machine-checked composition, and no claim,
figure, or statistic can drift from the deterministic artifact that produced
it.

## Active Inference in brief

Active Inference is a process theory derived from the Free Energy Principle
(FEP): a system that persists must, in a well-defined sense, minimize
variational free energy — an upper bound on surprise — and this single
imperative yields both perception (updating beliefs to match the world) and
action (changing the world to match beliefs). Action selection minimizes
**Expected Free Energy (EFE)**, which decomposes into an epistemic term
(information gain) and a pragmatic term (preference satisfaction), resolving
the exploration–exploitation dilemma inside one Bayesian objective rather
than via ad-hoc heuristics. The theoretical elegance comes at implementation
cost — evaluating counterfactual futures over deep policy trees — which is
exactly why this exemplar surrounds its models with a multi-track validation
environment.

The two scientific tracks instantiate this deliberately small:

- **Bernoulli–Ising analytical oracle.** A symmetric two-policy toy model
  with Ising coupling and a deformation parameter λ, giving closed-form
  mutual information that saturates toward log 2 as the streams entangle.
  The track never merely plots the closed form: an independent
  total-correlation recomputation must agree (zero residual is asserted by a
  gate), and the Theorem-5.1 free-energy decomposition must cancel exactly
  (the invariant suite gates on every check passing). Values and grids live
  in `output/data/` (e.g. `parameter_sweep.csv`, the invariant reports), not
  in this file.
- **pymdp sophisticated-inference harness.** A minimal T-maze POMDP run
  through [pymdp](https://github.com/infer-actively/pymdp), contrasting
  scripted `state_inference` rollouts with EFE-driven `policy_inference`
  across horizons and seeds (the policy-comparison artifact records the
  measured difference). Runtime warnings are themselves evidence: the
  validation spine pins the expected construction/warning counts in
  `pymdp_runtime_diagnostics.json`, so a silent upstream library change
  fails the pipeline instead of silently altering results.

## The manuscript as a cellular sheaf

The composition layer borrows from cellular-sheaf theory (Curry; Ghrist;
Hansen & Ghrist): attach data to the cells of a discrete space, with
restriction maps enforcing local-to-global consistency, and call a global
assignment a *section* only when every overlap agrees.

Concretely, the base space is the finite IMRAD poset — a strict chain
`Introduction ≺ Methods ≺ Results ≺ Discussion ≺ Appendix` with group ⊒
section containment inside each block (a finite Alexandrov space: the
topology IS the partial order). The presheaf assigns to each composing
section its bound fragment set — which tracks (prose, formalism, simulation,
lean, gnn, ontology, …) contribute which files — per
[`manuscript/sheaf/manifest.yaml`](../manuscript/sheaf/manifest.yaml), with
the track registry ([`manuscript/sheaf/tracks.yaml`](../manuscript/sheaf/tracks.yaml))
carrying each track's renderer, role, and global compose order.

Six laws are machine-verified by `verify_sheaf_laws`
([`src/manuscript/sheaf/laws.py`](../src/manuscript/sheaf/laws.py)) before any
markdown is composed, each paired with a negative control proving the gate
binds content, not shape:

| Law | What it enforces |
| --- | --- |
| Poset | IMRAD blocks form a strict chain; every composing section sits in a group row |
| Presheaf | Bound tracks come from the registered set; local track order is a monotone restriction of the global order |
| Separation | Section → output file is injective — distinct locals glue to distinct globals |
| Gluing | Compose order is a linear extension; every composing section appears exactly once |
| Typing | Every binding is well-typed against a registered renderer |
| Compositionality | Fragments are private to one section; composition is the coproduct of per-section bodies |

A coverage matrix (rendered as the manuscript's first page) classifies every
section×track cell as present / absent / missing-binding, so topological
coverage is a visible proof object rather than an editorial impression.

**Honest scope note:** what the code verifies are presheaf/coverage axioms
over a finite poset with law-checked gluing — "sheaf-composed" in that
precise sense, not sheaf cohomology.

## Semantic gluing — consistency where tracks overlap

Structural laws guarantee shape; science needs the overlapping *content* to
agree. Hydration therefore emits a **semantic gluing certificate**
(`output/data/sheaf_gluing_certificate.json`, with the evidence crosswalk and
validation dependency graph beside it) binding shared GNN variables, ontology
symbols, typed claim evidence, artifact producers/consumers, and manuscript
variables. If the analytical track's λ-grid artifact changes, every consumer
(simulation comparison, figures, prose tokens) must re-derive from the same
file or the certificate breaks; figures are source-mapped and hashed, and a
statistical bridge requires plotted claims to be backed by statistics rows.
Cross-track disagreement halts rendering — notation drift becomes a build
failure, not a referee's catch.

## The Lean 4 boundary

Tests confirm code runs as authored; they cannot prove necessity. The Lean
track formalizes the *finite boundary objects* the other tracks rely on —
graph-world reachability, finite policy enumeration, belief/posterior weight
witnesses, T-maze transition topology (e.g. goal absorption), and the EFE
additive identity ((risk + ambiguity) + (pragmatic + epistemic) = 0 from the
definitional relations) — compiled with `lake build`, `sorry`-free, with
`#print axioms` audited against a whitelist of core logic axioms. Theorem
statements are extracted into a traceability index so manuscript claims about
the T-maze or EFE must map to a named theorem, a model-checking witness, and
an evidence field. The epistemology is deliberately hybrid: empirical claims
are bounded by simulations; the axioms those simulations assume are proved.

## GNN and the Active Inference Ontology

Active Inference suffers a notation Babel across disciplines. Two contracts
mitigate it here:

- **Generalized Notation Notation (GNN)** (Smekal & Friedman 2023): the
  generative models are written as structured markdown
  (`gnn/*.gnn.md` — state-space blocks, connections), and an interop gate
  round-trips those declarations against the live Python variables
  (`gnn_roundtrip_report.json`) — the model description is a contract, not
  documentation.
- **Active Inference Ontology (AIO) concordance**: local symbols bind to
  ontology terms (couplings, policy vectors, posteriors, belief entropy) in
  an ontology profile matrix rendered into the manuscript; an unapproved
  alias or a renamed variable without a concordance update fails validation.

## What to take from this template

The exemplar's transferable lesson is not the T-maze: it is that **prose can
be subordinated to gated artifacts** — sheaf laws for document shape, a
semantic certificate for cross-track agreement, formal proofs for boundary
axioms, and notation contracts for interoperability — so the manuscript
behaves like a self-verifying computational laboratory. The promotion rule in
[`TODO.md`](../TODO.md) (producer + artifact + manuscript consumer + claim
evidence + semantic restriction + validation gate + negative control) is the
operational recipe for growing such a system one validated track at a time.

## Further reading

- Friston, K. — the Free Energy Principle line of work (e.g. *A free energy
  principle for the brain*, 2006; *The free-energy principle: a unified brain
  theory?*, 2010).
- Parr, T., Pezzulo, G., Friston, K. — *Active Inference: The Free Energy
  Principle in Mind, Brain, and Behavior* (MIT Press, 2022).
- Da Costa, L. et al. — *Active inference on discrete state-spaces: A
  synthesis* (J. Math. Psych., 2020).
- Friston, K. et al. — *Sophisticated Inference* (Neural Computation, 2021).
- Heins, C. et al. — *pymdp: A Python library for active inference in
  discrete state spaces* (JOSS, 2022).
- Curry, J. — *Sheaves, Cosheaves and Applications* (PhD thesis, UPenn, 2014).
- Ghrist, R. — *Elementary Applied Topology* (2014); Hansen, J. & Ghrist, R.
  — *Toward a spectral theory of cellular sheaves* (J. Appl. Comput.
  Topology, 2019).
- Smekal, J. & Friedman, D. — *Generalized Notation Notation for Active
  Inference Models* (Active Inference Institute, 2023).
- Moura, L. de & Ullrich, S. — *The Lean 4 Theorem Prover and Programming
  Language* (CADE, 2021).
- Active Inference Institute — *Active Inference Ontology*.
