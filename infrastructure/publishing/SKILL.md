---
name: infrastructure-publishing
description: Skill for the publishing infrastructure module providing academic publishing workflows including BibTeX CLI citation generation, APA/MLA citation helper functions, DOI management, Zenodo publication, arXiv submission preparation, GitHub releases, and publication readiness validation. Use when publishing research, generating citations, minting DOIs, or preparing submissions.
---

# Publishing Module

Academic publishing and dissemination tools for research projects.

## Platform subpackages

| Path | Use when |
| --- | --- |
| `infrastructure.publishing.zenodo` | Zenodo deposit, upload, publish, DOI |
| `infrastructure.publishing.github` | GitHub release + assets |
| `infrastructure.publishing.arxiv` | arXiv tarball from manuscript tree |

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

```python
from infrastructure.publishing.archival import ZenodoProvider, archive_publication

run = archive_publication(
    Path("output/project/executable_bundle"),
    providers=[ZenodoProvider(token=None)],
    dry_run=True,
)
```

CLI dry-run:

```bash
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/template_code_project/executable_bundle \
  --providers zenodo
```

See [`archival/README.md`](archival/README.md) and `scripts/09_archive_publication.py`.
