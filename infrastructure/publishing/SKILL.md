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

`registry.py` is the single source of truth for all adapter metadata (10 first-class + 2 documented platforms).

```python
from infrastructure.publishing.registry import get_platform, list_platforms, PublishingTier

info = get_platform("pypi")
print(info.env_vars)   # ('PYPI_TOKEN', 'TESTPYPI_TOKEN')

for p in list_platforms(tag="static_site"):
    print(p.name, p.adapter_class)
```

## Publication readiness

```python
from infrastructure.publishing import validate_publication_readiness, create_submission_checklist

readiness = validate_publication_readiness(project_path)
checklist = create_submission_checklist(metadata)
```

## Executable bundle (Stage 10)

```python
from infrastructure.publishing.executable_bundle import bundle_project

manifest_path = bundle_project(project_root, output_dir)
```

## Multi-target archival (Stage 11)

`archival/` is a proper subpackage. The flat `archival.py` at the package root is a backwards-compat shim that re-exports the same surface.

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
  --bundle output/template_code_project/executable_bundle \
  --providers zenodo software_heritage ipfs_pinata ipfs_web3storage
```

See [`archival/README.md`](archival/README.md) and `scripts/09_archive_publication.py`.
