# Publication validation package

This package composes existing project-drift, methods, evidence, figure,
artifact, and no-mock validators into one stable publication-readiness report.
It must remain read-only with respect to source trees and must not silently
rewrite generated outputs.

## Contract

- `PublicationFinding` carries a stable diagnostic code, project-relative path,
  severity, status, evidence, and remediation.
- `status: fail` is deterministic and blocks the CLI.
- `status: review_required` is advisory and records editorial or domain review
  work without turning subjective judgment into a fake binary proof.
- Serialization is timestamp-free so reports can participate in reproducibility
  comparisons.
- Rendered mode requires `output/reports/rendered_provenance.json`. The receipt
  binds a green output snapshot to stage, source, config, output, and explicit
  manuscript-consumption fingerprints without claiming per-stage lineage.
- Placeholder tokens are valid in hydratable source manuscripts. Scan only the
  canonical rendered manuscript input, once, and ignore literal code examples.
- Missing, malformed, stale, or incomplete rendered provenance is a
  deterministic failure, not an editorial review item.
- `models.py` defines the typed finding/report contract used by the audit
  orchestrator; keep its status and diagnostic fields stable for downstream
  JSON consumers.

## Commands

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --strict --rendered --format markdown
```
