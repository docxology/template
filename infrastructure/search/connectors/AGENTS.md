# `infrastructure/search/connectors/`

Agent guide for the ConnectorRegistry subpackage.

## Purpose

Provides a uniform Python connector interface to ~8 major science databases,
ported from the OpenScience TypeScript project
(https://github.com/synthetic-sciences/openscience).

Each connector satisfies the `Connector` protocol and is registered in an
ordered `ConnectorRegistry` that supports domain filtering and serialisable
catalog output.

## Module map

| File | Role |
|---|---|
| `types.py` | `ConnectorDomain` (StrEnum), `ConnectorHit`, `CatalogEntry`, `SearchOptions`, `FetchOptions`, `Connector` (Protocol), `ConnectorError` |
| `registry.py` | `ConnectorRegistry` — ordered registration, lookup, domain filtering, and catalog output |
| `http.py` | `ConnectorHttpClient` — stdlib urllib with retry, TTL cache, User-Agent |
| `stage.py` | Stage 08 config validation, dispatch, failure isolation, and report serialization |
| `cli.py` | `list-dbs` and `search` subcommands |
| `impl/openalex.py` | OpenAlex works (literature) |
| `impl/arxiv.py` | arXiv Atom API (literature) |
| `impl/semantic_scholar.py` | Semantic Scholar graph API (literature) |
| `impl/crossref.py` | CrossRef REST API (literature) |
| `impl/europepmc.py` | Europe PMC REST API (biology) |
| `impl/biorxiv.py` | bioRxiv content API (biology) |
| `impl/uniprot.py` | UniProtKB search API (proteomics) |
| `impl/pdb.py` | RCSB PDB search + data API (structure) |
| `impl/__init__.py` | Re-exports all instances; `_ALL_CONNECTORS` list |

## Usage

```python
from infrastructure.search.connectors import (
    ConnectorDomain, ConnectorRegistry, _ALL_CONNECTORS, SearchOptions
)

registry = ConnectorRegistry()
for connector_class in _ALL_CONNECTORS:
    registry.register(connector_class())

# List all biology connectors
bio = registry.by_domain(ConnectorDomain.biology)

# Search
hits = registry.get("arxiv").search("attention mechanism", SearchOptions(max_results=5))

# Convenience helpers (default registry)
from infrastructure.search.connectors import list_connectors, search_connector
catalog = list_connectors()
hits = search_connector("openalex", "CRISPR", max_results=3)
```

## CLI

```bash
uv run python -m infrastructure.search.connectors list-dbs
uv run python -m infrastructure.search.connectors search arxiv "active inference" --max-results 5
```

## Testing

```bash
uv run pytest tests/infra_tests/search/test_connectors.py -v
```

No mocks allowed. HTTP connectors tested via `pytest-httpserver`.

## Invariants

- Each connector id is unique (registry raises `ValueError` on duplicate).
- `ConnectorRegistry.catalog()` returns only serialisable `CatalogEntry` objects — no callables.
- `ConnectorHttpClient` uses stdlib `urllib` only — zero extra dependencies.
- `SearchOptions.max_results` defaults to 10; Stage 08 rejects non-positive caps.
- Per-connector errors raise `ConnectorError` — callers decide whether to surface or absorb.
- Stage 08 persists one status record per connector/query pair and exits 1 when any configured search fails.

## Adding a connector

1. Create `impl/mydb.py` with a class implementing the `Connector` protocol.
2. Export an instance: `mydb: Connector = _MyDBConnector()`.
3. Add to `impl/__init__.py`: import + append to `_ALL_CONNECTORS`.
4. Add tests to `tests/infra_tests/search/test_connectors.py` using `pytest-httpserver`.

## See also

- [`README.md`](README.md) — quick reference.
- [`../AGENTS.md`](../AGENTS.md) — search module overview.
