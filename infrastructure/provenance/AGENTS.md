# `infrastructure/provenance/` — Provenance DAG (PROVENANCE-1)

## Purpose

Records the **live lineage** of research sessions as a content-addressed DAG:
which tools ran, which artifacts they produced, which sources were consulted,
and which claims were verified or refuted.

This module complements the static `evidence_graph` (pipeline-DAG snapshot)
and `evidence_registry` (manuscript-facing claim ledger) by capturing dynamic
session provenance with full transitive lineage queries.

## Files

| File | Role |
|---|---|
| `models.py` | Typed dataclasses: `NodeKind`, `EdgeRelation`, `ArtifactNode`, `RunNode`, `SourceNode`, `ClaimNode`, `Edge` |
| `store.py` | Content-addressed JSON store; `Provenance` namespace with `record`, `link`, `get`, `query`, `list`, `clear`, `path` |
| `review.py` | Reviewer finding system; `Review` namespace with `record`, `findings_for_node` |
| `validation.py` | DAG structural and topological validator (`ProvenanceValidationReport`, `validate_provenance_dag`) |
| `cli.py` | CLI commands: `record-artifact`, `list`, `review`, `validate` |
| `__main__.py` | `python -m infrastructure.provenance` entry point |

## Architecture

### Content addressing

`content_id(payload)` = first 32 hex characters of SHA-256 of the JSON-
serialised payload with sorted keys. Two calls with semantically identical
dicts always return the same id, enabling automatic deduplication.

### Store layout

The store is a single JSON file:

```json
{
  "nodes": [ { "node_id": "<id>", "kind": "...", "label": "..." } ],
  "edges": [ { "from_id": "...", "to_id": "...", "relation": "..." } ]
}
```

Writes are atomic (write-temp + `os.replace`).
Existing stores are validated before use. Invalid JSON, malformed nodes or
edges, and unknown enum values raise `ProvenanceStoreError`; the CLI reports
that error and exits non-zero instead of treating the store as empty.

### Node kinds

| Kind | Class | Key fields |
|---|---|---|
| `artifact` | `ArtifactNode` | `path`, `content_hash`, `size`, `artifact_type` |
| `run` | `RunNode` | `tool`, `session_id`, `inputs`, `status` |
| `source` | `SourceNode` | `uri`, `source_type` |
| `claim` | `ClaimNode` | `claim_text`, `severity`, `evidence` |

### Edge relations

`derived_from`, `produced_by`, `cites`, `supports`, `contradicts`, `depends_on`,
`versioned_from`

## Store path

The core store has no implicit environment-variable resolution:

1. `Provenance.with_path(p)` — explicit directory override (useful in tests).
2. `Provenance(path)` — explicit backing-file path.
3. The CLI defaults to `output/provenance/dag.json` relative to cwd.

`ProvenanceConfig` can supply a project-specific output directory, but callers
must resolve that configuration and pass the resulting path to the store.

## Boundaries

- The provenance store is append-oriented and records *events*; it does not
  replace the static `evidence_graph` or `evidence_registry`.
- Do not read or write project manuscript files from this module.
- Keep this module free of optional heavy dependencies (no pandas, numpy, etc.).

## CLI

```bash
# Record an artifact
python -m infrastructure.provenance record-artifact "model.pkl" --path output/model.pkl

# List all nodes
python -m infrastructure.provenance list

# Record a reviewer finding
python -m infrastructure.provenance review

# Validate DAG structure and acyclicity
python -m infrastructure.provenance validate --json
```

## Tests

```bash
uv run pytest tests/infra_tests/provenance -q
```

## See Also

- [`README.md`](README.md)
- [`../reporting/AGENTS.md`](../reporting/AGENTS.md) — static evidence graph
- [`../validation/AGENTS.md`](../validation/AGENTS.md) — evidence registry
- [`../core/pipeline/AGENTS.md`](../core/pipeline/AGENTS.md) — artifact manifests
