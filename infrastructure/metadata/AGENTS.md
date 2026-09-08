# infrastructure/metadata — agent contract

Shared publication-metadata leaves consumed by the publishing, rendering,
documentation, and project layers. Extracted from `infrastructure/publishing/`
on 2026-09-07 so the rendering layer could reach these surfaces without an
inverted dependency on the publishing package (RENDERING-LAYERING-1).

## Modules

|Module|Purpose|Key exports|
|---|---|---|
|`repository_metadata.py`|Canonical repository-URL normalization (explicit URL or `owner/repo` slug)|`normalized_repository_url`|
|`metadata_package.py`|Ebook publication-metadata generation: ONIX XML, metadata JSON, EPUB OPF|`EbookPublicationMetadata`, `generate_onix_xml`, `generate_metadata_json`, `generate_epub_opf`, `generate_metadata_package`, `ebook_metadata_from_config`|

## Invariants

1. Leaf package: no imports from `infrastructure.publishing`,
   `infrastructure.rendering`, or `infrastructure.reporting`. Only stdlib +
   `infrastructure.core` (logging) are allowed.
2. Rendering may import this package directly; the rendering->publishing
   inversion guard (`tests/infra_tests/rendering/test_layering.py`) enforces
   that rendering never imports `infrastructure.publishing`.
3. The historical paths `infrastructure.publishing.repository_metadata` and
   `infrastructure.publishing.metadata_package` remain as re-export shims;
   new code imports `infrastructure.metadata.*` directly.

## Verification

```bash
uv run pytest tests/infra_tests/publishing/test_repository_metadata.py tests/infra_tests/publishing/test_metadata_package.py -q --no-cov
uv run pytest tests/infra_tests/rendering/test_layering.py -q --no-cov
```

## Cross-refs

- `infrastructure/publishing/AGENTS.md` — the shim paths and the publishing
  metadata pipeline (`metadata_stage.py`, `metadata_export.py`).
- `infrastructure/rendering/AGENTS.md` — the two retargeted consumers
  (`ebook_bundle.py`, `_pdf_title_page_publishing.py`).
