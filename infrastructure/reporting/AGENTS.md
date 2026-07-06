# Reporting Package

## Purpose

Reporting converts pipeline, test, validation, evidence, and release-readiness
facts into human and machine-readable artifacts. Reports should summarize real
local evidence; they must not present missing, stale, or optional network state
as verified success.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Pipeline reports | `pipeline_report_model.py`, `pipeline_io.py`, `pipeline_markdown.py`, `pipeline_html.py` | Structured per-run stage reports. |
| Multi-project summaries | `multi_project_reporter.py`, `multi_project_report.py` | Terminal and last-run multi-project summaries. |
| Executive reports | `executive_reporter.py`, `_executive_*`, `_dashboard_*`, `_csv_*` | Dashboard, CSV, HTML, image, and markdown report generation. |
| Evidence/release | `evidence_graph.py`, `release_readiness.py` | Local evidence graph and no-network release-readiness dashboard. |
| Error/test helpers | `error_aggregator.py`, `suite_runner.py`, `pipeline_test_runner.py`, `pytest_output_parser.py` | Test orchestration and failure aggregation. |
| Output organization | `output_organizer.py`, `output_statistics.py`, `page_grid.py`, `page_rendering.py` | Final report file layout and page grids. |

## Boundaries

- Reports consume existing artifacts; they do not run project analysis.
- Local readiness is not publication readiness. Network deposits, DOI state, and
  public endpoints need explicit publishing checks.
- Avoid hard-coded project rosters; use public scope helpers or generated docs.
- Keep charts deterministic and compact. Put metric definitions in source data
  or report prose, not hidden code comments.
- When a report quotes counts or coverage, cite generated facts or fresh command
  output.

## Public Commands

```bash
uv run python -m infrastructure.reporting.evidence_graph build templates/template_code_project --json /tmp/evidence_graph.json
uv run python -m infrastructure.reporting.release_readiness --repo-root . --out output/release_readiness.md
uv run python scripts/runner/execute_multi_project.py --public-projects
```

## Tests

```bash
uv run pytest tests/infra_tests/reporting -q
```

For changes that touch project test execution, also run the relevant
`scripts/pipeline/stage_01_test.py` mode because `pipeline_test_runner.py` controls the
project output lock used by pipeline stages.

## Change Checklist

- Add tests for JSON/Markdown/HTML shape when public report schema changes.
- Keep release-readiness aggregation offline unless a command explicitly says it
  performs network validation.
- Regenerate downstream report fixtures only through their producer commands.
- Run `git diff --check`; report markdown tables are easy to break with trailing
  whitespace.

## See Also

- [`README.md`](README.md)
- [`../core/pipeline/AGENTS.md`](../core/pipeline/AGENTS.md)
- [`../validation/AGENTS.md`](../validation/AGENTS.md)
