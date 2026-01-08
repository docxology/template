# utils/ - Project Utility Modules

## Overview

The `utils/` directory contains project-specific utility modules for the Active Inference Meta-Pragmatic Framework. These utilities provide logging, exception handling, figure management, and markdown integration functionality tailored to this research project's needs.

## Purpose

These utilities serve as lightweight wrappers and project-specific implementations that complement the generic infrastructure modules. They provide:

- **Logging**: Standardized logging configuration for project scripts
- **Exception Handling**: Project-specific exception types with context
- **Figure Management**: Figure registration and metadata tracking
- **Markdown Integration**: Basic markdown processing utilities

## Directory Structure

```
utils/
├── __init__.py              # Module exports
├── exceptions.py            # Custom exception classes
├── figure_manager.py        # Figure registration and management
├── logging.py              # Logging utilities
└── markdown_integration.py  # Markdown processing utilities
```

## Function Signatures

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
```

**Registry File:**
- Default location: `output/figures/figure_registry.json`
- Automatically created if it doesn't exist
- Stores figure metadata as JSON

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

### markdown_integration.py

#### MarkdownIntegration (class)
```python
class MarkdownIntegration:
    """Minimal markdown integration stub."""
    
    def __init__(self, manuscript_dir: Path) -> None:
        """Initialize with manuscript directory."""
    
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
        section: str,
        width: float = 0.8
    ) -> bool:
        """Insert figure in section (stub).
        
        Args:
            markdown_file: Path to markdown file
            figure_label: Label of figure to insert
            section: Section name where to insert
            width: Figure width (default: 0.8)
            
        Returns:
            Success status (currently returns False)
        """
```

**Note:** This is a minimal stub implementation. For full markdown integration capabilities, consider using `infrastructure.documentation.markdown_integration`.

## Usage Examples

### Basic Logging

```python
from projects.active_inference_meta_pragmatic.src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Starting analysis")
logger.debug("Detailed debug information")
```

### Exception Handling

```python
from projects.active_inference_meta_pragmatic.src.utils.exceptions import ValidationError

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
from projects.active_inference_meta_pragmatic.src.utils.figure_manager import FigureManager

# Initialize figure manager
fig_manager = FigureManager()

# Register a figure
metadata = fig_manager.register_figure(
    filename="convergence_plot.png",
    caption="Convergence analysis showing optimization progress",
    section="Results",
    generated_by="analysis_script.py",
    algorithm="gradient_descent",
    iterations=1000
)

print(f"Registered figure: {metadata.label}")
print(f"Caption: {metadata.caption}")
```

### Markdown Integration

```python
from pathlib import Path
from projects.active_inference_meta_pragmatic.src.utils.markdown_integration import MarkdownIntegration

manuscript_dir = Path("projects/active_inference_meta_pragmatic/manuscript")
md_integration = MarkdownIntegration(manuscript_dir)

# Detect sections (stub - returns empty list)
sections = md_integration.detect_sections(manuscript_dir / "01_introduction.md")

# Insert figure (stub - returns False)
success = md_integration.insert_figure_in_section(
    markdown_file=manuscript_dir / "02_results.md",
    figure_label="fig:convergence_plot",
    section="Convergence Analysis"
)
```

## Integration with Infrastructure

These utilities are designed to work alongside the generic infrastructure modules:

- **Logging**: For advanced logging features, see `infrastructure.core.logging_utils`
- **Figure Management**: For figure management, see `infrastructure.documentation.figure_manager`
- **Markdown Integration**: For full markdown processing, see `infrastructure.documentation.markdown_integration`
- **Validation**: For validation utilities, see `infrastructure.validation`

## Module Exports

The `__init__.py` exports the following:

```python
from .logging import get_logger
from .exceptions import ValidationError
from .figure_manager import FigureManager, FigureMetadata
from .markdown_integration import MarkdownIntegration
```

## See Also

- [infrastructure/core/AGENTS.md](../../../../infrastructure/core/AGENTS.md) - Core infrastructure utilities
- [infrastructure/documentation/AGENTS.md](../../../../infrastructure/documentation/AGENTS.md) - Documentation utilities
- [infrastructure/validation/AGENTS.md](../../../../infrastructure/validation/AGENTS.md) - Validation tools
- [projects/active_inference_meta_pragmatic/src/AGENTS.md](../AGENTS.md) - Project source documentation
