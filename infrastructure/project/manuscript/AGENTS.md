# Manuscript Utilities Module

## Overview

The `infrastructure/project/manuscript/` directory contains utilities for manuscript generation and technical documentation. This module provides automated generation of API documentation and technical appendices for research manuscripts.

## Directory Structure

```text
infrastructure/project/manuscript/
├── AGENTS.md                     # This technical documentation
└── 98_symbols_glossary.md       # Auto-generated API symbols glossary
```

## Key Components

### API Symbols Glossary (`98_symbols_glossary.md`)

**Auto-generated technical appendix for research manuscripts:**

**Purpose:**

- Document public APIs from `project/src/` modules
- Provide technical reference for research implementations
- Generate function and class documentation
- Integrate seamlessly into manuscript as Section 98

**Content Structure:**

```markdown
# API Symbols Glossary

This glossary is auto-generated from the public API in `src/`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Symbol | Type | Module | Description |
|--------|------|--------|-------------|
| `analyze_data` | function | `project.src.analysis` | Analyze research data with statistical methods |
| `DataProcessor` | class | `project.src.processing` | Main data processing class with validation |
| `validate_input` | method | `DataProcessor` | Validate input data format and constraints |
<!-- END: AUTO-API-GLOSSARY -->
```

**Generation Process:**

1. **AST Analysis**: Parse Python source files in `project/src/`
2. **Symbol Extraction**: Identify functions, classes, and methods
3. **Documentation Mining**: Extract docstrings and type hints
4. **Markdown Formatting**: Generate manuscript-compatible tables
5. **Integration**: Insert into manuscript Section 98

## Integration with Build Pipeline

### Automatic Execution

**Rendering Phase Integration (`scripts/03_render_pdf.py`):**

```python
# Automatic glossary generation during PDF rendering
from infrastructure.documentation.glossary_gen import generate_api_glossary

def render_manuscript_with_glossary():
    """Render manuscript with integrated API glossary."""

    # Generate glossary from project source
    glossary_content = generate_api_glossary('project/src/')

    # Update manuscript appendix
    update_manuscript_section(
        'project/manuscript/98_symbols_glossary.md',
        glossary_content
    )

    # Render manuscript
    render_pdf('project/manuscript/', 'output/pdf/project_combined.pdf')
```

**Validation Phase Integration (`scripts/04_validate_output.py`):**

```python
# Validate generated glossary
from infrastructure.validation.markdown_validator import validate_glossary

def validate_manuscript_glossary():
    """Validate API glossary in manuscript."""

    # Check glossary exists and is properly formatted
    validation_result = validate_glossary('project/manuscript/98_symbols_glossary.md')

    # Verify cross-references are valid
    cross_ref_result = validate_cross_references(validation_result)

    return validation_result and cross_ref_result
```

### Manual Usage

**Command-Line Generation:**

```bash
# Generate glossary manually
python3 -m infrastructure.documentation.cli generate-api project/src/

# Validate manuscript including glossary
python3 -m infrastructure.validation.cli markdown project/manuscript/
```

**Programmatic Usage:**

```python
from infrastructure.documentation.glossary_gen import generate_api_glossary

# Generate API documentation
glossary_markdown = generate_api_glossary('project/src/')

# Save to manuscript
with open('project/manuscript/98_symbols_glossary.md', 'w') as f:
    f.write(glossary_markdown)
```

## Technical Implementation

### AST-Based Analysis

**Symbol Extraction Process:**

```python
import ast
from typing import List, Dict, Any

def extract_api_symbols(source_path: str) -> List[Dict[str, Any]]:
    """Extract API symbols from Python source files."""

    symbols = []

    # Walk through Python files
    for py_file in Path(source_path).rglob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Extract symbols
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                symbol_info = extract_symbol_info(node, py_file)
                symbols.append(symbol_info)

    return symbols

def extract_symbol_info(node: ast.AST, file_path: Path) -> Dict[str, Any]:
    """Extract detailed information about a symbol."""

    return {
        'name': node.name,
        'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
        'module': str(file_path.relative_to('project/src')),
        'line_number': node.lineno,
        'docstring': extract_docstring(node),
        'signature': extract_signature(node) if isinstance(node, ast.FunctionDef) else None,
        'methods': extract_methods(node) if isinstance(node, ast.ClassDef) else None
    }
```

### Documentation Generation

**Markdown Table Generation:**

```python
def generate_glossary_table(symbols: List[Dict[str, Any]]) -> str:
    """Generate markdown table from symbol information."""

    lines = [
        "| Symbol | Type | Module | Description |",
        "|--------|------|--------|-------------|"
    ]

    for symbol in symbols:
        # Format symbol name with code markup
        symbol_name = f'`{symbol["name"]}`'

        # Determine symbol type
        symbol_type = symbol['type']

        # Format module path
        module_path = symbol['module'].replace('/', '.').replace('.py', '')

        # Extract description from docstring
        description = extract_description(symbol.get('docstring', ''))

        # Add table row
        lines.append(f"| {symbol_name} | {symbol_type} | `{module_path}` | {description} |")

    return '\n'.join(lines)
```

### Integration Markers

**Manuscript Integration:**

```markdown
# API Symbols Glossary

This glossary is auto-generated from the public API in `src/`.

<!-- BEGIN: AUTO-API-GLOSSARY -->
| Symbol | Type | Module | Description |
|--------|------|--------|-------------|
| `analyze_data` | function | `project.src.analysis` | Analyze research data |
<!-- END: AUTO-API-GLOSSARY -->
```

**Update Process:**

```python
def update_manuscript_glossary(glossary_file: Path, new_content: str):
    """Update glossary section in manuscript."""

    with open(glossary_file, 'r') as f:
        content = f.read()

    # Replace content between markers
    start_marker = '<!-- BEGIN: AUTO-API-GLOSSARY -->'
    end_marker = '<!-- END: AUTO-API-GLOSSARY -->'

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        # Preserve content outside markers
        before = content[:start_idx + len(start_marker)]
        after = content[end_idx:]

        # Update with new glossary
        updated_content = before + '\n' + new_content + '\n' + after

        with open(glossary_file, 'w') as f:
            f.write(updated_content)
```

## Configuration

### Environment Variables

**Manuscript Configuration:**

```bash
# Author information
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_EMAIL="jane.smith@university.edu"
export AUTHOR_ORCID="0000-0000-0000-1234"

# Project details
export PROJECT_TITLE="Research Project Title"
export PROJECT_VERSION="1.0"
```

### Build Configuration

**Integration Settings:**

```yaml
# project/manuscript/config.yaml
manuscript:
  generate_glossary: true
  glossary_section: 98
  include_private_symbols: false
  sort_by: module

build:
  include_api_glossary: true
  glossary_format: markdown_table
```

## Testing

### Integration Testing

**Glossary Generation Tests:**

```python
def test_glossary_generation():
    """Test API glossary generation from source code."""

    # Create test source file
    test_src = create_test_module()

    # Generate glossary
    glossary = generate_api_glossary(str(test_src))

    # Verify structure
    assert '<!-- BEGIN: AUTO-API-GLOSSARY -->' in glossary
    assert '<!-- END: AUTO-API-GLOSSARY -->' in glossary
    assert '| Symbol | Type | Module |' in glossary

    # Verify content
    assert '`test_function`' in glossary
    assert 'function' in glossary
    assert '`test.module`' in glossary
```

**Manuscript Integration Tests:**

```python
def test_manuscript_integration():
    """Test glossary integration into manuscript."""

    # Create test manuscript
    manuscript_dir = create_test_manuscript()
    glossary_file = manuscript_dir / '98_symbols_glossary.md'

    # Generate and integrate glossary
    update_manuscript_glossary(glossary_file, test_glossary_content)

    # Verify integration
    with open(glossary_file) as f:
        content = f.read()

    assert '<!-- BEGIN: AUTO-API-GLOSSARY -->' in content
    assert test_glossary_content in content
    assert '<!-- END: AUTO-API-GLOSSARY -->' in content
```

### Validation Testing

**Cross-Reference Validation:**

```python
def test_glossary_cross_references():
    """Test cross-reference validation in generated glossary."""

    glossary_content = generate_test_glossary()

    # Validate markdown structure
    validation_result = validate_markdown_glossary(glossary_content)

    assert validation_result.is_valid
    assert len(validation_result.symbols) > 0

    # Check cross-references
    for symbol in validation_result.symbols:
        assert is_valid_symbol_reference(symbol)
```

## Usage Examples

### Basic Usage

**Automatic Generation:**

```bash
# Generate glossary during build
python3 scripts/03_render_pdf.py

# Output includes updated glossary in manuscript
# Check: project/manuscript/98_symbols_glossary.md
```

**Manual Generation:**

```python
from infrastructure.documentation.glossary_gen import generate_api_glossary

# Generate from specific source directory
glossary = generate_api_glossary('project/src/')

# Save to custom location
with open('docs/api_reference.md', 'w') as f:
    f.write(glossary)
```

### Advanced Usage

**Filtered Generation:**

```python
# Generate glossary with filters
glossary = generate_api_glossary(
    'project/src/',
    include_private=False,  # Exclude _private functions
    include_tests=False,   # Exclude test functions
    sort_by='type'         # Sort by symbol type
)
```

**Custom Formatting:**

```python
# Generate with custom formatting
glossary = generate_api_glossary(
    'project/src/',
    format='html',  # HTML table instead of markdown
    include_signatures=True,  # Include function signatures
    max_description_length=100  # Limit description length
)
```

## Dependencies

### Required Modules

**Core Dependencies:**

- `infrastructure.documentation.glossary_gen` - Core glossary generation
- `infrastructure.documentation.markdown_integration` - Manuscript integration
- `infrastructure.core.file_operations` - File handling utilities

### External Dependencies

**Built-in Modules:**

- `ast` - Python AST parsing
- `pathlib` - Path handling
- `typing` - Type annotations

**Optional Dependencies:**

- `markdown` - markdown processing
- `pygments` - Syntax highlighting for code examples

## Troubleshooting

### Common Issues

**Empty Glossary Generation:**

```bash
# Check source directory exists and has Python files
ls -la project/src/

# Verify files are valid Python
python3 -m py_compile project/src/*.py

# Check for syntax errors
python3 -c "import project.src.module_name"
```

**Integration Failures:**

```bash
# Verify manuscript file exists
ls -la project/manuscript/98_symbols_glossary.md

# Check file permissions
ls -l project/manuscript/98_symbols_glossary.md

# Validate markers exist
grep -n "AUTO-API-GLOSSARY" project/manuscript/98_symbols_glossary.md
```

**Markdown Validation Errors:**

```bash
# Check generated markdown syntax
python3 -m infrastructure.validation.cli markdown project/manuscript/

# Validate table structure
python3 -c "
import markdown
md = open('project/manuscript/98_symbols_glossary.md').read()
html = markdown.markdown(md)
print('Markdown syntax valid')
"
```

### Debug Commands

**Verbose Generation:**

```bash
# Enable debug logging
LOG_LEVEL=0 python3 -m infrastructure.documentation.cli generate-api project/src/

# Check intermediate results
python3 -c "
from infrastructure.documentation.glossary_gen import extract_api_symbols
symbols = extract_api_symbols('project/src/')
print(f'Found {len(symbols)} symbols')
for symbol in symbols[:3]:
    print(f'  {symbol[\"name\"]} ({symbol[\"type\"]})')
"
```

**Validation Debug:**

```bash
# Test manuscript integration
python3 -c "
from infrastructure.documentation.markdown_integration import update_manuscript_glossary
from pathlib import Path
update_manuscript_glossary(Path('project/manuscript/98_symbols_glossary.md'), 'test content')
print('Integration test passed')
"
```

## Performance Considerations

### Generation Optimization

**Efficient AST Processing:**

- Single-pass parsing of source files
- Lazy loading of large modules
- Caching of parsed AST trees
- Parallel processing for multiple files

**Memory Management:**

- Streaming processing for large codebases
- Garbage collection of intermediate results
- Limited caching to prevent memory leaks

### Integration Performance

**Build Pipeline Integration:**

- Incremental glossary updates (only when source changes)
- Parallel execution with other build steps
- Resource limiting to prevent build bottlenecks
- Failure isolation (glossary errors don't break build)

## Future Enhancements

### Planned Features

**Documentation:**

- Interactive HTML glossary generation
- API usage examples in glossary
- Cross-reference linking between symbols
- Version history tracking for symbols

**Advanced Analysis:**

- Dependency graph generation
- Code complexity metrics
- Test coverage integration
- Performance profiling data

**Integration Improvements:**

- IDE integration for symbol lookup
- Documentation server for live updates
- Multi-format output (JSON, XML, PDF)
- Custom glossary templates

## See Also

**Related Documentation:**

- [`../../documentation/AGENTS.md`](../../documentation/AGENTS.md) - Documentation module details
- [`../../../scripts/AGENTS.md`](../../../scripts/AGENTS.md) - Build pipeline documentation

**System Integration:**

- [`../../AGENTS.md`](../../AGENTS.md) - system overview
- [`../../../docs/core/ARCHITECTURE.md`](../../../docs/core/ARCHITECTURE.md) - System architecture
- [`../../../docs/operational/BUILD_SYSTEM.md`](../../../docs/operational/BUILD_SYSTEM.md) - Build system details
