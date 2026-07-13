# Data

Committed, version-controlled inputs for the exemplar (no runtime downloads).

- `claim_ledger.yaml` — human-declared evidence links for policy constants and
  cited empirical values that cannot be derived by repository introspection.
  Live module, project, stage, and test counts are intentionally absent: the
  metrics generator re-derives those from the current tree.

See [`AGENTS.md`](AGENTS.md) for the ledger schema and the rule that only
project *inputs* — never pipeline outputs — belong in this directory.
