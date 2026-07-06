---
name: scientific-connectors
description: >
  Search 8+ scientific databases through a uniform Connector interface.
  Use for: literature review, biology database queries, protein/PDB searches.
  CLI: python -m infrastructure.search.connectors {list-dbs,search}.
  Config: set queries in projects/{name}/manuscript/config.yaml `connector_search:` block.
  Orchestrator: scripts/08_connector_search.py --project {name}
---

# Scientific Connector Registry

Uniform discovery layer over eight science databases (OpenAlex, arXiv,
Semantic Scholar, CrossRef, Europe PMC, bioRxiv, UniProt, PDB) via the
`Connector` protocol. All connectors are stdlib-only (`urllib`), retry-safe,
and optionally disk-cached.

## Quick Start

```python
from infrastructure.search.connectors import ConnectorRegistry, ConnectorDomain

registry = ConnectorRegistry.default()                    # all eight connectors pre-registered
hits = registry.search("protein folding", limit=10)       # query all connectors
hits = registry.search("CRISPR", domain=ConnectorDomain.BIOLOGY, limit=5)  # filter by domain
catalog = registry.list_all()                             # list registered connectors
```

## Fetch by ID

```python
hit = registry.fetch("uniprot", "P12345")      # fetch a specific record
hit = registry.fetch("pdb", "4HHB")            # fetch a PDB structure entry
```

## Available Connectors

```bash
uv run python -m infrastructure.search.connectors list-dbs
```

| ID | Database | Domain |
| --- | --- | --- |
| `openalex` | OpenAlex | multidisciplinary |
| `arxiv` | arXiv | multidisciplinary |
| `semantic_scholar` | Semantic Scholar | multidisciplinary |
| `crossref` | CrossRef | multidisciplinary |
| `europepmc` | Europe PMC | biology |
| `biorxiv` | bioRxiv | biology |
| `uniprot` | UniProt | biology |
| `pdb` | Protein Data Bank | biology |

## CLI

```bash
# List all registered databases with their domains and descriptions
uv run python -m infrastructure.search.connectors list-dbs

# Search across all connectors
uv run python -m infrastructure.search.connectors search "protein folding" --limit 10

# Search a specific connector by id
uv run python -m infrastructure.search.connectors search "CRISPR" --connector openalex

# Search and filter by domain
uv run python -m infrastructure.search.connectors search "membrane" --domain biology
```

## Pipeline Orchestrator

```bash
# Run connector search for a named project
uv run python scripts/08_connector_search.py --project my_project

# Dry-run to see what would be searched
uv run python scripts/08_connector_search.py --project my_project --dry-run
```

## Config Integration

Set connector queries in `projects/{name}/manuscript/config.yaml`:

```yaml
connector_search:
  queries:
    - "protein language model"
    - "AlphaFold structure prediction"
  domains:
    - biology
  limit: 20
  cache_dir: output/connector_cache
```

## Key Types

```python
from infrastructure.search.connectors import (
    Connector,           # Protocol — search(query, opts) + fetch(id, opts)
    ConnectorDomain,     # StrEnum: BIOLOGY, MULTIDISCIPLINARY, ...
    ConnectorHit,        # Normalised result record
    CatalogEntry,        # Registry metadata for a connector
    SearchOptions,       # limit, domain, cache_dir
    FetchOptions,        # cache_dir
    ConnectorError,      # Base exception
    ConnectorRegistry,   # register / list_all / search / fetch dispatch
)
```

## Reliability

- **Stdlib-only**: no third-party HTTP dependencies; uses `urllib` with
  exponential-backoff retry.
- **Per-connector failure isolation**: a network outage in one connector
  is recorded and does not abort others.
- **Optional disk cache**: pass `cache_dir=` in `SearchOptions` / `FetchOptions`
  for deterministic replay.

## Testing

```bash
uv run pytest tests/infra_tests/search/connectors/ -v
```

## See Also

- [`../SKILL.md`](../SKILL.md) — parent search module skill
- [`../AGENTS.md`](../AGENTS.md) — search module architecture overview
