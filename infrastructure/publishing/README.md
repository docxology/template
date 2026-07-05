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
| HuggingFace Hub | first_class | `infrastructure.publishing.huggingface` | `HUGGINGFACE_TOKEN` / `HF_TOKEN` |
| OSF | first_class | `infrastructure.publishing.osf` | `OSF_TOKEN` |

`first_class` = implemented, tested, locally verifiable. `documented` = future adapter; registered but no live implementation yet. All 12 registered platforms are currently `first_class`.

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
        BUNDLE[bundle_project<br/>Stage 12 executable bundle]
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
- **registry.py** - `PLATFORM_REGISTRY`, `list_platforms()`, `get_platform()`, `PublishingTier` enum: 12 first-class
- **status_report.py** - Compile registry + `config.yaml` metadata into a regenerable per-platform README status block (`compile_publishing_status()`, `render_status_block()`, `update_readme_block()`)
- **credential_check.py** - Read-only, non-destructive verification that publishing credentials authenticate (`run_probe()`, `check_all()`)
- **upload_runner.py** - Reusable multi-platform upload dispatch (`UploadTargets`, `CORE_UPLOADERS`, `OPTIONAL_UPLOADERS`, `select_jobs()`, `run_uploads()` returning an `UploadRun`); the per-platform helpers + batch orchestrator extracted from `scripts/publish/upload_gold_refinement.py`, which is now a thin CLI
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

# Archival dry-run (Stage 13; default is safe -- no real deposits)
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/templates/template_code_project/executable_bundle \
  --providers zenodo software_heritage ipfs_pinata ipfs_web3storage

# Compile per-platform publishing status into a project README (regenerable block).
# Rolled out across all 13 projects/templates/* exemplars (2026-06-30) -- every
# one now carries a `## Publication and rendering` section sourced from this CLI.
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement --write
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement --check
# Enforced (not just documented): infrastructure.project.drift.check_publishing_status_block_current
# runs this same check for every exemplar inside `scripts/check_template_drift.py --strict`,
# which is wired into CI (.github/workflows/ci.yml) and the pre-push hook -- a stale or
# missing block fails the gate, it does not silently rot.

# Verify publishing credentials authenticate (read-only, no writes)
uv run python -m infrastructure.publishing.credential_check --env-file .env
```

`status_report` reads durable identifiers from `manuscript/config.yaml` —
never machine credential presence — to decide each platform's state. Beyond the
DOIs and repository fields, the `publication:` block accepts a
`published_artifacts` map of `platform-name -> durable url` that marks those
platforms PUBLISHED in the generated block:

```yaml
publication:
  doi: "10.5281/zenodo.20931955"          # concept DOI
  version_doi: "10.5281/zenodo.20938523"  # this-version DOI
  github_repository: "owner/repo"
  published_artifacts:
    ipfs_pinata: "https://gateway.pinata.cloud/ipfs/Qm..."
    huggingface_hub: "https://huggingface.co/datasets/ActiveInference/template_gold_refinement"
    osf: "https://osf.io/u485p/"
```

`compile_publishing_status(..., published=...)` accepts the same map at the call
site, overriding config for an ad-hoc render.

## Multi-platform upload dispatch

`upload_runner.py` drives real uploads across several platforms from one call.
Bundle the per-project inputs into an `UploadTargets`, resolve the uploader set
with `select_jobs()`, then `run_uploads()`. Every uploader is **dry-run by
default** (`commit=False`); a failure on one platform is captured in the receipt,
never raised, so the batch always completes.

```python
from pathlib import Path
from infrastructure.publishing.upload_runner import (
    UploadTargets, select_jobs, run_uploads,
)

targets = UploadTargets(
    project_root=Path("projects/templates/template_gold_refinement"),
    pdf=Path("output/templates/template_gold_refinement/pdf/template_gold_refinement_combined.pdf"),
    web_dir=Path("output/templates/template_gold_refinement/web"),
    hf_repo_id="ActiveInference/template_gold_refinement",
    github_repo="owner/repo",
    osf_title="Template Gold Refinement",
)

# Core uploaders: pinata, huggingface, osf, testpypi.
# Opt in to github / static-site (netlify, cloudflare) when needed.
jobs = select_jobs(include_github=True, include_static=True)

run = run_uploads(targets, jobs=jobs, commit=False)  # DRY-RUN
print(run.mode, run.ok)        # "DRY-RUN" True
print(run.results["pinata"])   # per-platform receipt dict
```

Pass `only=[...]` to `select_jobs()` to restrict the run to named platforms, and
`commit=True` to `run_uploads()` to perform real uploads.

## Environment Variables

```bash
# Academic publishing
export ZENODO_TOKEN="your-token"          # Zenodo production (cli.py publish-zenodo; publish_project_release.py fallback)
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
