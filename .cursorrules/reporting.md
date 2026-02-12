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
- Keep reports **deterministic** (fixed ordering, seeded randomness).
- Include **context**: stage names, timings, counts, failures with categories and suggestions.
- For HTML/Markdown, reuse shared templates; avoid inline styling drift.
- Expose clear public API in `__init__.py`; keep helpers private (`_` prefix).

## Configuration

- Accept config via dataclasses with `from_env()` where appropriate (timeouts, paths, verbosity).
- Default to **quiet/concise**; allow opt-in verbosity.
- Document any environment variables in module README and in docstrings.

## Logging & Errors

- Use `infrastructure.core.logging_utils.get_logger(__name__)`.
- Raise module-specific errors from `infrastructure.core.exceptions` (e.g., `ValidationError`, `BuildError`) with context.
- Log summaries at INFO; detailed diagnostics at DEBUG.
- Never swallow errors—propagate with `raise ... from e`.

## Data & Security

- Validate inputs (schemas, file paths) before rendering; fail fast with context.
- Do not embed secrets or raw stack traces in human-facing outputs.
- Ensure file writes are atomic where possible; respect existing output directory conventions (`output/`).

## Testing

- **No mocks** for core logic; use real sample data.
- Cover JSON/Markdown/HTML outputs for structure and key fields.
- Test error aggregation edge cases (empty inputs, mixed severities).
- Keep coverage ≥60% for infrastructure code; integration paths should exercise orchestrator hooks.

## Documentation

- Update `infrastructure/AGENTS.md` and module README when APIs change.
- Cross-link from `.cursorrules/AGENTS.md` and `.cursorrules/README.md`.
- Provide minimal runnable examples that generate a report file.

## Quick Example

```python
from infrastructure.reporting import generate_pipeline_report, get_error_aggregator

errors = get_error_aggregator()
errors.add("validation", "missing figure", context={"file": "02_results.md"})

report = generate_pipeline_report(
    stages=["setup", "tests", "analysis"],
    durations={"setup": 3.2, "tests": 28.5, "analysis": 12.1},
    errors=errors,
)
report.save_markdown("output/reports/pipeline.md")
```
