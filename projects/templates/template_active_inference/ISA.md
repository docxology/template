---
project: template_active_inference
task: Strengthen the multi-track sheaf paradigm into a typed, composable, law-verified total-integrity exemplar
effort: E4
phase: observe
progress: 0/41
mode: algorithm
started: 2026-05-28
updated: 2026-05-28
---

# ISA — Sheaf Paradigm Integrity (template_active_inference)

## Problem

The "sheaf" in this project is **sheaf-flavored but not sheaf-rigorous**. The implementation
(`src/manuscript/sheaf/`) is a *coverage/incidence* structure: sections bind track→fragment
paths, and coverage cells (`P`/`—`/`M`) record file existence. The manuscript
(`08_methods_sheaf.md`, appendix formalism) borrows sheaf notation — a "partial binding map
$F_s : \mathcal{T} \rightharpoonup \mathrm{Path}$" — but the code verifies **none of the
structural laws that make a presheaf a sheaf**: there are no restriction maps, no separation
(locality) axiom, no gluing axiom, and no functoriality check. Typing is advisory only
(`renderer_suffix_mismatch` is a `warn`, and generated renderers bypass it). For a project
meant to be the *total-integrity holistic exemplar* of Active Inference projects, the gap
between the word "sheaf" and the math it actually enforces is the central integrity defect.

## Vision

The composer becomes a genuinely *typed, composable, law-verified* sheaf over the IMRAD base
poset. A single oracle (`verify_sheaf_laws`) checks — with negative controls that prove each
check bites — the presheaf functoriality, separation, gluing, well-typedness, and
compositionality laws. The manuscript states *exactly* what is verified and *explicitly* what
is not claimed (this is a coverage sheaf over a finite poset, not sheaf cohomology). A reader
recognizes instantly: the name "sheaf" is now *earned* — every law is machine-checked, cited
to a runnable oracle, and the prose neither under- nor over-claims.

## Out of Scope

- Sheaf **cohomology** ($H^0$/$H^1$, Čech complexes, derived functors) — not computed, and
  the manuscript must say so. We verify the sheaf *axioms* on a finite base, not cohomology.
- Rewriting the analytical/pymdp/Lean/GNN scientific tracks themselves — only their
  composition/typing as sheaf fragments is in scope.
- Fighting the repo's convergent-automation churn on the 112 pre-existing modified files —
  work lands on a new stable layer and is verified by running fresh.
- Any change that lowers the green baseline (153 passing tests).

## Principles

- **Earn the word.** Every sheaf-theoretic term in the manuscript maps to a machine-verified
  law in code. No aspirational notation.
- **Negative controls bind truth.** A law check is only trusted if a mutation that breaks the
  law is proven to be caught (shape tests don't bind truth — memory).
- **Honest ceiling.** State what is NOT verified as prominently as what is.
- **Own stable layer.** Additive modules over editing churned files; verify by fresh run.
- **Cite the oracle.** Manuscript counts/claims derive from `counts.py` / the laws report,
  never hand-typed.

## Constraints

- INVARIANT: baseline is **153 tests passing, exit 0** — must not regress (re-baseline after).
- INVARIANT: registry has **10 tracks**; manifest has **17 IMRAD rows** (5 groups + 12
  composing sections); `compose_all_sections` writes **12** files. (Verified this session via
  `counts.py` / `test_sheaf_compose.py::test_compose_writes_markdown_sections`.)
- INVARIANT: all 10 current track bindings are already well-typed (markdown→.md, ontology→.yaml,
  generated renderers exempt) — promoting typing to error-level must keep the live manifest green.
- bun/TypeScript rules are PAI-global; this project is Python/uv — use `uv run`, no mocks
  (CLAUDE.md No-Mocks policy), real fixtures only.
- Project coverage floor is 90% on `projects/{name}/src`; new module must carry tests.
- Subagent Write is denied in this template repo — author directly; Forge/Cato read-only.

## Goal

Add a machine-verified sheaf-laws layer (`src/manuscript/sheaf/laws.py`) that proves the
presheaf/separation/gluing/typing/compositionality axioms over the IMRAD base poset with
negative-control tests; wire it into the strict compose/validation path and structural counts;
and rewrite the sheaf methods + appendix formalism to state precisely what is verified and what
is not — leaving the project green (≥153 tests) and the sheaf claim fully earned.

## Criteria

### Laws layer (code)
- [ ] ISC-1: `src/manuscript/sheaf/laws.py` exists and imports cleanly under `uv run python -c`.
- [ ] ISC-2: A `SheafLaw` enumeration names ≥5 laws (poset, presheaf/functoriality, separation, gluing, typing, compositionality).
- [ ] ISC-3: `verify_sheaf_laws(project_root)` returns a structured report with per-law pass/fail + counter-examples.
- [ ] ISC-4: **Base poset** law — IMRAD block order is a total order and group⊒section containment holds; verified.
- [ ] ISC-5: **Presheaf/functoriality** law — every composing section's track-set ⊆ registry; track order is the monotone restriction of the global registry order; no duplicate registry orders.
- [ ] ISC-6: **Separation** law — section→output_name is injective over composing sections (unique global section).
- [ ] ISC-7: **Gluing** law — manifest compose order is a linear extension of the base poset; composing-section set == written-file set; each composing section appears exactly once.
- [ ] ISC-8: **Typing** law — every binding (track,path) is well-typed (renderer exists; suffix ∈ renderer suffixes; generated renderers explicitly type-exempt), error-level.
- [ ] ISC-9: **Compositionality** law — `compose(subset)` body equals the corresponding slice of `compose(all)` (coproduct/monoidal independence), verified on a real subset.
- [ ] ISC-10: `verify_sheaf_laws` on the LIVE project returns all-pass (0 violations).

### Validation wiring + operation
- [ ] ISC-11: Laws surfaced through a public API in `src/manuscript/sheaf/__init__.py`.
- [ ] ISC-12: Strict validation/compose path (`validate_manifest`/CLI `--validate-only --strict`) reports law violations as errors.
- [ ] ISC-13: `compose_manuscript.py --validate-only --strict` still exits 0 on the live manifest.
- [ ] ISC-14: A gate function (in `src/gates/` or laws module) exposes the laws to the pipeline validation surface.
- [ ] ISC-15: Structural counts expose `sheaf_law_count` (and laws-verified signal) via `counts.py`.

### Tests + negative controls
- [ ] ISC-16: `tests/test_sheaf_laws.py` exists; positive test asserts live project all-pass.
- [ ] ISC-17: Negative control — break **separation** (two sections → same output_name) ⇒ caught.
- [ ] ISC-18: Negative control — break **typing** (bind .txt to markdown renderer) ⇒ caught.
- [ ] ISC-19: Negative control — break **gluing/poset** (non-linear-extension order) ⇒ caught.
- [ ] ISC-20: Negative control — break **presheaf** (section binds unknown track / duplicate order) ⇒ caught.
- [ ] ISC-21: Negative control — break **compositionality** assumption ⇒ caught (or proven structurally impossible with a test asserting the coproduct identity).
- [ ] ISC-22: Anti: no test uses MagicMock/mocker/unittest.mock (No-Mocks policy).
- [ ] ISC-23: New module reaches project coverage floor (no coverage regression below 90% on src).

### Manuscript (methods + appendix)
- [ ] ISC-24: `08_methods_sheaf.md` formalism states the base poset $P$, the presheaf $\mathcal{F}$, restriction maps, and names the verified laws.
- [ ] ISC-25: `08_methods_sheaf.md` states separation + gluing conditions in precise prose, citing the oracle (`verify_sheaf_laws` / tests).
- [ ] ISC-26: A typing judgment is stated (track→renderer→accepted-fragment-type) in the methods section.
- [ ] ISC-27: An explicit **honesty note** declares what is NOT claimed (no cohomology; finite-base coverage sheaf).
- [ ] ISC-28: Appendix formalism (`appendix_full_sheaf/formalism.md`) extended with the law-verification statement, no hand-typed counts (uses `{{...}}` variables).
- [ ] ISC-29: Any new manuscript count uses a `{{variable}}` resolved by `counts.py` — no hardcoded numbers.
- [ ] ISC-30: Manuscript composes cleanly: `compose_manuscript.py` regenerates `08_methods_sheaf.md` without error and the new prose appears.

### Documentation + total-integrity exemplar surface
- [ ] ISC-31: `src/manuscript/sheaf/README.md` documents the laws layer and how to run the oracle.
- [ ] ISC-32: `src/manuscript/sheaf/AGENTS.md` references the laws module + negative-control discipline.
- [ ] ISC-33: The sheaf prose fragment / coverage doc explains the laws to a reader (validation operation documented).

### Integrity gates (anti-criteria + verification)
- [ ] ISC-34: Anti: NO status-report-without-edits — every deliverable produces a concrete on-disk change (the dominant prior failure).
- [ ] ISC-35: Anti: NO over-claim — manuscript does not assert any law the oracle does not actually check (RedTeam-verified).
- [ ] ISC-36: Anti: baseline not regressed — full `pytest tests/` ≥153 pass, exit 0 after all edits.
- [ ] ISC-37: Anti: no hardcoded counts introduced into manuscript prose.
- [ ] ISC-38: Advisor invoked against final artifact set (HARD at E4).
- [ ] ISC-39: Cross-vendor audit (Forge read-only) returns no unaddressed CRITICAL on laws/manuscript honesty.
- [ ] ISC-40: Cato cross-vendor audit attempted (E4 mandatory); verdict combined per truth-table.
- [ ] ISC-41: `ruff` + `mypy` clean on the new module (CI parity).

## Test Strategy

| isc | type | check | threshold | tool |
|-----|------|-------|-----------|------|
| ISC-1 | import | module imports | no error | `uv run python -c` |
| ISC-10 | oracle | live laws all-pass | 0 violations | `uv run python -c verify_sheaf_laws` |
| ISC-13 | gate | strict compose exits 0 | rc==0 | `compose_manuscript.py --validate-only --strict` |
| ISC-16..21 | test | pytest law tests + neg controls | all pass | `uv run pytest tests/test_sheaf_laws.py` |
| ISC-22 | grep | no mock imports | 0 matches | `grep -rn mock tests/test_sheaf_laws.py` |
| ISC-24..30 | read | prose contains required statements | present | `Read`/`grep` composed output |
| ISC-36 | suite | full baseline | ≥153 pass | `uv run pytest tests/` |
| ISC-41 | lint | ruff+mypy clean | 0 errors | `uvx ruff check`, `uv run mypy` |
| ISC-38..40 | audit | advisor + Forge + Cato | no unaddressed critical | Inference.ts / Agent |

## Features

| name | satisfies | depends_on | parallelizable |
|------|-----------|------------|----------------|
| laws-module | ISC-1..10 | ground-truth | no (core) |
| validation-wiring | ISC-11..15 | laws-module | no |
| law-tests-negctl | ISC-16..23 | laws-module | partly |
| manuscript-formalism | ISC-24..30 | laws-module | yes (after API stable) |
| docs-exemplar | ISC-31..33 | laws-module | yes |
| integrity-audit | ISC-34..41 | all above | no (final) |

## Decisions

- 2026-05-28: Tier set E4 not E5 — E5 mandates an Interview workflow before BUILD; given the
  documented prior-failure pattern ("re-ask/report instead of work"), an interactive interview
  gate would read as stalling. E4 gives HARD advisor + Cato + ≥6 thinking floor + all-twelve
  sections, which is the rigor the task needs. `effort_source: context-override`.
- 2026-05-28: ISA written directly (not via ISA-skill subprocess) per doctrine's standing
  allowance ("model uses Read/Edit/Write and invokes ISA workflows directly" until CLI lands) —
  preserves momentum, the #1 lesson from failure history.
- 2026-05-28: Typing strengthened as an *additive error-level law* under strict, NOT by mutating
  the existing `warn`-level `renderer_suffix_mismatch` — avoids churn-fighting and keeps back-compat.
- 2026-05-28: Delegation floor (E4 soft ≥2) met by Forge + Cato in VERIFY (read-only, since
  subagent Write is denied here). Authoring is single-author by necessity (template repo blocks
  subagent Edit/Write) — show-your-math: a producer agent would be denied on disk, so producing
  code via Forge would waste a fan-out; Forge's value here is the cross-vendor audit.

## Changelog

(appended at LEARN)

## Verification

(appended at EXECUTE/VERIFY with quoted artifact tokens)
