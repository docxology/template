# Publishing Module

## Purpose

The Publishing module provides tools for academic publishing workflows. It enables DOI management, citation generation in multiple formats, publication metadata extraction, and automated publishing to major academic platforms (Zenodo, arXiv, GitHub).

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
| `archival.py` | Multi-target archival providers (Stage 11) — see [`archival/README.md`](archival/README.md) |
| `executable_bundle.py` | Stage 10 executable bundle |
| `cli.py`, `publish_cli.py`, `archival_cli.py` | CLI entry points |

### Platform subpackages

| Subpackage | Role |
| --- | --- |
| [`zenodo/`](zenodo/) | [Zenodo REST Deposit API](https://developers.zenodo.org/) — `ZenodoClient`, `publish_to_zenodo` |
| [`github/`](github/) | GitHub Releases API — `create_github_release` |
| [`arxiv/`](arxiv/) | Local arXiv tarball preparation — `prepare_arxiv_submission` |

### Backwards-compatible shims

| Module | Role |
| --- | --- |
| `platforms.py` | Re-exports `publish_to_zenodo`, `create_github_release`, `prepare_arxiv_submission` |
| `api.py` | Re-exports `ZenodoClient`, `ZenodoConfig`, `DepositionResult`, `REQUEST_TIMEOUT` |

Prefer `infrastructure.publishing.zenodo` (and sibling subpackages) for new code. Shims are retained intentionally so existing imports and tests keep working; do not add logic to shim modules.

## Public API index

| Module | Symbols | Env / credentials |
| --- | --- | --- |
| `zenodo/` | `ZenodoClient`, `ZenodoConfig`, `DepositionResult`, `PublishResult`, `publish_to_zenodo`, `publish_new_version_to_zenodo` | caller-provided token; `sandbox=True` default |
| `github/` | `create_github_release` | `GITHUB_TOKEN` |
| `arxiv/` | `prepare_arxiv_submission` | — (local tarball only) |
| `archival.py` | `archive_publication`, `load_credentials`, `ZenodoProvider`, … | `ZENODO_API_TOKEN`, `PINATA_JWT`, `WEB3_STORAGE_TOKEN` |
| `executable_bundle.py` | `bundle_project` | — |
| `cli.py` | `main`, `publish_zenodo_command`, `extract_metadata_command`, … | `--token`, `ZENODO_PROD_TOKEN`, `ZENODO_TOKEN` |
| `publish_cli.py` | `main` | `--token`, `--repo`, `--tag`, `--name` |
| `scripts/publish_project_release.py` | `run_release_workflow` (via thin script) | `--project`, `--tag`, `--repo`, GitHub + Zenodo tokens |
| `archival_cli.py` | `main`, `_build_providers` | `--commit` for real deposits |
| `citations.py` | `generate_citation_*`, `format_authors_apa`, `format_authors_mla` | — |
| `pypi_release.py` | `run_test_pypi_release` (manual TestPyPI gate; not pytest) | `TEST_PYPI_API_TOKEN` via `scripts/publish/test_pypi.py` |

Archival Zenodo deposits use empty deposition metadata (bundle mirror). Rich metadata paths: `publish_to_zenodo` and `cli.publish_zenodo_command`.

## Future (deferred)

- Split `archival.py` into `archival/providers/` submodules (file is ~670 lines, under 1k gate)
- Metadata subpackage consolidation

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

### Unified release (GitHub + Zenodo + DOI → render)

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
    pdf_sha256="b591a0ce…",
    project_name="template_code_project",
    release_tag="v2.0.0",
    deposit_filename_config={"enabled": True},
)
# → Author_2026_Convergence_b591a0ce.pdf
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
- `GITHUB_TOKEN` — GitHub releases

## Troubleshooting

### Zenodo upload fails

- Verify token matches sandbox vs production (`sandbox=True` default).
- Uploads must use the bucket URL from `create_deposition`, not the deposition id.
- Check file sizes and API rate limits.

### GitHub release creation fails

- Token needs `repo` scope; tag must not already exist.

### arXiv package issues

- Ensure `manuscript/` sibling of `output/` contains `.tex` / `.bib` sources.

## See also

- [README.md](README.md)
- [`zenodo/AGENTS.md`](zenodo/AGENTS.md) · [`github/AGENTS.md`](github/AGENTS.md) · [`arxiv/AGENTS.md`](arxiv/AGENTS.md)
- [`../core/`](../core/) · [`../validation/`](../validation/)
