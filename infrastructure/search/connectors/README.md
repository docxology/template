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
    print(entry.name, entry.domain.value, entry.description)

# Search
hits = search_connector("openalex", "transformer neural network", max_results=5)
for h in hits:
    print(h.id, h.title, h.abstract)
```

## Registry

```python
from infrastructure.search.connectors import ConnectorDomain, ConnectorRegistry, _ALL_CONNECTORS

registry = ConnectorRegistry()
for connector_class in _ALL_CONNECTORS:
    registry.register(connector_class())

# By domain
bio = registry.by_domain(ConnectorDomain.biology)
# Serialisable catalog
catalog = registry.catalog()   # list[CatalogEntry] — no callables
```

## CLI

```bash
# List all connectors
uv run python -m infrastructure.search.connectors list-dbs

# Search
uv run python -m infrastructure.search.connectors search pdb "spike protein" --max-results 3
```

## Pipeline Stage 08

Configure reproducible project searches in `manuscript/config.yaml`:

```yaml
connector_search:
  enabled: true
  max_results: 10
  connectors:
    arxiv:
      - active inference
    openalex:
      - reproducible generative research
```

Then run:

```bash
uv run python scripts/pipeline/stage_08_connector_search.py \
  --project templates/template_code_project
```

The stage writes a normalized report to
`output/data/connector_search/results.json` inside the project. Every search
entry records its connector, query, status, error, and full
`ConnectorHit.to_dict()` results, including the `abstract` field. A configured
connector failure is isolated and persisted in the report, then makes the
stage exit 1; absent or disabled configuration exits 2.

## HTTP helper

`ConnectorHttpClient` wraps `urllib` with:
- `User-Agent: template-connectors/1.0`
- Timeout (default 30 s)
- Retry with exponential backoff on 429/5xx (default 3 retries)
- In-memory TTL cache for GETs (default 5 min)

```python
from infrastructure.search.connectors.http import ConnectorHttpClient

client = ConnectorHttpClient(timeout=10, ttl=60)
data = client.get_json(
    "https://api.openalex.org/works",
    params={"search": "CRISPR"},
)
```

## Testing

```bash
uv run pytest \
  tests/infra_tests/search/test_connectors.py \
  tests/infra_tests/search/test_connector_scripts.py -v
```

See `AGENTS.md` for the full agent guide.
