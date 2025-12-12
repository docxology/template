# Core Module

Core functionality for literature search, configuration, and CLI interface.

## Components

- **core.py**: Main `LiteratureSearch` class for searching and managing papers
- **config.py**: Configuration management with environment variable support
- **cli.py**: Command-line interface for interactive use

## Quick Start

```python
from infrastructure.literature.core import LiteratureSearch, LiteratureConfig

# Initialize with default config
searcher = LiteratureSearch()

# Or with custom config
config = LiteratureConfig(
    default_limit=50,
    sources=["arxiv", "semanticscholar"]
)
searcher = LiteratureSearch(config)

# Search for papers
results = searcher.search("machine learning", limit=10)
```

## CLI Usage

```bash
python3 -m infrastructure.literature.core.cli search "machine learning" --limit 10
python3 -m infrastructure.literature.core.cli library list
python3 -m infrastructure.literature.core.cli library stats
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


