---
name: infrastructure-publishing
description: Skill for the publishing infrastructure module providing academic publishing workflows including citation generation (BibTeX, APA, MLA), DOI management, Zenodo publication, arXiv submission preparation, GitHub releases, and publication readiness validation. Use when publishing research, generating citations, minting DOIs, or preparing submissions.
---

# Publishing Module

Academic publishing and dissemination tools for research projects.

## Publication Metadata (`core.py`)

```python
from infrastructure.publishing import PublicationMetadata, extract_publication_metadata

# Extract metadata from project config
metadata = extract_publication_metadata(config_path)

# Access publication details
print(metadata.title, metadata.authors, metadata.doi)
```

## Citation Generation

```python
from infrastructure.publishing import (
    generate_citation_bibtex, generate_citation_apa, generate_citation_mla,
    generate_citations_markdown, CitationStyle,
    extract_citations_from_markdown,
)

# Generate citations in different formats
bibtex = generate_citation_bibtex(metadata)
apa = generate_citation_apa(metadata)
mla = generate_citation_mla(metadata)

# Generate full citations markdown
citations_md = generate_citations_markdown(metadata)

# Extract existing citations from manuscript
existing = extract_citations_from_markdown(manuscript_text)
```

## DOI Management

```python
from infrastructure.publishing import validate_doi, generate_doi_badge

is_valid = validate_doi("10.5281/zenodo.12345678")
badge_md = generate_doi_badge("10.5281/zenodo.12345678")
```

## Zenodo Publication

```python
from infrastructure.publishing import publish_to_zenodo, ZenodoClient, ZenodoConfig

# Quick publish
result = publish_to_zenodo(metadata, files_dir)

# Advanced usage with client
config = ZenodoConfig(access_token="...")
client = ZenodoClient(config)
deposition = client.create_deposition(metadata)
client.upload_files(deposition, files_dir)
client.publish(deposition)
```

## arXiv Submission

```python
from infrastructure.publishing import prepare_arxiv_submission

# Prepare submission package
package = prepare_arxiv_submission(manuscript_dir, output_dir)
```

## GitHub Releases

```python
from infrastructure.publishing import create_github_release

release = create_github_release(
    repo="user/repo",
    tag="v1.0.0",
    title="Release 1.0.0",
    body=release_notes,
)
```

## Publication Readiness

```python
from infrastructure.publishing import (
    validate_publication_readiness, create_submission_checklist,
    generate_publication_summary, generate_publication_metrics,
    create_publication_package, create_publication_announcement,
    create_academic_profile_data, create_repository_metadata,
    calculate_complexity_score, calculate_file_hash,
)

# Check if ready to publish
readiness = validate_publication_readiness(project_path)

# Generate submission checklist
checklist = create_submission_checklist(metadata)

# Create publication package
package = create_publication_package(project_path, output_dir)

# Generate metrics
metrics = generate_publication_metrics(project_path)
```
