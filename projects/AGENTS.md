# projects/ - Multi-Project Research Template

## Overview

The `projects/` directory contains multiple independent research projects within a single repository. Each project follows the template's two-layer architecture with complete isolation and reproducible builds. This structure enables:

- **Multi-project management** within one repository
- **Project isolation** with independent source code, tests, and outputs
- **Template reuse** across different research domains
- **Comparative analysis** of different approaches

## Key Concepts

- **Project Independence**: Each project has its own src/, tests/, scripts/, manuscript/, and output/
- **Template Consistency**: All projects follow identical structure and build processes
- **Resource Sharing**: Common infrastructure/ modules shared across projects
- **Scalable Organization**: Easy addition of new projects without conflicts

## Directory Structure

```
projects/
├── project/                    # Default template project (complete example)
│   ├── src/                    # Scientific algorithms and data processing
│   ├── tests/                  # Unit and integration tests
│   ├── scripts/                # Analysis workflows (thin orchestrators)
│   ├── manuscript/             # Research content and metadata
│   ├── output/                 # Generated outputs (PDFs, figures, data)
│   ├── docs/                   # Project-specific documentation
│   ├── pyproject.toml          # Project configuration
│   └── README.md               # Project overview
├── small_code_project/         # Minimal computational project
│   ├── src/                    # Basic optimization algorithms
│   ├── tests/                  # Algorithm validation tests
│   ├── scripts/                # Analysis pipeline
│   ├── manuscript/             # Research manuscript
│   └── output/                 # Generated outputs
├── small_prose_project/        # Minimal prose-focused project
│   ├── src/                    # Minimal computational requirements
│   ├── tests/                  # Basic validation tests
│   ├── manuscript/             # Academic writing example
│   └── output/                 # Generated outputs
└── [future_project]/           # Template for new projects
    └── ...
```

## Project Types

### Full Template Project (`project/`)

**Complete example project** with all features:
- Advanced algorithms and data processing
- Comprehensive test suite (90%+ coverage)
- Complex analysis pipelines
- Full manuscript with equations and figures
- Extensive documentation and examples

**Use cases:**
- New research projects requiring full functionality
- Template for complex computational research
- Examples and best practices demonstration

### Small Code Project (`small_code_project/`)

**Computation-focused minimal project**:
- Basic optimization algorithms
- Essential data analysis capabilities
- Streamlined test coverage
- Focused manuscript on computational methods

**Use cases:**
- Algorithm development and testing
- Minimal viable research prototypes
- Educational examples of core concepts

### Small Prose Project (`small_prose_project/`)

**Prose-focused minimal project**:
- Minimal computational requirements
- Emphasis on academic writing and structure
- Mathematical notation examples
- Documentation of research methodology

**Use cases:**
- Literature reviews and theoretical work
- Educational content creation
- Research planning and design documents

## Project Management

### Project Discovery

The template automatically discovers projects by scanning the `projects/` directory:

```python
# Automatic discovery in scripts/
def discover_projects(repo_root: Path) -> List[str]:
    """Discover all valid projects in projects/ directory."""
    projects_dir = repo_root / "projects"
    valid_projects = []

    for item in projects_dir.iterdir():
        if item.is_dir() and is_valid_project(item):
            valid_projects.append(item.name)

    return valid_projects

def is_valid_project(project_dir: Path) -> bool:
    """Check if directory contains valid project structure."""
    required = ["src", "tests", "manuscript"]
    return all((project_dir / subdir).exists() for subdir in required)
```

### Project Selection

**Command-line project specification:**
```bash
# Run specific project
python3 scripts/run_all.py --project small_code_project

# Run all projects sequentially
python3 scripts/run_all.py --all-projects

# Interactive selection (future enhancement)
./run.sh --select-project
```

### Project Isolation

Each project maintains complete isolation:

- **Independent outputs**: `projects/{name}/output/` for working files, `output/{name}/` for deliverables
- **Separate configurations**: Individual `pyproject.toml` and `manuscript/config.yaml`
- **Isolated testing**: Project-specific test execution and coverage
- **Resource management**: Per-project environment and dependencies

## API Reference

### Project Discovery (`infrastructure/project/`)

#### discover_projects (function)
```python
def discover_projects(repo_root: Path) -> List[str]:
    """Discover all valid projects in the projects/ directory.

    Args:
        repo_root: Repository root directory

    Returns:
        List of project names (directory names)
    """
```

#### validate_project_structure (function)
```python
def validate_project_structure(project_dir: Path) -> Dict[str, bool]:
    """Validate that a project directory has required structure.

    Args:
        project_dir: Project directory to validate

    Returns:
        Dictionary mapping required directories to existence status
    """
```

#### get_project_config (function)
```python
def get_project_config(project_name: str, repo_root: Path) -> Dict[str, Any]:
    """Get configuration for a specific project.

    Args:
        project_name: Name of the project
        repo_root: Repository root directory

    Returns:
        Project configuration dictionary
    """
```

#### setup_project_environment (function)
```python
def setup_project_environment(project_name: str, repo_root: Path) -> Dict[str, Any]:
    """Setup environment variables and paths for project execution.

    Args:
        project_name: Name of the project
        repo_root: Repository root directory

    Returns:
        Environment setup information
    """
```

## Usage Examples

### Adding a New Project

1. **Copy template structure:**
```bash
# Copy from existing project
cp -r projects/project projects/my_research

# Or create minimal structure
mkdir -p projects/my_research/{src,tests,scripts,manuscript,output}
```

2. **Customize project files:**
```bash
# Update configuration
vim projects/my_research/pyproject.toml
vim projects/my_research/manuscript/config.yaml

# Add research code
vim projects/my_research/src/my_algorithm.py

# Write tests
vim projects/my_research/tests/test_my_algorithm.py

# Create analysis scripts
vim projects/my_research/scripts/analysis.py

# Write manuscript
vim projects/my_research/manuscript/01_introduction.md
```

3. **Run project:**
```bash
# Test the new project
python3 scripts/run_all.py --project my_research

# Generate outputs
python3 scripts/03_render_pdf.py --project my_research
```

### Comparative Analysis

Run multiple projects for comparison:

```bash
# Run all projects
python3 scripts/run_all.py --all-projects

# Compare outputs
ls -la output/*/pdf/*.pdf  # Compare generated PDFs
ls -la output/*/figures/   # Compare figure quality
cat output/*/reports/validation_summary.json  # Compare validation results
```

## Configuration

### Project-Specific Configuration

Each project has independent configuration:

**`projects/{name}/pyproject.toml`:**
```toml
[project]
name = "my_research"
version = "0.1.0"
description = "My research project"
dependencies = [
    "numpy",
    "scipy",
    "matplotlib"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

**`projects/{name}/manuscript/config.yaml`:**
```yaml
paper:
  title: "My Research Title"
  subtitle: "Subtitle if needed"

authors:
  - name: "Dr. Researcher Name"
    email: "researcher@university.edu"
    affiliation: "University Name"

publication:
  license: "MIT"
```

## Testing

### Project-Specific Testing

Each project maintains independent test coverage:

```bash
# Test specific project
pytest projects/my_research/tests/ --cov=projects/my_research/src

# Test all projects
for project in $(ls projects/); do
    if [ -d "projects/$project/tests" ]; then
        pytest projects/$project/tests/ -v
    fi
done
```

### Integration Testing

Cross-project integration tests ensure compatibility:

```bash
# Run infrastructure tests (shared across projects)
pytest tests/infrastructure/ -v

# Run project integration tests
pytest tests/integration/ -v
```

## Build Process

### Project-Specific Builds

Each project builds independently:

```bash
# Build specific project
python3 scripts/run_all.py --project my_research

# Build all projects
python3 scripts/run_all.py --all-projects
```

### Output Organization

Project outputs are organized hierarchically:

```
output/
├── project/                    # Default project outputs
│   ├── pdf/
│   ├── figures/
│   ├── data/
│   └── reports/
├── small_code_project/         # Small code project outputs
└── small_prose_project/        # Small prose project outputs
```

## Troubleshooting

### Common Issues

**Project not discovered:**
- Ensure project has required directories: `src/`, `tests/`, `manuscript/`
- Check directory permissions
- Verify project name doesn't conflict with reserved names

**Configuration conflicts:**
- Each project should have independent configuration
- Check for shared environment variables
- Verify project-specific paths in scripts

**Resource conflicts:**
- Projects should not share output directories
- Use project-specific data files
- Implement proper cleanup in scripts

**Dependency issues:**
- Projects can have different dependency requirements
- Use virtual environments per project if needed
- Document project-specific setup requirements

## Best Practices

### Project Organization

- **Clear naming**: Use descriptive project names
- **Independent scope**: Each project should have clear, independent goals
- **Minimal overlap**: Avoid code duplication between projects
- **Documentation**: Document project-specific setup and requirements

### Code Quality

- **Consistent structure**: Follow template conventions
- **Test coverage**: Maintain 90%+ coverage for project code
- **Documentation**: Document project-specific algorithms and methods
- **Reproducibility**: Ensure all results are reproducible

### Maintenance

- **Regular updates**: Keep projects current with template changes
- **Dependency management**: Track and update project dependencies
- **Output cleanup**: Regularly clean generated outputs
- **Backup strategy**: Backup important project data separately

## Advanced Features

### Custom Project Templates

Create specialized project templates:

```python
# infrastructure/project/templates.py
def create_project_template(template_type: str, project_name: str):
    """Create project from specialized template."""
    templates = {
        "computational": create_computational_template,
        "literature": create_literature_template,
        "educational": create_educational_template
    }

    if template_type in templates:
        templates[template_type](project_name)
```

### Project Metrics

Track project health and progress:

```python
# infrastructure/project/metrics.py
def get_project_metrics(project_name: str) -> Dict[str, Any]:
    """Get comprehensive project metrics."""
    return {
        "test_coverage": calculate_coverage(project_name),
        "code_complexity": analyze_complexity(project_name),
        "documentation_completeness": check_documentation(project_name),
        "build_status": get_build_status(project_name)
    }
```

## See Also

- [README.md](README.md) - Quick reference for projects directory
- [project/AGENTS.md](project/AGENTS.md) - Default project technical documentation
- [small_code_project/AGENTS.md](small_code_project/AGENTS.md) - Code-focused project documentation
- [small_prose_project/AGENTS.md](small_prose_project/AGENTS.md) - Prose-focused project documentation
- [infrastructure/project/AGENTS.md](../infrastructure/project/AGENTS.md) - Project management utilities