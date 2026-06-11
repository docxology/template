## Function Signatures

### content/pdf_validator.py

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
    """PDF validation for research documents.

    Args:
        pdf_path: Path to PDF file to validate
        n_words: Number of words to extract for preview (default: 200)

    Returns:
        Validation report with issues, preview, and metadata

    Raises:
        PDFValidationError: If PDF validation fails critically
    """
```

### content/discovery.py

#### discover_markdown_files (function)
```python
def discover_markdown_files(
    root: Path,
    *,
    scope: Literal["tree", "repo", "link_audit"] = "tree",
    repo_root: Path | None = None,
) -> List[Path]:
    """Discover markdown files under *root* according to *scope*.

    Scopes:
        tree — non-recursive ``*.md`` in one directory (manuscript dirs).
        repo — recursive scan with ``DEFAULT_EXCLUDE_PARTS`` (doc scanner).
        link_audit — recursive scan with link-checker exclusions.

    Returns:
        Sorted list of markdown file paths
    """
```

### content/markdown_validator.py

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
) -> List[DiagnosticEvent]:
    """Validate that all image references in markdown files exist.

    Args:
        md_paths: List of markdown file paths
        repo_root: Repository root directory

    Returns:
        List of diagnostic events
    """
```

#### validate_refs (function)
```python
def validate_refs(
    md_paths: List[str],
    repo_root: str | Path
) -> List[DiagnosticEvent]:
    """Validate cross-references in markdown files.

    Args:
        md_paths: List of markdown file paths
        repo_root: Repository root directory
        labels: Set of available labels
        anchors: Set of available anchors

    Returns:
        List of diagnostic events
    """
```

#### validate_math (function)
```python
def validate_math(
    md_paths: List[str],
    repo_root: str | Path
) -> List[DiagnosticEvent]:
    """Validate mathematical equations in markdown files.

    Args:
        md_paths: List of markdown file paths
        repo_root: Repository root directory

    Returns:
        List of diagnostic events
    """
```

#### validate_markdown (function)
```python
def validate_markdown(
    markdown_dir: str | Path,
    repo_root: str | Path,
    strict: bool = False
) -> Tuple[List[DiagnosticEvent], int]:
    """markdown validation for research manuscripts.

    Args:
        markdown_dir: Directory containing markdown files
        repo_root: Repository root directory
        strict: Enable strict validation mode (default: False)

    Returns:
        Tuple of (diagnostic_events, exit_code)
    """
```

#### find_manuscript_directory (function)
```python
def find_manuscript_directory(repo_root: str | Path, project_name: str = "project") -> Path:
    """Find the manuscript directory at the standard location.

    Args:
        repo_root: Repository root directory

    Returns:
        Path to manuscript directory (projects/{name}/manuscript/)

    Raises:
        FileNotFoundError: If manuscript directory not found
    """
```

### integrity/checks.py

#### IntegrityReport (class)
```python
@dataclass
class IntegrityReport:
    """Container for integrity verification results."""
    file_integrity: dict[str, bool] = field(default_factory=dict)
    cross_reference_integrity: dict[str, bool] = field(default_factory=dict)
    data_consistency: dict[str, bool] = field(default_factory=dict)
    academic_standards: dict[str, bool] = field(default_factory=dict)
    overall_integrity: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
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
def verify_output_integrity(output_dir: Path, manuscript_dir: Path | None = None) -> IntegrityReport:
    """output integrity verification.

    Args:
        output_dir: Output directory to verify
        manuscript_dir: Optional manuscript directory for cross-reference checks

    Returns:
        integrity report
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

### cli/main.py

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

#### validate_prerender_command (function)
```python
def validate_prerender_command(args):
    """CLI command for the strict source-markdown pre-render gate.

    Invoked as `python -m infrastructure.validation.cli prerender <manuscript_dir>`
    (options: `--repo-root`, `--bib`).
    """
```

#### validate_evidence_command (function)
```python
def validate_evidence_command(args):
    """CLI command validating manuscript claims against registered evidence.

    Invoked as `python -m infrastructure.validation.cli evidence <project_root>`
    (options: `--manuscript-dir`, `--output-json`, `--fail-on-issues`).
    """
```

#### validate_prose_quality_command (function)
```python
def validate_prose_quality_command(args):
    """CLI command scanning manuscript prose for AI-writing fingerprints.

    Invoked as `python -m infrastructure.validation.cli prose-quality <path>`
    (options: `--json`, `--fail-on-flags`).
    """
```

#### main (function)
```python
def main():
    """Main CLI entry point for validation tools."""
```

### cli/pdf.py

PDF validation CLI invoked as `python -m infrastructure.validation.cli pdf …`.
Entry points: `main()`, `print_validation_report()`, and helpers for default
`output/{project}/pdf/{project}_combined.pdf` discovery (requires `--project` when
not passing an explicit path).

### cli/main.py — `markdown` subcommand

Markdown validation via `python -m infrastructure.validation.cli markdown …`
(handled by `validate_markdown_command` in `main.py`). Delegates to
`infrastructure.validation.content.markdown_validator.validate_markdown`.
Warn-only by default: exits non-zero **only with `--strict`** when ERROR-severity
issues are found. Use `--strict` when invoking it as a quality gate.

### output/pipeline.py

Pipeline-stage output validation orchestrator (`scripts/04_validate_output.py`).

#### validate_manuscript_output_markdown (function)
```python
def validate_manuscript_output_markdown(project_name: str = "project") -> bool:
    """Validate manuscript markdown for a project during the output pipeline.

    Resolves ``projects/{project_name}/manuscript/``, then calls content
    ``validate_markdown(manuscript_dir, repo_root)``. Returns True when the
    manuscript dir is missing or validation passes.

    Not the same as content ``validate_markdown(dir, repo_root)`` — use this
    name only for the pipeline wrapper; use content ``validate_markdown`` for
    direct directory validation.
    """
```

### output/validator.py

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

### content/figure_validator.py

#### validate_figure_registry (function)
```python
def validate_figure_registry(
    registry_path: Path, manuscript_dir: Path
) -> tuple[bool, list[str]]:
    """Validate that every ``\\ref{}`` / ``\\label{}`` figure key in
    ``manuscript_dir`` is present in the registry at ``registry_path``.

    Two registry shapes are accepted, both encoding the same set of labels:

    * **Dict shape** — ``{"fig:label": {...}, ...}`` (emitted by
      :class:`infrastructure.documentation.figure_manager.FigureManager`).
    * **List shape** — ``[{"label": "fig:label", ...}, ...]`` (emitted by
      project-side scripts that produce a flat manifest, e.g.
      ``projects/cognitive_case_diagrams/scripts/generate_diagrams.py``).

    Items in the list shape that lack a ``label`` field are skipped with a
    warning rather than aborting validation; an unexpected top-level JSON
    type produces a single descriptive load error.

    Returns:
        ``(success, issues)`` — ``success`` is ``True`` iff every reference
        resolves; ``issues`` is the list of unresolved labels (or a single
        load-error string).
    """
```

### integrity/link_validator.py

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

### repo/models.py

#### RepoScanResults (class)
```python
@dataclass
class RepoScanResults:
    """Container for repository scan results."""
    accuracy_issues: List[ScanAccuracyIssue] = field(default_factory=list)
    completeness_gaps: List[CompletenessGap] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
```

#### ScanAccuracyIssue (class)
```python
@dataclass(init=False)
class ScanAccuracyIssue:
    """Accuracy issue found during repository-wide scanning."""
    category: str
    severity: str
    file: str
    line: int = 0
    message: str = ""
    details: str = ""
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

### repo/scanner.py

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

### docs/scanner.py

#### DocumentationScanner (class)
```python
class DocumentationScanner:
    """Documentation quality scanner."""

    def __init__(self, repo_root: Path):
        """Initialize documentation scanner.

        Args:
            repo_root: Repository root directory
        """

    def run_verification_checks(self) -> dict[str, Any]:
        """Run documentation verification checks.

        Delegates to ``run_verification_checks()`` in ``verification.py`` —
        ``run_docs_lint``, ``validate_markdown``, ``verify_commands``,
        and ``detect_markdown_link_cycles()``; see
        ``infrastructure/validation/docs/AGENTS.md`` for status vocabulary.
        """
```

#### main (function)
```python
def main():
    """Main function for documentation scanning CLI."""
```

### docs/quality.py

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

#### assess_documentation_quality (function)
```python
def assess_documentation_quality(md_files: List[Path], repo_root: Path) -> Tuple[Dict, List[QualityIssue]]:
    """Assess documentation quality.

    Args:
        md_files: List of markdown files
        repo_root: Repository root

    Returns:
        Tuple of (summary_dict, issues_list)
    """
```

### docs/models.py

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

#### ScanAccuracyIssue (class)
```python
@dataclass
class ScanAccuracyIssue:
    """Represents an accuracy issue."""
    category: str
    severity: str
    file: str
    line: int = 0
    message: str = ""
    details: str = ""
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

### docs/discovery.py

Documentation inventory helpers (config/script discovery, hierarchy, categorization).
Markdown enumeration uses `discover_markdown_files(repo_root, scope="repo")` from
`content/discovery.py` — not defined in this module.

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

#### discover_documentation (function)
```python
def discover_documentation(repo_root: Path) -> Dict:
    """Discover and inventory documentation across the repository.

    Args:
        repo_root: Repository root directory

    Returns:
        Discovery results dictionary
    """
```

### docs/completeness.py

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
def check_config_documentation(
    config_files: Dict[str, Path],
    repo_root: Path,
) -> List[CompletenessGap]:
    """Check configuration documentation completeness.

    Args:
        config_files: Dictionary of config files
        repo_root: Repository root directory

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
def check_cross_reference_completeness(repo_root: Path) -> List[CompletenessGap]:
    """Check cross-reference completeness.

    Args:
        repo_root: Repository root directory

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

#### analyze_documentation_completeness (function)
```python
def analyze_documentation_completeness(repo_root: Path, documentation_files: List[DocumentationFile]) -> Tuple[Dict, List[CompletenessGap]]:
    """Analyze documentation completeness gaps.

    Args:
        repo_root: Repository root directory
        documentation_files: List of documentation files

    Returns:
        Tuple of (summary_dict, gaps_list)
    """
```

### docs/accuracy.py

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
def verify_commands(md_files: List[Path], repo_root: Path) -> List[ScanAccuracyIssue]:
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
def check_file_paths(md_files: List[Path], repo_root: Path) -> List[ScanAccuracyIssue]:
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
def validate_config_options(
    md_files: List[Path],
    config_files: Dict[str, Path],
    repo_root: Path,
) -> List[ScanAccuracyIssue]:
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
def check_terminology(md_files: List[Path], repo_root: Path) -> List[ScanAccuracyIssue]:
    """Check terminology consistency.

    Args:
        md_files: List of markdown files

    Returns:
        List of accuracy issues
    """
```

#### verify_documentation_accuracy (function)
```python
def verify_documentation_accuracy(
    md_files: List[Path],
    repo_root: Path,
    config_files: Dict[str, Path],
) -> Tuple[Dict, List[ScanAccuracyIssue]]:
    """Verify documentation accuracy.

    Args:
        md_files: List of markdown files
        repo_root: Repository root
        config_files: Dictionary of config files

    Returns:
        Tuple of (summary_dict, issues_list)
    """
```

### integrity/check_links.py

#### discover_markdown_files (function)
```python
def discover_markdown_files(
    root: Path,
    *,
    scope: Literal["tree", "repo", "link_audit"] = "tree",
    repo_root: Path | None = None,
) -> List[Path]:
    """Re-export from ``content.discovery`` — use ``scope=\"link_audit\"`` for link audits.

    Canonical implementation: ``infrastructure.validation.content.discovery``.
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
