# Publishing Module

> **Academic publishing workflow assistance**

**Location:** `infrastructure/publishing/` — see [`infrastructure/publishing/AGENTS.md`](../../../infrastructure/publishing/AGENTS.md) for the full API index.

**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Architecture

| Path | Role |
| --- | --- |
| `registry.py` | Single source of truth for the publishing surface — `PLATFORM_REGISTRY`, `list_platforms`, `get_platform`, `first_class_platforms` |
| `metadata.py`, `_metadata_*.py` | Metadata extraction and reporting |
| `citations.py` | Citation helpers: BibTeX CLI target plus APA/MLA library helpers |
| `zenodo/` | Zenodo Deposit API — `ZenodoClient`, `publish_to_zenodo`, `publish_new_version_to_zenodo`, `reserve_zenodo_deposition`, `publish_reserved_deposition_to_zenodo` |
| `github/` | GitHub Releases — `create_github_release` |
| `arxiv/` | arXiv tarball — `prepare_arxiv_submission` |
| `pypi/` | PyPI / TestPyPI distribution — `PyPIAdapter`, `run_pypi_release` |
| `archival/providers.py` | IPFS (Pinata, Web3.Storage) and Software Heritage deposit providers |
| `static_site/` | Static-site deploys — `GitHubPagesAdapter`, `CloudflarePagesAdapter`, `NetlifyAdapter` |
| `huggingface/` | HuggingFace Hub publishing — `HuggingFaceHubAdapter` |
| `osf/` | Open Science Framework deposit — `OSFAdapter` |
| `metadata_from_config.py`, `config_doi.py` | Config-driven metadata and DOI write-back |
| `status_report.py` | Compile the registry + `config.yaml` into a regenerable README publishing-status block |
| `credential_check.py` | Read-only, non-destructive verification that publishing credentials authenticate |
| `upload_runner.py` | Reusable multi-platform upload dispatch (`UploadTargets`, `select_jobs`, `run_uploads`) |
| `release_workflow.py` | Unified GitHub + Zenodo + re-render orchestration |
| `release_workflow_zenodo.py` | Reserve-first DOI phase and Zenodo publish paths |
| `platforms.py`, `api.py` | Backwards-compatible re-exports |
| `executable_bundle.py` | Stage 12 executable bundle (`bundle_project`) |
| `archival/` | Stage 13 multi-target archival — see [`archival/README.md`](../../../infrastructure/publishing/archival/README.md) |
| `cli.py`, `publish_cli.py`, `archival_cli.py` | CLI entry points |
| `scripts/publish_project_release.py` | Thin orchestrator for unified release (opt-in) |
| `scripts/publish/upload_gold_refinement.py` | Thin CLI over `upload_runner` (worked example) |

---

## Platform Registry

`registry.py` is the single source of truth for the publishing surface. It exposes
**12 platforms, all `first_class`** (`tier=PublishingTier.FIRST_CLASS` — implemented,
tested, and locally verifiable). Adding a platform here automatically surfaces it in
the README status block (see [Publishing Status Report](#publishing-status-report))
and the credential check.

| Platform | Adapter (class / entry) | Env vars | Tier |
| --- | --- | --- | --- |
| `zenodo` | `ZenodoProvider` / `publish_to_zenodo` | `ZENODO_API_TOKEN` | first-class |
| `github` | `create_github_release` | `GITHUB_TOKEN` | first-class |
| `arxiv` | `prepare_arxiv_submission` | _(none — local tarball)_ | first-class |
| `pypi` | `PyPIAdapter` / `run_pypi_release` | `PYPI_TOKEN`, `TESTPYPI_TOKEN` | first-class |
| `ipfs_pinata` | `IPFSPinataProvider.deposit` | `PINATA_JWT` | first-class |
| `ipfs_web3storage` | `IPFSWeb3StorageProvider.deposit` | `WEB3_STORAGE_TOKEN` | first-class |
| `software_heritage` | `SoftwareHeritageProvider.deposit` | _(none — public repo save-code-now)_ | first-class |
| `github_pages` | `GitHubPagesAdapter.deploy` | `GITHUB_TOKEN` | first-class |
| `cloudflare_pages` | `CloudflarePagesAdapter.deploy` | `CLOUDFLARE_API_TOKEN` | first-class |
| `netlify` | `NetlifyAdapter.deploy` | `NETLIFY_AUTH_TOKEN` | first-class |
| `huggingface_hub` | `HuggingFaceHubAdapter.publish` | `HUGGINGFACE_TOKEN` / `HF_TOKEN` | first-class |
| `osf` | `OSFAdapter.publish` | `OSF_TOKEN` | first-class |

```python
from infrastructure.publishing.registry import first_class_platforms, get_platform

print(len(first_class_platforms()))      # 12
zenodo = get_platform("zenodo")
print(zenodo.env_vars)                    # ('ZENODO_API_TOKEN',)
print(zenodo.adapter_module, zenodo.adapter_class)
```

`PlatformInfo` also records `description`, `requires_network`, `supports_dry_run`,
and `tags` (e.g. `archival`, `doi`, `static_site`). Filter with
`list_platforms(tier=..., tag=...)`.

---

## Key Features

- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX from the CLI; BibTeX, APA, and MLA through Python helpers
- **Publication Metadata**: Comprehensive metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Platform registry**: 12 first-class platforms (`registry.py`) — single source of truth
- **Platform publishing**: Zenodo, arXiv, GitHub Releases, PyPI/TestPyPI, IPFS, Software Heritage, HuggingFace Hub, OSF, static-site hosts
- **Long-horizon archival**: Zenodo, Software Heritage, IPFS providers
- **Status reporting**: Regenerable README publishing-status block (`status_report.py`)
- **Credential verification**: Read-only, non-destructive token checks (`credential_check.py`)
- **Multi-platform upload dispatch**: Batch uploads with per-platform error isolation (`upload_runner.py`)

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

### Publishing Status Report

`status_report.py` compiles the registry plus a project's `manuscript/config.yaml`
into a compact, regenerable Markdown block for the project README. The committed
block reflects **durable publication state only** — DOIs, repository, and release
identifiers recorded in `config.yaml`. It never encodes machine-specific credential
presence (that is the separate, opt-in concern of `credential_check.py`).

The block is delimited by stable HTML-comment markers so it can be rewritten
deterministically without disturbing surrounding prose:

```
<!-- PUBLISHING-STATUS:START (generated by infrastructure.publishing.status_report) -->
...
<!-- PUBLISHING-STATUS:END -->
```

```python
from pathlib import Path

from infrastructure.publishing.status_report import (
    compile_publishing_status,
    update_readme_block,
    status_report_is_current,
)

report = compile_publishing_status(Path("projects/templates/template_gold_refinement"))
print(report.published_count)            # e.g. 7
print([(p.name, p.state.value) for p in report.platforms])

readme = Path("README.md").read_text(encoding="utf-8")
new_text, changed = update_readme_block(
    readme, report, init_after_heading="## Publication and rendering"
)
if changed:
    Path("README.md").write_text(new_text, encoding="utf-8")
```

Key API:

- `compile_publishing_status(project_root, *, config_path=None, published=None) -> PublishingStatusReport`
  — a caller-supplied `published` map (platform → URL) overrides config and only
  ever upgrades a row to `PUBLISHED`.
- `render_status_markdown(report)` / `render_status_block(report)` — render the
  inner Markdown / the full marker-wrapped block.
- `update_readme_block(readme_text, report, *, init_after_heading=None) -> (text, changed)`.
- `status_report_is_current(readme_text, report)` — drift check used by `--check`.

Each platform row carries a `PublicationState`:

- `PUBLISHED` — a durable identifier exists (DOI, repo, release, CID).
- `AVAILABLE` — adapter implemented and locally verifiable, not yet published here.
- `PLANNED` — documented intent only, no live adapter.

### Credential Check

`credential_check.py` answers one question reproducibly — *can we actually publish?*
For each platform that exposes a read-only identity endpoint, it sends a single
authenticated `GET` and reports whether the token authenticates. It never writes,
uploads, or mutates anything, and **token values are never printed** (only HTTP
status and public identity fields such as login or account name).

```python
from infrastructure.publishing.credential_check import check_all, format_results

results = check_all(only=["github", "zenodo"])
print(format_results(results))
for r in results:
    print(r.name, r.status, r.ok)        # status: pass | fail | skipped | no-endpoint
```

The `PROBES` catalogue covers `github`, `huggingface_hub`, `osf`, `ipfs_pinata`,
`zenodo`, `netlify`, `cloudflare_pages`, and the monetization-adjacent platforms
`gumroad`, `leanpub`, and `stripe`. `pypi` has no read-only endpoint, so it
reports `no-endpoint` (its token is validated at upload time). `run_probe(probe, env,
*, override_base=None)` accepts an `override_base` to redirect the host for tests.

### Multi-Platform Upload Runner

`upload_runner.py` houses the per-platform upload helpers and the batch orchestrator
(extracted from `scripts/publish/upload_gold_refinement.py`, now a thin CLI). Every
uploader is **dry-run by default** and returns a plain `dict` receipt; a failure in
one platform is captured, never raised, so a batch always completes.

```python
from pathlib import Path

from infrastructure.publishing.upload_runner import (
    UploadTargets,
    select_jobs,
    run_uploads,
)

targets = UploadTargets(
    project_root=Path("projects/templates/template_gold_refinement"),
    pdf=Path("output/pdf/template_gold_refinement_combined.pdf"),
    web_dir=Path("output/web"),
    hf_repo_id="docxology/template_gold_refinement",
    github_repo="docxology/template_gold_refinement",
    osf_title="Refinement of Gold",
)

jobs = select_jobs()                      # CORE_UPLOADERS only (dry-run safe)
run = run_uploads(targets, jobs=jobs, commit=False)
print(run.mode, run.ok)                   # "DRY-RUN", True
print(run.results)
```

- `CORE_UPLOADERS` = `{pinata, huggingface, osf, testpypi}` (run by default).
- `OPTIONAL_UPLOADERS` = `{github, netlify, cloudflare}` (opt-in — real release /
  CLI dependencies).
- `select_jobs(*, only=None, include_github=False, include_static=False)` resolves
  the ordered uploader set.
- `run_uploads(targets, *, jobs, commit, env=None) -> UploadRun`; `UploadRun.results`,
  `.mode`, and `.ok` (false when any receipt has `status == "error"`).

### Publication config schema (`published_artifacts`)

The `publication:` block in `projects/<name>/manuscript/config.yaml` holds the
durable identifiers consumed by `status_report.py`:

```yaml
publication:
  doi: "10.5281/zenodo.20931955"          # concept DOI
  version_doi: "10.5281/zenodo.20938523"
  version_record: "https://zenodo.org/records/20938523"
  github_repository: "docxology/template_gold_refinement"
  repository_url: "https://github.com/docxology/template_gold_refinement"
  repository_label: "docxology/template_gold_refinement"
  journal: ""
  volume: ""
  pages: ""
  year: "2026"
  # Durable references for artifacts published outside the Zenodo/GitHub pair.
  # platform_name -> durable URL; marks the platform PUBLISHED in the status block.
  published_artifacts:
    ipfs_pinata: "https://gateway.pinata.cloud/ipfs/Qm..."
    huggingface_hub: "https://huggingface.co/datasets/ActiveInference/template_gold_refinement"
    osf: "https://osf.io/u485p/"
    pypi: "https://test.pypi.org/project/template-gold-refinement/0.1.0/"
    software_heritage: "https://archive.softwareheritage.org/browse/origin/?origin_url=..."
```

`zenodo` (via `doi`) and `github` (via `github_repository`) are marked `PUBLISHED`
automatically; `published_artifacts` records the rest. A caller-supplied `published=`
map (or the CLI `--published name=url`) overrides config.

---

## Worked Example: `template_gold_refinement`

`template_gold_refinement` was published and fetch-back-confirmed on **2026-06-27**
across all credentialed platforms — the canonical end-to-end example:

| Platform | Durable identifier |
| --- | --- |
| `zenodo` | concept DOI `10.5281/zenodo.20931955`, version DOI `10.5281/zenodo.20938523` |
| `github` | release `v0.1.0` of `docxology/template_gold_refinement` |
| `ipfs_pinata` | CID `QmQBXK5qoGv5NSWC8mzcx22AgkHeqBJL8z8HrCgEy7nzio` |
| `huggingface_hub` | `https://huggingface.co/datasets/ActiveInference/template_gold_refinement` |
| `osf` | `https://osf.io/u485p/` |
| `pypi` (TestPyPI) | `template-gold-refinement` 0.1.0 |
| `software_heritage` | save-request 2375286 (task succeeded) |

The resulting README status block reads **"12 platforms, 7 published"**. Reproduce
the upload dispatch through the thin CLI over `upload_runner.py`:

```bash
# 1. Verify tokens authenticate (read-only, no writes)
uv run python -m infrastructure.publishing.credential_check --env-file .env

# 2. Dry-run every credentialed platform (safe default)
uv run python scripts/publish/upload_gold_refinement.py

# 3. Real uploads (core platforms)
uv run python scripts/publish/upload_gold_refinement.py --commit \
  --only pinata huggingface osf testpypi

# 4. Add the GitHub release + static-site deploys (opt-in)
uv run python scripts/publish/upload_gold_refinement.py --commit \
  --include-github --include-static

# 5. Regenerate the README status block from config
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement --write
```

A JSON receipt is written to
`output/templates/template_gold_refinement/upload_receipts.json`.

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

# Archival dry-run (Stage 13)
uv run python scripts/09_archive_publication.py --project templates/template_code_project

# Unified GitHub + Zenodo + DOI release (opt-in)
uv run python scripts/publish_project_release.py \
  --project template_code_project --tag v1.0.0 --repo owner/repo --dry-run

# Read-only credential check (never prints token values; exits 1 if any present credential fails)
uv run python -m infrastructure.publishing.credential_check --env-file .env
uv run python -m infrastructure.publishing.credential_check --only github zenodo

# Print / write / drift-check the README publishing-status block
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement \
  --write --init-after "## Publication and rendering"
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement --check   # CI gate: non-zero on drift

# Override / add published references on the command line
uv run python -m infrastructure.publishing.status_report \
  --project projects/templates/template_gold_refinement \
  --published ipfs_pinata=https://gateway.pinata.cloud/ipfs/Qm... --write

# Turnkey multi-platform upload runner (dry-run by default; --commit for real uploads)
uv run python scripts/publish/upload_gold_refinement.py
uv run python scripts/publish/upload_gold_refinement.py --commit \
  --only pinata huggingface osf testpypi
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DOI validation failures | Check DOI format and checksum |
| Citation format errors | Verify BibTeX syntax |
| Metadata extraction issues | Ensure manuscript has proper frontmatter |
| Zenodo upload fails | Use sandbox first; uploads must target `links.bucket` from create response |
| HuggingFace upload 400s on large PDFs | The shipped `HuggingFaceHubAdapter` base64-inlines blobs; for real binary PDFs use the official `huggingface_hub` `HfApi.upload_file` (auto-LFS) |
| HuggingFace "cannot create repo" | The repo namespace must match the token's account — a no-org token cannot create under another namespace |
| TestPyPI upload fails | Install `twine` in the venv; version `0.1.0` is one-shot — confirm via the `/simple/` index, not the `/pypi/<name>/json` endpoint |
| Software Heritage deposit can't find origin | `deposit()` resolves the git origin from the dir's `origin` remote, or a text file whose first line is the repo URL |
| README status block won't insert | Markers are absent — pass `--init-after "## <heading>"` (or `update_readme_block(..., init_after_heading=...)`) on first write |
| Credential check shows `no-endpoint` | Expected for `pypi` — it has no read-only identity endpoint; the token is validated at upload time |

---

> **Never edit text between the `PUBLISHING-STATUS:START` / `PUBLISHING-STATUS:END`
> markers by hand.** Edit `manuscript/config.yaml`, then regenerate with
> `status_report.py --write`. The committed block is durable identifiers only —
> never machine credential presence.

---

**Related:** [Integrity Module](integrity-module.md) | [Rendering Module](rendering-module.md) | [Publishing AGENTS.md](../../../infrastructure/publishing/AGENTS.md)
