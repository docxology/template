# Sources Module

API adapters for external academic databases.

## Available Sources

- **arxiv.py**: arXiv API client
- **semanticscholar.py**: Semantic Scholar API client
- **unpaywall.py**: Unpaywall API for open access PDFs
- **biorxiv.py**: bioRxiv/medRxiv preprint API
- **pubmed.py**: PubMed API client
- **europepmc.py**: Europe PMC API client
- **crossref.py**: CrossRef API client
- **openalex.py**: OpenAlex API client
- **dblp.py**: DBLP API client
- **base.py**: Base classes and utilities

## Quick Start

```python
from infrastructure.literature.sources import ArxivSource

source = ArxivSource()
results = source.search("machine learning", limit=10)
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


