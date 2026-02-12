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
cat projects/project/output/reports/pipeline_report.json | jq

# Open HTML report in browser
open projects/project/output/reports/pipeline_report.html

# Read Markdown report
cat projects/project/output/reports/pipeline_report.md
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
cat projects/project/output/reports/log_summary.txt

# Quick check for errors
grep -i error projects/project/output/reports/log_summary.txt
```

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
cat projects/project/output/reports/output_statistics.txt

# Parse JSON for programmatic access
python3 -c "import json; print(json.load(open('projects/project/output/reports/output_statistics.json')))"
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
python3 scripts/execute_pipeline.py --project project

# Multi-project - generates all reports + executive summary
python3 scripts/execute_multi_project.py
```

### Manual Generation

Generate specific reports independently:

```bash
# Validation report only
python3 scripts/04_validate_output.py --project project

# Output statistics only
python3 scripts/05_copy_outputs.py --project project

# Executive report only
python3 scripts/07_generate_executive_report.py
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
if jq -e '.summary.all_passed == true' projects/project/output/reports/validation_report.json > /dev/null; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi

# Check if pipeline succeeded
if jq -e 'all(.stages[]; .status == "passed")' projects/project/output/reports/pipeline_report.json > /dev/null; then
    echo "Pipeline succeeded"
else
    echo "Pipeline failed"
    exit 1
fi
```

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
cat projects/project/output/logs/pipeline.log | grep -i report

# Verify write permissions
touch projects/project/output/reports/test.txt && rm projects/project/output/reports/test.txt

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
python3 scripts/04_validate_output.py --project project

# Check for errors in logs
grep -i "failed to generate report" projects/project/output/logs/pipeline.log
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
jq . projects/project/output/reports/pipeline_report.json

# Regenerate report
python3 scripts/execute_pipeline.py --project project --stage validate
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
- [Logging Guide](logging-guide.md)
- [Performance Optimization](performance-optimization.md)
- [Troubleshooting Guide](troubleshooting-guide.md)

## Support

For issues with reporting:
1. Check logs for report generation errors
2. Verify all dependencies installed
3. Ensure pipeline completed successfully
4. Review this guide for report interpretation
5. Consult troubleshooting guide for specific issues
