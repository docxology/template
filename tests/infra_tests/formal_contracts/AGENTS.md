# `tests/infra_tests/formal_contracts/` — agent guide

Tests for [`infrastructure/formal_contracts/`](../../../infrastructure/formal_contracts/) —
the typed, machine-checkable manuscript contract layer ("well-typed research" seed).

## Files

| File | Covers |
| --- | --- |
| `test_model.py` | Block dataclasses, `EvidenceTier` ordering, `DependencyEdge`/`MatchPolicy` invariants |
| `test_compose.py` | `compose`/`check_manuscript`: unique ids, resolvable edges, acyclicity, orphans; negative controls fail with their specific `FORMAL.*` diagnostic |
| `test_laws.py` | Monoidal composition laws (associativity, identity) via derandomized Hypothesis property tests |
| `test_reader.py` | Markdown fenced-div reader incl. 7 error paths |

## Conventions

- No mock frameworks; real objects and real temp files only.
- Every diagnostic has a proof-of-detection negative control — a check that
  only shows the happy path does not count as covered.
- Property tests are derandomized (fixed derandomize) so the suite stays
  deterministic in CI.

## Run

```bash
uv run pytest tests/infra_tests/formal_contracts -q
```

## See also

- [`../../../infrastructure/formal_contracts/AGENTS.md`](../../../infrastructure/formal_contracts/AGENTS.md)
- [`../AGENTS.md`](../AGENTS.md)
