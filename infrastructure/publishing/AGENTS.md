# Publishing Module

## Purpose

The Publishing module provides tools for academic publishing workflows. It enables DOI management, citation generation in multiple formats, publication metadata extraction, and automated publishing to major academic platforms (Zenodo, arXiv, GitHub) as well as package distribution (PyPI), static-site hosting, and long-horizon multi-target archival.

## Architecture

### Core components (package root)

| Module | Role |
| --- | --- |
| `metadata.py` / `_metadata_*.py` | Publication metadata extraction and reporting |
| `models.py` | `PublicationMetadata`, `AuthorRecord`, `CitationStyle` |
| `citations.py` | Citation helpers: BibTeX CLI target plus APA/MLA library helpers |
| `package.py` | Publication package, checklist, readiness re-exports |
| `metadata_from_config.py` | `publication_metadata_from_config`, `load_publication_release_context` — single-parse metadata + deposit context + prior DOI from `config.yaml` |
| `abstract_plaintext.py` | Plaintext abstract + cross-link footer for Zenodo/GitHub (`build_deposit_description`, `build_github_release_body`) |
| `config_doi.py` | `update_publication_doi`, `read_publication_doi`, `update_publication_after_zenodo_deposit` — comment-preserving DOI write-back (concept DOI preserved when `version_doi` is declared) |
| `release_workflow.py` | Unified GitHub + Zenodo + DOI + re-render orchestration |
| `release_workflow_zenodo.py` | Reserve-first DOI phase + `publish_zenodo_for_release` (leaf of release workflow) |
| `deposit_filename.py` | `build_deposit_filename`, `DepositPublishContext`, `deposit_context_from_config` — metadata-driven Zenodo/GitHub upload basename |
| `publication_ledger.py` | Append-only release ledger for transmission bookends |
| `release_pairing.py` | Structural GitHub ↔ Zenodo pairing validation |
| `transmission_bookends.py` | Generated begin/end transmission manuscript pages |
| `transmission_barcode_strip.py` | Dual-row 7-QR + Code128 strip PNG; writes `transmission_manifest.json` |
| `transmission_figure.py` | Matplotlib pairing-flow diagram for bookends |
| `transmission_page_check.py` | PDF page-span gate (BEGIN page 1, END last page only) |
| `zenodo_urls.py` | `zenodo_record_url_from_doi` (no rendering import cycle) |
| `announcement.py`, `checklist.py`, `readiness.py` | Pre-publication helpers |
| `archival.py` | Backwards-compat shim — re-exports `archival/` subpackage surface (Stage 11) |
| `executable_bundle.py` | Stage 10 executable bundle |
| `registry.py` | `PLATFORM_REGISTRY`, `list_platforms()`, `get_platform()`, `PublishingTier` — central adapter registry |
| `cli.py`, `publish_cli.py`, `archival_cli.py` | CLI entry points |

### Platform subpackages

| Subpackage | Role |
| --- | --- |
| [`zenodo/`](zenodo/) | [Zenodo REST Deposit API](https://developers.zenodo.org/) — `ZenodoClient`, `publish_to_zenodo` |
| [`github/`](github/) | GitHub Releases API — `create_github_release` |
| [`arxiv/`](arxiv/) | Local arXiv tarball preparation — `prepare_arxiv_submission` |
| [`pypi/`](pypi/) | PyPI / TestPyPI distribution — `PyPIAdapter`, `build_dist`, `upload_dist`, `check_dist`, `verify_install` |
| [`static_site/`](static_site/) | Static-site hosting adapters — `GitHubPagesAdapter`, `CloudflarePagesAdapter`, `NetlifyAdapter`, `get_adapter()` |
| [`archival/`](archival/) | Multi-target long-horizon archival providers — `ZenodoProvider`, `IPFSPinataProvider`, `IPFSWeb3StorageProvider`, `SoftwareHeritageProvider` (proper subpackage; flat `archival.py` retained for backwards compat) |

### pypi/ — PyPI / TestPyPI publishing

`infrastructure.publishing.pypi` is a build then check then upload pipeline for Python package distribution.

| Symbol | Module | Role |
| --- | --- | --- |
| `PyPIAdapter` | `pypi/adapter.py` | High-level orchestrator: `build_dist`, `check_dist`, `upload_dist` in one call |
| `run_pypi_release` | `pypi/adapter.py` | Convenience one-liner with optional post-upload `verify_install` |
| `build_dist` | `pypi/build.py` | `uv build` wrapper; cleans `dist/` before building; raises `RuntimeError` on non-zero exit |
| `upload_dist` | `pypi/upload.py` | `twine upload` wrapper; `dry_run=True` default; never raises — returns `PyPIResult` |
| `check_dist` | `pypi/upload.py` | `twine check` on `dist/`; returns list of FAILED / ERROR strings (empty = clean) |
| `verify_install` | `pypi/verify.py` | Isolated venv install from the configured index URL; optional entry-point smoke test |
| `PyPIConfig` | `pypi/models.py` | `token`, `test`, `repository_url`, `timeout` |
| `PyPIResult` | `pypi/models.py` | `status`, `package_name`, `version`, `url`, `wheel_files`, `sdist_files`, `error`, `timestamp_utc` |

**Environment variables:**

- `PYPI_TOKEN` — production PyPI API token (username `__token__`).
- `TESTPYPI_TOKEN` — TestPyPI API token; used when `PyPIConfig(test=True)`.

Both are resolved automatically from `os.environ` when `config.token` is `None`. Pass `env=` to `PyPIAdapter` for hermetic tests without real env vars.

**Usage:**

```python
from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

adapter = PyPIAdapter(PyPIConfig(test=True))         # reads TESTPYPI_TOKEN
result  = adapter.publish(Path("."), dry_run=False)  # real upload
print(result.url)                                    # https://test.pypi.org/project/.../

# Equivalent one-liner with post-upload verification
from infrastructure.publishing.pypi import run_pypi_release
result = run_pypi_release(Path("."), test=True, verify=True, package_name="mylib")
```

Flat shim `pypi_release.py` (package root) re-exports `run_test_pypi_release` for backwards compatibility; new code should import from `infrastructure.publishing.pypi`.

### static_site/ — Static-site hosting adapters

`infrastructure.publishing.static_site` provides a uniform `deploy(dry_run=True)` interface for three hosting platforms, selected via `SiteHosting` enum and the `get_adapter()` factory.

| Class | Module | Mechanism | Credentials |
| --- | --- | --- | --- |
| `GitHubPagesAdapter` | `static_site/github_pages.py` | `git push` to `gh-pages` branch | `GITHUB_TOKEN` (injected into remote URL) |
| `CloudflarePagesAdapter` | `static_site/cloudflare_pages.py` | `wrangler pages deploy` CLI | `CLOUDFLARE_API_TOKEN` |
| `NetlifyAdapter` | `static_site/netlify.py` | `netlify deploy` CLI | `NETLIFY_AUTH_TOKEN` |

**Factory:**

```python
from infrastructure.publishing.static_site import SiteDeployConfig, SiteHosting, get_adapter

config  = SiteDeployConfig(
    hosting=SiteHosting.GITHUB_PAGES,
    site_dir="output/docs",
    repo="owner/repo",
    branch="gh-pages",
)
adapter = get_adapter(config)         # returns GitHubPagesAdapter
result  = adapter.deploy(dry_run=True)
print(result.status, result.url)
```

`STATIC_SITE_ADAPTERS` is a `dict[SiteHosting, type]` mapping all three entries; import directly from `infrastructure.publishing.static_site` when iterating the registry. Every adapter's `deploy()` returns `SiteDeployResult(hosting, status, url, error, timestamp_utc)` and never raises on deployment failure.

### archival/ — Multi-target archival subpackage

`infrastructure.publishing.archival` is now a proper subpackage (previously a single flat file). The flat `archival.py` at the package root is retained as a backwards-compatible shim that re-exports the same public surface.

| Symbol | Module | Role |
| --- | --- | --- |
| `archive_publication` | `archival/orchestrate.py` | Top-level multi-provider runner |
| `ZenodoProvider` | `archival/providers.py` | Zenodo archival mirror (empty-metadata deposition) |
| `IPFSPinataProvider` | `archival/providers.py` | Content-addressed IPFS via Pinata |
| `IPFSWeb3StorageProvider` | `archival/providers.py` | Content-addressed IPFS via Web3.Storage |
| `SoftwareHeritageProvider` | `archival/providers.py` | Software Heritage save-code-now |
| `ArchivalRunResult` | `archival/models.py` | Per-provider result + aggregate |
| `load_credentials` | `archival/providers.py` | Env-var credential loader |

Prefer importing from the subpackage (`infrastructure.publishing.archival`) for new code. See [`archival/README.md`](archival/README.md) and [`archival/AGENTS.md`](archival/AGENTS.md) for the full provider reference.

### registry.py — Platform registry

`infrastructure.publishing.registry` is the single source of truth for every publishing platform adapter.

| Symbol | Role |
| --- | --- |
| `PLATFORM_REGISTRY` | Immutable tuple of all `PlatformInfo` entries, in definition order |
| `list_platforms(tier=, tag=)` | Filter-aware registry query |
| `get_platform(name)` | Lookup by name; raises `KeyError` if unknown |
| `first_class_platforms()` | Convenience: `FIRST_CLASS` tier only |
| `documented_platforms()` | Convenience: `DOCUMENTED` tier only |
| `PublishingTier` | `str` enum — `FIRST_CLASS` (implemented, tested) vs `DOCUMENTED` (future) |
| `PlatformInfo` | Frozen dataclass: `name`, `tier`, `description`, `adapter_module`, `adapter_class`, `env_vars`, `requires_network`, `supports_dry_run`, `tags` |

**Current registry contents (10 first-class + 2 documented):**

| Name | Tier | Adapter class | Tags |
| --- | --- | --- | --- |
| `zenodo` | first_class | `ZenodoProvider` | archival, doi, academic |
| `github` | first_class | — | release, software |
| `arxiv` | first_class | — | academic, preprint |
| `pypi` | first_class | `PyPIAdapter` | package, software |
| `ipfs_pinata` | first_class | `IPFSPinataProvider` | archival, ipfs, decentralized |
| `ipfs_web3storage` | first_class | `IPFSWeb3StorageProvider` | archival, ipfs, decentralized |
| `software_heritage` | first_class | `SoftwareHeritageProvider` | archival, source-code |
| `github_pages` | first_class | `GitHubPagesAdapter` | static_site, docs |
| `cloudflare_pages` | first_class | `CloudflarePagesAdapter` | static_site, hosting |
| `netlify` | first_class | `NetlifyAdapter` | static_site, hosting |
| `huggingface_hub` | documented | — | ml, dataset |
| `osf` | documented | — | academic, open-science |

```python
from infrastructure.publishing.registry import get_platform, list_platforms, PublishingTier

info = get_platform("pypi")
print(info.env_vars)       # ('PYPI_TOKEN', 'TESTPYPI_TOKEN')

static = list_platforms(tag="static_site")
print([p.name for p in static])   # ['github_pages', 'cloudflare_pages', 'netlify']

first_class = list_platforms(tier=PublishingTier.FIRST_CLASS)
```

### Backwards-compatible shims

| Module | Role |
| --- | --- |
| `platforms.py` | Re-exports `publish_to_zenodo`, `create_github_release`, `prepare_arxiv_submission` |
| `api.py` | Re-exports `ZenodoClient`, `ZenodoConfig`, `DepositionResult`, `REQUEST_TIMEOUT` |
| `archival.py` | Re-exports the `archival/` subpackage public surface |
| `pypi_release.py` | Re-exports `run_test_pypi_release` from `pypi/` |

Prefer `infrastructure.publishing.zenodo` (and sibling subpackages) for new code. Shims are retained intentionally so existing imports and tests keep working; do not add logic to shim modules.

## Public API index

| Module | Symbols | Env / credentials |
| --- | --- | --- |
| `zenodo/` | `ZenodoClient`, `ZenodoConfig`, `DepositionResult`, `PublishResult`, `publish_to_zenodo`, `publish_new_version_to_zenodo` | caller-provided token; `sandbox=True` default |
| `github/` | `create_github_release` | `GITHUB_TOKEN` |
| `arxiv/` | `prepare_arxiv_submission` | — (local tarball only) |
| `pypi/` | `PyPIAdapter`, `PyPIConfig`, `PyPIResult`, `build_dist`, `upload_dist`, `check_dist`, `run_pypi_release` | `PYPI_TOKEN` (prod), `TESTPYPI_TOKEN` (test) |
| `static_site/` | `GitHubPagesAdapter`, `CloudflarePagesAdapter`, `NetlifyAdapter`, `get_adapter`, `SiteDeployConfig`, `SiteDeployResult`, `SiteHosting` | `GITHUB_TOKEN`, `CLOUDFLARE_API_TOKEN`, `NETLIFY_AUTH_TOKEN` |
| `archival/` | `archive_publication`, `load_credentials`, `ZenodoProvider`, `IPFSPinataProvider`, `IPFSWeb3StorageProvider`, `SoftwareHeritageProvider` | `ZENODO_API_TOKEN`, `PINATA_JWT`, `WEB3_STORAGE_TOKEN` |
| `archival.py` | backwards-compat shim — same surface as `archival/` above | same as `archival/` |
| `registry.py` | `PLATFORM_REGISTRY`, `list_platforms`, `get_platform`, `first_class_platforms`, `documented_platforms`, `PublishingTier`, `PlatformInfo` | — |
| `executable_bundle.py` | `bundle_project` | — |
| `cli.py` | `main`, `publish_zenodo_command`, `extract_metadata_command`, ... | `--token`, `ZENODO_PROD_TOKEN`, `ZENODO_TOKEN` |
| `publish_cli.py` | `main` | `--token`, `--repo`, `--tag`, `--name` |
| `scripts/publish_project_release.py` | `run_release_workflow` (via thin script) | `--project`, `--tag`, `--repo`, GitHub + Zenodo tokens |
| `archival_cli.py` | `main`, `_build_providers` | `--commit` for real deposits |
| `citations.py` | `generate_citation_*`, `format_authors_apa`, `format_authors_mla` | — |
| `pypi_release.py` | `run_test_pypi_release` (manual TestPyPI gate; not pytest) — shim for `pypi/` | `TEST_PYPI_API_TOKEN` via `scripts/publish/test_pypi.py` |

Archival Zenodo deposits use empty deposition metadata (bundle mirror). Rich metadata paths: `publish_to_zenodo` and `cli.publish_zenodo_command`.

## Future (deferred)

- Metadata subpackage consolidation
- HuggingFace Hub adapter (`huggingface_hub` entry in `PLATFORM_REGISTRY` is `DOCUMENTED`)
- Open Science Framework adapter (`osf` entry in `PLATFORM_REGISTRY` is `DOCUMENTED`)

## Key features

### Metadata extraction

```python
from infrastructure.publishing import extract_publication_metadata

metadata = extract_publication_metadata([Path("manuscript.md")])
```

### Citation generation

```python
from infrastructure.publishing import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
)

bibtex = generate_citation_bibtex(metadata)
```

### Publishing to platforms

```python
from infrastructure.publishing import (
    publish_to_zenodo,
    prepare_arxiv_submission,
    create_github_release,
)

result = publish_to_zenodo(metadata, files, access_token)
assert isinstance(result.doi, str)
arxiv_package = prepare_arxiv_submission(Path("output/"), metadata)
url = create_github_release("v1.0", "Release 1.0", "Notes", files, token, "owner/repo")
```

### PyPI / TestPyPI publishing

```python
from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig

adapter = PyPIAdapter(PyPIConfig(test=True))           # reads TESTPYPI_TOKEN
result  = adapter.publish(Path("."), dry_run=False)    # real TestPyPI upload
print(result.url)

# One-liner with verify
from infrastructure.publishing.pypi import run_pypi_release
result = run_pypi_release(Path("."), test=False, verify=True, package_name="mylib")
```

### Static-site deployment

```python
from infrastructure.publishing.static_site import (
    SiteDeployConfig, SiteHosting, get_adapter,
)

config  = SiteDeployConfig(
    hosting=SiteHosting.CLOUDFLARE_PAGES,
    site_dir="output/docs",
    project_name="my-docs",
)
result = get_adapter(config).deploy(dry_run=False)
print(result.url)
```

### Unified release (GitHub + Zenodo + DOI to render)

```python
from pathlib import Path

from infrastructure.publishing.release_workflow import ReleaseRequest, run_release_workflow

result = run_release_workflow(
    ReleaseRequest(
        repo_root=Path("."),
        project_name="template_code_project",
        tag="v2.0.0",
        github_repo="owner/template",
        github_token="ghp_...",
        zenodo_token="...",
        sandbox=True,
    )
)
print(result.doi, result.receipt_path, result.pdf_sha256)
```

### Transmission bookends

```python
from pathlib import Path

from infrastructure.publishing.transmission_bookends import write_transmission_bookends

paths = write_transmission_bookends(
    Path("projects/templates/template_prose_project"),
    "template_prose_project",
    repo_root=Path("."),
)
# None when publication.transmission_bookends.enabled is false
```

When enabled, [`PDFRenderer.render_combined`](../rendering/pdf_renderer.py) passes `skip_title_page=True` and `before_end_transmission=True` into [`inject_latex_preamble` / `inject_bibliography`](../rendering/_pdf_combined_renderer.py) so BEGIN is page 1 and END is the last page. Bookends embed `output/figures/transmission_integrity_strip.png` from `write_transmission_barcode_strip` and write `output/data/transmission_manifest.json`. End bookend dedupes metadata; prior rows capped at `min(max_prior_releases, 3)`.

```python
from pathlib import Path

from infrastructure.publishing.transmission_page_check import check_transmission_bookend_pages

result = check_transmission_bookend_pages(
    Path("projects/templates/template_code_project/output/pdf/template_code_project_combined.pdf")
)
assert result.valid, result.issues
```

Stage 04 (`infrastructure.validation.output.pipeline.validate_transmission_bookends`) calls the same check when bookends are enabled.

### Deposit upload filename

Local renders keep `{project}_combined.pdf`. `prepare_release_bundle` copies the combined PDF into `output/{project}/release_bundle/` under a metadata-driven name for Zenodo and GitHub uploads:

```python
from infrastructure.publishing.deposit_filename import build_deposit_filename
from infrastructure.publishing.metadata_from_config import publication_metadata_from_config

metadata = publication_metadata_from_config(Path("projects/templates/template_code_project/manuscript/config.yaml"))
name = build_deposit_filename(
    metadata=metadata,
    pdf_sha256="b591a0ce...",
    project_name="template_code_project",
    release_tag="v2.0.0",
    deposit_filename_config={"enabled": True},
)
# Author_2026_Convergence_b591a0ce.pdf
```

Pattern: `{Author}_{Year}_{Topic}_{Hash8}.pdf` (PascalCase author/topic segments; lowercase hash prefix). Config: `publication.deposit_filename.enabled` (default true), `publication.deposit_filename.topic` (optional override). Set `enabled: false` to restore `{project}_combined.pdf`. Manifest/receipt fields: `deposit_filename`, `source_pdf_name`.

### Plaintext deposit metadata

```python
from pathlib import Path

from infrastructure.publishing.abstract_plaintext import (
    DepositCrossLinks,
    build_deposit_description,
    build_github_release_body,
    render_abstract_plaintext,
)

cross_links = DepositCrossLinks(
    project="template_prose_project",
    tag="v1.0.0",
    github_repo="owner/repo",
    pdf_sha256="abc123...",
    doi="10.5281/zenodo.12345",
)
description = build_deposit_description(
    abstract_source=Path("projects/templates/template_prose_project/manuscript/00_abstract.md"),
    variables_path=Path("output/template_prose_project/data/manuscript_variables.json"),
    cross_links=cross_links,
    override_text=None,  # or publication.zenodo_description from config
)
github_body = build_github_release_body(
    project_name="template_prose_project",
    tag="v1.0.0",
    abstract_plaintext=render_abstract_plaintext(Path(".../00_abstract.md")),
    doi="10.5281/zenodo.12345",
    pdf_sha256="abc123...",
)
```

Thin orchestrator (opt-in; not part of the default pipeline DAG):

```bash
uv run python scripts/publish_project_release.py \
  --project template_code_project \
  --tag v2.0.0 \
  --repo owner/template \
  --dry-run

# Production Zenodo after render pipeline:
uv run python scripts/publish_project_release.py \
  --project template_code_project \
  --tag v2.0.0 \
  --repo owner/template \
  --production
```

Environment: `GITHUB_TOKEN`, `GITHUB_REPO`, `ZENODO_SANDBOX_TOKEN` (sandbox) or `ZENODO_PROD_TOKEN` / `ZENODO_TOKEN` (production). Metadata is read from `projects/{name}/manuscript/config.yaml` and `00_abstract.md`. The default workflow publishes to **Zenodo first**, patches the live deposition description with the minted DOI (best-effort via `patch_deposition_description`), then creates the GitHub release (body includes DOI, Zenodo URL, GitHub URL, version, and PDF hash), writes `publication.doi`, and re-renders locally. With `--reserve-doi-first`, the workflow creates a Zenodo draft, reserves the version DOI, writes the concept DOI to `publication.doi` and the version DOI to `publication.version_doi`, re-renders first, uploads the DOI-bearing PDF to that draft, publishes, and only then creates the GitHub release. Deposit descriptions use plaintext normalization (`abstract_plaintext.py`); see [`docs/guides/publishing-guide.md`](../../docs/guides/publishing-guide.md).

`publish_to_zenodo` and `publish_new_version_to_zenodo` return `PublishResult(doi, deposition_id)` from `infrastructure.publishing.zenodo.models`.

Or import from subpackages directly:

```python
from infrastructure.publishing.zenodo import ZenodoClient, ZenodoConfig
```

## Testing

```bash
uv run pytest tests/infra_tests/publishing/
```

## Configuration

Environment variables:

- `ZENODO_TOKEN` / `ZENODO_PROD_TOKEN` — Zenodo API (CLI, production release workflow, and direct `publish_to_zenodo` calls)
- `ZENODO_SANDBOX_TOKEN` — sandbox token for `scripts/publish_project_release.py`
- `ZENODO_API_TOKEN` — archival Zenodo provider
- `GITHUB_TOKEN` — GitHub releases and GitHub Pages deployment
- `PYPI_TOKEN` — PyPI production upload (`pypi/` subpackage; `__token__` username)
- `TESTPYPI_TOKEN` — TestPyPI upload (`PyPIConfig(test=True)`)
- `CLOUDFLARE_API_TOKEN` — Cloudflare Pages deployment via Wrangler CLI
- `NETLIFY_AUTH_TOKEN` — Netlify deployment via netlify CLI
- `PINATA_JWT` — IPFS archival via Pinata
- `WEB3_STORAGE_TOKEN` — IPFS archival via Web3.Storage

## Troubleshooting

### Zenodo upload fails

- Verify token matches sandbox vs production (`sandbox=True` default).
- Uploads must use the bucket URL from `create_deposition`, not the deposition id.
- Check file sizes and API rate limits.

### GitHub release creation fails

- Token needs `repo` scope; tag must not already exist.

### arXiv package issues

- Ensure `manuscript/` sibling of `output/` contains `.tex` / `.bib` sources.

### PyPI upload fails

- Check that `PYPI_TOKEN` / `TESTPYPI_TOKEN` is set and valid.
- Run `check_dist(dist_dir)` before uploading — returns a list of twine issues.
- `dry_run=True` is the default; pass `dry_run=False` explicitly for real uploads.
- `PyPIResult.status == "error"` and `PyPIResult.error` contain the failure reason without raising.

### Static-site deployment fails

- GitHub Pages: token needs `repo` scope; `gh-pages` branch is created automatically on first push.
- Cloudflare Pages: ensure `wrangler` CLI is installed (`npm i -g wrangler`) and `CLOUDFLARE_API_TOKEN` has Pages edit permission.
- Netlify: ensure `netlify` CLI is installed (`npm i -g netlify-cli`) and `NETLIFY_AUTH_TOKEN` is set.
- All adapters return `SiteDeployResult` and never raise; inspect `result.status` and `result.error`.

## See also

- [README.md](README.md)
- [`zenodo/AGENTS.md`](zenodo/AGENTS.md) · [`github/AGENTS.md`](github/AGENTS.md) · [`arxiv/AGENTS.md`](arxiv/AGENTS.md) · [`archival/AGENTS.md`](archival/AGENTS.md) · [`pypi/AGENTS.md`](pypi/AGENTS.md) · [`static_site/AGENTS.md`](static_site/AGENTS.md)
- [`../core/`](../core/) · [`../validation/`](../validation/)
