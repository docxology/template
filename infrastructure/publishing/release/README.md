# Release receipts, pairing, and workflow

Deterministic receipts for every release-plumbing command, structural
GitHub-Zenodo pairing validation, and the unified release workflow.

```python
from infrastructure.publishing.release import release_receipts, release_workflow

receipt = release_receipts.build_release_metadata_receipt(...)
result = release_workflow.run_release_workflow(...)
```

Import the nested `release.*` modules directly; the flat module paths have
been removed. See [`AGENTS.md`](AGENTS.md) for the module
graph and invariants.
