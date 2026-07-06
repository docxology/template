# infrastructure.search.connectors

Python port of the [OpenScience ConnectorRegistry](https://github.com/synthetic-sciences/openscience)
pattern. Provides a uniform `Connector` protocol and `ConnectorRegistry` over
~8 major science databases.

## Connectors

| id | Name | Domain |
|---|---|---|
| `openalex` | OpenAlex | literature |
| `arxiv` | arXiv | literature |
| `semantic_scholar` | Semantic Scholar | literature |
| `crossref` | CrossRef | literature |
| `europepmc` | Europe PMC | biology |
| `biorxiv` | bioRxiv | biology |
| `uniprot` | UniProt | proteomics |
| `pdb` | RCSB PDB | structure |

## Quick start

```python
from infrastructure.search.connectors import search_connector, list_connectors

# List available connectors
for entry in list_connectors():
    print(entry.id, entry.domain, entry.description)

# Search
hits = search_connector("openalex", "transformer neural network", limit=5)
for h in hits:
    print(h.id, h.title)
```

## Registry

```python
from infrastructure.search.connectors import ConnectorRegistry, _ALL_CONNECTORS

registry = ConnectorRegistry()
for c in _ALL_CONNECTORS:
    registry.register(c)

# By domain
bio = registry.by_domain("biology")
# Serialisable catalog
catalog = registry.catalog()   # list[CatalogEntry] — no callables
```

## CLI

```bash
# List all connectors
uv run python -m infrastructure.search.connectors list-dbs

# Filter by domain
uv run python -m infrastructure.search.connectors list-dbs --domain proteomics

# Search
uv run python -m infrastructure.search.connectors search pdb "spike protein" --limit 3
```

## HTTP helper

`ConnectorHttpClient` wraps `urllib` with:
- `User-Agent: template-connectors/1.0`
- Timeout (default 30 s)
- Retry with exponential backoff on 429/5xx (default 3 retries)
- In-memory TTL cache for GETs (default 5 min)

```python
from infrastructure.search.connectors.http import ConnectorHttpClient

client = ConnectorHttpClient(timeout=10, cache_ttl=60)
resp = client.get("https://api.openalex.org/works", params={"search": "CRISPR"})
data = resp.json()
```

## Testing

```bash
uv run pytest tests/infra_tests/search/test_connectors.py -v
```

See `AGENTS.md` for the full agent guide.
