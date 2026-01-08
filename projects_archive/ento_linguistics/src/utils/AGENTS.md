# utils/ - Project Utility Modules

## Overview

The `utils/` directory contains project-specific utility modules for the Ento-Linguistic Research Project. These utilities provide logging, exception handling, figure management, validation, reporting, and markdown integration functionality tailored to this research project's needs.

## Purpose

These utilities serve as lightweight wrappers and project-specific implementations that complement the generic infrastructure modules. They provide:

- **Logging**: Standardized logging configuration with progress tracking
- **Exception Handling**: Project-specific exception types with context
- **Figure Management**: Figure registration and metadata tracking
- **Validation**: Wrappers around infrastructure validation tools
- **Reporting**: Pipeline reporting and error aggregation
- **Markdown Integration**: Basic markdown processing utilities

## Directory Structure

```
utils/
├── __init__.py              # Module exports
├── exceptions.py            # Custom exception classes
├── figure_manager.py        # Figure registration and management
├── logging.py              # Logging utilities with progress tracking
├── validation.py            # Validation wrappers
├── reporting.py             # Reporting utilities
└── markdown_integration.py  # Markdown processing utilities
```

## Function Signatures

### logging.py

#### get_logger (function)
```python
def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
```

**Configuration:**
- Log level controlled by `LOG_LEVEL` environment variable:
  - `'0'`: DEBUG
  - `'1'`: INFO (default)
  - `'2'`: WARNING
  - `'3'`: ERROR
- Console handler with standard formatter: `%(levelname)s - %(name)s - %(message)s`

#### log_substep (function)
```python
def log_substep(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a substep with indentation.

    Args:
        message: Message to log
        logger: Logger instance (creates default if None)
    """
```

#### log_progress_bar (function)
```python
def log_progress_bar(current: int, total: int, task: str, logger: Optional[logging.Logger] = None) -> None:
    """Log progress with a simple bar.

    Args:
        current: Current progress
        total: Total items
        task: Task description
        logger: Logger instance (creates default if None)
    """
```

#### log_stage (function)
```python
def log_stage(stage_num: int, total_stages: int, stage_name: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a pipeline stage header.

    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        logger: Logger instance (creates default if None)
    """
```

### exceptions.py

#### ValidationError (class)
```python
class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(
        self,
        message: str,
        context: dict = None,
        suggestions: list = None
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            context: Additional context information
            suggestions: Suggested actions to fix the error
        """
```

**Attributes:**
- `message` (str): Error message
- `context` (dict): Additional context information
- `suggestions` (list): Suggested actions to fix the error

### figure_manager.py

#### FigureMetadata (class)
```python
@dataclass
class FigureMetadata:
    """Metadata for a registered figure."""
    
    filename: str
    caption: str
    label: Optional[str] = None
    section: Optional[str] = None
    generated_by: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

**Attributes:**
- `filename` (str): Figure filename
- `caption` (str): Figure caption
- `label` (Optional[str]): Figure label for cross-referencing
- `section` (Optional[str]): Section where figure appears
- `generated_by` (Optional[str]): Script that generated the figure
- `parameters` (Optional[Dict[str, Any]]): Additional parameters

#### FigureManager (class)
```python
class FigureManager:
    """Minimal figure manager for registering figures."""
    
    def __init__(self, registry_file: Optional[str] = None) -> None:
        """Initialize figure manager.

        Args:
            registry_file: Path to figure registry file
        """
    
    def register_figure(
        self,
        filename: str,
        caption: str,
        label: Optional[str] = None,
        section: Optional[str] = None,
        generated_by: Optional[str] = None,
        **kwargs
    ) -> FigureMetadata:
        """Register a figure.

        Args:
            filename: Figure filename
            caption: Figure caption
            label: Figure label (auto-generated if None)
            section: Section where figure appears
            generated_by: Script that generated the figure
            **kwargs: Additional parameters

        Returns:
            FigureMetadata object
        """
    
    def get_figure(self, label: str) -> Optional[FigureMetadata]:
        """Get figure metadata by label.

        Args:
            label: Figure label

        Returns:
            FigureMetadata if found, None otherwise
        """
```

**Registry File:**
- Default location: `output/figures/figure_registry.json`
- Automatically created if it doesn't exist
- Stores figure metadata as JSON

### validation.py

#### validate_markdown (function)
```python
def validate_markdown(markdown_path: str, strict: bool = False) -> Dict[str, Any]:
    """Validate markdown files using infrastructure validation.

    Args:
        markdown_path: Path to markdown files
        strict: Whether to use strict validation

    Returns:
        Validation results dictionary with status, issues, and summary
    """
```

#### validate_figure_registry (function)
```python
def validate_figure_registry() -> Dict[str, Any]:
    """Validate figure registry using infrastructure validation.

    Returns:
        Validation results dictionary with status, errors, and warnings
    """
```

#### verify_output_integrity (function)
```python
def verify_output_integrity(output_path: Path) -> Dict[str, Any]:
    """Verify output integrity using infrastructure validation.

    Args:
        output_path: Path to output directory

    Returns:
        Integrity report dictionary
    """
```

#### validate_pdf_rendering (function)
```python
def validate_pdf_rendering(pdf_path: str) -> Dict[str, Any]:
    """Validate PDF rendering using infrastructure validation.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Validation results dictionary
    """
```

#### IntegrityReport (class)
```python
class IntegrityReport:
    """Integrity report dataclass."""
    # Attributes defined in infrastructure.validation.integrity
```

### reporting.py

#### get_error_aggregator (function)
```python
def get_error_aggregator() -> ErrorAggregator:
    """Get error aggregator instance from infrastructure.

    Returns:
        ErrorAggregator instance for collecting and reporting errors
    """
```

#### generate_pipeline_report (function)
```python
def generate_pipeline_report(*args, **kwargs) -> Dict[str, Any]:
    """Generate pipeline report using infrastructure.

    Args:
        *args: Positional arguments passed to infrastructure function
        **kwargs: Keyword arguments passed to infrastructure function

    Returns:
        Pipeline report dictionary
    """
```

#### save_pipeline_report (function)
```python
def save_pipeline_report(*args, **kwargs) -> List[Path]:
    """Save pipeline report using infrastructure.

    Args:
        *args: Positional arguments passed to infrastructure function
        **kwargs: Keyword arguments passed to infrastructure function

    Returns:
        List of saved report file paths
    """
```

#### ReportGenerator (class)
```python
class ReportGenerator:
    """Generate reports from simulation and analysis results."""
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize report generator.

        Args:
            output_dir: Directory for saving reports
        """
    
    def generate_markdown_report(
        self,
        title: str,
        results: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """Generate markdown report.

        Args:
            title: Report title
            results: Results dictionary
            filename: Output filename (without extension)

        Returns:
            Path to generated report
        """
```

### markdown_integration.py

#### MarkdownIntegration (class)
```python
class MarkdownIntegration:
    """Minimal markdown integration stub."""
    
    def __init__(self, manuscript_dir: Path) -> None:
        """Initialize with manuscript directory.
        
        Args:
            manuscript_dir: Path to manuscript directory
        """
    
    def detect_sections(self, markdown_file: Path) -> List[str]:
        """Detect sections in markdown file (stub).
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            List of section names (currently returns empty list)
        """
    
    def insert_figure_in_section(
        self,
        markdown_file: Path,
        figure_label: str,
        section_name: str,
        position: str = "after"
    ) -> bool:
        """Insert figure in specific section.
        
        Args:
            markdown_file: Path to markdown file
            figure_label: Figure label
            section_name: Section name
            position: Position relative to section (before, after)
            
        Returns:
            True if successful (currently returns False - stub implementation)
        """
```

#### ImageManager (class)
```python
class ImageManager:
    """Minimal image manager stub."""
    
    def __init__(self) -> None:
        """Initialize image manager."""
    
    def register_image(
        self,
        filename: str,
        caption: str,
        alt_text: Optional[str] = None
    ) -> None:
        """Register an image (stub).
        
        Args:
            filename: Image filename
            caption: Image caption
            alt_text: Alternative text for image
        """
    
    def get_image_info(self, filename: str) -> Optional[Dict]:
        """Get image information (stub).
        
        Args:
            filename: Image filename
            
        Returns:
            Image information dictionary if found, None otherwise
        """
```

## Usage Examples

### Logging with Progress Tracking

```python
from projects.ento_linguistics.src.utils.logging import (
    get_logger, log_substep, log_progress_bar, log_stage
)

logger = get_logger(__name__)
log_stage(1, 5, "Data Collection", logger)
log_substep("Loading corpus files", logger)
log_progress_bar(50, 100, "Processing documents", logger)
```

### Exception Handling

```python
from projects.ento_linguistics.src.utils.exceptions import ValidationError

try:
    # Validation logic
    if not data:
        raise ValidationError(
            message="Data validation failed",
            context={"data_type": type(data).__name__},
            suggestions=["Check data source", "Verify input format"]
        )
except ValidationError as e:
    logger.error(f"Validation error: {e.message}")
    if e.suggestions:
        logger.info(f"Suggestions: {', '.join(e.suggestions)}")
```

### Figure Management

```python
from projects.ento_linguistics.src.utils.figure_manager import FigureManager

# Initialize figure manager
fig_manager = FigureManager()

# Register a figure
metadata = fig_manager.register_figure(
    filename="domain_analysis.png",
    caption="Domain analysis showing terminology networks",
    section="Results",
    generated_by="analysis_script.py"
)

# Retrieve figure metadata
fig_info = fig_manager.get_figure(metadata.label)
```

### Validation

```python
from projects.ento_linguistics.src.utils.validation import (
    validate_markdown, validate_figure_registry, verify_output_integrity
)

# Validate markdown files
result = validate_markdown("projects/ento_linguistics/manuscript/", strict=False)
print(f"Status: {result['status']}")
print(f"Issues found: {result['summary']['total_issues']}")

# Validate figure registry
registry_result = validate_figure_registry()
if registry_result['status'] == 'validated':
    print("Figure registry is valid")

# Verify output integrity
from pathlib import Path
integrity = verify_output_integrity(Path("projects/ento_linguistics/output/"))
```

### Reporting

```python
from projects.ento_linguistics.src.utils.reporting import (
    get_error_aggregator, ReportGenerator
)

# Error aggregation
aggregator = get_error_aggregator()
aggregator.add_error("test_failure", "Test failed", stage="tests")
aggregator.save_report(Path("output/reports"))

# Report generation
report_gen = ReportGenerator(output_dir="output/reports")
report_path = report_gen.generate_markdown_report(
    title="Analysis Results",
    results={"summary": {"total": 100}, "findings": ["Finding 1", "Finding 2"]}
)
```

## Integration with Infrastructure

These utilities are designed to work alongside the generic infrastructure modules:

- **Logging**: For advanced logging features, see `infrastructure.core.logging_utils`
- **Figure Management**: For figure management, see `infrastructure.documentation.figure_manager`
- **Validation**: Wrappers around `infrastructure.validation` modules
- **Reporting**: Wrappers around `infrastructure.reporting` modules
- **Markdown Integration**: For full markdown processing, see `infrastructure.documentation.markdown_integration`

## Module Exports

The `__init__.py` exports the following:

```python
from .logging import get_logger, log_substep, log_progress_bar, log_stage
from .exceptions import ValidationError
from .figure_manager import FigureManager, FigureMetadata
from .validation import (
    validate_markdown, validate_figure_registry, verify_output_integrity,
    IntegrityReport, validate_pdf_rendering
)
from .reporting import (
    generate_pipeline_report, save_pipeline_report,
    get_error_aggregator, ReportGenerator
)
from .markdown_integration import MarkdownIntegration, ImageManager
```

## See Also

- [README.md](README.md) - Quick reference guide
- [../AGENTS.md](../AGENTS.md) - Project source documentation
- [../../../../infrastructure/core/AGENTS.md](../../../../infrastructure/core/AGENTS.md) - Core infrastructure utilities
- [../../../../infrastructure/documentation/AGENTS.md](../../../../infrastructure/documentation/AGENTS.md) - Documentation utilities
- [../../../../infrastructure/validation/AGENTS.md](../../../../infrastructure/validation/AGENTS.md) - Validation tools
- [../../../../infrastructure/reporting/AGENTS.md](../../../../infrastructure/reporting/AGENTS.md) - Reporting tools
