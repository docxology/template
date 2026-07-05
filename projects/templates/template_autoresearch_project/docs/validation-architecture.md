# Validation architecture

This exemplar's value is not that it runs green — it is that **its gates bind
truth**. A research-artifact pipeline is only trustworthy if a hollow, degraded,
or fabricated run is *caught*, not silently certified. This document describes the
veridicality gates, what each one binds, and — critically — what each one does
*not* claim. Every gate has a fault-injecting negative-control test that proves it
fails closed (`tests/test_gate_negative_controls.py`, `tests/test_gate_improvements.py`).

## The substance predicate (shared foundation)

`src/artifact_content.is_substantive_artifact(path)` is the single shared check
that distinguishes a real artifact from a hollow one. A file is substantive only
if it exists **and** carries non-trivial, parseable content:

- empty / whitespace-only → not substantive;
- `.csv` → must have a data row beyond the header;
- JSON (by suffix **or** by leading `{`/`[`) → must be an object/array with at
  least one *substantive value, checked recursively* — `{}`, `[]`, `{"x": null}`,
  `{"a": {"b": null}}`, `[{"k": null}]`, a bare `0`/`false`/`null`, and `NaN`/`Inf`
  all fail;
- otherwise (`.md`/`.txt`) → must contain non-whitespace text.

The claim, figure-quality, and benchmark gates all delegate to this predicate, so
"present" can never masquerade as "real".

## The gates

| Gate | Binds | Enforcement | Source |
| --- | --- | --- | --- |
| **Claim support** | a research question is `supported` only if its evidence file is *substantive* | per-claim flag, surfaced in readiness | `src/loop.build_claims` |
| **Figure quality** | a figure is `valid` only if its **source data artifact** is substantive (not just pixels non-uniform) | `valid` flag, all-figures gate | `src/figures/figure_quality.py` |
| **Benchmark readiness** | measured: core artifacts substantive **+ ≥1 supported claim whose evidence is substantive + ML accuracy improved over baseline** by a configurable threshold | score `< 1.0` ⇒ `incomplete` | `src/writers._grade_absent_benchmark` |
| **Schema conformance** | a tagged governance payload must satisfy its registered field/type contract | **HARD gate** — `write_schema_manifest` raises and aborts the loop on a nonconforming payload | `src/artifact_schemas` |
| **Local integrity** | a present-but-empty required file → fail; the input MNIST fixture is cross-checked against its **committed declared** `npz_sha256` (external truth) | `status: "failed"` on any empty/mismatch/missing-declared-hash | `src/security.integrity_attestation_payload` |
| **Evidence (default)** | a manuscript number that matches **no** generated artifact (fabrication) → error | pipeline "Evidence registry" check | `infrastructure/validation/evidence_registry` |
| **Output-path self-report** | `output_paths` lists only artifacts that actually exist (no overclaim) and covers the `required_artifacts` contract | derived, existence-filtered | `src/loop_phases.final_output_path_payload` |

## Configurability

The benchmark threshold and core-artifact set are config-driven via the optional
`grading:` block in `autoresearch.yaml`, with **loud rejection** of out-of-range
*and typo'd* keys (a silently-ignored knob is a dead knob). `metric_direction`
flips the improvement comparison. The effective threshold is recorded in the
grade payload so a lowered bar is visible in the audit trail.

## Deliberate boundaries (what these gates do NOT claim)

Honesty about scope is part of veridicality. The following are stated, not hidden:

- **Strict evidence tiers are opt-in, not default-enforced.** The evidence
  registry can require strict-zone manuscript numbers to trace to *trusted*
  source tiers (external/input/declared) via
  `validate_text_against_registry(..., trusted_number_tiers=...)`. But an
  AutoResearch manuscript legitimately *reports its own run's metrics* — the
  hydrated manuscript contains ~285 such strict-zone numbers — so forcing this on
  would reject the paper's own findings. The **default** gate already fails
  fabrication; the strict-tier check is for manuscripts that cite external
  numbers. The registry's `source_tiers` field discloses the provenance mix.
- **Local integrity is self-attestation within a local boundary**, plus the one
  external anchor (the committed fixture-provenance hash). It does not claim
  external signing, SLSA, or runtime monitoring.
- **The research-object manifest** is a path/size/checksum/empty inventory; it
  surfaces empty artifacts but is not a content validator.

## Testing philosophy: negative controls

Every gate ships with a test that **injects the fault and asserts the gate flips
red** — empty/garbage evidence, a hollow figure source, a missing/empty core
artifact, an unevaluated neural candidate, a tag-only schema payload, a tampered
fixture, a typo'd config key. A gate that has only ever been exercised on the
happy path is unproven; a passing test suite that cannot fail on a degraded run is
verification theater. Paired positive controls confirm the healthy run still
passes.

## Determinism

All computational artifacts (results, ledgers, confusion matrices, CSVs) and
rendered PNGs are byte-identical across runs. Figures pin `savefig` metadata
(`Software`/`Creation Time`/`Date` → `None`) so PNGs are reproducible across
machines, dates, and matplotlib versions, not just back-to-back on one host.
Inter-figure order independence is covered by
`tests/test_figures.py::test_isolated_equals_batch_no_order_leakage`.
