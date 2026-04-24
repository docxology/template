# Validation Module

> **Comprehensive quality assurance for research outputs**

**Location:** `infrastructure/validation/`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **PDF Validation**: Structural integrity checks, xref table verification, trailer validation, text extraction
- **Markdown Validation**: Heading hierarchy, image paths, cross-references, math expression checks
- **Output Integrity**: File integrity, data consistency, academic standards verification
- **Figure Validation**: Figure registry completeness and correctness
- **Repository Scanning**: Accuracy and completeness audits across the entire repository
- **No-Mock Enforcement**: Ensures test suites comply with the no-mocks policy
- **Issue Categorization**: Severity assignment, false-positive filtering, prioritization
- **CLI Interface**: Unified command-line entry point for all validation tasks

---

## Usage Examples

### PDF Validation

```python
from pathlib import Path
from infrastructure.validation import validate_pdf_rendering, extract_text_from_pdf, scan_for_issues

pdf_path = Path("output/code_project/pdf/code_project_combined.pdf")

# Validate structural integrity of a rendered PDF
results = validate_pdf_rendering(pdf_path)

# Extract text content for downstream analysis
text = extract_text_from_pdf(pdf_path)

# Scan extracted text for rendering issues
issues = scan_for_issues(text)
```

### Markdown Validation

```python
from pathlib import Path
from infrastructure.validation import (
    find_markdown_files, validate_markdown, validate_images, validate_refs, validate_math,
)
from infrastructure.validation.content.markdown_validator import collect_symbols

repo_root = Path(".")
manuscript_dir = repo_root / "projects" / "code_project" / "manuscript"

# Validate all markdown files in a manuscript directory
problems, exit_code = validate_markdown(manuscript_dir, repo_root)

# Individual checks
md_files = find_markdown_files(manuscript_dir)
labels, anchors = collect_symbols(md_files)

image_issues = validate_images(md_files, repo_root)
ref_issues = validate_refs(md_files, repo_root, labels, anchors)
math_issues = validate_math(md_files, repo_root)
```

### Output Integrity Verification

```python
from pathlib import Path
from infrastructure.validation import (
    verify_output_integrity, verify_file_integrity,
    verify_cross_references, verify_data_consistency,
    verify_academic_standards, generate_integrity_report,
)

output_dir = Path("output/code_project")

# Full integrity check across all output artifacts
report = verify_output_integrity(output_dir)

# Targeted checks
verify_file_integrity(output_dir / "pdf" / "code_project_combined.pdf")
verify_cross_references(Path("projects/code_project/manuscript"))
verify_data_consistency(output_dir / "data")
verify_academic_standards(Path("projects/code_project/manuscript"))

# Generate a structured integrity report
integrity_report = generate_integrity_report(output_dir)
```

### Figure Validation

```python
from pathlib import Path
from infrastructure.validation import validate_figure_registry

success, issues = validate_figure_registry(
    Path("projects/code_project/output/figures/figure_registry.json"),
    Path("projects/code_project/manuscript"),
)
```

Both registry shapes are accepted:

* **Dict shape** — ``{"fig:label": {...}, ...}`` (emitted by
  ``FigureManager``).
* **List shape** — ``[{"label": "fig:label", ...}, ...]`` (emitted by
  project-side scripts, e.g. ``cognitive_case_diagrams/scripts/generate_diagrams.py``).

### Repository Audit and Issue Management

```python
from pathlib import Path
from infrastructure.validation import (
    run_comprehensive_audit, generate_audit_report,
    categorize_by_type, assign_severity,
    filter_false_positives, prioritize_issues, generate_issue_summary,
)

project_path = Path("projects/code_project")

# Run all validation checks in a single pass
audit_results = run_comprehensive_audit(project_path)
report = generate_audit_report(audit_results)

# Process and triage discovered issues
categorized = categorize_by_type(audit_results)
filtered = filter_false_positives(categorized)
prioritized = prioritize_issues(filtered)
summary = generate_issue_summary(prioritized)
```

### Output Structure Validation

```python
from pathlib import Path
from infrastructure.validation import validate_output_structure, validate_copied_outputs

validate_output_structure(Path("output/code_project"))
validate_copied_outputs(
    source_dir=Path("projects/code_project/output"),
    dest_dir=Path("output/code_project"),
)
```

### Link Verification

```python
from pathlib import Path
from infrastructure.validation import LinkValidator

validator = LinkValidator()
results = validator.check_all(Path("docs"))
```

---

## CLI Usage

```bash
# Validate PDFs in an output directory
python3 -m infrastructure.validation.cli pdf output/{project}/pdf/

# Validate markdown manuscript files
python3 -m infrastructure.validation.cli markdown projects/{name}/manuscript/

# Both commands support the unified CLI entry point
python3 -m infrastructure.validation.cli --help
```

---

## Module Organization

The validation package is organized into four logical subpackage groups:

| Group | Modules | Purpose |
|-------|---------|---------|
| **Content** | `pdf_validator`, `markdown_validator`, `figure_validator` | File-type-specific validation |
| **Integrity** | `integrity`, `link_validator`, `check_links` | Cross-reference and link verification |
| **Repository** | `repo_scanner`, `audit_orchestrator`, `issue_categorizer` | Project-wide scanning and triage |
| **Output** | `output_validator` | Pipeline output structure checks |

All public functions are re-exported from `infrastructure.validation` for convenient single-import access.

---

## Related Documentation

- [Rendering Module](rendering-module.md) -- generates the outputs that validation checks
- [Reporting Module](reporting-module.md) -- aggregates validation results into pipeline reports
- [Testing Strategy](../../architecture/testing-strategy.md) -- no-mocks policy and coverage requirements
- [PDF Validation Guide](../pdf-validation.md) -- detailed PDF validation reference
