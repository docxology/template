# Validation Module

## Purpose

The Validation module provides comprehensive quality assurance and validation tools for research documents. It ensures PDF rendering integrity, markdown structure validity, and data consistency across the research project.

## Architecture

### Core Components

**pdf_validator.py**
- PDF text extraction and analysis
- Rendering issue detection (unresolved references, warnings, errors)
- Document structure verification
- First-N-words extraction for preview

**markdown_validator.py**
- Markdown file discovery and collection
- Image reference validation
- Cross-reference verification
- Mathematical equation validation
- Link and URL integrity checking
- Section anchor validation

**integrity.py**
- File integrity verification (SHA-256 hashing)
- Cross-reference validation across documents
- Data consistency checking
- Academic standards compliance
- Build artifact verification
- Completeness validation

## Key Features

### PDF Validation
```python
from infrastructure.validation import validate_pdf_rendering

report = validate_pdf_rendering(Path("output/pdf/manuscript.pdf"))
# Returns: issues, text preview, document structure validation
```

### Markdown Validation
```python
from infrastructure.validation import validate_markdown

problems, exit_code = validate_markdown("manuscript/", ".")
# Validates images, references, equations, links
```

### Integrity Verification
```python
from infrastructure.validation import verify_output_integrity

report = verify_output_integrity(Path("output/"))
# Comprehensive file, cross-ref, data, and academic standards checks
```

## Testing

Run validation tests with:
```bash
pytest tests/infrastructure/test_validation/
```

## Configuration

No specific configuration required. All validation operates with sensible defaults.

## Integration

Validation module is used by:
- Build pipeline (4-validate_output.py) for quality gates
- Quality checker for document analysis
- CI/CD systems for automated validation

## See Also

- [`core/`](../core/) - Foundation utilities
- [`build/`](../build/) - Build & reproducibility tools

