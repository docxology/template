---
name: provenance-dag
description: >
  Content-addressed provenance DAG for research lineage tracking.
  Use for: recording which pipeline stage produced which artifact,
  tracing artifact ancestry, recording reviewer findings.
  CLI: python -m infrastructure.provenance {record,link,query,list,review}.
  Config: set in projects/{name}/manuscript/config.yaml `provenance:` block.
  Orchestrator: scripts/09_provenance_record.py --project {name} --stage NAME
---

# Provenance DAG

Content-addressed provenance DAG for tracking research artifact lineage.
Every artifact node is identified by a SHA-256 content hash; edges record
which pipeline stage produced each artifact from which inputs.

## Quick Start

```python
from infrastructure.provenance import ProvenanceStore

store = ProvenanceStore("output/.provenance")

# Record that stage "analysis" produced "results.json"
node_id = store.record(
    artifact_path="output/results.json",
    stage="analysis",
    metadata={"script": "02_run_analysis.py"},
)

# Link a downstream artifact to its source
store.link(source_id=node_id, target_path="output/manuscript.pdf", stage="render")
```

## CLI

```bash
# Record an artifact
uv run python -m infrastructure.provenance record output/results.json --stage analysis

# Link two artifacts
uv run python -m infrastructure.provenance link <source-id> output/manuscript.pdf --stage render

# Query ancestry of an artifact
uv run python -m infrastructure.provenance query output/manuscript.pdf

# List all recorded artifacts
uv run python -m infrastructure.provenance list

# Record a reviewer finding against an artifact
uv run python -m infrastructure.provenance review <artifact-id> --note "Needs citation"
```

## Pipeline Orchestrator

```bash
# Record provenance for a named project and pipeline stage
uv run python scripts/09_provenance_record.py --project my_project --stage analysis

# Record with custom artifact paths
uv run python scripts/09_provenance_record.py \
    --project my_project \
    --stage render \
    --artifacts output/manuscript.pdf
```

## Config Integration

Set provenance options in `projects/{name}/manuscript/config.yaml`:

```yaml
provenance:
  store_dir: output/.provenance
  record_stages:
    - analysis
    - render
    - validate
  auto_link: true
```

## Key Types

```python
from infrastructure.provenance import (
    ProvenanceStore,   # Main interface — record / link / query / list / review
    ProvenanceNode,    # Immutable artifact record with SHA-256 content address
    ProvenanceEdge,    # Directed stage edge between two nodes
    ReviewRecord,      # Reviewer finding attached to an artifact node
)
```

## Content Addressing

Every artifact is stored by SHA-256 hash of its content:

```python
node = store.record("output/results.json", stage="analysis")
print(node.content_hash)   # "sha256:abc123..."
print(node.artifact_path)  # resolved absolute path at record time
```

Re-recording the same unchanged file is idempotent — the same node is
returned. A changed file produces a new node, preserving the full history.

## Ancestry Tracing

```python
ancestors = store.query("output/manuscript.pdf")
for node in ancestors:
    print(f"  {node.stage} → {node.artifact_path} ({node.content_hash[:12]})")
```

## Reviewer Findings

```python
store.review(node_id, note="Missing error bars in Fig 3", reviewer="LLM-review")
findings = store.list_reviews(node_id)
```

## Testing

```bash
uv run pytest tests/infra_tests/provenance/ -v
```

## See Also

- [`AGENTS.md`](AGENTS.md) — operating contract and architecture
- [`../search/SKILL.md`](../search/SKILL.md) — search module skill
- [`../core/pipeline/AGENTS.md`](../core/pipeline/AGENTS.md) — pipeline integration
