# Lean4 and Mathlib4 Context — fep_lean

**Last Updated**: 2026-04-20 (aligned with canonical_facts.md)

## What is Lean4?

[Lean4](https://leanprover.github.io/) is a functional programming language and **interactive theorem prover** developed at Microsoft Research / Carnegie Mellon University. It combines:

- A **dependent type theory** foundation (Calculus of Inductive Constructions)
- An efficient compiled runtime (LLVM-based)
- A powerful metaprogramming/tactic framework
- **Mathlib4** — the largest mathematical library in existence for any proof assistant

In `fep_lean`, Lean4 is used to express theorems about the Free Energy Principle as **formally precise mathematical statements** that compile cleanly under `lake env lean` with Mathlib4 **v4.29.0**. All 50 catalogue sketches are `sorry`-free. Mathlib is pinned via `lean/lakefile.lean` (`require mathlib from git "https://github.com/leanprover-community/mathlib4.git" @ "v4.29.0"`); the Lean toolchain matches `lean/lean-toolchain` (**`leanprover/lean4:v4.29.0`**).

For verification, use `uv run python scripts/03_lean_verify_only.py --topic <id>` or full pipeline with `FEP_LEAN_GAUSS_WORKFLOWS=1`. See `docs/_generated/canonical_facts.md` for current status.

---

## Catalogue source of truth

Sketches exist in three shapes; keep them aligned when you change proof text.

| Layer | Role |
| ----- | ---- |
| [`scripts/catalogue_sketches.py`](../scripts/catalogue_sketches.py) (`SKETCHES`) | **Canonical bodies** for [`LeanVerifier`](../src/verification/lean_verifier.py): bodies omit a leading `import`; the verifier prepends Mathlib and `open` lines. |
| [`scripts/_maint_build_topics_catalogue.py`](../scripts/_maint_build_topics_catalogue.py) | Regenerates [`config/topics.yaml`](../config/topics.yaml) from `METADATA` + `SKETCHES` (each `lean_sketch` is `SKETCHES[topic_id]`). After editing sketches or catalogue metadata, run from `projects/fep_lean`: `uv run python scripts/_maint_build_topics_catalogue.py`. |
| [`config/topics.yaml`](../config/topics.yaml) | Loaded at runtime by [`FEPTopicCatalogue`](../src/catalogue/topics.py) for the pipeline, tests, and Hermes; must match regenerated output whenever `SKETCHES` changes. |
| [`lean/FepSketches/fep_all.lean`](../lean/FepSketches/fep_all.lean) | **Generated** Lake aggregate: each topic is wrapped in `namespace fep_fepNNN ... end fep_fepNNN` over a single hoisted `import Mathlib` for whole-workspace `lake build`. Regenerate with `uv run python scripts/_maint_build_fep_all_lean.py` after any `SKETCHES` edit (CI sorry-gates this file and [`Basic.lean`](../lean/FepSketches/Basic.lean); the file itself is gitignored). |
| [`scripts/_maint_build_fep_all_lean.py`](../scripts/_maint_build_fep_all_lean.py) | **Generator** for `lean/FepSketches/fep_all.lean` and the matching `Basic.lean` stub. Reads `SKETCHES` (single source of truth) and emits the aggregate; safe to re-run any time. |
| [`tests/test_catalogue_sketches_ssot.py`](../tests/test_catalogue_sketches_ssot.py) | Asserts every `topics.yaml` `lean_sketch` equals `SKETCHES[id]` (fast drift check, no `lake` required). |
| `lean/FepSketches/_verify_*.lean` | **Transient** verifier outputs from `LeanVerifier` — do not edit; safe to delete (regenerated per topic compile, gitignored). |

---

## Cursor lean4 commands (fep_lean) {#cursor-lean4-commands}

Editor **lean4-skills** slash commands apply to **Lean** in this repo. They do not replace Python tests or the optional Hermes + [`GaussRunner`](../src/gauss/runner.py) pipeline (Gauss **workflow stages** named `draft` / `prove` / `review` are HTTP + SQLite driven and require `FEP_LEAN_GAUSS_WORKFLOWS=1` — analogous intent to some `/lean4:*` commands but **not** the same implementation).

### Command map (lean4-skills)

| Command | Role (plugin) | In `fep_lean` |
| ------- | ------------- | ------------- |
| `/lean4:draft` | Skeleton declarations from informal claims | **Not** wired into the Python pipeline. For catalogue work, bodies live in [`SKETCHES`](../scripts/catalogue_sketches.py); Hermes can run a Gauss **`draft`** stage when workflows are enabled. |
| `/lean4:formalize` | Interactive draft + proving | Same boundary as **draft** for committed rows: merge via `SKETCHES` + [`_maint_build_topics_catalogue.py`](../scripts/_maint_build_topics_catalogue.py). |
| `/lean4:autoformalize` | Unattended source → proof | Off-catalogue or local experiments only for **committed** catalogue; see [authorship-guide.md](authorship-guide.md). |
| `/lean4:prove` / `/lean4:autoprove` | Fill `sorry` / multi-cycle proof | Shipped **`SKETCHES` are sorry-free**; use for scratch files or a branch that relaxes CI policy. Gauss **`prove`** is separate (Hermes). |
| `/lean4:checkpoint` | Save progress + build gate | Use normal `git` + [`Verification gates](#verification-gates)` below; no project-specific hook. |
| `/lean4:review` | Read-only proof review | Complements pipeline [`Reporter`](../src/output/reporter.py) JSON/Markdown output; does not substitute for `pytest`. |
| `/lean4:learn` | Repo or Mathlib discovery | **Repo:** [`catalogue_sketches.py`](../scripts/catalogue_sketches.py) → [`LeanVerifier`](../src/verification/lean_verifier.py) → optional GaussRunner → [`Reporter`](../src/output/reporter.py). **Mathlib:** table below + [topics-reference.md](topics-reference.md). |
| `/lean4:doctor` | Plugin / toolchain diagnostics | **Plugin** (elan, `LEAN4_SCRIPTS`, MCP). **This repo:** [`fep-lean-preflight`](../README.md) + [troubleshooting.md](troubleshooting.md#lean4-skills-lean4doctor-vs-this-repo). |
| `/lean4:refactor` | Simplify proofs, leverage mathlib | **Lake files:** [`lean/FepSketches/`](../lean/FepSketches/). **Catalogue:** edit `SKETCHES` → regenerate YAML → gates below. |
| `/lean4:golf` | Shorten / speed up proofs | Same surfaces as refactor; run after proofs are stable. |

GaussRunner and `/lean4:*` are **orthogonal**: Hermes + SQLite sessions vs local editor skill loops over the same [`lean/`](../lean/) workspace.

### Verification gates

After any sketch or aggregate change:

```bash
cd projects/fep_lean/lean && lake build
cd projects/fep_lean && uv run python scripts/01_run_tests.py --project fep_lean
```

Single-topic check: `uv run python scripts/03_lean_verify_only.py --topic fep-NNN` (see [cli-reference.md](cli-reference.md)).

---

## What is Mathlib4?

[Mathlib4](https://leanprover-community.github.io/mathlib4_docs/) is the community mathematics library for Lean4. It contains formalized proofs covering:

- **Measure Theory** (`MeasureTheory`): sigma-algebras, measures, Lebesgue integration, probability measures
- **Probability Theory** (`Probability`): conditional expectations, KL divergence, stochastic processes
- **Topology and Analysis** (`Topology`, `Analysis`): manifolds, differential geometry, functional analysis
- **Linear Algebra** (`LinearAlgebra`, `Matrix`): inner product spaces, positive definite matrices
- **Geometry** (`Geometry`): Riemannian manifolds, geodesics

All 50 `fep_lean` topics reference Mathlib4 modules in their `mathlib` field. Each topic carries **`mathlib_status: real`**: the committed `lean_sketch` text is the corresponding entry in **`SKETCHES`** (regenerated into `config/topics.yaml`), a **`sorry`-free** fragment that typechecks under `import Mathlib` plus the verifier opens. The `mathlib` string remains a **navigation hint** toward fuller formalizations, not a claim that every named module path is exercised by the sketch.

---

## Mathlib4 Modules Used in fep_lean {#mathlib4-modules-used-in-fep_lean}

This table classifies **how deeply Mathlib covers** the named module paths for the themes in this catalogue. It is **not** `TopicEntry.mathlib_status` (every shipped topic is `real` in `config/topics.yaml`).

| Module Path | Library coverage | Area | Representative Topics |
|-------------|------------------|------|-----------------------|
| `MeasureTheory.Measure.MeasureSpace` | real | FEP, BayesianMechanics | fep-001, 005, 011, 014 |
| `MeasureTheory.Measure.WithDensity` | real | FEP | fep-001, 012 |
| `MeasureTheory.Decomposition.RadonNikodym` | real | FEP | fep-001, 002 |
| `Analysis.SpecialFunctions.Log` | real | FEP, InfoGeometry | fep-001, 002, 013, 014 |
| `Data.Finset.Basic` | real | ActiveInference | fep-007, 008, 021 |
| `Topology.Basic` | real | FEP | fep-006, 024 |
| `Probability.ProbabilityMeasure` | real | BayesianMechanics | fep-014, 019 |
| `MeasureTheory.Kernel` | real | BayesianMechanics | fep-005, 011, 019 |
| `Analysis.Calculus.Deriv.Basic` | partial | InfoGeometry | fep-004, 016, 017 |
| `Analysis.InnerProductSpace.Basic` | partial | InfoGeometry | fep-004, 016, 017 |
| `Geometry.Manifold.MFDeriv` | partial | InfoGeometry | fep-004, 017 |
| `LinearAlgebra.Matrix.PosDef` | partial | FEP, InfoGeometry | fep-006, 009, 016 |
| `MeasureTheory.Integral.Bochner` | partial | Thermodynamics | fep-036, 040, 047 |
| `Probability.ConditionalExpectation` | partial | ActiveInference | fep-003, 021 |
| `Analysis.Convex.Hessian` | real | FEP | fep-006, 009 |
| `Probability.KL` | aspirational | FEP, InfoGeometry | fep-001, 017 |
| `Analysis.Manifold.Riemannian` | aspirational | InfoGeometry | fep-017, 018 |
| `Probability.Distributions.Gaussian` | real | Thermodynamics | fep-042 |
| `Analysis.VectorCalculus` | aspirational | Thermodynamics | fep-041 |

---

## Common Lean 4 tactics used in fep_lean sketches

The committed sketches mix term-mode with short tactic blocks. The tactics most commonly seen across the 50 topics:

| Tactic | Purpose |
|--------|---------|
| `simp` | Rewrite by the default simp set (normalize expressions, unfold definitions). |
| `exact` | Close a goal with a precisely-typed term. |
| `apply` | Chain a lemma whose conclusion matches the goal; leaves premises as new goals. |
| `ring` | Discharge equalities in commutative (semi)rings — used for measure-theoretic algebra. |
| `norm_num` | Decide goals about concrete numerals (non-negativity, inequalities, arithmetic). |
| `rw` | Rewrite by an equality or `iff` lemma. |
| `nlinarith` | Nonlinear arithmetic solver; discharges inequalities combining products and sums. |
| `positivity` | Prove `0 < x` / `0 ≤ x` goals by structural rules on sub-expressions. |
| `have` | Introduce a named intermediate lemma within a proof. |
| `calc` | Chain equalities / inequalities step-by-step with human-readable justification. |
| `intro` | Introduce a hypothesis or bound variable for a `∀` / `→` goal. |
| `constructor` | Split an And/Exists/structure goal into its constituent subgoals. |

These cover nearly every proof in the catalogue; more specialised tactics (`measurability`, `fun_prop`, `gcongr`) appear in a minority of topics.

---

## `lake env lean` workflow

`LeanVerifier` does not feed the raw `SKETCHES` body to Lean directly. For each topic it builds a throw-away `.lean` file of the form:

```lean
import Mathlib

open MeasureTheory Measure ProbabilityTheory Real NNReal ENNReal Filter Topology Finset

-- >>> SKETCHES[topic_id] body spliced here <<<
```

and then runs `lake env lean <that file>` from `projects/fep_lean/lean/`. The prepended `import Mathlib` is an **umbrella import** — it pulls the whole library so that any of the paths listed in the `mathlib` field of `config/topics.yaml` resolve without a per-topic import statement. The `open` line normalises namespaces that appear across every area.

This is why stored `SKETCHES` bodies **omit** their own `import` lines: the verifier supplies them. Anything checked into `lean/FepSketches/fep_all.lean` follows a different (namespace-based) convention — see below.

### Namespace wrapping convention

Every committed sketch in `config/topics.yaml` is wrapped in a per-topic namespace so names do not collide across the 50-topic catalogue:

```lean
namespace FEPNNN

-- definitions, lemmas, theorems, with prefixed names like `fepNNN_foo_bar`
...

end FEPNNN
```

where `NNN` is the zero-padded topic number (`FEP001`, `FEP002`, …, `FEP050`). This convention is enforced by `scripts/_maint_build_topics_catalogue.py` when regenerating YAML from `SKETCHES` and is checked (by shape, not by full namespace equality) in the test suite.

---

## SSOT chain (single source of truth)

There is exactly one canonical location for sketch bodies, and four downstream consumers:

```
scripts/catalogue_sketches.py   (SKETCHES dict — SSOT)
             │
             ▼
scripts/_maint_build_topics_catalogue.py    (regenerator)
             │
             ▼
config/topics.yaml              (generated; loaded at runtime)
             │
             ▼
LeanVerifier  →  lake env lean (per-topic compilation check)
```

Test `tests/test_catalogue_sketches_ssot.py` (drift check, no `lake` needed) and the per-row sweep in `scripts/03_lean_verify_only.py` (real compilation; logs to stdout) keep these layers honest. After a full pipeline run with workflows enabled, **`Reporter`** writes **`verification_manifest.json`** under `output/reports/run_*/`. Any edit to a sketch MUST start in `SKETCHES`; regenerate YAML immediately.

---

## Lean4 Theorem Sketch Structure

Every topic in `config/topics.yaml` has a `lean_sketch` field copied from **`SKETCHES`** (see table above). Stored bodies **omit** a leading `import`; [`LeanVerifier`](../src/verification/lean_verifier.py) supplies `import Mathlib` and the standard `open` lines before `lake env lean`.

### Committed catalogue shape (from `SKETCHES`)

```lean
variable {α : Type*} [MeasurableSpace α]

/-- Docstring; theorem names use the fepNNN_* prefix. -/
theorem fep001_measure_union_le (μ : Measure α) (s t : Set α) :
    μ (s ∪ t) ≤ μ s + μ t :=
  measure_union_le s t
```

### Mathlib Implicit vs Explicit Arguments

Mathlib4 uses implicit arguments extensively. The most common mistake when writing `SKETCHES` is supplying type-class or measure arguments that Mathlib expects to be inferred:

```lean
-- WRONG: μ is implicit in measure_union_le
measure_union_le μ s t

-- CORRECT: μ is inferred from the goal context
measure_union_le s t
```

Rule: if the Mathlib4 signature has `{μ : Measure α}` (curly braces), do **not** pass `μ` explicitly. The `variable` block at the top of the sketch (e.g. `variable {α : Type*} [MeasurableSpace α] [Measure α]`) supplies `μ` implicitly. Supplying it explicitly produces `error: function expected at μ`.

Similarly for `MeasurableSpace`, `TopologicalSpace`, `NormedAddCommGroup`, and other type-class arguments — they are almost always `[...]` instances inferred from the local context, not explicit parameters to pass at call sites.

### Generic Mathlib layout (not copy-paste for `SKETCHES`)

When exploring in the REPL you may write full files with `import Mathlib` and namespaces. To **commit** a sketch, port the body (no leading `import`) into `SKETCHES` and regenerate YAML.

```lean
import Mathlib
-- ... then experiment; fold results back into SKETCHES without the import lines.
```

### Stylized examples (off-catalogue narration)

[topics-reference.md](topics-reference.md) and Hermes drafts sometimes show multi-line lemmas with extra imports or `sorry`. The **shipped** catalogue is sorry-free; treat those snippets as narrative, not as the verifier-ready `SKETCHES` text.

---

## `sorry` Usage

Under the current policy, all 50 Lean4 sketches in `fep_lean` are **`sorry`-free** — each `SKETCHES` body type-checks cleanly without proof placeholders. `sorry` is still useful when **staging** work or in narrative-only examples:

- `sorry` closes any goal for type-checking incomplete proofs
- The shipped catalogue and CI gates expect **no** `sorry` in `SKETCHES` and in `fep_all.lean` / `Basic.lean` (see [authorship-guide.md](authorship-guide.md) §4)
- The manuscript maturity taxonomy (§3c) can still describe progression for readers even when the repo stays all-`real`

The Hermes explainer produces (1) a 2–4 sentence explanation of the proof strategy and (2) a refined Lean 4 sketch in a fenced `lean` code block. Its assessment covers:

1. The type signature makes sense for the theorem
2. The Mathlib4 imports are plausible and available
3. Whether a proof would work with the given sketch approach
4. What additional lemmas or definitions would be needed

---

## Verification Challenges & False Positives

During the formal verification processes via `lake env lean`, mathematical validity can be overshadowed by infrastructure orchestration anomalies.

**The MacOS ELAN Sandbox Contention Matrix**
During automated agentic sweeps, verifying 50 Lean scripts via parallel threading (`ThreadPoolExecutor`) routinely triggers fatal macOS Sandbox environment limits. The ELAN proxy macro fails to lock dependency pathways correctly across 10+ subshells.
The parser successfully boots, but blindly drops cached `.olean` imports, yielding outputs like: `error: unknown identifier 'measure_union_le'`.
* **Lesson Learned**: In automated verification, do not inherently trust Lean parsing errors if executing asynchronously. Isolate the mathematical proof test linearly—the infrastructure deadlock mask mathematical validity.

---

## Validity of the Sketches

The Lean4 sketches in `fep_lean` are designed to be:

1. **Type-correct**: The theorem statement parses and type-checks in Lean4 cleanly (current catalogue: no `sorry`)
2. **Mathematically sound**: The statement captures the correct mathematical content
3. **Mathlib-grounded**: References real Mathlib4 module paths (verified in Mathlib4 March 2026)
4. **Proof-plausible**: The proposed proof approach could work with additional lemmas

They are NOT designed to be:

- Complete deep proofs of every theorem claim in the topic title (sketches prove structural lemmas that anchor the topic)
- Identical to any particular Mathlib4 formalization
- Optimal in terms of generality or abstraction

---

## Lean4 Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Lean4 documentation | <https://leanprover.github.io/lean4/> | Language reference |
| Mathlib4 docs | <https://leanprover-community.github.io/mathlib4_docs/> | Library API |
| Mathlib4 GitHub | <https://github.com/leanprover-community/mathlib4> | Source code |
| Lean4 Zulip | <https://leanprover.zulipchat.com/> | Community Q&A |
| Natural Number Game | <https://adam.math.hhu.de/> | Interactive tutorial |

---

## Navigation

- [← FEP Background](fep-background.md)
- [Topics Reference →](topics-reference.md)
- [Testing (SSOT + suite)](testing.md)
- [Authorship guide](authorship-guide.md)
- [← docs/README.md](README.md)
