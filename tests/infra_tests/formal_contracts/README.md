# formal_contracts tests

Unit, negative-control, and property tests for the
[`infrastructure/formal_contracts`](../../../infrastructure/formal_contracts/)
manuscript-contract layer: typed blocks, evidence-tier policies, monoidal
composition, and the fail-closed checker with stable `FORMAL.*` diagnostics.

```bash
uv run pytest tests/infra_tests/formal_contracts -q
```

Technical details: [`AGENTS.md`](AGENTS.md).
