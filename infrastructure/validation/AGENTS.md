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
- Manuscript directory discovery at `projects/{name}/manuscript/`
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

## Function Signatures

### pdf_validator.py

#### extract_text_from_pdf (function)
```python
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text content as a string

    Raises:
        PDFValidationError: If PDF cannot be read or processed
    """
```

#### scan_for_issues (function)
```python
def scan_for_issues(text: str) -> Dict[str, int]:
    """Scan extracted PDF text for common rendering issues.

    Args:
        text: Extracted PDF text content

    Returns:
        Dictionary with issue counts by type
    """
```

#### decode_pdf_hex_strings (function)
```python
def decode_pdf_hex_strings(text: str) -> str:
    """Decode PDF hex-encoded strings in extracted text.

    Args:
        text: Raw PDF text with potential hex strings

    Returns:
        Text with hex strings decoded to readable characters
    """
```

#### extract_first_n_words (function)
```python
def extract_first_n_words(text: str, n: int = 200) -> str:
    """Extract the first N words from PDF text for preview.

    Args:
        text: Extracted PDF text
        n: Number of words to extract (default: 200)

    Returns:
        First N words of the document
    """
```

#### validate_pdf_rendering (function)
```python
def validate_pdf_rendering(
    pdf_path: Path,
    n_words: int = 200
) -> Dict[str, Any]:
    """Comprehensive PDF validation for research documents.

    Args:
        pdf_path: Path to PDF file to validate
        n_words: Number of words to extract for preview (default: 200)

    Returns:
        Validation report with issues, preview, and metadata

    Raises:
        PDFValidationError: If PDF validation fails critically
    """
```

### markdown_validator.py

#### find_markdown_files (function)
```python
def find_markdown_files(markdown_dir: str | Path) -> List[str]:
    """Find all markdown files in a directory recursively.

    Args:
        markdown_dir: Directory to search for markdown files

    Returns:
        List of markdown file paths as strings
    """
```

#### collect_symbols (function)
```python
def collect_symbols(md_paths: List[str]) -> Tuple[Set[str], Set[str]]:
    """Collect all labels and anchors from markdown files.

    Args:
        md_paths: List of markdown file paths

    Returns:
        Tuple of (labels, anchors) sets
    """
```

#### validate_images (function)
```python
def validate_images(
    md_paths: List[str],
    repo_root: str | Path
) -> List[str]:
    """Validate that all image references in markdown files exist.

    Args:
        md_paths: List of markdown file paths
        repo_root: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### validate_refs (function)
```python
def validate_refs(
    md_paths: List[str],
    labels: Set[str],
    anchors: Set[str],
    repo_root: str | Path
) -> List[str]:
    """Validate cross-references in markdown files.

    Args:
        md_paths: List of markdown file paths
        labels: Set of available labels
        anchors: Set of available anchors
        repo_root: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### validate_math (function)
```python
def validate_math(
    md_paths: List[str],
    repo_root: str | Path
) -> List[str]:
    """Validate mathematical equations in markdown files.

    Args:
        md_paths: List of markdown file paths
        repo_root: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### validate_markdown (function)
```python
def validate_markdown(
    markdown_dir: str | Path,
    repo_root: str | Path,
    strict: bool = False
) -> Tuple[List[str], int]:
    """Comprehensive markdown validation for research manuscripts.

    Args:
        markdown_dir: Directory containing markdown files
        repo_root: Repository root directory
        strict: Enable strict validation mode (default: False)

    Returns:
        Tuple of (error_messages, exit_code)
    """
```

#### find_manuscript_directory (function)
```python
def find_manuscript_directory(repo_root: str | Path) -> Path:
    """Find the manuscript directory at the standard location.

    Args:
        repo_root: Repository root directory

    Returns:
        Path to manuscript directory (projects/{name}/manuscript/)

    Raises:
        FileNotFoundError: If manuscript directory not found
    """
```

### integrity.py

#### IntegrityReport (class)
```python
@dataclass
class IntegrityReport:
    """Comprehensive integrity report for output validation."""
    total_files: int = 0
    file_integrity: Dict[str, bool] = field(default_factory=dict)
    cross_references: Dict[str, bool] = field(default_factory=dict)
    data_consistency: Dict[str, bool] = field(default_factory=dict)
    academic_standards: Dict[str, bool] = field(default_factory=dict)
    build_artifacts: Dict[str, Any] = field(default_factory=dict)
    completeness: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
```

#### verify_file_integrity (function)
```python
def verify_file_integrity(
    file_paths: List[Path],
    expected_hashes: Optional[Dict[str, str]] = None
) -> Dict[str, bool]:
    """Verify file integrity using SHA-256 hashing.

    Args:
        file_paths: List of file paths to check
        expected_hashes: Optional dictionary of filename to expected hash

    Returns:
        Dictionary mapping file paths to integrity status
    """
```

#### calculate_file_hash (function)
```python
def calculate_file_hash(
    file_path: Path,
    algorithm: str = 'sha256'
) -> Optional[str]:
    """Calculate hash of a file.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm (default: 'sha256')

    Returns:
        Hexadecimal hash string, or None if file cannot be read
    """
```

#### verify_cross_references (function)
```python
def verify_cross_references(markdown_files: List[Path]) -> Dict[str, bool]:
    """Verify cross-references between markdown files.

    Args:
        markdown_files: List of markdown file paths

    Returns:
        Dictionary mapping reference types to validation status
    """
```

#### verify_data_consistency (function)
```python
def verify_data_consistency(data_files: List[Path]) -> Dict[str, bool]:
    """Verify data file consistency and format validity.

    Args:
        data_files: List of data file paths

    Returns:
        Dictionary mapping data files to consistency status
    """
```

#### verify_academic_standards (function)
```python
def verify_academic_standards(markdown_files: List[Path]) -> Dict[str, bool]:
    """Verify compliance with academic writing standards.

    Args:
        markdown_files: List of markdown file paths

    Returns:
        Dictionary mapping standards to compliance status
    """
```

#### verify_output_integrity (function)
```python
def verify_output_integrity(output_dir: Path) -> IntegrityReport:
    """Comprehensive output integrity verification.

    Args:
        output_dir: Output directory to verify

    Returns:
        Complete integrity report
    """
```

#### generate_integrity_report (function)
```python
def generate_integrity_report(report: IntegrityReport) -> str:
    """Generate human-readable integrity report.

    Args:
        report: Integrity report to format

    Returns:
        Formatted report string
    """
```

#### validate_build_artifacts (function)
```python
def validate_build_artifacts(
    output_dir: Path,
    expected_files: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """Validate build artifacts exist and are properly structured.

    Args:
        output_dir: Output directory to check
        expected_files: Optional expected file structure

    Returns:
        Validation results dictionary
    """
```

#### check_file_permissions (function)
```python
def check_file_permissions(output_dir: Path) -> Dict[str, Any]:
    """Check file permissions for generated outputs.

    Args:
        output_dir: Output directory to check

    Returns:
        Permission check results
    """
```

#### verify_output_completeness (function)
```python
def verify_output_completeness(output_dir: Path) -> Dict[str, Any]:
    """Verify output directory has all expected deliverables.

    Args:
        output_dir: Output directory to check

    Returns:
        Completeness check results
    """
```

#### create_integrity_manifest (function)
```python
def create_integrity_manifest(output_dir: Path) -> Dict[str, Any]:
    """Create integrity manifest for output directory.

    Args:
        output_dir: Output directory to document

    Returns:
        Integrity manifest dictionary
    """
```

#### save_integrity_manifest (function)
```python
def save_integrity_manifest(
    manifest: Dict[str, Any],
    output_path: Path
) -> None:
    """Save integrity manifest to file.

    Args:
        manifest: Integrity manifest to save
        output_path: Path to save manifest file
    """
```

#### load_integrity_manifest (function)
```python
def load_integrity_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """Load integrity manifest from file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Loaded manifest dictionary, or None if loading fails
    """
```

#### verify_integrity_against_manifest (function)
```python
def verify_integrity_against_manifest(
    current_manifest: Dict[str, Any],
    saved_manifest: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare current integrity against saved manifest.

    Args:
        current_manifest: Current integrity manifest
        saved_manifest: Previously saved manifest

    Returns:
        Comparison results dictionary
    """
```

### cli.py

#### validate_pdf_command (function)
```python
def validate_pdf_command(args):
    """CLI command for PDF validation.

    Args:
        args: Parsed command line arguments
    """
```

#### validate_markdown_command (function)
```python
def validate_markdown_command(args):
    """CLI command for markdown validation.

    Args:
        args: Parsed command line arguments
    """
```

#### verify_integrity_command (function)
```python
def verify_integrity_command(args):
    """CLI command for integrity verification.

    Args:
        args: Parsed command line arguments
    """
```

#### main (function)
```python
def main():
    """Main CLI entry point for validation tools."""
```

## Key Features

### PDF Validation
```python
from infrastructure.validation import validate_pdf_rendering

report = validate_pdf_rendering(Path("output/pdf/manuscript.pdf"))
# Returns: issues, text preview, document structure validation
```

### Markdown Validation
```python
from infrastructure.validation import validate_markdown, find_manuscript_directory

# Find manuscript directory at standard location
manuscript_dir = find_manuscript_directory(Path("."))
# Returns projects/{name}/manuscript/ directory

problems, exit_code = validate_markdown("manuscript/", ".")
# Validates images, references, equations, links
```

**Manuscript Directory Discovery**: The `find_manuscript_directory()` function locates the manuscript directory at `projects/{name}/manuscript/`.

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

