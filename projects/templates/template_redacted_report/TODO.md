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
- `src/redacted_report/redaction.py`'s `_SENSITIVE_MARKERS` hardcodes a literal `"2026-"` year-prefix as a residual-risk marker; it will silently stop matching once the calendar rolls past 2026. Replace with a marker derived from the current year (or a rolling window) before this exemplar is forked past 2026, and flag the fixture-only nature of this marker in a forker-facing doc rather than only in source.
- Post-fix adversarial check (2026-07-13): re-rendering the full 16-variant dev-proof PDF matrix and `pdftotext`-scanning every page turned up a residual second, undecided mention of `platform` in segment `s4` (`data/example_segments.json`: text has `"...SIGINT collection platform deployed near the selector. The platform transmitted from 192.0.2.10..."`; only the first `platform`/`selector` mention and two short spans are covered by `s4`'s five redaction decisions — the second `platform` mention and the `192.0.2.10` example IP have no covering decision). The IP is RFC 5737 `TEST-NET-1` (deliberately non-routable, safe), and most other same-word hits across the rendered PDF are false positives from unrelated prose (a TPM computing "platform" in the Kmyth appendix, `Controls: SIGINT`-style reason-category labels that are intentionally disclosed metadata, not leaked content) — but the second `s4` `platform` mention itself looks like a genuine missed span. This needs a fixture-author judgment call (is a bare repeated `platform` reference, with no new operational specific, meant to stay redacted or is it intentionally left as unclassified connective prose?) that a static audit can't resolve alone — do not silently patch `s4`'s decisions without that call. Recommended next step: run a systematic decision-coverage audit across *all* segments (not just `s5`) comparing every `_SENSITIVE_MARKERS` occurrence in each segment's raw text against its decision spans, and add a validator (in `verify_dev_variant_outputs`) that runs `pdftotext` on each generated dev-variant PDF and flags any `_SENSITIVE_MARKERS` term appearing outside a documented-safe context (reason-category labels, RFC 5737/5738 example addresses, and the Kmyth/TPM appendix should be an explicit allowlist, not silently assumed).

## Ordered improvement ladder

1. Keep redaction validator tests green.
2. Sanitized release-packet export — shipped in source/tests.
3. Policy taxonomy adapters — shipped in source/tests.
4. Source-safe ledgers, segment hashes, residual-risk reports, and approval gates — shipped in source/tests.
5. Add rendered public report examples — shipped in output generation.
6. Visual redaction/background proof matrix with provenance PDFs — shipped in source/script/tests.
7. Typed canonical audit/ledger generation in the normal Stage 02 order — shipped in source/script/tests/output.
