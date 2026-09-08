# `infrastructure/publishing/metadata/`

Metadata pipeline family, subpackaged out of the flat
`infrastructure.publishing` namespace by RENDERING-LAYERING-1 phase 2b.

**Not** the shared `infrastructure.metadata` leaf package: that one is a
rendering-safe surface (repository-URL normalization, ebook metadata
generation). This family is publishing-side pipeline code.

## Module graph

| File | Role |
| --- | --- |
| `metadata_stage.py` | `run_metadata_package` — thin stage orchestrator (Stage 12): resolve project, load config, build ebook metadata, write `output/metadata/` |
| `metadata_export.py` | `build_citation_cff`, `build_codemeta(_json)`, `build_zenodo(_json)`, `write_metadata_files` — generate `CITATION.cff`, `codemeta.json`, `.zenodo.json` from `manuscript/config.yaml` |
| `metadata_export_cli.py` | `main` — `metadata-export` CLI (`python -m infrastructure.publishing.metadata.metadata_export_cli metadata-export --project <name>`) |
| `metadata_from_config.py` | `publication_metadata_from_config(_dict)`, `load_publication_release_context` — single-parse metadata + deposit context + prior DOI |
| `metadata_aggregate.py` | The historical `metadata.py` aggregator, re-exporting the `_metadata_extraction` / `_metadata_reporting` helpers |

## Public API

The package `__init__` re-exports the aggregate symbols so the historical
`from infrastructure.publishing.metadata import <symbol>` path keeps
resolving. The flat `metadata_*.py` paths remain as silent re-export shims.

## Invariants

- Config-driven export gives `paper` fields precedence with a complete
  `book`-schema fallback; `released_date` is optional for byte-stable output.
- No rendering-layer imports: the layering guard
  (`tests/infra_tests/rendering/test_layering.py`) runs with an empty
  allowlist; this package must never be imported from `infrastructure/rendering`.
