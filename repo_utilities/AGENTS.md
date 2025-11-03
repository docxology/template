# repo_utilities/ - Build Orchestration and Utilities

## Purpose

The `repo_utilities/` directory contains build orchestration tools and generic utilities that work with any project following this template structure. These are **not core business logic** - they are infrastructure tools for building, validating, and managing the project.

## Why Separate from src/?

`repo_utilities/` is kept separate because:
- **Not core business logic** - These are build and development tools
- **Orchestration focus** - Scripts coordinate between components
- **Generic utilities** - Work with any project using this template
- **Build infrastructure** - Part of development workflow, not application code

`src/` contains:
- Core business logic
- Mathematical implementations
- Domain-specific functionality
- 100% test coverage requirement

## Script Categories

### Build Tools

| Script | Purpose | Type | Lines |
|--------|---------|------|-------|
| `render_pdf.sh` | Complete PDF generation pipeline | Bash | 1019 |
| `clean_output.sh` | Clean all generated outputs | Bash | 40 |
| `generate_pdf_from_scratch.sh` | Fresh build from clean state | Bash | ~100 |

**render_pdf.sh** - Master orchestrator:
1. Cleans previous outputs
2. Runs tests with 100% coverage requirement
3. Executes all project scripts
4. Validates markdown integrity
5. Generates glossary from `src/`
6. Builds individual and combined PDFs
7. Creates HTML and IDE-friendly versions

**clean_output.sh** - Safe cleanup:
- Removes `output/` directory (all disposable)
- Removes `latex/` directory if present
- Preserves all source files

### Validation Tools

| Script | Purpose | Type | Tested |
|--------|---------|------|--------|
| `validate_markdown.py` | Validate markdown integrity | Python | ✅ 100% |
| `validate_pdf_output.py` | Validate PDF rendering quality | Python | ✅ 100% |

**validate_markdown.py**:
- Validates image references exist
- Checks cross-reference integrity
- Validates equation labels
- Detects bare URLs
- Ensures proper LaTeX math syntax

**validate_pdf_output.py**:
- Detects unresolved references (??)
- Finds missing citations ([?])
- Scans for LaTeX warnings
- Extracts first N words for preview
- Thin orchestrator using `src/pdf_validator.py`

### Generation Tools

| Script | Purpose | Type | Tested |
|--------|---------|------|--------|
| `generate_glossary.py` | Auto-generate API docs from src/ | Python | ✅ 100% |

**generate_glossary.py**:
- Scans `src/` for public APIs
- Extracts function and class definitions
- Generates markdown table
- Injects into `markdown/10_symbols_glossary.md`
- Thin orchestrator using `src/glossary_gen.py`

### Utility Scripts

| Script | Purpose | Type |
|--------|---------|------|
| `open_manuscript.sh` | Open manuscript in appropriate viewer | Bash |
| `rename_project.sh` | Rename project and update references | Bash |

**open_manuscript.sh**:
- Opens PDF, HTML, or IDE-friendly version
- Detects available applications
- Platform-agnostic (macOS, Linux)

**rename_project.sh**:
- Renames project systematically
- Updates all references
- Creates configuration files
- Sets default metadata

### Styling and Filters

| File | Purpose | Type |
|------|---------|------|
| `ide_style.css` | CSS for HTML manuscript | CSS |
| `convert_latex_images.lua` | Pandoc filter for LaTeX images | Lua |

**ide_style.css**:
- Professional typography for HTML
- Responsive design
- Syntax highlighting
- Clean table formatting

**convert_latex_images.lua**:
- Pandoc Lua filter
- Converts LaTeX `\includegraphics` to HTML `<img>` tags
- Handles width conversion
- Ensures proper image paths

## Testing

### Python Scripts (100% Coverage)

All Python scripts in `repo_utilities/` are tested in `tests/test_repo_utilities.py`:

```python
# tests/test_repo_utilities.py
from generate_glossary import _repo_root, _ensure_glossary_file
from validate_markdown import find_markdown_files, validate_images
```

**Test coverage:**
- `generate_glossary.py` - 100+ tests
- `validate_markdown.py` - Comprehensive validation tests
- `validate_pdf_output.py` - Full coverage

**Run tests:**
```bash
pytest tests/test_repo_utilities.py -v
```

### Bash Scripts (Not Tested)

Bash scripts are orchestrators and not directly tested:
- `render_pdf.sh` - Tested through integration tests
- `clean_output.sh` - Simple, safe cleanup
- `open_manuscript.sh` - Platform-specific, manual validation

These are validated by:
1. Integration tests (`tests/test_integration_pipeline.py`)
2. Regular execution in CI/CD
3. Manual testing across platforms

## Script Descriptions

### render_pdf.sh - Complete Build Pipeline

The master orchestrator that runs the entire build process:

**Phase 0: Cleanup**
```bash
./repo_utilities/clean_output.sh
```

**Phase 1: Test Validation**
```bash
pytest tests/ --cov=src --cov-fail-under=70
```
- Requires 70% coverage (adjustable)
- All tests must pass before proceeding

**Phase 2: Script Execution**
```bash
# Runs all .py files in scripts/
python3 scripts/example_figure.py
python3 scripts/generate_research_figures.py
```

**Phase 2.5: Repository Utilities**
```bash
python3 repo_utilities/generate_glossary.py
python3 repo_utilities/validate_markdown.py
```

**Phase 3: Preamble Generation**
```bash
# Extract LaTeX from preamble.md
sed -n '/^```latex$/,/^```$/p' manuscript/preamble.md
```

**Phase 4: Individual PDF Generation**
```bash
# For each manuscript/*.md file
pandoc 01_abstract.md -o output/pdf/01_abstract.pdf
```

**Phase 5: Combined PDF Generation**
```bash
# Combine all sections
pandoc project_combined.md -o output/pdf/project_combined.pdf
```

**Phase 5.5: Additional Versions**
```bash
# IDE-friendly PDF
pandoc project_combined.md -o output/pdf/project_combined_ide_friendly.pdf

# HTML version with embedded resources
pandoc project_combined.md --embed-resources -o output/project_combined.html
```

### Configuration

Environment variables control metadata:

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_ORCID="0000-0000-0000-1234"
export AUTHOR_EMAIL="jane.smith@university.edu"
export PROJECT_TITLE="Advanced Research Framework"
export DOI="10.5281/zenodo.12345678"  # Optional
export LOG_LEVEL=1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

./repo_utilities/render_pdf.sh
```

### clean_output.sh - Safe Cleanup

Removes all generated content safely:

```bash
#!/bin/bash
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/output"
LATEX_DIR="$REPO_ROOT/latex"

# Remove output directory
rm -rf "$OUTPUT_DIR"

# Remove latex directory
rm -rf "$LATEX_DIR"
```

**Safe by design:**
- Only removes `output/` and `latex/`
- Never touches source files
- All removed content is regenerable

### validate_markdown.py - Markdown Validation

Comprehensive markdown validation:

```python
from validate_markdown import (
    find_markdown_files,
    collect_symbols,
    validate_images,
    validate_refs,
    validate_math
)

# Find markdown files
md_files = find_markdown_files("manuscript/")

# Validate everything
problems = []
problems += validate_images(md_files, repo_root)
problems += validate_refs(md_files, labels, anchors, repo_root)
problems += validate_math(md_files, repo_root)
```

**Validation checks:**
- Image files exist
- Cross-references resolve
- Equation labels are unique
- No bare URLs
- Proper equation environments

**Usage:**
```bash
# Standard validation
python3 repo_utilities/validate_markdown.py

# Strict mode (fail on any issues)
python3 repo_utilities/validate_markdown.py --strict
```

### validate_pdf_output.py - PDF Quality Validation

Validates rendered PDF quality (thin orchestrator):

```python
from pdf_validator import validate_pdf_rendering

# Validate PDF
report = validate_pdf_rendering(pdf_path, n_words=200)

# Check results
if report['summary']['has_issues']:
    print(f"Found {report['issues']['total_issues']} issues")
```

**Detects:**
- Unresolved references (??)
- Missing citations ([?])
- LaTeX warnings
- Rendering errors

**Usage:**
```bash
# Validate default PDF
python3 repo_utilities/validate_pdf_output.py

# Validate specific PDF
python3 repo_utilities/validate_pdf_output.py output/pdf/01_abstract.pdf

# Verbose output
python3 repo_utilities/validate_pdf_output.py --verbose
```

### generate_glossary.py - API Documentation

Auto-generates API reference from `src/` (thin orchestrator):

```python
from glossary_gen import build_api_index, generate_markdown_table

# Build API index
entries = build_api_index("src/")

# Generate table
table = generate_markdown_table(entries)

# Inject into markdown
inject_between_markers(text, "<!-- BEGIN -->", "<!-- END -->", table)
```

**Process:**
1. Scans all Python files in `src/`
2. Extracts public functions and classes
3. Gets first sentence of docstrings
4. Generates markdown table
5. Writes directly to `manuscript/98_symbols_glossary.md`

**Usage:**
```bash
python3 repo_utilities/generate_glossary.py
```

### open_manuscript.sh - Manuscript Viewer

Opens manuscript in appropriate application:

```bash
# Open standard PDF
./repo_utilities/open_manuscript.sh pdf

# Open HTML version (best for IDEs)
./repo_utilities/open_manuscript.sh html

# Open IDE-friendly version
./repo_utilities/open_manuscript.sh ide

# List available versions
./repo_utilities/open_manuscript.sh list
```

**Platform detection:**
- Detects available PDF viewers (evince, okular)
- Detects browsers for HTML
- Falls back gracefully

### rename_project.sh - Project Renaming

Systematically renames project:

```bash
# Edit configuration section
PROJECT_NAME="my-awesome-project"
AUTHOR_NAME="Dr. Jane Smith"
PROJECT_TITLE="My Research"

# Run script
./repo_utilities/rename_project.sh
```

**Updates:**
- `pyproject.toml` metadata
- All markdown files
- README.md
- Environment variable defaults
- Creates `.project_config` file

## IDE-Friendly Features

### HTML Version
- Generated with `--embed-resources` (Pandoc 3.1.9+)
- Custom CSS for better rendering
- Works in all IDEs and browsers
- Absolute image paths for IDE compatibility

### PDF Versions
- Standard: Professional printing
- IDE-friendly: Simplified fonts
- Web-optimized: Screen viewing

### Image Handling
- Lua filter converts LaTeX to HTML
- Absolute paths in HTML output
- Embedded resources for portability

## Development Workflow

### Daily Development
```bash
# Make changes to src/ or manuscript/
vim src/example.py
vim manuscript/02_introduction.md

# Clean and rebuild
./repo_utilities/clean_output.sh
./repo_utilities/render_pdf.sh

# View result
./repo_utilities/open_manuscript.sh html
```

### Adding Features
```bash
# 1. Implement in src/
vim src/new_module.py

# 2. Add tests
vim tests/test_new_module.py

# 3. Create script if needed
vim scripts/new_figure.py

# 4. Update manuscript
vim manuscript/04_experimental_results.md

# 5. Build and validate
./repo_utilities/render_pdf.sh
```

## Best Practices

### Using Utilities
- Run `clean_output.sh` before important builds
- Use `validate_markdown.py` before committing
- Check `validate_pdf_output.py` after building
- Open HTML version for quick previews

### Extending Utilities
- Add new validation checks to existing scripts
- Create new utilities as separate scripts
- Test Python utilities comprehensively
- Document new utilities in this file

### Configuration
- Set environment variables for project metadata
- Use `.project_config` for permanent settings
- Override in CI/CD as needed

## Troubleshooting

### render_pdf.sh Fails

**Check Phase:**
```bash
# Which phase failed?
cat output/pdf/*_compile.log
```

**Common issues:**
- Tests failing → Fix tests first
- Scripts failing → Check script imports
- PDF generation → Check LaTeX syntax

### Validation Failures

**Markdown issues:**
```bash
python3 repo_utilities/validate_markdown.py --strict
# Fix reported issues
```

**PDF issues:**
```bash
python3 repo_utilities/validate_pdf_output.py --verbose
# Check for ?? or [?] in output
```

### Missing Dependencies

**System dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-xetex

# macOS
brew install pandoc
brew install --cask mactex
```

**Python dependencies:**
```bash
uv sync
# or
pip install -r requirements.txt
```

## See Also

- [`README.md`](README.md) - Utilities overview
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
- [`../docs/HOW_TO_USE.md`](../docs/HOW_TO_USE.md) - Usage guide
- [`../tests/test_repo_utilities.py`](../tests/test_repo_utilities.py) - Utility tests

