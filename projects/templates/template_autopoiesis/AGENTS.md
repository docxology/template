# AGENTS.md — template_autopoiesis

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md).

## Overview

`template_autopoiesis` is a combinatoric project generator. It uses a grammar to deterministically emit complete child projects from a seeded expansion. The architecture is: grammar → spec → materialize → verify → seal.

---

## Module Inventory (`src/`)

| Module | Role |
|---|---|
| `src/cli.py` | CLI entry point: `enumerate`, `expand`, `sample`, `materialize`, `verify`, `honesty` |
| `src/common.py` | Shared dataclasses: `CheckResult`, `CheckReport`, `trunc()` |
| `src/cover_art.py` | Ouroboros ring cover art: `render_cover()`, `branch_segments()`, `build_ring_geometry()` |
| `src/emit_templates.py` | `@@KEY@@`-templated child file bodies: template strings + substitution from a `Spec` |
| `src/expand.py` | Deterministic grammar expansion: `expand()`, `enumerate_all()`, `sample()`, `derive_seed()` |
| `src/figures.py` | Figure rendering: `render_primitive_figure()`, `build_figure_registry()` |
| `src/grammar.py` | Grammar parsing: `parse_grammar()`, `load_grammar()`, `force_domain()` |
| `src/honesty.py` | Honesty manifest: `build_manifest()`, `verify_honesty()`, `STRUCTURAL_EVIDENCE` |
| `src/integrity.py` | Integrity hashing: `sha256_text()`, `sha256_bytes()`, `tree_hash_from_content_hashes()`, `merkle_root()` |
| `src/manuscript_contract.py` | Phase 10 source contract: `validate_phase10_contract()` |
| `src/manuscript_figures.py` | Manuscript figure writers plus the label/filename provenance specs consumed by `output/figures/figure_registry.json` |
| `src/manuscript_variables.py` | Manuscript token generation: `generate_variables()`, `save_variables()` |
| `src/materialize.py` | Child project writer: `materialize()`, `child_name()`, `_build_tree()` |
| `src/primitives/__init__.py` | Registry: `collect_primitives()` |
| `src/primitives/base.py` | `PrimitiveSpec` dataclass |
| `src/primitives/dynamics.py` | Damped oscillator kernel |
| `src/primitives/graph.py` | BFS distances + PageRank kernels |
| `src/primitives/optimization.py` | Gradient descent + analytic minimizer kernels |
| `src/primitives/signal.py` | DFT + convolve_known kernels |
| `src/primitives/statistics.py` | OLS regression kernel |
| `src/project_paths.py` | Output directory helpers: `project_output_dirs()` |
| `src/realize.py` | Child pipeline orchestration: `run_child_stage()`, `run_analysis_stage()`, `validate_child()` |
| `src/sealing.py` | QR seal: `qr_matrix()`, `build_payload()`, `embed_semi_transparent()` |
| `src/verify.py` | Integrity verification: `verify_child()`, `verify_child_full()`, `verify_seal()` |

---

## Key Invariants

| Invariant | Where enforced |
|---|---|
| Slot selections are deterministic | `expand.py::_digest_index` uses SHA-256, no entropy |
| Tree hash is order-independent | `integrity.py::tree_hash_from_content_hashes` sorts paths |
| Reserved slots do not vary effective product | `grammar.py::effective_product_size` excludes RESERVED_SLOTS |
| Stub `run_analysis` must fail | `test_meta_teeth.py` parametrized over KNOWN_DOMAINS |
| Verify never trusts cached hash | `verify.py::verify_child` re-reads files from disk |
| Honesty manifest checks live AST | `honesty.py::build_manifest` inspects source at test time |

---

## Grammar Description

Defined in `manuscript/config.yaml` under `autopoiesis:`:
- `seed`: 42
- `slots`: primitive_domain (5), track (3), section_set (3), figure_profile (2, reserved), qr_profile (2, reserved), integrity_profile (2, reserved)
- Nominal product: 5×3×3×2×2×2 = 360
- Effective product: 5×3×3 = 45 (reserved slots excluded)
- Grammar hash: 16-char SHA-256 prefix of canonical JSON (re-derive from `load_grammar()` — do not hard-code)

---

## Drive Commands

```bash
# From project root
uv run python scripts/autopoiesis.py expand
uv run python scripts/autopoiesis.py materialize
uv run python scripts/autopoiesis.py verify output/children/child_DOMAIN_HASH
uv run python scripts/autopoiesis.py honesty
uv run python scripts/autopoiesis.py enumerate
uv run python scripts/autopoiesis.py sample --count 10
uv run python scripts/realize_archetypes.py
uv run python scripts/realize_child_full.py
uv run python scripts/01_generate_manuscript_assets.py
uv run python scripts/generate_cover_art.py
uv run python scripts/z_generate_manuscript_variables.py
```

`01_generate_manuscript_assets.py` requires the real per-module
`output/data/coverage_full.json`; it fails closed if that input or any of the
four referenced figures is missing, and writes the deterministic figure
registry only after the complete set exists.

```bash
# From repo root
uv run pytest projects/templates/template_autopoiesis/tests/ --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90 -q
```

---

## Test Files

The live suite count is measured by `pytest --collect-only` and published in
the generated repository snapshot [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md).
The detailed table below is a historical 2026-08-09 receipt for audit context,
not a current release claim; refresh the project measurement before citing it:

| Test file | Collected items | What it covers |
|---|---:|---|
| `test_cli.py` | 21 | Parser and CLI command behavior |
| `test_common.py` | 7 | `CheckResult`, `CheckReport`, `trunc()` |
| `test_cover_art.py` | 29 | Ring geometry, cover rendering, QR-seal branch |
| `test_deps_vendoring.py` | 16 | Vendor mode, seam file, dependency resolution |
| `test_emit_templates.py` | 32 | Child file templates and substitutions |
| `test_figures.py` | 23 | Primitive figure rendering and registry roundtrip |
| `test_grammar_and_expand.py` | 57 | Grammar parsing, expansion, enumeration, sampling |
| `test_honesty.py` | 17 | Honesty manifest and AST evidence |
| `test_integrity_and_verify.py` | 32 | Hashes, Merkle roots, verification and tamper cases |
| `test_manuscript_assets_script.py` | 3 | Asset generation and registry validation |
| `test_manuscript_figures.py` | 9 | Manuscript figure writers |
| `test_manuscript_mermaid.py` | 6 | Mermaid grammar rendering constraints |
| `test_manuscript_variables.py` | 14 | Derived manuscript tokens and measurements |
| `test_materialize.py` | 33 | Child tree structure, stability, provenance |
| `test_meta_teeth.py` | 20 | Stub rejection, real-kernel acceptance, controls |
| `test_primitives_dynamics.py` | 13 | Damped oscillator and controls |
| `test_primitives_graph.py` | 17 | BFS, PageRank, graph controls |
| `test_primitives_optimization.py` | 13 | Gradient descent, minimizer, controls |
| `test_primitives_registry.py` | 10 | Primitive registry completeness |
| `test_primitives_signal.py` | 17 | DFT, convolution, smoothing controls |
| `test_primitives_statistics.py` | 13 | OLS recovery, R², shuffled control |
| `test_project_paths.py` | 7 | Output directory helpers |
| `test_property_invariants.py` | 28 | Hypothesis determinism and integrity properties |
| `test_realize.py` | 16 | Child-stage orchestration and validation |
| `test_realize_pure.py` | 7 | Pure realization helpers |
| `test_seal_child.py` | 7 | End-to-end child sealing |
| `test_sealing.py` | 26 | Payloads, QR matrices, optional decode path |
| `test_stress_edge_cases.py` | 19 | Boundary seeds, Merkle and sampling stress |

---

## Key Metadata

- **Coverage target**: 90% (`fail_under=90`)
- **Test count**: measured live by `measure_test_summary()` — see `output/data/manuscript_variables.json` for the value at last render, and [`COUNTS.md`](../../../docs/_generated/COUNTS.md) for the regenerated repo-wide totals (the count drifts upward release to release as tests are added, so it is not pinned here)
- **Coverage**: measured live in `output/data/manuscript_variables.json`; use
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) for the
  current repo-wide snapshot.
- **Grammar seed**: 42
- **Domains**: optimization, dynamics, statistics, signal, graph
- **Reserved slots**: figure_profile, qr_profile, integrity_profile
- **Schema version**: `autopoiesis/spec/1`
- **Provenance schema**: `autopoiesis/provenance/1`
