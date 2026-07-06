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
| `cli.py` | CLI commands: `record`, `link`, `query`, `list`, `review` |
| `__main__.py` | `python -m infrastructure.provenance` entry point |

## Architecture

### Content addressing

`content_id(payload)` = first 16 hex characters of SHA-256 of the JSON-
serialised payload with sorted keys. Two calls with semantically identical
dicts always return the same id, enabling automatic deduplication.

### Store layout

The store is a single JSON file:

```json
{
  "nodes": { "<id>": { ... node dict ... } },
  "edges": [ { "from_id": "...", "to_id": "...", "relation": "..." } ]
}
```

Writes are atomic (write-temp + `os.replace`).

### Node kinds

| Kind | Class | Key fields |
|---|---|---|
| `artifact` | `ArtifactNode` | `path`, `content_hash`, `size`, `artifact_type` |
| `run` | `RunNode` | `tool`, `session_id`, `inputs`, `status` |
| `source` | `SourceNode` | `uri`, `source_type` |
| `claim` | `ClaimNode` | `claim_text`, `severity`, `evidence` |

### Edge relations

`produced`, `consumed`, `derived-from`, `supports`, `refutes`

## Store path

Resolution order:

1. `Provenance.with_path(p)` — per-call override (useful in tests).
2. `TEMPLATE_PROVENANCE_PATH` environment variable.
3. Default: `.provenance/graph.json` relative to cwd.

## Boundaries

- The provenance store is append-oriented and records *events*; it does not
  replace the static `evidence_graph` or `evidence_registry`.
- Do not read or write project manuscript files from this module.
- Keep this module free of optional heavy dependencies (no pandas, numpy, etc.).

## CLI

```bash
# Record a run node
python -m infrastructure.provenance record run "train model" --tool train.py

# Record an artifact
python -m infrastructure.provenance record artifact "model.pkl" --path output/model.pkl

# Link them (produced edge)
python -m infrastructure.provenance link <run_id> <artifact_id> produced

# Query lineage
python -m infrastructure.provenance query <artifact_id>

# List all nodes
python -m infrastructure.provenance list

# Record a reviewer finding
python -m infrastructure.provenance review <target_id> "Table 3, row 2" \
    "p-value mismatch" major "output/stats.json:42"
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
