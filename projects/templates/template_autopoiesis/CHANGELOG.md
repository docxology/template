# CHANGELOG — template_autopoiesis

## Wave 9 — Deep Review Pass

### Closed

**A. Honesty manifest coverage**
- `STRUCTURAL_EVIDENCE` now covers all six key functions: `parse_grammar`, `expand`, `_digest_index`, `materialize`, `tree_hash_from_content_hashes`, `verify_child`, `collect_primitives`.
- `verify_honesty` scans manuscript for unsupported quantitative claims.
- `test_honesty.py` confirms all structural evidence passes on the live source AST.

**B. Reserved slot accounting**
- `generate_variables` now computes and surfaces `PRODUCT_SIZE`, `EFFECTIVE_PRODUCT_SIZE`, `RESERVED_SLOT_COUNT`, and `NOMINAL_OVER_EFFECTIVE` as manuscript tokens.
- The abstract explicitly reports the inflation factor.
- `test_manuscript_variables.py` asserts `EFFECTIVE_PRODUCT_SIZE == 45` and `RESERVED_SLOT_COUNT == 3`.

**C. Mutation meta-gate completeness**
- `test_meta_teeth.py` parametrized over all 5 `KNOWN_DOMAINS`:
  - Stub `run_analysis` (constant success=True) must fail the gate
  - Real primitive call must pass the gate
  - Negative controls produce distinguishable output
- Gate has teeth: four domain-specific keys checked.

**D. Verify tests completeness**
- `test_integrity_and_verify.py` covers: tampered file, missing file, missing provenance.json, `verify_child_full` schema version check, `verify_seal` with and without seal.json.
- All three failure modes (tamper/delete/add) are tested.

**E. Property invariants**
- `test_property_invariants.py` uses Hypothesis for:
  - Grammar product invariants across arbitrary seeds
  - Expand determinism across any seed in [0, 10^9]
  - Double materialize byte-stability per domain
  - Verify passes clean / fails tamper per domain
  - QR matrix square and deterministic for arbitrary text
- `test_stress_edge_cases.py` covers: single slot, zero options/slots raises, all-reserved effective product = 1, boundary seeds (0, MAX_INT, -1), 1000-seed stress, Merkle invariants.
