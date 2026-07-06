# Provenance DAG — `infrastructure/provenance/`

Content-addressed provenance DAG for the template research infrastructure.
Records the live lineage of research sessions: runs, artifacts, sources, and
reviewer findings.

## Installation

No extra dependencies — uses Python stdlib only (`hashlib`, `json`, `os`,
`pathlib`, `dataclasses`, `enum`).

## Quick start

```python
from infrastructure.provenance import (
    Provenance, RunNode, ArtifactNode, Edge, EdgeRelation, NodeKind
)

# Record a run
run = Provenance.record(
    RunNode(id="", kind=NodeKind.RUN, label="train model", tool="scripts/train.py")
)

# Record the artifact it produced
artifact = Provenance.record(
    ArtifactNode(id="", kind=NodeKind.ARTIFACT, label="model.pkl",
                 path="output/model.pkl", artifact_type="model")
)

# Link them
Provenance.link(Edge(from_id=run.id, to_id=artifact.id,
                     relation=EdgeRelation.PRODUCED))

# Transitive lineage query
nodes, edges = Provenance.query(artifact.id)
```

## Store configuration

| Priority | Source |
|---|---|
| 1 | `Provenance.with_path(path)` |
| 2 | `TEMPLATE_PROVENANCE_PATH` env var |
| 3 | `.provenance/graph.json` (cwd-relative default) |

## Node kinds

| Kind | Description |
|---|---|
| `artifact` | A file or dataset (model, figure, dataset, report) |
| `run` | A tool/script execution |
| `source` | An external source (paper, URL, database) |
| `claim` | A verifiable claim or reviewer finding |

## Edge relations

| Relation | Meaning |
|---|---|
| `produced` | Run → Artifact it emitted |
| `consumed` | Run → Artifact it read |
| `derived-from` | Artifact → Artifact it was derived from |
| `supports` | Evidence node → Claim it supports |
| `refutes` | Reviewer finding → Claim it disputes |

## Review system

```python
from infrastructure.provenance import Review, Finding, Severity

result = Review.record(
    target=artifact.id,
    finding=Finding(
        claim="Table 3, row 2",
        issue="p-value 0.048 does not match replication (0.061)",
        severity=Severity.MAJOR,
        evidence="output/replication/stats.json:42",
    ),
    reviewer="agent-qa",
)

# Query all findings
findings = Review.findings_for_node(artifact.id)
```

## CLI

```bash
# Record nodes
python -m infrastructure.provenance record run "fit model" --tool train.py
python -m infrastructure.provenance record artifact "model.pkl" --path output/model.pkl

# Link nodes
python -m infrastructure.provenance link <from_id> <to_id> produced

# Query
python -m infrastructure.provenance query              # full graph
python -m infrastructure.provenance query <id>         # lineage of one node
python -m infrastructure.provenance list               # all nodes

# Review
python -m infrastructure.provenance review <target_id> "claim" "issue" major "evidence"
python -m infrastructure.provenance review <target_id> "claim" "verified" info "evidence" --verdict supports
```

## Design notes

- **Content addressing**: `content_id(payload)` = 16-hex-char SHA-256 prefix
  of JSON-serialised payload with sorted keys.  Same inputs → same id,
  enabling deduplication.
- **Atomic writes**: every store write uses write-temp + `os.replace`.
- **BFS lineage**: `Provenance.query(id)` returns the connected component
  (traversing edges in both directions) for full transitive lineage.
- **No mocks needed in tests**: use `Provenance.with_path(tmp_path / "g.json")`.

## Tests

```bash
uv run pytest tests/infra_tests/provenance -q
```

## See Also

- `infrastructure/reporting/evidence_graph.py` — static pipeline DAG snapshot
- `infrastructure/validation/evidence_registry.py` — manuscript-facing claim ledger
- `infrastructure/core/pipeline/artifacts.py` — SHA-256 artifact manifests
