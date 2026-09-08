---
name: infrastructure-metadata
description: Skill for the shared metadata infrastructure module providing repository-URL normalization and ebook publication-metadata generation. Use when normalizing publication repository URLs, generating ONIX XML, metadata.json, or EPUB OPF metadata packages, or building ebook metadata from project config.
---

# Metadata Module

Shared publication-metadata leaves consumed by the publishing, rendering,
documentation, and project layers. Extracted from `infrastructure/publishing`
so the rendering layer can import these surfaces without an inverted
dependency on the publishing package (RENDERING-LAYERING-1).

## Repository URL normalization (`repository_metadata.py`)

```python
from infrastructure.metadata.repository_metadata import normalized_repository_url

url = normalized_repository_url(publication)  # explicit URL or owner/repo slug
```

## Ebook metadata package (`metadata_package.py`)

```python
from infrastructure.metadata.metadata_package import (
    EbookPublicationMetadata,
    ebook_metadata_from_config,
    generate_epub_opf,
    generate_metadata_json,
    generate_metadata_package,
    generate_onix_xml,
)

meta = ebook_metadata_from_config(config, project_slug)
write_text(generate_metadata_package(meta), output_dir / "metadata.xml")
```

## Invariants

- Leaf package: imports only stdlib plus `infrastructure.core`; never imports
  publishing, rendering, or reporting.
- Rendering may import this package directly; the layering guard
  (`tests/infra_tests/rendering/test_layering.py`) enforces zero
  rendering->publishing edges with an empty allowlist.
- Historical paths `infrastructure.publishing.repository_metadata` and
  `infrastructure.publishing.metadata_package` remain as re-export shims.
