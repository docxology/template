# `infrastructure/search/connectors/`

Agent guide for the ConnectorRegistry subpackage.

## Purpose

Provides a uniform Python connector interface to ~8 major science databases,
ported from the OpenScience TypeScript project
(https://github.com/synthetic-sciences/openscience).

Each connector satisfies the `Connector` protocol and is registered in a
`ConnectorRegistry` that supports domain filtering and serialisable catalog
output.

## Module map

| File | Role |
|---|---|
| `types.py` | `ConnectorDomain` (StrEnum), `ConnectorHit`, `CatalogEntry`, `SearchOptions`, `FetchOptions`, `Connector` (Protocol), `ConnectorError` |
| `registry.py` | `ConnectorRegistry` — thread-safe, ordered dict of connectors |
| `http.py` | `ConnectorHttpClient` — stdlib urllib with retry, TTL cache, User-Agent |
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
    ConnectorRegistry, _ALL_CONNECTORS, SearchOptions
)

registry = ConnectorRegistry()
for c in _ALL_CONNECTORS:
    registry.register(c)

# List all biology connectors
bio = registry.by_domain("biology")

# Search
hits = registry.get("arxiv").search("attention mechanism", SearchOptions(limit=5))

# Convenience helpers (default registry)
from infrastructure.search.connectors import list_connectors, search_connector
catalog = list_connectors(domain="literature")
hits = search_connector("openalex", "CRISPR", limit=3)
```

## CLI

```bash
uv run python -m infrastructure.search.connectors list-dbs
uv run python -m infrastructure.search.connectors list-dbs --domain biology
uv run python -m infrastructure.search.connectors search arxiv "active inference" --limit 5
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
- `SearchOptions.limit=None` means connector uses its own default (typically 10).
- Per-connector errors raise `ConnectorError` — callers decide whether to surface or absorb.

## Adding a connector

1. Create `impl/mydb.py` with a class implementing the `Connector` protocol.
2. Export an instance: `mydb: Connector = _MyDBConnector()`.
3. Add to `impl/__init__.py`: import + append to `_ALL_CONNECTORS`.
4. Add tests to `tests/infra_tests/search/test_connectors.py` using `pytest-httpserver`.

## See also

- [`README.md`](README.md) — quick reference.
- [`../AGENTS.md`](../AGENTS.md) — search module overview.
