---
name: infrastructure-validation
description: Skill for the validation infrastructure module providing PDF validation, markdown validation, output integrity checks, link verification, documentation audits, issue categorization, and repository scanning. Use when validating research outputs, checking document quality, running audits, or verifying cross-references.
---

# Validation Module

Quality assurance and content validation tools for research outputs. Covers PDFs, markdown, links, output integrity, and comprehensive audits.

## PDF Validation (`content/pdf_validator.py`)

```python
from infrastructure.validation import validate_pdf_rendering, extract_text_from_pdf, scan_for_issues

# Validate a rendered PDF
results = validate_pdf_rendering(pdf_path)

# Extract text for analysis
text = extract_text_from_pdf(pdf_path)

# Scan for rendering issues
issues = scan_for_issues(text)
```

**CLI:**

```bash
uv run python -m infrastructure.validation.cli.main pdf output/{project}/pdf/
uv run python -m infrastructure.validation.cli.pdf output/{project}/pdf/
```

## Markdown Validation (`markdown_validator.py`)

```python
from pathlib import Path

from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.markdown_validator import (
    collect_symbols,
    validate_images,
    validate_markdown,
    validate_math,
    validate_refs,
)

repo_root = Path(".")
manuscript_dir = repo_root / "projects" / "project" / "manuscript"
md_files = [str(path) for path in discover_markdown_files(manuscript_dir, scope="tree")]
labels, anchors = collect_symbols(md_files)

# Validate all markdown in a directory
problems, exit_code = validate_markdown(manuscript_dir, repo_root)

# Individual checks
image_issues = validate_images(md_files, repo_root)
ref_issues = validate_refs(md_files, repo_root, labels, anchors)
math_issues = validate_math(md_files, repo_root)
```

**CLI:**

```bash
uv run python -m infrastructure.validation.cli.main markdown projects/{name}/manuscript/
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/
```

## Output Integrity (`integrity/checks.py`)

```python
from infrastructure.validation import (
    verify_output_integrity, verify_file_integrity,
    verify_cross_references, verify_data_consistency,
    verify_academic_standards, generate_integrity_report,
)

# Full integrity check
report = verify_output_integrity(output_dir)

# Individual checks
verify_file_integrity(file_path)
verify_cross_references(manuscript_dir)
verify_data_consistency(data_dir)
verify_academic_standards(manuscript_dir)
```

## Output Structure Validation (`output/validator.py`)

```python
from infrastructure.validation import validate_output_structure, validate_copied_outputs

validate_output_structure(output_dir)
validate_copied_outputs(source_dir, dest_dir)
```

## Link Verification (`integrity/check_links.py`, `integrity/link_validator.py`)

```python
from pathlib import Path
from infrastructure.validation import LinkValidator

validator = LinkValidator(Path("."))
results = validator.validate_all_markdown_files()
```

## Figure Validation (`figure_validator.py`)

```python
from pathlib import Path
from infrastructure.validation import validate_figure_registry

success, issues = validate_figure_registry(
    Path("projects/<name>/output/figures/figure_registry.json"),
    Path("projects/<name>/manuscript"),
)
```

Both registry shapes are accepted: ``{"fig:label": {...}, ...}`` (dict, emitted
by ``FigureManager``) and ``[{"label": "fig:label", ...}, ...]`` (list, emitted
by project-side scripts that produce a flat manifest).

## Audit Orchestration (`repo/audit_orchestrator.py`)

```python
from infrastructure.validation import run_comprehensive_audit, generate_audit_report

# Run all validation checks in one pass
audit_results = run_comprehensive_audit(project_path)
report = generate_audit_report(audit_results)
```

## Issue Categorization (`repo/issue_categorizer.py`)

```python
from infrastructure.validation import (
    categorize_by_type, assign_severity, filter_false_positives,
    prioritize_issues, group_related_issues, generate_issue_summary,
)

categorized = categorize_by_type(raw_issues)
filtered = filter_false_positives(categorized)
prioritized = prioritize_issues(filtered)
summary = generate_issue_summary(prioritized)
```

## Documentation Scanning (`docs/scanner.py`, `docs/accuracy.py`, `docs/completeness.py`)

Comprehensive scanning of documentation for accuracy, completeness, and quality:

```python
from infrastructure.validation.docs.scanner import DocumentationScanner
from infrastructure.validation.docs.accuracy import verify_documentation_accuracy
from infrastructure.validation.docs.completeness import analyze_documentation_completeness

scanner = DocumentationScanner(repo_root)
inventory = scanner.discover_inventory()
accuracy_report, link_issues, accuracy_issues, headings = verify_documentation_accuracy(
    md_files, repo_root, config_files
)
completeness_report, gaps = analyze_documentation_completeness(repo_root, documentation_files, config_files)
```

## Repository Scanning (`repo/scanner.py`)

```python
from infrastructure.validation.repo.scanner import RepositoryScanner
scanner = RepositoryScanner(repo_root)
results = scanner.scan_all()
```

## Additional CLI Subcommands

```bash
# Strict source-markdown gate: pitfalls + undefined citations
uv run python -m infrastructure.validation.cli prerender projects/{name}/manuscript/

# Validate manuscript claims against registered project evidence
uv run python -m infrastructure.validation.cli evidence projects/{name} --fail-on-issues

# Scan manuscript prose for AI-writing fingerprints
uv run python -m infrastructure.validation.cli prose-quality projects/{name}/manuscript/
```

## Mock Validation (`output/no_mock_enforcer.py`)

The enforced lexical API reports prohibited mock-framework imports/calls. It
does not prove that monkeypatch dependency replacements are absent:

```python
from infrastructure.validation.output.no_mock_enforcer import validate_no_mocks
violations = validate_no_mocks(tests_dir, repo_root)
```

Repository-level commands:

```bash
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory
```
