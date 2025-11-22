# Publishing Module

## Purpose

The Publishing module provides comprehensive tools for academic publishing workflows. It enables DOI management, citation generation in multiple formats, publication metadata extraction, and automated publishing to major academic platforms (Zenodo, arXiv, GitHub).

## Architecture

### Core Components

**core.py**
- Publication metadata extraction and management
- DOI validation and formatting
- Citation generation (BibTeX, APA, MLA formats)
- Publication package creation
- Submission checklist generation
- Academic standards compliance
- Publication metrics and complexity analysis
- Repository metadata generation

**api.py**
- Zenodo API client with sandbox support
- arXiv submission package preparation
- GitHub release creation and automation
- DOI minting and archival
- Metrics tracking and reporting

## Key Features

### Metadata Extraction
```python
from infrastructure.publishing import extract_publication_metadata

metadata = extract_publication_metadata([Path("manuscript.md")])
```

### Citation Generation
```python
from infrastructure.publishing import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla
)

bibtex = generate_citation_bibtex(metadata)
apa = generate_citation_apa(metadata)
mla = generate_citation_mla(metadata)
```

### Publishing to Platforms
```python
from infrastructure.publishing import (
    publish_to_zenodo,
    prepare_arxiv_submission,
    create_github_release
)

# Publish to Zenodo
doi = publish_to_zenodo(metadata, files, access_token)

# Prepare arXiv submission
arxiv_package = prepare_arxiv_submission(Path("output/"), metadata)

# Create GitHub release
url = create_github_release(
    "v1.0", "Release 1.0", "Release notes", files, token, "owner/repo"
)
```

## Testing

Run publishing tests with:
```bash
pytest tests/infrastructure/test_publishing/
```

## Configuration

Environment variables:
- `ZENODO_TOKEN` - Zenodo API token (for `publish_to_zenodo`)
- `GITHUB_TOKEN` - GitHub API token (for `create_github_release`)

## Integration

Publishing module is used by:
- Publication automation workflows
- Repository management
- DOI and citation management
- Academic dissemination pipelines

## See Also

- [`core/`](../core/) - Foundation utilities
- [`validation/`](../validation/) - Validation & quality assurance

