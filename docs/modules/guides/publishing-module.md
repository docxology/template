# Publishing Module

> **Academic publishing workflow assistance**

**Location:** `infrastructure/publishing/` — see [`infrastructure/publishing/AGENTS.md`](../../../infrastructure/publishing/AGENTS.md) for the full API index.

**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Architecture

| Path | Role |
| --- | --- |
| `metadata.py`, `_metadata_*.py` | Metadata extraction and reporting |
| `citations.py` | Citation helpers: BibTeX CLI target plus APA/MLA library helpers |
| `zenodo/` | Zenodo Deposit API — `ZenodoClient`, `publish_to_zenodo`, `publish_new_version_to_zenodo` |
| `github/` | GitHub Releases — `create_github_release` |
| `arxiv/` | arXiv tarball — `prepare_arxiv_submission` |
| `metadata_from_config.py`, `config_doi.py` | Config-driven metadata and DOI write-back |
| `release_workflow.py` | Unified GitHub + Zenodo + re-render orchestration |
| `platforms.py`, `api.py` | Backwards-compatible re-exports |
| `executable_bundle.py` | Stage 10 executable bundle (`bundle_project`) |
| `archival.py` | Stage 11 multi-target archival — see [`archival/README.md`](../../../infrastructure/publishing/archival/README.md) |
| `cli.py`, `publish_cli.py`, `archival_cli.py` | CLI entry points |
| `scripts/publish_project_release.py` | Thin orchestrator for unified release (opt-in) |

---

## Key Features

- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX from the CLI; BibTeX, APA, and MLA through Python helpers
- **Publication Metadata**: Comprehensive metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Platform publishing**: Zenodo, arXiv, GitHub Releases
- **Long-horizon archival**: Zenodo, Software Heritage, IPFS providers

---

## Usage Examples

### DOI Validation and Citation Generation

```python
from infrastructure.publishing import validate_doi, generate_citation_bibtex, PublicationMetadata

doi = "10.5281/zenodo.12345678"
if validate_doi(doi):
    print("Valid DOI")

metadata = PublicationMetadata(
    title="Research Project Title",
    authors=["Dr. Jane Smith", "Dr. John Doe"],
    abstract="A research project abstract.",
    keywords=["research", "template"],
    doi=doi,
    publication_date="2024",
)

bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

### Zenodo (subpackage import)

```python
from pathlib import Path

from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.zenodo import publish_to_zenodo

metadata = PublicationMetadata(
    title="My Paper",
    authors=["Author"],
    abstract="Abstract.",
    keywords=["research"],
)

result = publish_to_zenodo(
    metadata,
    [Path("output/project/pdf/project_combined.pdf")],
    access_token="...",
    sandbox=True,
)
print(result.doi)
```

### Metadata Extraction

```python
from pathlib import Path

from infrastructure.publishing import extract_publication_metadata

metadata = extract_publication_metadata([Path("manuscript/01_abstract.md")])
print(metadata.title)
```

---

## CLI Integration

```bash
# Metadata and citations
uv run python -m infrastructure.publishing.cli extract-metadata manuscript/
uv run python -m infrastructure.publishing.cli generate-citation manuscript/ --format bibtex

# Zenodo upload
uv run python -m infrastructure.publishing.cli publish-zenodo output/ --token $ZENODO_TOKEN

# GitHub release (wrapper; expects output/pdf/*.pdf in cwd)
uv run python -m infrastructure.publishing.publish_cli \
  --token $GITHUB_TOKEN --repo owner/repo --tag v1.0.0 --name "Release 1.0.0"

# Archival dry-run (Stage 11)
uv run python scripts/09_archive_publication.py --project template_code_project

# Unified GitHub + Zenodo + DOI release (opt-in)
uv run python scripts/publish_project_release.py \
  --project template_code_project --tag v1.0.0 --repo owner/repo --dry-run
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DOI validation failures | Check DOI format and checksum |
| Citation format errors | Verify BibTeX syntax |
| Metadata extraction issues | Ensure manuscript has proper frontmatter |
| Zenodo upload fails | Use sandbox first; uploads must target `links.bucket` from create response |

---

**Related:** [Integrity Module](integrity-module.md) | [Rendering Module](rendering-module.md) | [Publishing AGENTS.md](../../../infrastructure/publishing/AGENTS.md)
