# Reporting System Guide

## Overview

The research project template includes a reporting system that generates detailed reports at every pipeline stage. This guide explains the reporting features, output locations, and how to interpret the generated reports.

## Report Types

### 1. Pipeline Reports

**Location**: `projects/{name}/output/reports/pipeline_report.*`

**Formats**: JSON, HTML, Markdown

**Contents**:
- stage execution results
- Stage durations and success/failure status
- Test results and coverage data
- Validation results
- Performance metrics
- Error summaries
- Output statistics

**Usage**:
```bash
# View JSON report
cat projects/{name}/output/reports/pipeline_report.json | jq

# Open HTML report in browser
open projects/{name}/output/reports/pipeline_report.html

# Read Markdown report
cat projects/{name}/output/reports/pipeline_report.md
```

### 2. Validation Reports

**Location**: `projects/{name}/output/reports/validation_report.json`

**Contents**:
- PDF validation results
- Markdown validation results
- Output structure validation
- Figure registry validation
- Per-check results with pass/fail status
- Detailed issue breakdowns by severity
- Actionable recommendations

**Key Fields**:
- `checks`: Dictionary of validation check results
- `figure_issues`: List of figure reference issues
- `output_statistics`: File counts and sizes
- `recommendations`: Actionable items to resolve issues
- `summary`: Overall validation summary

### 3. Log Summaries

**Location**: `projects/{name}/output/reports/log_summary.txt`

**Contents**:
- Message counts by log level
- Recent errors (last 5-10)
- Recent warnings (last 5-10)
- Total line count

**Usage**:
```bash
# View log summary
cat projects/{name}/output/reports/log_summary.txt

# Quick check for errors
grep -i error projects/{name}/output/reports/log_summary.txt
```

### 3.5 Telemetry Reports and Retention

**Location**: `projects/{name}/output/reports/telemetry.{json,txt}`
**Archive**: `projects/{name}/output/reports/.history/telemetry-<unix_ts>.json`

**Contents** (`telemetry.json`):
- Per-stage timing, memory, CPU, and I/O
- Diagnostic event counts (errors / warnings) per stage
- Performance warnings (slow stage, high memory, high CPU)
- System info captured at run start
- Configuration snapshot

**Retention behaviour:**
Each pipeline run, `TelemetryCollector.finalize()` rotates the previous
run's `telemetry.json` into `.history/` before writing the new one. The
in-flight report for the current run is never touched. The number of
archived files retained is controlled by the `TELEMETRY_KEEP`
environment variable (default `10`); the oldest archived files beyond
that count are pruned.

**Inspect history:**
```bash
# Walk the archive in chronological order
ls -1 projects/{name}/output/reports/.history/

# View the most recent prior run
jq . "$(ls -1t projects/{name}/output/reports/.history/telemetry-*.json | head -1)"

# Override retention for a single run
TELEMETRY_KEEP=25 uv run python scripts/runner/execute_pipeline.py --project {name} --core-only
```

The rotation function is `infrastructure.core.telemetry.retention.rotate`
and is idempotent — running it twice without a new live report leaves
the archive unchanged. See
[Configuration Guide → Telemetry Retention](config/configuration.md#telemetry-retention)
for the full env-var contract.

### 4. Output Statistics

**Location**: `projects/{name}/output/reports/output_statistics.*`

**Formats**: TXT, JSON

**Contents**:
- File counts by directory
- File sizes by directory
- Largest files (top 10)
- Missing expected files
- File type distributions
- Total output size

**Usage**:
```bash
# View text report
cat projects/{name}/output/reports/output_statistics.txt

# Parse JSON for programmatic access
uv run python -c "import json; print(json.load(open('projects/{name}/output/reports/output_statistics.json')))"
```

### 5. Multi-Project Summary

**Location**: `output/multi_project_summary/`

**Files**:
- `multi_project_summary.json` - Structured data
- `multi_project_summary.md` - Human-readable summary

**Contents**:
- Per-project execution results
- Success/failure counts
- Performance analysis (slowest/fastest projects)
- Error aggregation across projects
- Cross-project recommendations

**Usage**:
```bash
# View summary
cat output/multi_project_summary/multi_project_summary.md

# Check for failed projects
jq '.projects | to_entries | map(select(.value.success == false))' output/multi_project_summary/multi_project_summary.json
```

### 6. Executive Reports

**Location**: `output/executive_summary/`

**Files**:
- `executive_summary.json` - Metrics and data
- `executive_summary.html` - Interactive dashboard
- `executive_summary.md` - Text summary
- `dashboard_matplotlib.png` - Static dashboard
- `dashboard_plotly.html` - Interactive dashboard
- `metrics.csv` - CSV data export

**Contents**:
- Cross-project metrics aggregation
- Health scores for each project
- Visual dashboards with charts
- Performance comparisons
- Resource usage statistics

## Report Generation

### Automatic Generation

Reports are automatically generated during pipeline execution:

```bash
# Single project - generates all reports
uv run python scripts/runner/execute_pipeline.py --project project

# Multi-project - generates all reports + executive summary
uv run python scripts/runner/execute_multi_project.py
```

### Manual Generation

Generate specific reports independently:

```bash
# Validation report only
uv run python scripts/pipeline/stage_04_validate.py --project project

# Output statistics only
uv run python scripts/pipeline/stage_05_copy.py --project project

# Executive report only
uv run python scripts/pipeline/stage_07_executive_report.py
```

## Interpreting Reports

### Pipeline Report

**Key Metrics**:
- `total_duration`: Total execution time in seconds
- `stages[].status`: "passed" or "failed" for each stage
- `stages[].duration`: Time spent in each stage

**Red Flags**:
- Any stage with `"status": "failed"`
- `error_summary.total_errors > 0`
- Long stage durations (> 300s)

### Validation Report

**Key Metrics**:
- `summary.all_passed`: Boolean indicating overall validation status
- `summary.failed`: Number of failed checks
- `figure_issues_count`: Number of figure reference issues

**Red Flags**:
- `"all_passed": false`
- Non-empty `figure_issues` list
- Any recommendations with `"priority": "high"`

### Output Statistics

**Key Metrics**:
- `total_files`: Total number of generated files
- `total_size_mb`: Total output size in MB
- `largest_files`: Top 10 largest files

**Red Flags**:
- Non-empty `missing_expected_files` list
- Unusually large files (> 100 MB)
- Zero files in expected directories

### Multi-Project Summary

**Key Metrics**:
- `successful_projects`: Count of successful projects
- `failed_projects`: Count of failed projects
- `performance_analysis.average_duration`: Average execution time

**Red Flags**:
- `failed_projects > 0`
- High average duration (> 300s per project)
- Non-empty `recommendations` list

## Report Retention

### Temporary Reports

**Location**: `projects/{name}/output/reports/`

**Lifecycle**: Cleaned on next pipeline run

**Purpose**: Working reports during development

### Final Reports

**Location**: `output/{name}/reports/`

**Lifecycle**: Preserved across runs

**Purpose**: Deliverable reports for publication

## Integration with CI/CD

Reports can be integrated into CI/CD pipelines:

```bash
# Check if validation passed
if jq -e '.summary.all_passed == true' projects/{name}/output/reports/validation_report.json > /dev/null; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi

# Check if pipeline succeeded
if jq -e 'all(.stages[]; .status == "passed")' projects/{name}/output/reports/pipeline_report.json > /dev/null; then
    echo "Pipeline succeeded"
else
    echo "Pipeline failed"
    exit 1
fi
```

## Pipeline Summary Format

The end-of-run terminal summary block is rendered by **`format_multi_project_detailed_report`**
in [`infrastructure/reporting/multi_project_report.py`](../../infrastructure/reporting/multi_project_report.py)
(re-exported from [`infrastructure/core/pipeline/multi_project.py`](../../infrastructure/core/pipeline/multi_project.py)
for backward compatibility). This is the **canonical pipeline-completion reporting surface** — every full-run option
(interactive menu, `./run.sh --pipeline`, and direct `infrastructure.orchestration` invocations)
prints this block via the orchestrator in
[`infrastructure/orchestration/pipeline_runner.py`](../../infrastructure/orchestration/pipeline_runner.py).

The per-project rendering summary printed during Stage 5 is rendered by
**`log_rendering_summary`** (paired with `generate_rendering_summary`) in
[`infrastructure/rendering/_pipeline_summary.py`](../../infrastructure/rendering/_pipeline_summary.py).
This is the **canonical per-project rendering reporting surface** — wrapped in
`RENDERING RESULTS SUMMARY` separator bars, it lists the combined PDF, individual
section PDFs, web outputs, slides, and total output size.

For the full visual contract — the canonical clean-run block, the failure-mode shape,
the schema of every section, and the verbosity dial that controls terminal-vs-file
output — see [logging/output-design.md](logging/output-design.md).

**Stability contract.** Both functions ship with explicit `STABILITY:` docstrings.
Section headers (`MULTI-PROJECT EXECUTION SUMMARY`, `PROJECT STATUS`,
`STAGE TIMING BREAKDOWN`, `PERFORMANCE HIGHLIGHTS`, `RENDERING RESULTS SUMMARY`,
`Combined Manuscript PDF`, `Web Outputs`, `Presentation Slides`) are part of the
public contract: tests assert on their substring presence, downstream tooling
greps for them, and they must not change without coordinated updates. New
sections may be appended.

After each multi-project run, the rendered block is also persisted verbatim to
[`docs/_generated/last-run-summary.md`](../_generated/) so it can be diffed
across runs for regression detection. The write is best-effort — a docs-write
failure cannot crash the pipeline.

## Troubleshooting

### Reports Not Generated

**Symptom**: Report files missing after pipeline execution

**Causes**:
1. Pipeline failed before report generation
2. Insufficient permissions to write reports
3. Missing reporting module dependencies

**Solutions**:
```bash
# Check pipeline logs
cat projects/{name}/output/logs/pipeline.log | grep -i report

# Verify write permissions
touch projects/{name}/output/reports/test.txt && rm projects/{name}/output/reports/test.txt

# Reinstall dependencies
uv sync
```

### Incomplete Reports

**Symptom**: Reports generated but missing data

**Causes**:
1. Stage failed before data collection
2. Data collection errors
3. Corrupted intermediate outputs

**Solutions**:
```bash
# Re-run specific stage
uv run python scripts/pipeline/stage_04_validate.py --project project

# Check for errors in logs
grep -i "failed to generate report" projects/{name}/output/logs/pipeline.log
```

### Report Parsing Errors

**Symptom**: Cannot parse JSON reports

**Causes**:
1. Report file corrupted
2. Incomplete write
3. JSON syntax errors

**Solutions**:
```bash
# Validate JSON syntax
jq . projects/{name}/output/reports/pipeline_report.json

# Regenerate report
uv run python scripts/runner/execute_pipeline.py --project project --stage validate
```

## Best Practices

1. **Review Reports Regularly**: Check reports after each pipeline run
2. **Act on Recommendations**: Follow recommendations in validation reports
3. **Monitor Trends**: Compare reports across runs to identify patterns
4. **Archive Important Reports**: Save final reports before re-running pipeline
5. **Automate Checks**: Integrate report validation into CI/CD
6. **Share Reports**: Use HTML/Markdown formats for sharing with team

## Related Documentation

- [Validation Guide](../modules/pdf-validation.md)
- [Logging Guide](logging/)
- [Performance Optimization](config/performance-optimization.md)
- [Troubleshooting Guide](troubleshooting/)

## Support

For issues with reporting:
1. Check logs for report generation errors
2. Verify all dependencies installed
3. Ensure pipeline completed successfully
4. Review this guide for report interpretation
5. Consult troubleshooting guide for specific issues
