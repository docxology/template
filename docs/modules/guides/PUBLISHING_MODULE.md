# Publishing Module

> **Academic publishing workflow assistance**

**Location:** `infrastructure/publishing/core.py`  
**Quick Reference:** [Modules Guide](../MODULES_GUIDE.md) | [API Reference](../../reference/API_REFERENCE.md)

---

## Key Features

- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX, APA, MLA formats
- **Publication Metadata**: Comprehensive metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Academic Profile**: ORCID and repository integration

---

## Usage Examples

### DOI Validation and Citation Generation

```python
from infrastructure.publishing.core import validate_doi, generate_citation_bibtex

# Validate DOI
doi = "10.5281/zenodo.12345678"
if validate_doi(doi):
    print("✅ Valid DOI")
else:
    print("❌ Invalid DOI")

# Generate BibTeX citation
metadata = {
    'title': 'Research Project Title',
    'authors': ['Dr. Jane Smith', 'Dr. John Doe'],
    'year': '2024',
    'doi': doi
}

bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

**Output:**

```bibtex
@article{smith2024research,
  title={Research Project Title},
  author={Smith, Jane and Doe, John},
  year={2024},
  doi={10.5281/zenodo.12345678}
}
```

### Metadata Extraction

```python
from infrastructure.publishing.core import extract_publication_metadata

# Extract metadata from manuscript
markdown_files = ["manuscript/01_abstract.md", "manuscript/02_introduction.md"]
metadata = extract_publication_metadata(markdown_files)

print(f"Title: {metadata.title}")
print(f"Authors: {', '.join(metadata.authors)}")
print(f"DOI: {metadata.doi or 'Not specified'}")
```

---

## CLI Integration

```bash
# Prepare publication package
python3 -m infrastructure.publishing.cli prepare-submission output/ --format=arxiv

# Validate publication metadata
python3 -m infrastructure.publishing.cli validate-metadata manuscript/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DOI validation failures | Check DOI format and checksum |
| Citation format errors | Verify BibTeX syntax |
| Metadata extraction issues | Ensure manuscript has proper frontmatter |

---

**Related:** [Integrity Module](INTEGRITY_MODULE.md) | [Rendering Module](RENDERING_MODULE.md)
