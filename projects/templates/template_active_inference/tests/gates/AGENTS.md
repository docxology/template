# Gate Test Notes

Every gate in [`src/gates/`](../../src/gates/AGENTS.md) needs a paired negative
control here: construct a deliberately bad artifact and assert the gate fails
closed. A test that only exercises the happy path does not prove the gate works.

| Test module | Covers |
| --- | --- |
| [`test_claim_ledger.py`](test_claim_ledger.py) | `validate_manuscript` claim-ledger checks (missing file, invalid ledger) |
| [`test_manuscript_gates.py`](test_manuscript_gates.py) | `validate_manuscript` token/marker/hydration contracts |
| [`test_output_gates.py`](test_output_gates.py) | `validate_outputs` artifact existence and concordance checks |

Restore any artifact you mutate (back up, then write back in a `finally`) so the
test leaves the working tree unchanged.
