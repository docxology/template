# Publishing Module - Quick Reference

Tools for academic publishing, citations, and platform integration.

The Python API exposes BibTeX, APA, and MLA citation helpers. The
`generate-citation` CLI subcommand currently exposes BibTeX only.

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
result = publish_to_zenodo(
    metadata,
    [Path("output/{project_name}/pdf/{project_name}_combined.pdf")],
    os.getenv("ZENODO_TOKEN")
)
print(f"Published with DOI: {result.doi}")
```

## Platform adapters

| Platform | Tier | Module | Credentials needed |
| --- | --- | --- | --- |
| Zenodo | first_class | `infrastructure.publishing.zenodo` | caller-provided token; `ZENODO_API_TOKEN` (archival) |
| GitHub Releases | first_class | `infrastructure.publishing.github` | `GITHUB_TOKEN` |
| arXiv | first_class | `infrastructure.publishing.arxiv` | — (local tarball only) |
| PyPI | first_class | `infrastructure.publishing.pypi` | `PYPI_TOKEN` |
| TestPyPI | first_class | `infrastructure.publishing.pypi` | `TESTPYPI_TOKEN` |
| IPFS (Pinata) | first_class | `infrastructure.publishing.archival` | `PINATA_JWT` |
| IPFS (Web3.Storage) | first_class | `infrastructure.publishing.archival` | `WEB3_STORAGE_TOKEN` |
| Software Heritage | first_class | `infrastructure.publishing.archival` | — |
| GitHub Pages | first_class | `infrastructure.publishing.static_site` | `GITHUB_TOKEN` |
| Cloudflare Pages | first_class | `infrastructure.publishing.static_site` | `CLOUDFLARE_API_TOKEN` |
| Netlify | first_class | `infrastructure.publishing.static_site` | `NETLIFY_AUTH_TOKEN` |
| HuggingFace Hub | documented | `infrastructure.publishing.huggingface` | `HUGGINGFACE_TOKEN` |
| OSF | documented | `infrastructure.publishing.osf` | `OSF_TOKEN` |

`first_class` = implemented, tested, locally verifiable. `documented` = future adapter; registered but no live implementation yet.

Use `infrastructure.publishing.registry` to enumerate or look up platforms programmatically:

```python
from infrastructure.publishing.registry import list_platforms, get_platform, PublishingTier

for p in list_platforms(tier=PublishingTier.FIRST_CLASS):
    print(p.name, p.env_vars)

info = get_platform("pypi")
print(info.adapter_class)  # 'PyPIAdapter'
```

## Modules

```mermaid
graph TD
    subgraph Metadata["Metadata Management"]
        EXTRACT[extract_publication_metadata<br/>Extract from markdown<br/>Parse config.yaml]
        READINESS[validate_publication_readiness<br/>Pre-flight checks]
        PACKAGE[create_publication_package<br/>Bundle files + metadata]
    end

    subgraph Citations["Citation Generation"]
        BIBTEX[generate_citation_bibtex<br/>BibTeX format]
        APA[generate_citation_apa<br/>APA style]
        MLA[generate_citation_mla<br/>MLA style]
    end

    subgraph Platforms["Platform Publishing"]
        ZENODO[publish_to_zenodo<br/>DOI minting]
        ARXIV[prepare_arxiv_submission<br/>Preprint tarball]
        GITHUB[create_github_release<br/>Release + assets]
        PYPI[PyPIAdapter<br/>build then check then upload]
        STATIC[static_site/<br/>GitHub Pages and Cloudflare and Netlify]
    end

    subgraph Archival["Long-horizon Archival"]
        BUNDLE[bundle_project<br/>Stage 10 executable bundle]
        ARCHIVE[archive_publication<br/>Multi-target mirror]
    end

    Metadata --> Citations
    Metadata --> Platforms
    Platforms --> Archival
```

- **core** - Metadata, citations, packages, readiness
- **zenodo/** - [Zenodo REST API](https://developers.zenodo.org/) client and publish workflow
- **github/** - GitHub Releases API
- **arxiv/** - arXiv submission tarball preparation
- **pypi/** - PyPI / TestPyPI build, check, upload pipeline (`PyPIAdapter`, `build_dist`, `upload_dist`, `check_dist`, `verify_install`)
- **static_site/** - Static-site hosting adapters (`GitHubPagesAdapter`, `CloudflarePagesAdapter`, `NetlifyAdapter`, `get_adapter()`)
- **archival/** - Multi-target long-horizon archival subpackage (`ZenodoProvider`, `IPFSPinataProvider`, `IPFSWeb3StorageProvider`, `SoftwareHeritageProvider`)
- **registry.py** - `PLATFORM_REGISTRY`, `list_platforms()`, `get_platform()`, `PublishingTier` enum: 10 first-class + 2 documented
- **platforms.py** / **api.py** - Backwards-compatible re-exports

## Key Classes

### PublicationMetadata
- `title` - Publication title
- `authors` - Author list
- `abstract` - Paper abstract
- `keywords` - Keyword list
- `doi` - Optional DOI
- `journal` - Optional journal name
- `license` - License type

### API clients

- `ZenodoClient` / `ZenodoConfig` — [`zenodo/`](zenodo/) (also via `infrastructure.publishing.api`)
- `DepositionResult` — create-deposition result (id + bucket URL)
- `PublishResult` — high-level Zenodo publish result (DOI + deposition id)
- `PyPIAdapter` / `PyPIConfig` / `PyPIResult` — [`pypi/`](pypi/)
- `GitHubPagesAdapter` / `CloudflarePagesAdapter` / `NetlifyAdapter` — [`static_site/`](static_site/)
- `SiteDeployConfig` / `SiteDeployResult` / `SiteHosting` — [`static_site/`](static_site/)

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
- `generate_citations_markdown()` - BibTeX, APA, and MLA markdown through the Python API

### Publication Checklists
- `create_submission_checklist()` - Journal/conference submission
- `create_academic_profile_data()` - ORCID/ResearchGate data
- `generate_publication_summary()` - Repository README

### Publishing Platforms
- `publish_to_zenodo()` - Publish with DOI minting
- `prepare_arxiv_submission()` - Create arXiv package
- `create_github_release()` - Automate GitHub releases
- `PyPIAdapter.publish()` - Build, check, and upload to PyPI / TestPyPI
- `get_adapter(config).deploy()` - Deploy static site to GitHub Pages, Cloudflare Pages, or Netlify

### Utilities
- `extract_citations_from_markdown()` - Citation extraction
- `generate_publication_metrics()` - Complexity analysis
- `generate_doi_badge()` - DOI badge generation
- `create_publication_announcement()` - Social media ready

## CLI

```bash
# Extract metadata
uv run python -m infrastructure.publishing.cli extract-metadata manuscript/

# Generate citations (the CLI currently exposes BibTeX only)
uv run python -m infrastructure.publishing.cli generate-citation manuscript/ --format bibtex

# Publish to Zenodo (sandbox by default; pass --production for zenodo.org)
uv run python -m infrastructure.publishing.cli publish-zenodo output/ --token $ZENODO_TOKEN

# GitHub release wrapper (expects output/pdf/*.pdf in cwd)
uv run python -m infrastructure.publishing.publish_cli \
  --token $GITHUB_TOKEN --repo owner/repo --tag v1.0.0 --name "Release 1.0.0"

# Archival dry-run (Stage 11; default is safe -- no real deposits)
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/template_code_project/executable_bundle \
  --providers zenodo software_heritage ipfs_pinata ipfs_web3storage
```

## Environment Variables

```bash
# Academic publishing
export ZENODO_TOKEN="your-token"          # Zenodo production (release workflow)
export ZENODO_SANDBOX_TOKEN="your-token"  # Zenodo sandbox (scripts/publish_project_release.py)
export ZENODO_API_TOKEN="your-token"      # Archival Zenodo provider

# Code hosting / releases
export GITHUB_TOKEN="your-token"          # GitHub Releases and GitHub Pages

# Package distribution
export PYPI_TOKEN="your-token"            # PyPI production (pypi/)
export TESTPYPI_TOKEN="your-token"        # TestPyPI (PyPIConfig(test=True))

# Static-site hosting
export CLOUDFLARE_API_TOKEN="your-token"  # Cloudflare Pages via Wrangler
export NETLIFY_AUTH_TOKEN="your-token"    # Netlify via netlify CLI

# Long-horizon archival
export PINATA_JWT="your-jwt"              # IPFS archival via Pinata
export WEB3_STORAGE_TOKEN="your-token"    # IPFS archival via Web3.Storage
```

## Testing

```bash
uv run pytest tests/infra_tests/publishing/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).
