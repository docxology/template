# Publishing Research

> **From manuscript to DOI: citations, Zenodo, arXiv, and GitHub Releases**

**Skill Level**: 11-12  
**Quick Reference:** [Modules Guide](../modules/modules-guide.md) | [Publishing Module](../modules/guides/publishing-module.md)

---

## Setting Up Publication Metadata

Configure your project's `manuscript/config.yaml`:

```yaml
paper:
  title: "Your Research Title"
  version: "1.0"
  date: "2026-01-15"

authors:
  - name: "Author Name"
    orcid: "0000-0001-6232-9096"
    email: "author@example.com"
    affiliation: "Institution Name"
    corresponding: true
  - name: "Co-Author"
    orcid: "0000-0002-1234-5678"
    affiliation: "Other Institution"

publication:
  doi: "10.5281/zenodo.12345678"
  journal: "Zenodo"
  volume: "1"
  year: "2026"

keywords:
  - "reproducible research"
  - "your-topic"
```

---

## Generating Citations

```python
from infrastructure.publishing import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
    PublicationMetadata,
)

# Extract metadata from config.yaml
from infrastructure.publishing import extract_publication_metadata
from pathlib import Path

metadata = extract_publication_metadata(Path("projects/code_project/manuscript/config.yaml"))

# Generate citations in multiple formats
bibtex = generate_citation_bibtex(metadata)
apa = generate_citation_apa(metadata)
mla = generate_citation_mla(metadata)

print(bibtex)
# @article{friedman2026template,
#   title={A template/ approach to Reproducible Research},
#   author={Friedman, Daniel Ari},
#   year={2026},
#   doi={10.5281/zenodo.12345678}
# }
```

### Generate All Formats at Once

```python
from infrastructure.publishing import generate_citations_markdown

# Creates a markdown block with BibTeX, APA, and MLA
citations_md = generate_citations_markdown(metadata)
```

---

## Publishing to Zenodo

### Prerequisites

1. Create a [Zenodo account](https://zenodo.org)
2. Generate an API token: Settings → Applications → Personal access tokens
3. Set the token: `export ZENODO_TOKEN=your_token_here`

### Upload

```python
from infrastructure.publishing import publish_to_zenodo, ZenodoClient, ZenodoConfig

# Configure client
config = ZenodoConfig(token="your_token", sandbox=True)  # Use sandbox first!
client = ZenodoClient(config)

# Publish
result = publish_to_zenodo(
    pdf_path=Path("output/code_project/pdf/code_project_combined.pdf"),
    metadata=metadata,
    client=client,
)
print(f"DOI: {result.doi}")
print(f"URL: {result.url}")
```

### DOI Badge

```python
from infrastructure.publishing import generate_doi_badge

badge_md = generate_doi_badge("10.5281/zenodo.12345678")
# [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.12345678.svg)](...)
```

---

## arXiv Submission

```python
from infrastructure.publishing import prepare_arxiv_submission

# Package manuscript for arXiv
submission = prepare_arxiv_submission(
    manuscript_dir=Path("projects/code_project/manuscript/"),
    output_dir=Path("output/code_project/arxiv/"),
)
print(f"Submission package: {submission.package_path}")
print(f"Files included: {submission.file_list}")
```

---

## GitHub Releases

```python
from infrastructure.publishing import create_github_release

# Create a tagged release
release = create_github_release(
    tag="v1.0.0",
    title="Initial Release",
    notes="First public release of the research manuscript.",
    assets=[Path("output/code_project/pdf/code_project_combined.pdf")],
)
```

The CI workflow at `.github/workflows/release.yml` automates this on `v*.*.*` tags.

---

## Publication Readiness

```python
from infrastructure.publishing import (
    validate_publication_readiness,
    create_submission_checklist,
    create_publication_package,
)

# Check if everything is ready
readiness = validate_publication_readiness(
    project_dir=Path("projects/code_project/"),
)
print(f"Ready: {readiness.is_ready}")
for issue in readiness.issues:
    print(f"  - {issue}")

# Generate a checklist
checklist = create_submission_checklist(metadata)

# Bundle everything for submission
package = create_publication_package(
    project_dir=Path("projects/code_project/"),
    output_dir=Path("output/code_project/publication/"),
)
```

---

## DOI Validation

```python
from infrastructure.publishing import validate_doi

is_valid = validate_doi("10.5281/zenodo.12345678")
# True — valid DOI format
```

---

## Troubleshooting

**Missing ZENODO_TOKEN:**
- Set via environment: `export ZENODO_TOKEN=your_token`
- Or pass directly: `ZenodoConfig(token="...")`

**Sandbox vs Production:**
- Always test with `sandbox=True` first
- Sandbox DOIs are not permanent

**Missing metadata fields:**
- Run `validate_publication_readiness()` to identify gaps
- Ensure `config.yaml` has all required fields (title, authors, DOI)

---

## Related Documentation

- **[Publishing Module Reference](../modules/guides/publishing-module.md)** — API details
- **[Secure Research Guide](secure-research-guide.md)** — PDF watermarking and provenance
- **[New Project Setup](new-project-setup.md)** — config.yaml template
- **[Infrastructure AGENTS.md](../../infrastructure/publishing/AGENTS.md)** — Machine-readable spec
