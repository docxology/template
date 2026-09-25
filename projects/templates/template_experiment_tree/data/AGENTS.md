# data/ — agent notes

Layout map: one file, [claim_ledger.yaml](claim_ledger.yaml), binding each
public claim to the evidence paths that verify it. `manuscript/config.yaml`
consumes it; `src/template_experiment_tree/report.py` reads the tree, not
this directory.

Invariants: every `evidence` path must exist at HEAD; claims without a
matching answered tree node fail the variables generator. See
[../AGENTS.md](../AGENTS.md) for the tree-freeze invariant.

Verification: `uv run pytest tests/test_manuscript_variables.py` (from the
exemplar root) exercises the ledger → tree → token path.
