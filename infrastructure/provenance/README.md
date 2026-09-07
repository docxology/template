# Provenance DAG — `infrastructure/provenance/`

Content-addressed provenance DAG for the template research infrastructure.
Records the live lineage of research sessions: runs, artifacts, sources, and
reviewer findings.

## Installation

No extra dependencies — uses Python stdlib only (`hashlib`, `json`, `os`,
`pathlib`, `dataclasses`, `enum`).

## Quick start

```python
from pathlib import Path
from infrastructure.provenance import (
    ArtifactNode,
    EdgeRelation,
    NodeKind,
    Provenance,
    RunNode,
)

# Initialize store
prov = Provenance.with_path(Path("output/provenance"))

# Record a run
run = RunNode.create("train model", command="python scripts/train.py")
prov.record(run)

# Record the artifact it produced
artifact = ArtifactNode.create("model.pkl", path="output/model.pkl")
prov.record(artifact)

# Link them
prov.link(run.node_id, artifact.node_id, EdgeRelation.produced_by)

# Query
edges = prov.query(from_id=run.node_id)
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

## Review and Validation system

```python
from infrastructure.provenance import review_provenance_store, validate_provenance_dag

# Review standard node attributes
review_result = review_provenance_store(prov)
print("Review passed:", review_result.passed)

# Validate graph structural integrity & acyclicity
validation_report = validate_provenance_dag(prov)
print("DAG is valid:", validation_report.is_valid)
```

## CLI

```bash
# Record artifact
python -m infrastructure.provenance record-artifact "model.pkl" --path output/model.pkl

# List nodes
python -m infrastructure.provenance list
python -m infrastructure.provenance list --kind artifact --json

# Review node quality
python -m infrastructure.provenance review

# Validate DAG structure & acyclicity
python -m infrastructure.provenance validate --json
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
- `infrastructure/core/pipeline/artifacts/` — SHA-256 artifact manifests ([`AGENTS.md`](../core/pipeline/artifacts/AGENTS.md))
