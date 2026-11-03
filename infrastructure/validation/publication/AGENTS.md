# Publication validation package

This package composes existing project-drift, methods, evidence, figure,
artifact, and no-mock validators into one stable publication-readiness report.
It must remain read-only with respect to source trees and must not silently
rewrite generated outputs.

## Contract

- `PublicationFinding` carries a stable diagnostic code, project-relative path,
  severity, status, evidence, and remediation.
- `status: fail` is deterministic and blocks the CLI.
- `status: review_required` records editorial or domain review work. It does
  not fail the default `blocking` audit, but it does fail `--strict` (the release
  lane) and the gate's `strict` mode, where its findings block. It never turns
  subjective judgment into a fake binary proof.
- Serialization is timestamp-free so reports can participate in reproducibility
  comparisons.
- Rendered mode requires `output/reports/rendered_provenance.json`. The receipt
  binds a green output snapshot to stage, source, config, output, and explicit
  manuscript-consumption fingerprints without claiming per-stage lineage. The
  stage fingerprint covers every tracked implementation file under
  `infrastructure/` and `scripts/` (package documentation files are skipped), so
  editing a stage module or runtime asset invalidates existing receipts and
  requires re-running the exemplar producers.
- Placeholder tokens are valid in hydratable source manuscripts. Scan only the
  canonical rendered manuscript input, once, and ignore literal code examples.
- Missing, malformed, stale, or incomplete rendered provenance is a
  deterministic failure, not an editorial review item.
- `models.py` defines the typed finding/report contract used by the audit
  orchestrator; keep its status and diagnostic fields stable for downstream
  JSON consumers.
- `rendered_refresh.py` owns the canonical refresh and rebind for one exemplar's
  rendered-provenance receipt: render, validate and write, or revalidate
  unchanged bytes and rewrite the receipt for current tooling. A refused render
  re-admits the analysis boundary once, and a rebind is refused whenever the
  output tree no longer hashes to what the receipt recorded.
- `gate.py` owns roster selection. `--changed` may narrow the audited roster
  only for evidence that cannot reach another exemplar's output: an exact
  `projects/templates/<name>/...` path selects that exemplar (project ownership
  is resolved before any documentation exemption, so a manuscript edit is never
  mistaken for prose), and a repository-level documentation path
  (`docs/**`, root `*.md`) selects nothing and says so. Every other path —
  `infrastructure/**`, `scripts/**`, the toolchain, control files, unknown
  top-level paths, unknown or non-template project trees — widens the selection
  to the whole baseline roster, because a rendered-provenance receipt binds every
  tracked implementation file under `infrastructure/` and `scripts/`. An
  observed empty change set selects nothing; an unobservable one raises instead
  of guessing a clean tree. Widening never audits a project the caller excluded.
- A zero-project selection is reported as `skipped — nothing audited (<reason>)`
  and never as a bare `status: pass`. Publication-gate receipts are
  `template-publication-gate/v2` and carry a `selection` block (reason, widened,
  roster size), so a narrowed `--changed` run cannot be presented later as a
  whole-roster pass.

## Commands

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --strict --rendered --format markdown
```
