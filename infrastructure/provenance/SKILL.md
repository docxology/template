---
name: provenance-dag
description: >
  Content-addressed provenance DAG for research lineage tracking.
  Use for: recording which pipeline stage produced which artifact,
  querying edges between recorded nodes, running a DAG-wide review pass.
  CLI: python -m infrastructure.provenance {list,record-artifact,review}.
  Library: infrastructure.provenance.Provenance (record/link/get/list/query).
  Orchestrator: scripts/pipeline/stage_09_provenance_record.py --project {name} --stage NAME
---

# Provenance DAG

Content-addressed provenance DAG for tracking research artifact lineage.
Every artifact node is identified by a SHA-256 content hash; edges record
which pipeline stage produced each artifact from which inputs.

## Quick Start

```python
from infrastructure.provenance import ArtifactNode, EdgeRelation, Provenance, RunNode

store = Provenance.with_path("output/.provenance")

# Record that a run produced an artifact
run = RunNode.create("analysis run", command="uv run python 02_run_analysis.py")
artifact = ArtifactNode.create("results.json", path="output/results.json")
store.record(run)
store.record(artifact)

# Link the artifact to the run that produced it
store.link(run.node_id, artifact.node_id, EdgeRelation.produced_by)
```

## CLI

```bash
# Record an artifact node
uv run python -m infrastructure.provenance record-artifact "results.json" --path output/results.json

# List all recorded nodes (optionally filter by kind: artifact/run/source/claim)
uv run python -m infrastructure.provenance list --kind artifact

# Run the DAG-wide review pass (missing hashes, missing exit codes, etc.)
uv run python -m infrastructure.provenance review --json
```

There is no `link` or `query` CLI subcommand — those are library-only
(`Provenance.link()` / `Provenance.query()`); the CLI only exposes
`list`, `record-artifact`, and `review`.

## Pipeline Orchestrator

```bash
# Record provenance for a named project and pipeline stage
uv run python scripts/pipeline/stage_09_provenance_record.py --project my_project --stage analysis

# Record with explicit input/output glob patterns and a custom store path
uv run python scripts/pipeline/stage_09_provenance_record.py \
    --project my_project \
    --stage render \
    --outputs "output/*.pdf" \
    --store-path output/.provenance/dag.json
```

There is no `projects/{name}/manuscript/config.yaml` `provenance:` block —
config-driven provenance is not implemented; every run is parameterized via
CLI flags on the stage script above.

## Key Types

```python
from infrastructure.provenance import (
    Provenance,        # Main interface — record / link / get / list / query
    ArtifactNode,       # File/dataset node: .path, .content_hash, .size_bytes
    RunNode,            # Pipeline-run node: .command, .exit_code, .duration_seconds
    SourceNode,         # External-source node
    ClaimNode,          # Scientific-claim node
    Edge,               # Directed edge between two node ids: .from_id, .to_id, .relation
    EdgeRelation,       # Enum of edge relations (e.g. produced_by)
)
```

## Content Addressing

Every node id is a SHA-256 hash derived from its kind + identifying fields
(e.g. an `ArtifactNode`'s id is derived from its label + path):

```python
artifact = ArtifactNode.create("results.json", path="output/results.json", content_hash="sha256:abc123...")
print(artifact.node_id)       # deterministic id derived from label + path
print(artifact.content_hash)  # "sha256:abc123..." (caller-supplied, not computed by create())
```

Recording the same node id twice is idempotent — `record()` only sets
`created_at` and persists on first insert.

## Ancestry Tracing

`query()` filters **edges**, not nodes — it does not resolve a path to its
ancestors directly:

```python
edges = store.query(to_id=artifact.node_id)
for edge in edges:
    producer = store.get(edge.from_id)
    print(f"  {producer.label} --{edge.relation.value}--> {artifact.label}")
```

## Review Pass

There is no per-node `store.review(...)` method — review is a whole-store
audit function that flags missing hashes, missing exit codes, empty claim
confidence, and empty source URIs:

```python
from infrastructure.provenance import review_provenance_store

result = review_provenance_store(store)
for finding in result.findings:
    print(finding.severity.value, finding.code, finding.message)
```

## Testing

```bash
uv run pytest tests/infra_tests/provenance/ -v
```

## See Also

- [`AGENTS.md`](AGENTS.md) — operating contract and architecture
- [`../search/SKILL.md`](../search/SKILL.md) — search module skill
- [`../core/pipeline/AGENTS.md`](../core/pipeline/AGENTS.md) — pipeline integration
