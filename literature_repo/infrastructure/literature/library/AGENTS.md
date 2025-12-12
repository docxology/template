# Library Module - Complete Documentation

## Purpose

The library module manages paper indexing, BibTeX generation, statistics, and cleanup operations.

## Components

### LibraryIndex (index.py)

JSON-based index for tracking all papers in the library.

**Key Methods:**
- `add_entry()` - Add paper to index
- `get_entry()` - Get entry by citation key
- `list_entries()` - Get all entries
- `has_paper()` - Check if paper exists
- `get_stats()` - Get library statistics
- `export_json()` - Export to JSON file

**Features:**
- Automatic citation key generation
- Deduplication by DOI or title
- Full metadata storage
- PDF path tracking

### Library Statistics (stats.py)

Statistics and display utilities.

**Functions:**
- `get_library_statistics()` - Get comprehensive statistics
- `format_library_stats_display()` - Format for display

### ReferenceManager (references.py)

BibTeX generation and management.

**Key Methods:**
- `add_reference()` - Add paper to BibTeX file
- `export_library()` - Export library to JSON

**Features:**
- Automatic BibTeX entry generation
- Citation key consistency
- Deduplication

### Clear Operations (clear.py)

Cleanup operations for library maintenance.

**Functions:**
- `clear_pdfs()` - Remove all PDFs
- `clear_summaries()` - Remove all summaries
- `clear_library()` - Complete library cleanup

## Usage Examples

### Managing Library

```python
from infrastructure.literature.library import LibraryIndex
from infrastructure.literature.core import LiteratureConfig

config = LiteratureConfig()
index = LibraryIndex(config)

# Add entry
citation_key = index.add_entry(
    title="Paper Title",
    authors=["Author 1", "Author 2"],
    year=2024,
    doi="10.1234/example"
)

# Get entry
entry = index.get_entry(citation_key)

# List all entries
entries = index.list_entries()
```

### Statistics

```python
from infrastructure.literature.library import get_library_statistics

stats = get_library_statistics()
print(f"Total papers: {stats['total_entries']}")
print(f"PDFs downloaded: {stats['downloaded_pdfs']}")
```

### Cleanup

```python
from infrastructure.literature.library import clear_pdfs

result = clear_pdfs(confirm=True)
print(f"Removed {result['files_removed']} files")
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


