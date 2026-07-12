---
name: scientific-connectors
description: >
  Search 8+ scientific databases through a uniform Connector interface.
  Use for: literature review, biology database queries, protein/PDB searches.
  CLI: python -m infrastructure.search.connectors {list-dbs,search}.
  Config: set queries in projects/{name}/manuscript/config.yaml `connector_search:` block.
  Orchestrator: scripts/pipeline/stage_08_connector_search.py --project {name}
---

# Scientific Connector Registry

Uniform discovery layer over eight science databases (OpenAlex, arXiv,
Semantic Scholar, CrossRef, Europe PMC, bioRxiv, UniProt, PDB) via the
`Connector` protocol. All connectors are stdlib-only (`urllib`), retry-safe,
and backed by an optional in-memory HTTP cache.

## Quick Start

```python
from infrastructure.search.connectors import (
    ConnectorDomain,
    get_registry,
    list_connectors,
    search_connector,
)

catalog = list_connectors()
biology_connectors = get_registry().by_domain(ConnectorDomain.biology)
hits = search_connector("openalex", "protein folding", max_results=10)
```

## Fetch by ID

```python
registry = get_registry()
protein = registry.get("uniprot").fetch("P12345")
structure = registry.get("pdb").fetch("4HHB")
```

## Available Connectors

```bash
uv run python -m infrastructure.search.connectors list-dbs
```

| ID | Database | Domain |
| --- | --- | --- |
| `openalex` | OpenAlex | literature |
| `arxiv` | arXiv | physics |
| `semantic_scholar` | Semantic Scholar | literature |
| `crossref` | CrossRef | literature |
| `europepmc` | Europe PMC | biology |
| `biorxiv` | bioRxiv | biology |
| `uniprot` | UniProt | proteomics |
| `pdb` | Protein Data Bank | structure |

## CLI

```bash
# List all registered databases with their domains and descriptions
uv run python -m infrastructure.search.connectors list-dbs

# Search one connector
uv run python -m infrastructure.search.connectors search openalex "protein folding" --max-results 10

# Search all connectors (individual failures are reported as warnings)
uv run python -m infrastructure.search.connectors search --all "membrane" --max-results 5
```

## Pipeline Orchestrator

```bash
# Run connector search for a named project
uv run python scripts/pipeline/stage_08_connector_search.py --project my_project

# One-off override that bypasses project connector_search configuration
uv run python scripts/pipeline/stage_08_connector_search.py \
  --project my_project --connector arxiv --query "active inference" --max-results 5
```

## Config Integration

Set connector queries in `projects/{name}/manuscript/config.yaml`:

```yaml
connector_search:
  enabled: true
  max_results: 20
  connectors:
    arxiv:
      - protein language model
    openalex:
      - AlphaFold structure prediction
```

The default report path is
`projects/{name}/output/data/connector_search/results.json`. Each configured
connector/query pair has a `success` or `error` status and a normalized result
list produced by `ConnectorHit.to_dict()`. No configuration, disabled
configuration, or an empty connector map exits 2; malformed configuration or
any connector error exits 1 after the report is written.

## Key Types

```python
from infrastructure.search.connectors import (
    Connector,           # Protocol — search(query, opts) + fetch(id, opts)
    ConnectorDomain,     # Enum: biology, literature, proteomics, ...
    ConnectorHit,        # Normalised result record
    CatalogEntry,        # Registry metadata for a connector
    SearchOptions,       # max_results, year_min, year_max, extra
    FetchOptions,        # include_abstract, extra
    ConnectorError,      # Base exception
    ConnectorRegistry,   # register / get / catalog / domain filtering
)
```

## Reliability

- **Stdlib-only**: no third-party HTTP dependencies; uses `urllib` with
  exponential-backoff retry.
- **Per-connector failure isolation**: a network outage in one connector
  is recorded and does not abort others.
- **Bounded HTTP cache**: `ConnectorHttpClient` provides a configurable
  in-memory TTL cache; pass `ttl=0` when every request must reach the source.
- **Pipeline evidence**: Stage 08 records errors alongside successful searches
  rather than silently replacing failures with empty result lists.

## Testing

```bash
uv run pytest \
  tests/infra_tests/search/test_connectors.py \
  tests/infra_tests/search/test_connector_scripts.py -v
```

## See Also

- [`../SKILL.md`](../SKILL.md) — parent search module skill
- [`../AGENTS.md`](../AGENTS.md) — search module architecture overview
