# PDF Validation Feature

## Overview

The PDF validation system automatically scans generated PDFs for rendering issues and structural problems. It detects unresolved references (??), missing citations, warnings, errors, and verifies document structure by extracting the first N words.

## Architecture

Following the **thin orchestrator pattern**, the implementation consists of:

1. **Business Logic** (`src/pdf_validator.py`): Core validation algorithms
2. **Orchestrator** (`repo_utilities/validate_pdf_output.py`): I/O and user interface
3. **Tests** (`tests/test_pdf_validator.py`): 100% coverage with real data
4. **Integration** (`generate_pdf_from_scratch.sh`): Automated validation in build pipeline

## Components

### src/pdf_validator.py

Core validation module containing all business logic:

- `extract_text_from_pdf(pdf_path)`: Extract text from PDF files using pypdf
- `scan_for_issues(text)`: Scan for rendering problems
  - Unresolved references (??)
  - Warnings
  - Errors  
  - Missing citations [?]
- `extract_first_n_words(text, n)`: Extract first N words for structure verification
- `validate_pdf_rendering(pdf_path, n_words)`: Complete validation report

### repo_utilities/validate_pdf_output.py

Thin orchestrator script that:

- Imports methods from `src/pdf_validator.py`
- Handles command-line arguments
- Formats and prints validation reports
- Returns appropriate exit codes:
  - `0`: No issues detected
  - `1`: Issues found (with detailed report)
  - `2`: Error during validation

### Usage

#### Standalone Validation

```bash
# Validate default combined PDF
uv run python repo_utilities/validate_pdf_output.py

# Validate specific PDF
uv run python repo_utilities/validate_pdf_output.py output/pdf/01_abstract.pdf

# Show more words (default: 200)
uv run python repo_utilities/validate_pdf_output.py --words 500

# Verbose output
uv run python repo_utilities/validate_pdf_output.py --verbose

# Help
uv run python repo_utilities/validate_pdf_output.py --help
```

#### Automated Validation

The validation is automatically integrated into `generate_pdf_from_scratch.sh`:

```bash
./generate_pdf_from_scratch.sh
```

This will:
1. Clean output directory
2. Regenerate all PDFs
3. **Validate PDF output quality** (new stage)
4. Report any issues found

### Sample Output

```
🔍 Validating PDF: project_combined.pdf

======================================================================
📋 PDF VALIDATION REPORT
======================================================================
📄 File: project_combined.pdf

⚠️  Found 11 rendering issue(s):
   • Unresolved references (??): 11

----------------------------------------------------------------------
📖 First 200 words of document:
----------------------------------------------------------------------
References 1 [1] Alice Brown and Robert Wilson. Advanced optimization 
techniques for machine learning. In Proceedings of the International 
Conference on Machine Learning, pages 456–467. ICML, 2022...
----------------------------------------------------------------------
======================================================================
```

## Test Coverage

### Unit Tests (test_pdf_validator.py)

- ✅ 100% test coverage of `src/pdf_validator.py`
- ✅ Tests with real PDFs (no mocks)
- ✅ Tests edge cases and error handling
- ✅ Validates against actual project PDF when available

### Integration Tests (test_repo_utilities.py)

- ✅ Script existence and executability
- ✅ Import verification
- ✅ End-to-end validation on actual PDFs
- ✅ Error handling for nonexistent files
- ✅ Help text verification

Run tests:

```bash
# Run PDF validator tests
uv run pytest tests/test_pdf_validator.py -v

# Run with coverage
uv run pytest tests/test_pdf_validator.py --cov=pdf_validator --cov-report=term-missing

# Run integration tests
uv run pytest tests/test_repo_utilities.py::TestValidatePDFOutput -v
```

## Common Issues Detected

### Unresolved References (??)

LaTeX/Markdown references that didn't resolve properly:
- Missing section labels
- Undefined equation references
- Broken figure/table references
- Bibliography issues

**Solution**: Ensure all `\label{}` commands are properly defined and referenced.

### Missing Citations [?]

Bibliography references that couldn't be resolved:
- Missing BibTeX entries
- Incorrect citation keys
- Bibliography file not found

**Solution**: Check `references.bib` and ensure all cited keys exist.

### Document Structure Issues

First words showing incorrect page order:
- References appearing before title page
- Missing abstract or introduction
- Incorrect page ordering

**Solution**: Check manuscript source files and preamble order.

## Dependencies

- `pypdf>=5.0`: PDF text extraction (replaces deprecated PyPDF2)
- `reportlab>=4.0`: PDF generation for tests

These are automatically managed by `uv` and defined in `pyproject.toml`.

## Development Workflow

Following TDD principles:

1. Write tests first in `tests/test_pdf_validator.py`
2. Implement business logic in `src/pdf_validator.py`
3. Create thin orchestrator in `repo_utilities/validate_pdf_output.py`
4. Integrate into build pipeline
5. Verify 100% test coverage

## Future Enhancements

Potential improvements:

- [ ] Detect more LaTeX warning patterns
- [ ] Validate cross-reference consistency
- [ ] Check for orphaned figures/tables
- [ ] Verify equation numbering sequence
- [ ] Generate diff reports between PDF versions
- [ ] HTML report generation with highlighted issues
- [ ] Integration with CI/CD pipelines
- [ ] Configurable issue severity levels

## Troubleshooting

### "Module pdf_validator not found"

Ensure you're running from the repository root and using `uv run`:

```bash
cd /path/to/template
uv run python repo_utilities/validate_pdf_output.py
```

### "PDF file not found"

Generate PDFs first:

```bash
./repo_utilities/render_pdf.sh
```

Or run the complete pipeline:

```bash
./generate_pdf_from_scratch.sh
```

### High number of ?? issues

This typically indicates:
1. LaTeX compilation warnings were ignored
2. Missing label definitions
3. Bibliography not properly processed

Check the compilation logs in `output/pdf/*_compile.log` for detailed LaTeX warnings.

## References

- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [Thin Orchestrator Pattern](THIN_ORCHESTRATOR_SUMMARY.md)
- [Project Architecture](ARCHITECTURE.md)
- [Development Workflow](WORKFLOW.md)


