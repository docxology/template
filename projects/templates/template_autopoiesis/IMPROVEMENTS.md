# IMPROVEMENTS.md — template_autopoiesis

All improvement items A–E are **resolved and closed** as of Wave 9.

---

## A — Honesty manifest coverage ✅ CLOSED

**Problem:** `STRUCTURAL_EVIDENCE` only covered a subset of claimed functions.
**Resolution:** All six key functions (`parse_grammar`, `expand`, `_digest_index`, `materialize`, `tree_hash_from_content_hashes`, `verify_child`, `collect_primitives`) are now in `STRUCTURAL_EVIDENCE`. Tests confirm all pass on live AST.

---

## B — Reserved slot accounting ✅ CLOSED

**Problem:** The nominal product size was reported without the effective size or inflation factor.
**Resolution:** `generate_variables` now emits `PRODUCT_SIZE`, `EFFECTIVE_PRODUCT_SIZE`, `RESERVED_SLOT_COUNT`, and `NOMINAL_OVER_EFFECTIVE`. The abstract uses these tokens. `test_manuscript_variables.py` asserts exact values.

---

## C — Mutation meta-gate completeness ✅ CLOSED

**Problem:** `test_meta_teeth.py` was not parametrized over all domains; the gate logic needed sharpening.
**Resolution:** Fully parametrized over all 5 `KNOWN_DOMAINS`. Three tests per domain: stub fails gate, real primitive passes gate, negative controls produce distinguishable output.

---

## D — Verify test coverage ✅ CLOSED

**Problem:** Only happy-path verify tests existed; tamper/delete/missing-provenance cases were not covered.
**Resolution:** `test_integrity_and_verify.py` now covers all three failure modes (tamper, delete, missing provenance), `verify_child_full` schema version check, and `verify_seal` with and without seal.json.

---

## E — Property-based and stress testing ✅ CLOSED

**Problem:** No Hypothesis tests; edge cases (boundary seeds, all-reserved, zero options) were untested.
**Resolution:** `test_property_invariants.py` (Hypothesis) and `test_stress_edge_cases.py` (27 stress/edge tests) added. All pass.
