# template_redacted_report TODO

## Current validation evidence

- Tests cover classification ceilings, redaction bounds, overlap rejection, orphan decisions, sensitive-marker coverage, release authority, taxonomy adapters, sanitized in-memory packets, source-safe ledgers, segment hash manifests, reviewer approval gates, paragraph audit tables, mosaic-risk scoring, typed fixture loading, malformed/missing input failures, two-run artifact byte equality, source-canary non-disclosure, visual redaction styles, background modes, Kmyth requested/available matrix semantics, and the full 16-variant development matrix.
- Canonical Stage 02 analysis is shipped: `01_generate_release_artifacts.py` writes deterministic, text-free `output/reports/redaction_audit.json` and hashed `output/data/release_ledger.json` through the source-owned artifact contract.

## Integrity and template-status gaps

- Keep rendered sanitized report outputs and development visual-proof outputs regenerated after style, steganography, or Kmyth build changes.

## Configurable-surface gaps

- Add additional organization-specific marking taxonomies and review-role policies only as cleared, invented fixtures.

## Documentation and signposting gaps

- Keep public safety boundaries visible in README, AGENTS, and manuscript prose.

## Test and validator gaps

- Bind manuscript tables to the canonical audit JSON only if rendering can preserve the text-free projection and fails closed when the audit schema changes.
- Add pixel-level visual regression only if the repo adopts stable screenshot/PDF raster tooling for exemplar outputs.

## Ordered improvement ladder

1. Keep redaction validator tests green.
2. Sanitized release-packet export — shipped in source/tests.
3. Policy taxonomy adapters — shipped in source/tests.
4. Source-safe ledgers, segment hashes, residual-risk reports, and approval gates — shipped in source/tests.
5. Add rendered public report examples — shipped in output generation.
6. Visual redaction/background proof matrix with provenance PDFs — shipped in source/script/tests.
7. Typed canonical audit/ledger generation in the normal Stage 02 order — shipped in source/script/tests/output.
