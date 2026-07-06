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
| `src/expand.py` | Deterministic grammar expansion: `expand()`, `enumerate_all()`, `sample()`, `derive_seed()` |
| `src/figures.py` | Figure rendering: `render_primitive_figure()`, `build_figure_registry()` |
| `src/grammar.py` | Grammar parsing: `parse_grammar()`, `load_grammar()`, `force_domain()` |
| `src/honesty.py` | Honesty manifest: `build_manifest()`, `verify_honesty()`, `STRUCTURAL_EVIDENCE` |
| `src/integrity.py` | Integrity hashing: `sha256_text()`, `sha256_bytes()`, `tree_hash_from_content_hashes()`, `merkle_root()` |
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
uv run python scripts/realize_archetypes.py
uv run python scripts/realize_child_full.py
uv run python scripts/01_generate_manuscript_assets.py
uv run python scripts/generate_cover_art.py
uv run python scripts/z_generate_manuscript_variables.py
```

```bash
# From repo root
uv run pytest projects/templates/template_autopoiesis/tests/ --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90 -q
```

---

## Test Files

| Test file | Count | What it covers |
|---|---|---|
| `test_grammar_and_expand.py` | ~55 | Grammar parsing, slot validation, product sizes, expand, enumerate_all, sample, derive_seed |
| `test_materialize.py` | ~18 | Materialize structure, byte stability, tree hash, clean=True, provenance format |
| `test_integrity_and_verify.py` | ~32 | sha256_text/bytes, tree_hash, merkle_root, verify on clean/tampered/missing/added |
| `test_primitives_dynamics.py` | ~12 | damped_oscillator known output, envelope bound, negative control, PRIMITIVES |
| `test_primitives_graph.py` | ~14 | bfs_distances exact distances, pagerank sum-to-one, negative control, PRIMITIVES |
| `test_primitives_optimization.py` | ~12 | gradient_descent convergence, trajectory shape, analytic_minimizer, negative control |
| `test_primitives_signal.py` | ~14 | dft Parseval, convolve lengths, smoothing, identity kernel negative control |
| `test_primitives_statistics.py` | ~10 | ols_fit recovers beta, R², shuffled negative control |
| `test_primitives_registry.py` | ~10 | collect_primitives returns all 5 domains, 8 total kernels |
| `test_manuscript_variables.py` | ~10 | DOMAIN_COUNT=5, EFFECTIVE_PRODUCT_SIZE=45, RESERVED_SLOT_COUNT=3, roundtrip |
| `test_cli.py` | ~14 | Parser commands, main expand/enumerate/sample/honesty |
| `test_cover_art.py` | ~25 | ring_root_angles, domain_root_indices, branch_segments, build_ring_geometry, render_cover |
| `test_deps_vendoring.py` | ~14 | vendor mode, seam file, infra seam test, _resolve_deps, materialize with deps |
| `test_figures.py` | ~11 | render_primitive_figure per domain, scalar fallback, figure_registry roundtrip |
| `test_honesty.py` | ~16 | build_manifest, verify_honesty, STRUCTURAL_EVIDENCE, AST inspection |
| `test_manuscript_mermaid.py` | ~7 | Reserved slot values not in Mermaid node labels |
| `test_meta_teeth.py` | ~20 | Parametrized: stub must fail gate, real primitive passes, negative controls discriminate |
| `test_sealing.py` | ~18 | qr_matrix, build_payload, build_pointer_payload, embed_semi_transparent |
| `test_seal_child.py` | ~8 | Child seal flow end-to-end, verify_seal |
| `test_realize.py` | ~18 | _project_slug, _gate_python, run_child_stage, run_analysis_stage, validate_child |
| `test_realize_pure.py` | ~7 | Pure unit tests for realize (no fixtures) |
| `test_property_invariants.py` | ~20 | Hypothesis: grammar product, expand determinism, double materialize, verify invariants |
| `test_stress_edge_cases.py` | ~27 | Single slot, zero options raises, boundary seeds, 1000-seed stress, Merkle invariants |
| `test_project_paths.py` | ~7 | project_output_dirs creates dirs, idempotent |

---

## Key Metadata

- **Coverage target**: 90% (`fail_under=90`)
- **Test count**: 422 tests (measured live by `measure_test_summary()`)
- **Coverage**: 90.62% (measured live — see `output/data/manuscript_variables.json`)
- **Grammar seed**: 42
- **Domains**: optimization, dynamics, statistics, signal, graph
- **Reserved slots**: figure_profile, qr_profile, integrity_profile
- **Schema version**: `autopoiesis/spec/1`
- **Provenance schema**: `autopoiesis/provenance/1`
