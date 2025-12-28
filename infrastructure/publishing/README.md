# Publishing Module - Quick Reference

Tools for academic publishing, citations, and platform integration.

## Quick Start

```python
from infrastructure.publishing import (
    extract_publication_metadata,
    generate_citation_bibtex,
    publish_to_zenodo
)

# Extract metadata
metadata = extract_publication_metadata([Path("manuscript.md")])

# Generate citations
bibtex = generate_citation_bibtex(metadata)
print(bibtex)

# Publish to Zenodo
doi = publish_to_zenodo(
    metadata,
    [Path("output/pdf/manuscript.pdf")],
    os.getenv("ZENODO_TOKEN")
)
print(f"Published with DOI: {doi}")
```

## Modules

```mermaid
graph TD
    subgraph Metadata["Metadata Management"]
        EXTRACT[extract_publication_metadata<br/>Extract from markdown<br/>Parse config.yaml]
        VALIDATE[validate_metadata<br/>Check completeness<br/>Format validation]
        FORMAT[format_metadata<br/>Standardize format<br/>Citation preparation]
    end

    subgraph Citations["Citation Generation"]
        BIBTEX[generate_citation_bibtex<br/>BibTeX format<br/>Academic bibliography]
        APA[generate_citation_apa<br/>APA style<br/>Social sciences]
        MLA[generate_citation_mla<br/>MLA style<br/>Humanities]
    end

    subgraph Platforms["Platform Publishing"]
        ZENODO[publish_to_zenodo<br/>DOI minting<br/>Data/code archiving]
        ARXIV[prepare_arxiv_submission<br/>Preprint package<br/>Academic sharing]
        GITHUB[create_github_release<br/>Version tagging<br/>Code distribution]
    end

    subgraph Workflow["Publishing Workflow"]
        PREPARE[Prepare Materials<br/>Gather files<br/>Validate formats]
        METADATA_PROC[Process Metadata<br/>Extract & format<br/>Generate citations]
        UPLOAD[Upload to Platforms<br/>Zenodo, arXiv, GitHub<br/>DOI management]
        TRACK[Track Publication<br/>Monitor status<br/>Update records]
    end

    Metadata --> Citations
    Metadata --> Platforms

    Citations --> Workflow
    Platforms --> Workflow

    EXTRACT --> VALIDATE --> FORMAT
    FORMAT --> BIBTEX
    FORMAT --> APA
    FORMAT --> MLA

    FORMAT --> ZENODO
    FORMAT --> ARXIV
    FORMAT --> GITHUB

    PREPARE --> METADATA_PROC --> UPLOAD --> TRACK

    classDef metadata fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef citations fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef platforms fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef workflow fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class Metadata metadata
    class Citations citations
    class Platforms platforms
    class Workflow workflow
```

- **core** - Publishing workflows and metadata management
- **api** - Platform API clients (Zenodo, arXiv, GitHub)

## Key Classes

### PublicationMetadata
- `title` - Publication title
- `authors` - Author list
- `abstract` - Paper abstract
- `keywords` - Keyword list
- `doi` - Optional DOI
- `journal` - Optional journal name
- `license` - License type

### API Clients
- `ZenodoClient` - Zenodo platform integration
- `ZenodoConfig` - Zenodo configuration

## Key Functions

### Metadata Management
- `extract_publication_metadata()` - Parse manuscript for metadata
- `validate_doi()` - Check DOI format and validity
- `create_publication_package()` - Prepare publication package
- `validate_publication_readiness()` - Check completeness

### Citation Generation
- `generate_citation_bibtex()` - BibTeX format
- `generate_citation_apa()` - APA format
- `generate_citation_mla()` - MLA format
- `generate_citations_markdown()` - All formats with markdown

### Publication Checklists
- `create_submission_checklist()` - Journal/conference submission
- `create_academic_profile_data()` - ORCID/ResearchGate data
- `generate_publication_summary()` - Repository README

### Publishing Platforms
- `publish_to_zenodo()` - Publish with DOI minting
- `prepare_arxiv_submission()` - Create arXiv package
- `create_github_release()` - Automate GitHub releases

### Utilities
- `extract_citations_from_markdown()` - Citation extraction
- `generate_publication_metrics()` - Complexity analysis
- `generate_doi_badge()` - DOI badge generation
- `create_publication_announcement()` - Social media ready

## CLI

```bash
# Extract metadata
python3 -m infrastructure.publishing.cli extract-metadata manuscript/

# Generate citations
python3 -m infrastructure.publishing.cli generate-citation manuscript/ --format bibtex

# Prepare Zenodo upload
python3 -m infrastructure.publishing.cli publish-zenodo output/ --token $ZENODO_TOKEN
```

## Environment Variables

```bash
export ZENODO_TOKEN="your-token"
export GITHUB_TOKEN="your-token"
```

## Testing

```bash
pytest tests/infrastructure/test_publishing/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

