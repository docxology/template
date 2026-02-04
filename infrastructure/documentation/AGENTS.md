# Documentation Module

## Purpose

The Documentation module provides tools for managing figures, images, and markdown integration in research manuscripts. It enables automatic figure numbering, cross-reference management, and API documentation generation.

## Architecture

### Core Components

**figure_manager.py**
- Automatic figure numbering and registry management
- LaTeX figure block generation
- Cross-reference generation
- Figure list and table of figures generation
- Persistent figure registry in JSON format

**image_manager.py**
- Image file insertion into markdown
- Figure reference creation
- Image validation in markdown files
- Figure list extraction
- Insertion point detection and management

**markdown_integration.py**
- Markdown section detection
- Figure insertion into specific sections
- Table of figures generation
- Reference updates across documents
- Manuscript validation
- Figure statistics collection

**glossary_gen.py**
- API index building from source code via AST
- Markdown table generation from API entries
- Marker-based content injection

## Function Signatures

### figure_manager.py

#### FigureMetadata (class)
```python
@dataclass
class FigureMetadata:
    """Metadata for a registered figure."""
    filename: str
    label: str
    caption: str
    section: str
    number: int
    registered_at: str
    file_path: Optional[Path] = None
    width: Optional[float] = None
    height: Optional[float] = None
```

#### FigureManager (class)
```python
class FigureManager:
    """Manages figure registration and cross-reference generation."""

    def __init__(self, registry_file: Optional[str] = None):
        """Initialize figure manager.

        Args:
            registry_file: Path to figure registry file
        """
```

#### register_figure (method)
```python
def register_figure(
    self,
    filename: str,
    caption: str,
    label: Optional[str] = None,
    section: str = "",
    file_path: Optional[Path] = None
) -> FigureMetadata:
    """Register a new figure in the registry.

    Args:
        filename: Name of the figure file
        caption: Figure caption
        label: Figure label (auto-generated if None)
        section: Section where figure appears
        file_path: Path to figure file

    Returns:
        FigureMetadata for the registered figure
    """
```

#### get_figure (method)
```python
def get_figure(self, label: str) -> Optional[FigureMetadata]:
    """Get figure metadata by label.

    Args:
        label: Figure label

    Returns:
        FigureMetadata if found, None otherwise
    """
```

#### generate_latex_figure_block (method)
```python
def generate_latex_figure_block(
    self,
    label: str,
    width: float = 0.8,
    placement: str = "h"
) -> str:
    """Generate LaTeX figure block for a registered figure.

    Args:
        label: Figure label
        width: Figure width (0-1)
        placement: LaTeX placement specifier

    Returns:
        LaTeX figure environment
    """
```

#### generate_table_of_figures (method)
```python
def generate_table_of_figures(self, format: str = "markdown") -> str:
    """Generate table of figures in specified format.

    Args:
        format: Output format ("markdown" or "latex")

    Returns:
        Formatted table of figures
    """
```

#### save_registry (method)
```python
def save_registry(self) -> bool:
    """Save figure registry to JSON file.

    Returns:
        True if save successful, False otherwise
    """
```

#### load_registry (method)
```python
def load_registry(self) -> bool:
    """Load figure registry from JSON file.

    Returns:
        True if load successful, False otherwise
    """
```

#### clear_registry (method)
```python
def clear_registry(self) -> None:
    """Clear all registered figures."""
```

#### get_statistics (method)
```python
def get_statistics(self) -> Dict[str, Any]:
    """Get statistics about registered figures.

    Returns:
        Dictionary with figure statistics
    """
```

### image_manager.py

#### ImageManager (class)
```python
class ImageManager:
    """Manages image insertion into markdown files."""

    def __init__(self, figure_manager: Optional[FigureManager] = None):
        """Initialize image manager.

        Args:
            figure_manager: FigureManager instance for cross-references
        """
```

#### insert_figure (method)
```python
def insert_figure(
    self,
    markdown_file: Path,
    figure_label: str,
    section: Optional[str] = None,
    width: float = 0.8
) -> bool:
    """Insert figure reference into markdown file.

    Args:
        markdown_file: Path to markdown file
        figure_label: Figure label to insert
        section: Section to insert in (if None, insert at end)
        width: Figure width (0-1)

    Returns:
        True if insertion successful, False otherwise
    """
```

#### extract_figure_list (method)
```python
def extract_figure_list(self, markdown_file: Path) -> List[str]:
    """Extract list of figure labels from markdown file.

    Args:
        markdown_file: Path to markdown file

    Returns:
        List of figure labels found in file
    """
```

#### validate_figure_references (method)
```python
def validate_figure_references(
    self,
    markdown_file: Path,
    available_labels: Optional[Set[str]] = None
) -> List[str]:
    """Validate figure references in markdown file.

    Args:
        markdown_file: Path to markdown file
        available_labels: Set of available figure labels

    Returns:
        List of validation error messages
    """
```

#### find_insertion_point (method)
```python
def find_insertion_point(
    self,
    markdown_file: Path,
    section: str
) -> Optional[int]:
    """Find line number to insert figure in specified section.

    Args:
        markdown_file: Path to markdown file
        section: Section name

    Returns:
        Line number for insertion, or None if section not found
    """
```

### markdown_integration.py

#### MarkdownIntegration (class)
```python
class MarkdownIntegration:
    """Integrates figures and references into markdown manuscripts."""

    def __init__(self, manuscript_dir: Path):
        """Initialize markdown integration.

        Args:
            manuscript_dir: Directory containing manuscript files
        """
```

#### detect_sections (method)
```python
def detect_sections(self, markdown_file: Path) -> List[str]:
    """Detect all sections in a markdown file.

    Args:
        markdown_file: Path to markdown file

    Returns:
        List of section names
    """
```

#### insert_figure_in_section (method)
```python
def insert_figure_in_section(
    self,
    markdown_file: Path,
    figure_label: str,
    section: str,
    width: float = 0.8
) -> bool:
    """Insert figure reference in specific section.

    Args:
        markdown_file: Path to markdown file
        figure_label: Figure label to insert
        section: Section name
        width: Figure width (0-1)

    Returns:
        True if insertion successful, False otherwise
    """
```

#### generate_table_of_figures (method)
```python
def generate_table_of_figures(
    self,
    output_file: Path,
    format: str = "markdown"
) -> bool:
    """Generate table of figures and save to file.

    Args:
        output_file: Path to output file
        format: Output format ("markdown" or "latex")

    Returns:
        True if generation successful, False otherwise
    """
```

#### update_cross_references (method)
```python
def update_cross_references(self, markdown_files: List[Path]) -> bool:
    """Update cross-references across multiple markdown files.

    Args:
        markdown_files: List of markdown files to update

    Returns:
        True if update successful, False otherwise
    """
```

#### validate_manuscript (method)
```python
def validate_manuscript(self) -> Dict[str, Any]:
    """Validate entire manuscript structure.

    Returns:
        Validation results dictionary
    """
```

#### collect_figure_statistics (method)
```python
def collect_figure_statistics(self) -> Dict[str, Any]:
    """Collect statistics about figures in manuscript.

    Returns:
        Figure statistics dictionary
    """
```

### glossary_gen.py

#### ApiEntry (class)
```python
@dataclass
class ApiEntry:
    """Represents an API entry for documentation."""
    name: str
    kind: str  # 'function', 'class', 'method', 'constant'
    module: str
    signature: str
    docstring: Optional[str] = None
    line_number: Optional[int] = None
    source_file: Optional[str] = None
```

#### _first_sentence (function)
```python
def _first_sentence(doc: str | None) -> str:
    """Extract first sentence from docstring.

    Args:
        doc: Docstring text

    Returns:
        First sentence of docstring
    """
```

#### _iter_py_files (function)
```python
def _iter_py_files(root: str) -> Iterable[str]:
    """Iterate over Python files in directory tree.

    Args:
        root: Root directory to search

    Yields:
        Paths to Python files
    """
```

#### build_api_index (function)
```python
def build_api_index(src_dir: str) -> List[ApiEntry]:
    """Build API index from Python source files.

    Args:
        src_dir: Source directory to scan

    Returns:
        List of ApiEntry objects
    """
```

#### generate_markdown_table (function)
```python
def generate_markdown_table(entries: List[ApiEntry]) -> str:
    """Generate markdown table from API entries.

    Args:
        entries: List of ApiEntry objects

    Returns:
        Markdown table string
    """
```

#### inject_between_markers (function)
```python
def inject_between_markers(
    text: str,
    begin_marker: str,
    end_marker: str,
    content: str
) -> str:
    """Inject content between markers in text.

    Args:
        text: Original text
        begin_marker: Beginning marker
        end_marker: Ending marker
        content: Content to inject

    Returns:
        Modified text with content injected
    """
```

## Key Features

### Figure Management
```python
from infrastructure.documentation import FigureManager

fm = FigureManager()
metadata = fm.register_figure(
    filename="result.png",
    caption="Results visualization",
    label="fig:results",
    section="Results"
)
latex_block = fm.generate_latex_figure_block("fig:results")
```

### Image Management
```python
from infrastructure.documentation import ImageManager

im = ImageManager()
success = im.insert_figure(
    Path("manuscript/03_results.md"),
    "fig:results",
    section="Results"
)
```

### Markdown Integration
```python
from infrastructure.documentation import MarkdownIntegration

mi = MarkdownIntegration(manuscript_dir=Path("manuscript"))
sections = mi.detect_sections(Path("manuscript/intro.md"))
mi.insert_figure_in_section(Path("manuscript/results.md"), "fig:results", "Results")
```

### API Documentation
```python
from infrastructure.documentation import build_api_index, generate_markdown_table

entries = build_api_index("src/")
markdown = generate_markdown_table(entries)
```

## Testing

Run documentation tests with:
```bash
pytest tests/infra_tests/test_documentation/
```

## Configuration

No specific configuration required. Figure registry stored in `output/figures/figure_registry.json`.

## Integration

Documentation module is used by:
- Manuscript generation pipeline
- Figure numbering workflows
- API reference generation
- Cross-reference systems

## Troubleshooting

### Figure Registration Fails

**Issue**: `register_figure()` fails or doesn't persist figure data.

**Solutions**:
- Verify output directory is writable
- Check figure registry JSON file permissions
- Ensure figure file exists before registration
- Review JSON serialization for special characters
- Check disk space availability

### Image Insertion Errors

**Issue**: `insert_figure()` fails to insert figure into markdown.

**Solutions**:
- Verify markdown file exists and is writable
- Check section name matches exactly (case-sensitive)
- Ensure figure is registered before insertion
- Review markdown file structure for insertion points
- Check file encoding (UTF-8 required)

### Cross-Reference Generation Issues

**Issue**: Generated cross-references are incorrect or missing.

**Solutions**:
- Verify figure labels follow naming conventions
- Check LaTeX label syntax is correct
- Ensure figures are registered before reference generation
- Review reference format requirements
- Check for duplicate labels

### API Documentation Generation Fails

**Issue**: `build_api_index()` returns empty or incomplete index.

**Solutions**:
- Verify source directory path is correct
- Check Python files are parseable (no syntax errors)
- Ensure functions have docstrings
- Review AST parsing for complex code
- Check file permissions for source files

### Markdown Integration Errors

**Issue**: `MarkdownIntegration` methods fail or produce incorrect results.

**Solutions**:
- Verify manuscript directory path is correct
- Check markdown file structure is valid
- Ensure sections are properly formatted
- Review section detection logic
- Check file encoding and line endings

## Best Practices

### Figure Management

- **Register Early**: Register figures immediately after generation
- **Consistent Labels**: Use consistent label naming conventions
- **Persistent Registry**: Keep figure registry in version control
- **Validate References**: Check all references before final rendering

### Image Handling

- **Relative Paths**: Use relative paths for portability
- **Validate Existence**: Check images exist before insertion
- **Consistent Formatting**: Use consistent image formatting
- **Optimize Images**: Optimize images for publication quality

### Cross-Reference Management

- **Unique Labels**: Ensure all labels are unique
- **Consistent Format**: Use consistent reference formats
- **Validate References**: Check references before rendering
- **Document Patterns**: Document reference patterns for team

### API Documentation

- **Docstrings**: Write docstrings
- **Type Hints**: Include type hints for better documentation
- **Examples**: Provide usage examples in docstrings
- **Keep Current**: Update documentation with code changes

### Markdown Integration

- **Structured Sections**: Use consistent section structure
- **Clear Markers**: Use clear markers for insertion points
- **Validate Structure**: Validate markdown structure before processing
- **Test Integration**: Test integration with actual manuscript files

### Documentation Workflow

- **Automate**: Integrate documentation generation into build pipeline
- **Version Control**: Track documentation changes
- **Review Regularly**: Review documentation for accuracy
- **Update Promptly**: Update documentation when code changes

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

