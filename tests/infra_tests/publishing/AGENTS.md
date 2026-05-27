# Publishing Module — Agent Guide

## Overview

Tests for `infrastructure/publishing/`: metadata, citations, platform clients, archival, CLIs, release workflow, and readiness. **362 tests**; coverage gate **≥85%** on `infrastructure.publishing`.

## Test modules (on disk)

| File | Focus |
| --- | --- |
| `conftest.py` | `zenodo_test_server`, `zenodo_version_test_server`, `github_test_server` fixtures |
| `test_api.py` | Zenodo client via `api.py` shim |
| `test_archival.py` | Multi-target archival providers |
| `test_archival_cli.py` | `archival_cli.main`, `_build_providers` |
| `test_citations.py` | BibTeX, APA, MLA, author formatters |
| `test_deposit_filename.py` | Metadata-driven deposit PDF filenames |
| `test_cli.py` | Legacy CLI smoke |
| `test_executable_bundle.py` | Stage 10 `bundle_project` |
| `test_metadata.py` | Metadata extraction and reporting |
| `test_metadata_export.py` | Metadata JSON export CLI |
| `test_models.py` | `PublicationMetadata`, `CitationStyle` |
| `test_platforms.py` | `platforms.py` re-exports (arXiv, GitHub, Zenodo E2E) |
| `test_publication_ledger.py` | Release ledger for transmission bookends |
| `test_publish_cli.py` | `publish_cli.main` (GitHub release wrapper) |
| `test_publishing.py` | Core workflows, dissemination |
| `test_publishing_cli.py` | `cli.py` subcommands including `publish_zenodo_command` |
| `test_publishing_core.py` | Package/checklist/readiness |
| `test_readiness.py` | Publication readiness validation |
| `test_release_pairing.py` | GitHub/Zenodo release pairing helpers |
| `test_release_workflow.py` | Unified release workflow, `config_doi`, `metadata_from_config` |
| `test_transmission_bookends.py` | Transmission begin/end manuscript pages |
| `test_zenodo_client.py` | Canonical `zenodo/` client, `publish_to_zenodo`, versioning |

## Running tests

```bash
uv run pytest tests/infra_tests/publishing/ --cov=infrastructure.publishing --cov-fail-under=85 -v
```

## Design rules

- No mocks — use `pytest-httpserver` and temp files.
- Inject test-server URLs via `base_url=` on clients or `ZenodoConfig(base_url=...)`.
- Mark live-network tests explicitly; default suite is hermetic.

## See also

- [`../../../infrastructure/publishing/AGENTS.md`](../../../infrastructure/publishing/AGENTS.md)
- [`../AGENTS.md`](../AGENTS.md)
