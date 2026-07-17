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

## Commands

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --strict --rendered --format markdown
```
