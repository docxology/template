# Validation Module

## Purpose

The Validation module provides quality assurance and validation tools for research documents. It ensures PDF rendering integrity, markdown structure validity, and data consistency across the research project.

## Architecture

### Core Components

**content/pdf_validator.py**
- PDF text extraction and analysis
- Rendering issue detection (unresolved references, warnings, errors)
- Document structure verification
- First-N-words extraction for preview

**content/discovery.py**
- Canonical markdown enumeration: `discover_markdown_files(root, scope=...)`
- Scopes: `tree` (non-recursive `*.md` in one directory), `repo` (shared doc-scan exclusions), `link_audit` (link-checker exclusions)

**content/markdown_validator.py**
- Manuscript directory discovery at `projects/{name}/manuscript/` (`find_manuscript_directory`)
- Image reference validation
- Cross-reference verification
- Mathematical equation validation
- Link and URL integrity checking
- Section anchor validation
- Does **not** own file discovery — use `content/discovery.py`

**integrity/link_extract.py**
- Library surface for markdown link extraction and validation (no CLI)
- `extract_links`, `extract_code_blocks`, path/import/placeholder validators, `check_file_reference`, `LinkCheckResult`
- Link audits enumerate markdown via `discover_markdown_files(..., scope="link_audit")` from `content/discovery.py`

**integrity/check_links.py**
- Documentation link verification CLI (~140 lines); re-exports `discover_markdown_files` and `link_extract` helpers

**integrity/link_validator.py**
- `LinkValidator.resolve_link_target()` delegates path resolution to `paths.resolve_markdown_target()` with directory index-file fallback

**integrity/link_audit_core.py**
- `run_link_audit(repo_root)` - comprehensive markdown link audit loop

**integrity/link_policies.py**
- Skip policies for manuscript cross-refs and generated output paths

**paths.py**
- `resolve_markdown_target(target, source_file, repo_root)` - canonical path resolver shared by link and accuracy validators

**line_count.py**
- `scan_infrastructure_and_scripts(repo_root)` — warn ≥800 / fail ≥950 for `infrastructure/` and `scripts/`
- `scan_project_scripts(repo_root)` — warn ≥150 / fail ≥250 for every `projects/*/scripts/` tree
- Used by `scripts/gates/module_line_count_check.py` and drift tooling

**docs/lint_runner.py**
- `run_docs_lint(...)` — orchestrates markdown consistency checks (used by `scripts/lint_docs.py`)

**security_gate.py** / **plugin_export.py**
- CI gate logic extracted from `scripts/gates/security_scan.py` and `plugin_export_check.py`

**integrity/checks.py**
- File integrity verification (SHA-256 hashing)
- Cross-reference validation across documents
- Data consistency checking
- Academic standards compliance
- Build artifact verification
- Completeness validation

**repo/audit_orchestrator.py**
- audit coordination across all validation modules
- Unified audit interface with structured results
- Project-aware discovery and categorization
- Multi-format report generation (markdown, JSON)
- Configurable validation options

**repo/issue_categorizer.py**
- Intelligent issue categorization by type and severity
- False positive filtering for common artifacts
- Issue prioritization and grouping
- Severity level assignment
- Statistical analysis of audit results

## Function Signatures

Detailed reference moved to [`References/function-signatures.md`](References/function-signatures.md).

## Key Features

### PDF Validation
```python
from infrastructure.validation import validate_pdf_rendering

report = validate_pdf_rendering(Path("output/{project_name}/pdf/{project_name}_combined.pdf"))
# Returns: issues, text preview, document structure validation
```

### Markdown Validation
```python
from pathlib import Path

from infrastructure.validation import discover_markdown_files, validate_markdown
from infrastructure.validation.content.markdown_validator import collect_symbols, find_manuscript_directory

# Find manuscript directory at standard location
manuscript_dir = find_manuscript_directory(Path("."), project_name="template_code_project")
# Returns projects/{name}/manuscript/ directory

md_paths = [str(p) for p in discover_markdown_files(manuscript_dir, scope="tree")]
labels, anchors = collect_symbols(md_paths)

problems, exit_code = validate_markdown(manuscript_dir, Path("."))
# Validates images, references, equations, links
```

**Naming:** Content `validate_markdown(dir, repo_root)` validates a manuscript tree.
Pipeline `validate_manuscript_output_markdown(project_name)` in `output/pipeline.py`
is the Stage 4 wrapper — do not conflate the two.

**Manuscript Directory Discovery**: The `find_manuscript_directory()` function locates the manuscript directory at `projects/{name}/manuscript/`.

### Integrity Verification
```python
from infrastructure.validation import verify_output_integrity

report = verify_output_integrity(Path("output/"))
# file, cross-ref, data, and academic standards checks
```

### Audit Orchestrator

#### run_comprehensive_audit (function)
```python
def run_comprehensive_audit(
    repo_root: Path,
    verbose: bool = False,
    include_code_validation: bool = True,
    include_directory_validation: bool = True,
    include_import_validation: bool = True,
    include_placeholder_validation: bool = True
) -> ScanResults:
    """Run audit across all validation modules.

    Args:
        repo_root: Repository root directory
        verbose: Enable verbose logging
        include_code_validation: Include code block path validation
        include_directory_validation: Include directory structure validation
        include_import_validation: Include Python import validation
        include_placeholder_validation: Include placeholder consistency validation

    Returns:
        scan results with all issues categorized
    """
```

#### generate_audit_report (function)
```python
def generate_audit_report(scan_results: ScanResults, output_format: str = 'markdown') -> str:
    """Generate a formatted audit report.

    Args:
        scan_results: scan results
        output_format: Output format ('markdown' or 'json')

    Returns:
        Formatted report string
    """
```

### Issue Categorizer

#### categorize_by_type (function)
```python
def categorize_by_type(issues: List[Issue]) -> Dict[str, List[Issue]]:
    """Categorize issues by their type and severity.

    Args:
        issues: List of issues from any validation module

    Returns:
        Dictionary mapping category names to lists of issues
    """
```

#### assign_severity (function)
```python
def assign_severity(issue: Issue) -> str:
    """Assign severity level to an issue.

    Args:
        issue: Issue to evaluate

    Returns:
        Severity level: 'critical', 'error', 'warning', or 'info'
    """
```

#### is_false_positive (function)
```python
def is_false_positive(issue: Issue) -> bool:
    """Determine if an issue is likely a false positive.

    Args:
        issue: Issue to evaluate

    Returns:
        True if issue appears to be a false positive
    """
```

#### filter_false_positives (function)
```python
def filter_false_positives(issues: List[Issue]) -> List[Issue]:
    """Filter out false positive issues from the list.

    Args:
        issues: List of issues to filter

    Returns:
        List with false positives removed
    """
```

#### group_related_issues (function)
```python
def group_related_issues(issues: List[Issue]) -> List[List[Issue]]:
    """Group related issues together for better analysis.

    Args:
        issues: List of issues to group

    Returns:
        List of issue groups (each group is a list of related issues)
    """
```

#### prioritize_issues (function)
```python
def prioritize_issues(issues: List[Issue]) -> List[Issue]:
    """Sort issues by priority (severity, then type).

    Args:
        issues: List of issues to prioritize

    Returns:
        Sorted list with highest priority issues first
    """
```

#### generate_issue_summary (function)
```python
def generate_issue_summary(issues: List[Issue]) -> Dict[str, int]:
    """Generate a summary of issues by category and severity.

    Args:
        issues: List of issues to summarize

    Returns:
        Dictionary with summary statistics
    """
```

### security_gate.py

Optional security scanner aggregation used by `scripts/gates/security_scan.py` (not the default `./run.sh` pipeline).

#### aggregate_security_findings (function)

```python
def aggregate_security_findings(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge per-tool scan payloads into one report.

    Entries with ``status: "skipped"`` are listed under ``skipped_tools`` and do
    not contribute to ``total_findings`` or ``tools_run``. An empty dict from a
    missing tool is **not** treated as a clean scan — callers must emit skipped
    status explicitly.
    """
```

#### run_security_scan (function)

```python
def run_security_scan(repo_root: Path) -> tuple[dict[str, Any], int]:
    """Run bandit, safety, and pip-audit when installed; exit 1 on HIGH findings."""
```

## Testing

Run validation tests with:
```bash
uv run pytest tests/infra_tests/validation/ -q
uv run pytest tests/infra_tests/validation/test_security_gate.py -q
```

## Configuration

No specific configuration required. All validation operates with sensible defaults.

## Integration

Validation module is used by:
- Build pipeline (4-validate_output.py) for quality gates
- Quality checker for document analysis
- CI/CD systems for automated validation

## Troubleshooting

### PDF Validation Fails

**Issue**: `validate_pdf_rendering()` fails to extract text or analyze PDF.

**Solutions**:
- Verify PDF file exists and is readable
- Check PDF is not password-protected
- Ensure PDF contains extractable text (not just images)
- Review PDF file permissions
- Try with a different PDF to isolate file-specific issues

### Markdown Validation Errors

**Issue**: `validate_markdown()` reports false positives or misses issues.

**Solutions**:
- Verify manuscript directory path is correct
- Check markdown file encoding (UTF-8 required)
- Review image paths are relative to manuscript directory
- Ensure figure files exist before validation
- Check LaTeX syntax in markdown files

### Image References Not Found

**Issue**: Validation reports missing image files.

**Solutions**:
- Verify image paths are relative to manuscript directory
- Check image file extensions match references
- Ensure images are generated before validation
- Review path resolution logic for your directory structure
- Check for case sensitivity issues (Linux vs macOS/Windows)

### Cross-Reference Validation Fails

**Issue**: Cross-references reported as unresolved.

**Solutions**:
- Verify reference labels match exactly (case-sensitive)
- Check that referenced sections/equations/figures exist
- Ensure LaTeX label syntax is correct (`\label{...}`)
- Review reference format (`\ref{...}`, `\eqref{...}`, etc.)
- Check for typos in reference keys

### Integrity Check False Positives

**Issue**: Integrity verification reports issues that don't exist.

**Solutions**:
- Verify file paths are correct
- Check file modification times (may affect hash comparison)
- Review integrity check configuration
- Ensure files are not being modified during check
- Compare integrity reports over time

## Best Practices

### PDF Validation

- **Validate Early**: Check PDFs immediately after generation
- **Check Structure**: Verify document structure before content
- **Review Warnings**: Address warnings before they become errors
- **Track Issues**: Log all validation issues for tracking

### Markdown Validation

- **Validate Before Rendering**: Check markdown before PDF generation
- **Use Strict Mode**: Enable strict mode in CI/CD pipelines
- **Fix References**: Resolve all reference issues before proceeding
- **Validate Images**: Ensure all referenced images exist

### Integrity Verification

- **Run Regularly**: Integrate integrity checks into build pipeline
- **Compare Baselines**: Compare against known-good baselines
- **Track Changes**: Monitor integrity reports for unexpected changes
- **Document Issues**: Document any expected integrity differences

### Cross-Reference Management

- **Use Consistent Labels**: Follow consistent naming conventions
- **Validate References**: Check references before final rendering
- **Document Patterns**: Document reference patterns for team
- **Automate Checks**: Integrate reference validation into workflow

### Error Reporting

- **Provide Context**: Include file paths and line numbers in errors
- **Actionable Messages**: Give specific steps to fix issues
- **Categorize Issues**: Distinguish errors from warnings
- **Track Trends**: Monitor validation results over time

## See Also

- [README.md](README.md) - Quick reference guide
- [`core/`](../core/) - Foundation utilities

