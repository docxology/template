# Private-project promotion

Composable, read-only promotion contracts for deciding whether a private
candidate is safe to route into the public template workflow. The package does
not authenticate, copy, publish, or mutate candidate content.

## Contracts

- `attestation.py` validates identity, authorization, redaction, storage,
  routing, MCP-boundary, and export-test evidence at a deterministic `as_of`.
- `security_gate.py` scans the candidate checkout and returns a typed gate
  report without exposing secrets.
- `composite.py` combines both reports into the final eligibility decision.
- `cli.py` retains the legacy positional form and adds explicit `attestation`
  and `candidate` commands.

```bash
uv run python -m infrastructure.project.promotion attestation promotion.yaml \
  --as-of 2026-07-20
uv run python -m infrastructure.project.promotion candidate \
  --project-root /path/to/private/candidate --attestation promotion-security.yaml \
  --as-of 2026-07-20 --json
```

See [`AGENTS.md`](AGENTS.md) for module ownership and compatibility guarantees.
