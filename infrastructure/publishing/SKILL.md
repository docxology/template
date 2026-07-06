---
name: infrastructure-publishing
description: Skill for the publishing infrastructure module providing academic publishing workflows including BibTeX CLI citation generation, APA/MLA citation helper functions, DOI management, Zenodo publication, arXiv submission preparation, GitHub releases, PyPI and TestPyPI package distribution, static-site deployment to GitHub Pages / Cloudflare Pages / Netlify, multi-target long-horizon archival (IPFS Pinata, Web3.Storage, Software Heritage), a central platform registry, and publication readiness validation. Use when publishing research, generating citations, minting DOIs, distributing Python packages, deploying documentation sites, or preparing archival submissions.
---

# Publishing Module

Academic publishing and dissemination tools for research projects.

## Platform subpackages

| Path | Use when |
| --- | --- |
| `infrastructure.publishing.zenodo` | Zenodo deposit, upload, publish, DOI |
| `infrastructure.publishing.github` | GitHub release + assets |
| `infrastructure.publishing.arxiv` | arXiv tarball from manuscript tree |
| `infrastructure.publishing.pypi` | PyPI / TestPyPI package distribution |
| `infrastructure.publishing.static_site` | GitHub Pages, Cloudflare Pages, or Netlify deployment |
| `infrastructure.publishing.archival` | IPFS Pinata, Web3.Storage, Software Heritage, Zenodo mirror |
| `infrastructure.publishing.registry` | Enumerate or look up all platform adapters |

Root exports (`infrastructure.publishing`) and `platforms.py` / `api.py` remain for backwards compatibility.

## Publication metadata

```python
from infrastructure.publishing import PublicationMetadata, extract_publication_metadata

metadata = extract_publication_metadata([Path("manuscript/01_introduction.md")])
```

The `publication:` block in `manuscript/config.yaml` records durable identifiers
(`doi`, `version_doi`, `version_record`, `github_repository`, `repository_url`).
The `publication.published_artifacts` key — a `{platform_name: durable_url}` map —
records artifacts published outside those fields (e.g. an IPFS CID or a
HuggingFace dataset URL) and is consumed by `status_report.py` to mark those
platforms as published.

## Citation generation

The Python API exposes BibTeX, APA, and MLA helpers. The
`infrastructure.publishing.cli generate-citation` command currently exposes
BibTeX only.

```python
from infrastructure.publishing import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla,
)

bibtex = generate_citation_bibtex(metadata)
```

## Zenodo publication

```python
from infrastructure.publishing.zenodo import publish_to_zenodo, ZenodoClient, ZenodoConfig

result = publish_to_zenodo(metadata, [Path("output/paper.pdf")], access_token="...", sandbox=True)
print(result.doi)

config = ZenodoConfig(access_token="...", sandbox=True)
client = ZenodoClient(config)
dep = client.create_deposition({"title": metadata.title, "upload_type": "publication"})
client.upload_file(dep.bucket_url, Path("paper.pdf"))
doi = client.publish(dep.deposition_id)
```

## arXiv submission

```python
from infrastructure.publishing.arxiv import prepare_arxiv_submission

package = prepare_arxiv_submission(output_dir, metadata)
```

## GitHub releases

```python
from infrastructure.publishing.github import create_github_release

url = create_github_release(
    "v1.0.0", "Release 1.0.0", "Notes", [Path("paper.pdf")], token, "owner/repo"
)
```

## PyPI / TestPyPI distribution

`pypi/` implements a build, check, upload pipeline via `uv build` and `twine`. `dry_run=True` is the default at every layer — no accidental uploads.

```python
from infrastructure.publishing.pypi import PyPIAdapter, PyPIConfig, run_pypi_release

# Using the adapter directly
adapter = PyPIAdapter(PyPIConfig(test=True))       # reads TESTPYPI_TOKEN from env
result  = adapter.publish(Path("."), dry_run=False)
print(result.status, result.url)

# One-liner with post-upload verification
result = run_pypi_release(
    Path("."),
    test=False,          # production PyPI
    dry_run=False,
    verify=True,
    package_name="mylib",
)
```

Environment: `PYPI_TOKEN` (production), `TESTPYPI_TOKEN` (test). Both resolved from `os.environ` when `config.token` is `None`.

## Static-site deployment

`static_site/` provides `GitHubPagesAdapter`, `CloudflarePagesAdapter`, and `NetlifyAdapter` behind a common `deploy(dry_run=True)` interface.

```python
from infrastructure.publishing.static_site import (
    SiteDeployConfig, SiteHosting, get_adapter,
)

config  = SiteDeployConfig(
    hosting=SiteHosting.GITHUB_PAGES,
    site_dir="output/docs",
    repo="owner/repo",
    branch="gh-pages",
)
result = get_adapter(config).deploy(dry_run=False)
print(result.status, result.url)
```

Credentials: `GITHUB_TOKEN` (GitHub Pages), `CLOUDFLARE_API_TOKEN` (Cloudflare), `NETLIFY_AUTH_TOKEN` (Netlify). All adapters never raise on failure — inspect `result.status` and `result.error`.

## Platform registry

`registry.py` is the single source of truth for all adapter metadata (12 first-class platforms; `documented_platforms()` is currently empty).

```python
from infrastructure.publishing.registry import get_platform, list_platforms, PublishingTier

info = get_platform("pypi")
print(info.env_vars)   # ('PYPI_TOKEN', 'TESTPYPI_TOKEN')

for p in list_platforms(tag="static_site"):
    print(p.name, p.adapter_class)
```

## README publishing-status compilation

`status_report.py` turns the registry (which platforms exist) plus a project's
`manuscript/config.yaml` (what has been published) into a regenerable README
block delimited by `<!-- PUBLISHING-STATUS:START ... -->` / `<!-- PUBLISHING-STATUS:END -->`
markers. The committed block reflects durable publication state (DOIs, repo,
`published_artifacts`) only — never machine-specific credential presence.

```python
from pathlib import Path
from infrastructure.publishing.status_report import (
    compile_publishing_status, render_status_block, update_readme_block,
)

report = compile_publishing_status(Path("projects/templates/template_gold_refinement"))
print(report.published_count)              # e.g. 7
block = render_status_block(report)        # marker-wrapped Markdown
new_text, changed = update_readme_block(
    readme_text, report, init_after_heading="## Publication and rendering"
)
```

A caller-supplied `published={"ipfs_pinata": "https://..."}` map upgrades extra
rows to PUBLISHED, overriding config. `PublicationState` is `PUBLISHED`,
`AVAILABLE`, or `PLANNED`.

```bash
uv run python -m infrastructure.publishing.status_report --project <path> --write \
  --init-after "## Publication and rendering"
uv run python -m infrastructure.publishing.status_report --project <path> --check  # CI gate: exits non-zero on drift
```

## Credential verification

`credential_check.py` is a read-only, non-destructive check that publishing
credentials authenticate. It sends a single GET per platform and never writes,
uploads, or prints token values. `PROBES` covers `github`, `huggingface_hub`,
`osf`, `ipfs_pinata`, `zenodo`, `netlify`, `cloudflare_pages`, `gumroad`,
`leanpub`, and `stripe`; `pypi` has no read-only endpoint and reports
`no-endpoint`.

```python
from infrastructure.publishing.credential_check import check_all, format_results

results = check_all(only=["github", "zenodo"])   # ProbeResult.status: pass|fail|skipped|no-endpoint
print(format_results(results))
```

```bash
uv run python -m infrastructure.publishing.credential_check [--only NAMES] [--env-file .env]
# exits 1 if any present credential fails
```

## Multi-platform upload runner

`upload_runner.py` houses the reusable per-platform upload helpers and the batch
orchestrator (extracted from `scripts/publish/upload_gold_refinement.py`, now a
thin CLI). Every uploader is dry-run by default and returns a receipt dict; a
per-platform failure is captured, never aborting the batch.

```python
from pathlib import Path
from infrastructure.publishing.upload_runner import (
    UploadTargets, select_jobs, run_uploads,
)

targets = UploadTargets(
    project_root=Path("."),
    pdf=Path("output/paper.pdf"),
    web_dir=Path("output/web"),
    hf_repo_id="org/dataset",
    github_repo="owner/repo",
    osf_title="My Project",
)
jobs = select_jobs(include_github=False, include_static=False)  # CORE_UPLOADERS only
run = run_uploads(targets, jobs=jobs, commit=False)             # dry-run
print(run.mode, run.ok, run.results)
```

`CORE_UPLOADERS` are `pinata`, `huggingface`, `osf`, `testpypi`;
`OPTIONAL_UPLOADERS` (`github`, `netlify`, `cloudflare`) are opt-in via
`include_github` / `include_static`. `commit=True` performs real uploads.

## Publication readiness

```python
from infrastructure.publishing import validate_publication_readiness, create_submission_checklist

readiness = validate_publication_readiness(markdown_files, pdf_files)  # both list[Path]
# -> dict: ready_for_publication, completeness_score, missing_elements, recommendations, skipped_files
checklist = create_submission_checklist(metadata)
```

## Executable bundle (Stage 12)

```python
from infrastructure.publishing.executable_bundle import bundle_project

manifest_path = bundle_project(project_root, output_dir)
```

## Multi-target archival (Stage 13)

`archival/` is a proper subpackage. The flat `archival.py` shim that used to sit at the package root has been removed; `import infrastructure.publishing.archival` resolves directly to the package.

```python
from infrastructure.publishing.archival import (
    ZenodoProvider,
    IPFSPinataProvider,
    SoftwareHeritageProvider,
    archive_publication,
)

run = archive_publication(
    Path("output/project/executable_bundle"),
    providers=[ZenodoProvider(token=None), SoftwareHeritageProvider()],
    dry_run=True,
)
```

CLI dry-run:

```bash
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/templates/template_code_project/executable_bundle \
  --providers zenodo software_heritage ipfs_pinata ipfs_web3storage
```

See [`archival/README.md`](archival/README.md) and `scripts/runner/archive_publication.py`.
