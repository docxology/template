# Library Module

Library management, indexing, statistics, references, and cleanup operations.

## Components

- **index.py**: `LibraryIndex` for JSON-based paper tracking
- **stats.py**: Library statistics and display utilities
- **references.py**: `ReferenceManager` for BibTeX generation
- **clear.py**: Cleanup operations for PDFs, summaries, and library

## Quick Start

```python
from infrastructure.literature.library import (
    LibraryIndex,
    get_library_statistics,
    ReferenceManager
)
from infrastructure.literature.core import LiteratureConfig

config = LiteratureConfig()
index = LibraryIndex(config)

# Get all entries
entries = index.list_entries()

# Get statistics
stats = get_library_statistics(config)
```

## Features

- JSON-based index with full metadata
- BibTeX generation with deduplication
- Statistics and reporting
- Cleanup operations

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


