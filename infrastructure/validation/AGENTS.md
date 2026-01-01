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

**audit_orchestrator.py**
- Comprehensive audit coordination across all validation modules
- Unified audit interface with structured results
- Project-aware discovery and categorization
- Multi-format report generation (markdown, JSON)
- Configurable validation options

**issue_categorizer.py**
- Intelligent issue categorization by type and severity
- False positive filtering for common artifacts
- Issue prioritization and grouping
- Severity level assignment
- Statistical analysis of audit results

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

#### validate_links_command (function)
```python
def validate_links_command(args):
    """CLI command for link validation.

    Args:
        args: Parsed command line arguments
    """
```

#### main (function)
```python
def main():
    """Main CLI entry point for validation tools."""
```

### validate_pdf_cli.py

#### print_validation_report (function)
```python
def print_validation_report(report: dict, verbose: bool = False) -> None:
    """Print PDF validation report to console.

    Args:
        report: Validation report dictionary
        verbose: Enable verbose output
    """
```

#### main (function)
```python
def main(pdf_path: Optional[Path] = None, n_words: int = 200, verbose: bool = False) -> int:
    """Main function for PDF validation CLI.

    Args:
        pdf_path: Path to PDF file to validate
        n_words: Number of words to extract for preview
        verbose: Enable verbose output

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
```

### validate_markdown_cli.py

#### _repo_root (function)
```python
def _repo_root() -> str:
    """Get repository root directory.

    Returns:
        Repository root path as string
    """
```

#### find_markdown_files (function)
```python
def find_markdown_files(directory: str) -> list:
    """Find all markdown files in directory.

    Args:
        directory: Directory to search

    Returns:
        List of markdown file paths
    """
```

#### collect_symbols (function)
```python
def collect_symbols(md_files: list) -> tuple:
    """Collect symbols from markdown files.

    Args:
        md_files: List of markdown file paths

    Returns:
        Tuple of (labels, anchors) sets
    """
```

#### validate_images (function)
```python
def validate_images(md_files: list, repo_root_str: str) -> list:
    """Validate image references in markdown files.

    Args:
        md_files: List of markdown file paths
        repo_root_str: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### validate_refs (function)
```python
def validate_refs(md_files: list, labels: dict, anchors: dict, repo_root_str: str) -> list:
    """Validate cross-references in markdown files.

    Args:
        md_files: List of markdown file paths
        labels: Dictionary of available labels
        anchors: Dictionary of available anchors
        repo_root_str: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### validate_math (function)
```python
def validate_math(md_files: list, repo_root_str: str) -> list:
    """Validate mathematical equations in markdown files.

    Args:
        md_files: List of markdown file paths
        repo_root_str: Repository root directory

    Returns:
        List of validation error messages
    """
```

#### main (function)
```python
def main() -> int:
    """Main function for markdown validation CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
```

### output_validator.py

#### validate_copied_outputs (function)
```python
def validate_copied_outputs(output_dir: Path) -> bool:
    """Validate that outputs were copied correctly.

    Args:
        output_dir: Output directory to validate

    Returns:
        True if validation passes, False otherwise
    """
```

#### validate_root_output_structure (function)
```python
def validate_root_output_structure(repo_root: Path) -> Dict[str, Any]:
    """Validate the root output directory structure.

    Args:
        repo_root: Repository root directory

    Returns:
        Validation results dictionary
    """
```

#### validate_output_structure (function)
```python
def validate_output_structure(output_dir: Path) -> Dict:
    """Validate output directory structure and contents.

    Args:
        output_dir: Output directory to validate

    Returns:
        Validation results dictionary
    """
```

### figure_validator.py

#### validate_figure_registry (function)
```python
def validate_figure_registry(registry_path: Path) -> Dict[str, Any]:
    """Validate figure registry integrity.

    Args:
        registry_path: Path to figure registry file

    Returns:
        Validation results dictionary
    """
```

### link_validator.py

#### LinkValidator (class)
```python
class LinkValidator:
    """Validate links and references in documentation."""

    def __init__(self, repo_root: Path):
        """Initialize link validator.

        Args:
            repo_root: Repository root directory
        """
```

#### main (function)
```python
def main() -> int:
    """Main function for link validation CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
```

### repo_scanner.py

#### AccuracyIssue (class)
```python
@dataclass
class AccuracyIssue:
    """Represents an accuracy issue found during scanning."""
    file: Path
    line: int
    issue_type: str
    description: str
    severity: str = "medium"
```

#### CompletenessGap (class)
```python
@dataclass
class CompletenessGap:
    """Represents a completeness gap found during scanning."""
    category: str
    description: str
    severity: str
    affected_files: List[Path] = field(default_factory=list)
```

#### ScanResults (class)
```python
@dataclass
class ScanResults:
    """Results of repository scanning."""
    accuracy_issues: List[AccuracyIssue] = field(default_factory=list)
    completeness_gaps: List[CompletenessGap] = field(default_factory=list)
    scanned_files: int = 0
    scan_duration: float = 0.0
```

#### RepositoryScanner (class)
```python
class RepositoryScanner:
    """Scan repository for documentation quality issues."""

    def __init__(self, repo_root: Path):
        """Initialize repository scanner.

        Args:
            repo_root: Repository root directory
        """
```

#### main (function)
```python
def main():
    """Main function for repository scanning CLI."""
```

### doc_scanner_refactored.py

#### DocumentationFile (class)
```python
@dataclass
class DocumentationFile:
    """Represents a documentation file."""
    path: Path
    content: str
    headings: Set[str]
    links: List[str]
```

#### LinkIssue (class)
```python
@dataclass
class LinkIssue:
    """Represents a link validation issue."""
    source_file: Path
    target: str
    line: int
    issue_type: str
```

#### AccuracyIssue (class)
```python
@dataclass
class AccuracyIssue:
    """Represents an accuracy issue."""
    file: Path
    issue_type: str
    description: str
    severity: str
```

#### CompletenessGap (class)
```python
@dataclass
class CompletenessGap:
    """Represents a completeness gap."""
    category: str
    description: str
    severity: str
```

#### QualityIssue (class)
```python
@dataclass
class QualityIssue:
    """Represents a quality issue."""
    file: Path
    line: int
    issue_type: str
    description: str
    severity: str
```

#### ScanResults (class)
```python
@dataclass
class ScanResults:
    """Documentation scan results."""
    accuracy_issues: List[AccuracyIssue] = field(default_factory=list)
    completeness_gaps: List[CompletenessGap] = field(default_factory=list)
    quality_issues: List[QualityIssue] = field(default_factory=list)
```

#### DocumentationScanner (class)
```python
class DocumentationScanner:
    """Comprehensive documentation scanner."""

    def __init__(self, repo_root: Path):
        """Initialize documentation scanner.

        Args:
            repo_root: Repository root directory
        """
```

#### main (function)
```python
def main():
    """Main function for documentation scanning CLI."""
```

### doc_scanner.py

#### DocumentationScanner (class)
```python
class DocumentationScanner:
    """Documentation quality scanner."""

    def __init__(self, repo_root: Path):
        """Initialize documentation scanner.

        Args:
            repo_root: Repository root directory
        """
```

#### main (function)
```python
def main():
    """Main function for documentation scanning CLI."""
```

### doc_quality.py

#### assess_clarity (function)
```python
def assess_clarity(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess documentation clarity.

    Args:
        content: File content
        md_file: Markdown file path
        lines: File lines
        repo_root: Repository root

    Returns:
        List of quality issues
    """
```

#### assess_actionability (function)
```python
def assess_actionability(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess documentation actionability.

    Args:
        content: File content
        md_file: Markdown file path
        lines: File lines
        repo_root: Repository root

    Returns:
        List of quality issues
    """
```

#### assess_maintainability (function)
```python
def assess_maintainability(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess documentation maintainability.

    Args:
        content: File content
        md_file: Markdown file path
        lines: File lines
        repo_root: Repository root

    Returns:
        List of quality issues
    """
```

#### check_formatting (function)
```python
def check_formatting(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Check documentation formatting.

    Args:
        content: File content
        md_file: Markdown file path
        lines: File lines
        repo_root: Repository root

    Returns:
        List of quality issues
    """
```

#### group_quality_by_type (function)
```python
def group_quality_by_type(issues: List[QualityIssue]) -> Dict[str, int]:
    """Group quality issues by type.

    Args:
        issues: List of quality issues

    Returns:
        Dictionary of issue counts by type
    """
```

#### group_quality_by_severity (function)
```python
def group_quality_by_severity(issues: List[QualityIssue]) -> Dict[str, int]:
    """Group quality issues by severity.

    Args:
        issues: List of quality issues

    Returns:
        Dictionary of issue counts by severity
    """
```

#### run_quality_phase (function)
```python
def run_quality_phase(md_files: List[Path], repo_root: Path) -> Tuple[Dict, List[QualityIssue]]:
    """Run quality assessment phase.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        Tuple of (summary_dict, issues_list)
    """
```

### doc_models.py

#### DocumentationFile (class)
```python
@dataclass
class DocumentationFile:
    """Represents a documentation file."""
    path: Path
    content: str
    headings: Set[str]
    links: List[str]
```

#### LinkIssue (class)
```python
@dataclass
class LinkIssue:
    """Represents a link validation issue."""
    source_file: Path
    target: str
    line: int
    issue_type: str
```

#### AccuracyIssue (class)
```python
@dataclass
class AccuracyIssue:
    """Represents an accuracy issue."""
    file: Path
    issue_type: str
    description: str
    severity: str
```

#### CompletenessGap (class)
```python
@dataclass
class CompletenessGap:
    """Represents a completeness gap."""
    category: str
    description: str
    severity: str
```

#### QualityIssue (class)
```python
@dataclass
class QualityIssue:
    """Represents a quality issue."""
    file: Path
    line: int
    issue_type: str
    description: str
    severity: str
```

### doc_discovery.py

#### find_markdown_files (function)
```python
def find_markdown_files(repo_root: Path) -> List[Path]:
    """Find all markdown files in repository.

    Args:
        repo_root: Repository root directory

    Returns:
        List of markdown file paths
    """
```

#### catalog_agents_readme (function)
```python
def catalog_agents_readme(md_files: List[Path], repo_root: Path) -> List[str]:
    """Catalog AGENTS.md and README.md files.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        List of AGENTS.md/README.md files
    """
```

#### find_config_files (function)
```python
def find_config_files(repo_root: Path) -> Dict[str, Path]:
    """Find configuration files in repository.

    Args:
        repo_root: Repository root directory

    Returns:
        Dictionary of config file types to paths
    """
```

#### find_script_files (function)
```python
def find_script_files(repo_root: Path) -> List[Path]:
    """Find script files in repository.

    Args:
        repo_root: Repository root directory

    Returns:
        List of script file paths
    """
```

#### create_hierarchy (function)
```python
def create_hierarchy(md_files: List[Path], repo_root: Path) -> Dict[str, List[str]]:
    """Create documentation hierarchy.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        Dictionary of hierarchy information
    """
```

#### identify_cross_references (function)
```python
def identify_cross_references(md_files: List[Path]) -> Set[str]:
    """Identify cross-references between files.

    Args:
        md_files: List of markdown files

    Returns:
        Set of cross-reference identifiers
    """
```

#### categorize_documentation (function)
```python
def categorize_documentation(md_files: List[Path], repo_root: Path) -> Dict[str, List[str]]:
    """Categorize documentation files.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        Dictionary of categories to file lists
    """
```

#### analyze_documentation_file (function)
```python
def analyze_documentation_file(md_file: Path, repo_root: Path) -> DocumentationFile:
    """Analyze individual documentation file.

    Args:
        md_file: Markdown file path
        repo_root: Repository root

    Returns:
        DocumentationFile object
    """
```

#### run_discovery_phase (function)
```python
def run_discovery_phase(repo_root: Path) -> Dict:
    """Run documentation discovery phase.

    Args:
        repo_root: Repository root directory

    Returns:
        Discovery results dictionary
    """
```

### doc_completeness.py

#### check_feature_documentation (function)
```python
def check_feature_documentation(repo_root: Path, documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check feature documentation completeness.

    Args:
        repo_root: Repository root directory
        documentation_files: List of documentation files

    Returns:
        List of completeness gaps
    """
```

#### check_script_documentation (function)
```python
def check_script_documentation(repo_root: Path) -> List[CompletenessGap]:
    """Check script documentation completeness.

    Args:
        repo_root: Repository root directory

    Returns:
        List of completeness gaps
    """
```

#### check_config_documentation (function)
```python
def check_config_documentation(config_files: Dict[str, Path]) -> List[CompletenessGap]:
    """Check configuration documentation completeness.

    Args:
        config_files: Dictionary of config files

    Returns:
        List of completeness gaps
    """
```

#### check_troubleshooting (function)
```python
def check_troubleshooting(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check troubleshooting documentation completeness.

    Args:
        documentation_files: List of documentation files

    Returns:
        List of completeness gaps
    """
```

#### check_workflow_documentation (function)
```python
def check_workflow_documentation(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check workflow documentation completeness.

    Args:
        documentation_files: List of documentation files

    Returns:
        List of completeness gaps
    """
```

#### check_onboarding (function)
```python
def check_onboarding(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check onboarding documentation completeness.

    Args:
        documentation_files: List of documentation files

    Returns:
        List of completeness gaps
    """
```

#### check_cross_reference_completeness (function)
```python
def check_cross_reference_completeness() -> List[CompletenessGap]:
    """Check cross-reference completeness.

    Returns:
        List of completeness gaps
    """
```

#### group_gaps_by_category (function)
```python
def group_gaps_by_category(gaps: List[CompletenessGap]) -> Dict[str, int]:
    """Group completeness gaps by category.

    Args:
        gaps: List of completeness gaps

    Returns:
        Dictionary of gap counts by category
    """
```

#### group_gaps_by_severity (function)
```python
def group_gaps_by_severity(gaps: List[CompletenessGap]) -> Dict[str, int]:
    """Group completeness gaps by severity.

    Args:
        gaps: List of completeness gaps

    Returns:
        Dictionary of gap counts by severity
    """
```

#### run_completeness_phase (function)
```python
def run_completeness_phase(repo_root: Path, documentation_files: List[DocumentationFile]) -> Tuple[Dict, List[CompletenessGap]]:
    """Run completeness assessment phase.

    Args:
        repo_root: Repository root directory
        documentation_files: List of documentation files

    Returns:
        Tuple of (summary_dict, gaps_list)
    """
```

### doc_accuracy.py

#### extract_headings (function)
```python
def extract_headings(content: str) -> Set[str]:
    """Extract headings from markdown content.

    Args:
        content: Markdown content

    Returns:
        Set of heading texts
    """
```

#### resolve_file_path (function)
```python
def resolve_file_path(target: str, source_file: Path, repo_root: Path) -> Tuple[bool, str]:
    """Resolve file path relative to source.

    Args:
        target: Target file path
        source_file: Source file path
        repo_root: Repository root

    Returns:
        Tuple of (exists, resolved_path)
    """
```

#### check_links (function)
```python
def check_links(md_files: List[Path], repo_root: Path, all_headings: Dict[str, Set[str]]) -> List[LinkIssue]:
    """Check links in markdown files.

    Args:
        md_files: List of markdown files
        repo_root: Repository root
        all_headings: Dictionary of headings by file

    Returns:
        List of link issues
    """
```

#### extract_script_name (function)
```python
def extract_script_name(command: str) -> Optional[str]:
    """Extract script name from command.

    Args:
        command: Command string

    Returns:
        Script name if found, None otherwise
    """
```

#### verify_commands (function)
```python
def verify_commands(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Verify commands in documentation.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        List of accuracy issues
    """
```

#### check_file_paths (function)
```python
def check_file_paths(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Check file paths in documentation.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        List of accuracy issues
    """
```

#### validate_config_options (function)
```python
def validate_config_options(md_files: List[Path], config_files: Dict[str, Path]) -> List[AccuracyIssue]:
    """Validate configuration options in documentation.

    Args:
        md_files: List of markdown files
        config_files: Dictionary of config files

    Returns:
        List of accuracy issues
    """
```

#### check_terminology (function)
```python
def check_terminology(md_files: List[Path]) -> List[AccuracyIssue]:
    """Check terminology consistency.

    Args:
        md_files: List of markdown files

    Returns:
        List of accuracy issues
    """
```

#### run_accuracy_phase (function)
```python
def run_accuracy_phase(md_files: List[Path], repo_root: Path, config_files: Dict[str, Path]) -> Tuple[Dict, List[AccuracyIssue]]:
    """Run accuracy assessment phase.

    Args:
        md_files: List of markdown files
        repo_root: Repository root
        config_files: Dictionary of config files

    Returns:
        Tuple of (summary_dict, issues_list)
    """
```

### check_links.py

#### find_all_markdown_files (function)
```python
def find_all_markdown_files(repo_root: str) -> List[Path]:
    """Find all markdown files in repository.

    Args:
        repo_root: Repository root directory

    Returns:
        List of markdown file paths
    """
```

#### extract_links (function)
```python
def extract_links(content: str, file_path: Path) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Extract links from markdown content.

    Args:
        content: Markdown content
        file_path: Source file path

    Returns:
        Tuple of (file_links, heading_links, external_links)
    """
```

#### check_file_reference (function)
```python
def check_file_reference(target: str, source_file: Path, repo_root: Path) -> Tuple[bool, str]:
    """Check if file reference exists.

    Args:
        target: Target file path
        source_file: Source file path
        repo_root: Repository root

    Returns:
        Tuple of (exists, resolved_path)
    """
```

#### extract_headings (function)
```python
def extract_headings(content: str) -> Set[str]:
    """Extract headings from markdown content.

    Args:
        content: Markdown content

    Returns:
        Set of headings
    """
```

#### main (function)
```python
def main():
    """Main function for link checking CLI."""
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
    """Run comprehensive audit across all validation modules.

    Args:
        repo_root: Repository root directory
        verbose: Enable verbose logging
        include_code_validation: Include code block path validation
        include_directory_validation: Include directory structure validation
        include_import_validation: Include Python import validation
        include_placeholder_validation: Include placeholder consistency validation

    Returns:
        Complete scan results with all issues categorized
    """
```

#### generate_audit_report (function)
```python
def generate_audit_report(scan_results: ScanResults, output_format: str = 'markdown') -> str:
    """Generate a formatted audit report.

    Args:
        scan_results: Complete scan results
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

