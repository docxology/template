# Reporting Module Standards

## Overview

Guidelines for using and extending the reporting utilities (multi-format reports in JSON/Markdown/HTML) that summarize pipeline outcomes, errors, and performance. Applies to infrastructure reporting helpers and any thin orchestrator wrappers.

## Scope & Structure

- **Layer**: Infrastructure (generic, reusable)
- **Location**: `infrastructure/reporting/` (APIs) and orchestrator touch points in `scripts/`
- **Pattern**: Thin orchestrator → call reporting APIs; business logic stays in module core
- **Outputs**: JSON for machines, Markdown/HTML for humans; keep schemas stable

## Usage Patterns

- Prefer high-level helpers (e.g., `generate_pipeline_report`, `get_error_aggregator`) over ad-hoc formatting.
- Keep reports **deterministic** (fixed ordering and canonical serialization;
  reporting code should not introduce randomness).
- Include **context**: schema version, run/source/config identity, generation
  mode, producer, stage names, timings, counts with denominators, failures with
  categories, and suggested remediation.
- For HTML/Markdown, reuse shared templates; avoid inline styling drift.
- Expose clear public API in `__init__.py`; keep helpers private (`_` prefix).

## Configuration

- Accept config via dataclasses with `from_env()` where appropriate (timeouts, paths, verbosity).
- Default to **quiet/concise**; allow opt-in verbosity.
- Document any environment variables in module README and in docstrings.

## Logging & Errors

- Use `infrastructure.core.logging.utils.get_logger(__name__)`.
- Raise module-specific errors from `infrastructure.core.exceptions` (e.g., `ValidationError`, `BuildError`) with context.
- Log summaries at INFO; detailed diagnostics at DEBUG.
- Never swallow errors—propagate with `raise ... from e`.

## Data & Security

- Validate inputs (schemas, file paths) before rendering; fail fast with context.
- Do not embed secrets or raw stack traces in human-facing outputs.
- Ensure file writes are atomic where possible; respect existing output directory conventions (`output/`).

## Scientific and Provenance Semantics

- Distinguish `passed`, `failed`, `blocked`, `not_run`, `unavailable`,
  `excluded`, and `skipped`; never coerce missing/unavailable observations to
  zero or omit them from a denominator.
- Label values as observed, derived, configured, or asserted. Include units,
  population/sample, estimator, aggregation, uncertainty/error-bar definition,
  and exclusions when a report carries scientific or performance statistics.
- Preserve stage and artifact lineage: input/config hashes, producer revision,
  parent artifact identifiers, output hashes, and warnings. A current-output
  checksum snapshot is integrity evidence, not proof of which stage produced an
  artifact or that the underlying source was current.
- Generate result-bearing manuscript variables and figure-caption metadata from
  the report's typed raw fields. Do not parse rounded display prose or hand-copy
  report values into manuscript Markdown.
- Treat engineering, scientific, accessibility, provenance, owner-approval,
  and release-authority outcomes as separate fields. A green test or readable
  artifact must not be summarized as publication approval.
- Keep claim wording bounded to the evidence represented in the report. A
  citation identifier, source count, or successful metadata lookup does not
  establish that a cited source supports the claim.

## Testing

- **No mocks** for core logic; use real sample data.
- Cover JSON/Markdown/HTML outputs for structure and key fields.
- Test error aggregation edge cases (empty inputs, mixed severities).
- Keep coverage ≥60% for infrastructure code; integration paths should exercise orchestrator hooks.

## Documentation

- Update `infrastructure/AGENTS.md` and module README when APIs change.
- Cross-link from **[`docs/rules/AGENTS.md`](AGENTS.md)** and **[`docs/rules/README.md`](README.md)** (and root **[`AGENTS.md`](../../AGENTS.md)** when describing pipeline-wide behaviour).
- Provide minimal runnable examples that generate a report file.

## Quick Example

```python
from pathlib import Path

from infrastructure.reporting import (
    generate_pipeline_report,
    get_error_aggregator,
    save_pipeline_report,
)

errors = get_error_aggregator()
# Illustrative input; real stage records must come from the current run.
errors.add_error("validation", "missing figure", context={"file": "02_results.md"})

report = generate_pipeline_report(
    stage_results=[
        {"name": "setup", "exit_code": 0, "duration": 3.2},
        {"name": "tests", "exit_code": 0, "duration": 28.5},
        {"name": "analysis", "exit_code": 0, "duration": 12.1},
    ],
    total_duration=43.8,
    repo_root=Path("."),
    error_summary=errors.get_summary(),
)
save_pipeline_report(report, Path("output/reports"), formats=["markdown"])
```
