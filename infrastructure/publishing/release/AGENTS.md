# `infrastructure/publishing/release/`

Release receipt/pairing/workflow family, subpackaged out of the flat
`infrastructure.publishing` namespace by RENDERING-LAYERING-1 phase 2b.

## Module graph

| File | Role |
| --- | --- |
| `release_receipts.py` | Versioned command, release-authority, coverage-gap, and clean-checkout receipts (the `REHEARSAL_RECEIPT_TOKEN` protocol lives here) |
| `release_pairing.py` | Structural GitHub-Zenodo pairing validation (`validate_release_pairing`, checklist formatters) |
| `release_workflow.py` | Unified GitHub + Zenodo + DOI + re-render orchestration (`run_release_workflow`, `ReleaseRequest`) |
| `release_workflow_zenodo.py` | Reserve-first DOI phase + `publish_zenodo_for_release` (leaf of the release workflow) |
| `release_cli.py` | Stable argument parser and credential-source resolution for `scripts/publish/publish_project_release.py` |

## Public API

Package-level re-exports live in `infrastructure/publishing/__init__.py`
(receipt classes and builders). The historical flat paths
(`infrastructure.publishing.release_receipts`, `.release_workflow`, ...) remain
as silent re-export shims; new code imports the nested paths.

## Invariants

- Cross-family imports are absolute: the workflow pulls metadata building
  blocks from `infrastructure.publishing.metadata.metadata_from_config`.
- Receipts are deterministic (schema-versioned; digests exclude timestamps).
- No rendering-layer imports: the layering guard
  (`tests/infra_tests/rendering/test_layering.py`) runs with an empty
  allowlist; this package must never be imported from `infrastructure/rendering`.
