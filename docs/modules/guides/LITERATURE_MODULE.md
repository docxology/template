# Literature Search Module

> **Academic literature search and reference management**

**Location:** `infrastructure/literature/core.py`  
**Quick Reference:** [Modules Guide](../MODULES_GUIDE.md) | [API Reference](../../reference/API_REFERENCE.md)

---

## Key Features

- **Multi-Source Search**: Unified search across arXiv, Semantic Scholar, and CrossRef
- **PDF Download**: Automatic paper retrieval with retry logic
- **Citation Extraction**: Extract citations and generate BibTeX
- **BibTeX Management**: Generate and manage bibliography files
- **Reference Deduplication**: Merge results from multiple sources
- **Library Management**: Organize papers with JSON-based indexing

---

## Usage Examples

### Basic Literature Search

```python
from infrastructure.literature import LiteratureSearch

# Initialize searcher
searcher = LiteratureSearch()

# Search for papers
papers = searcher.search("machine learning", limit=10)

for paper in papers:
    print(f"{paper.title} ({paper.year})")
    print(f"  Authors: {', '.join(paper.authors)}")
    print(f"  DOI: {paper.doi or 'N/A'}")
```

### Download and Manage Papers

```python
# Download PDF (saved as citation_key.pdf)
pdf_path = searcher.download_paper(papers[0])

# Add to library (both BibTeX and JSON index)
citation_key = searcher.add_to_library(papers[0])
print(f"Added to library with key: {citation_key}")

# Get library statistics
stats = searcher.get_library_stats()
print(f"Total papers: {stats['total_entries']}")
print(f"Total citations: {stats['total_citations']}")
```

### Export References

```python
# Export BibTeX
searcher.export_bibtex("references.bib")

# Export library as JSON
searcher.export_library("library.json")
```

---

## CLI Integration

```bash
# Search for papers
python3 -m infrastructure.literature.cli search "deep learning" --limit 20

# Search with download
python3 -m infrastructure.literature.cli search "transformers" --download

# List library
python3 -m infrastructure.literature.cli library list

# Show statistics
python3 -m infrastructure.literature.cli library stats
```

---

**Related:** [LLM Module](LLM_MODULE.md) | [Publishing Module](PUBLISHING_MODULE.md)
