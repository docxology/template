# Gate tests

Negative-control tests for the validation gates in
[`src/gates/`](../../src/gates/README.md). Each gate must be proven to reject a
bad artifact, not merely accept a good one.

- `test_claim_ledger.py` — claim-ledger gate rejects a missing/invalid ledger.
- `test_manuscript_gates.py` — manuscript gates reject missing tokens, markers, and hydration gaps.
- `test_output_gates.py` — output gates reject missing or inconsistent pipeline artifacts.
