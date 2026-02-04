# Project Management - Quick Reference

Project discovery, validation, and metadata extraction for multi-project support.

## Overview

The project module enables the template to manage multiple independent research projects within a single repository. It provides utilities for discovering, validating, and extracting metadata from projects.

## Quick Start

```python
from infrastructure.project import discover_projects, validate_project_structure

# Discover all projects
repo_root = Path("/path/to/template")
projects = discover_projects(repo_root)

# Validate a specific project
is_valid, message = validate_project_structure(Path("projects/my_research"))
```

## Key Functions

### Project Discovery

```python
from infrastructure.project import discover_projects

# Find all valid projects in projects/ directory
projects = discover_projects(Path("."))

for project in projects:
    print(f"Found: {project.name}")
    print(f"  Valid: {project.is_valid}")
    print(f"  Has src: {project.has_src}")
    print(f"  Has manuscript: {project.has_manuscript}")
```

### Project Validation

```python
from infrastructure.project import validate_project_structure

# Check if a directory is a valid project
project_dir = Path("projects/my_research")
is_valid, message = validate_project_structure(project_dir)

if is_valid:
    print("✅ Valid project")
else:
    print(f"❌ Invalid: {message}")
```

### Metadata Extraction

```python
from infrastructure.project import get_project_metadata

# Extract metadata from project files
metadata = get_project_metadata(Path("projects/project"))

print(f"Name: {metadata['name']}")
print(f"Authors: {metadata['authors']}")
print(f"Description: {metadata['description']}")
```

## Project Structure Requirements

### Required Directories

Every valid project **must** have:
- `src/` - Python source code directory
- `tests/` - Test suite directory

### Optional Directories

Recommended for full functionality:
- `scripts/` - Analysis scripts (discovered by pipeline)
- `manuscript/` - Research content (processed by build system)

### Example Structure

```
projects/my_research/
├── src/                    # Required: Source code
│   ├── __init__.py
│   └── analysis.py
├── tests/                  # Required: Test suite
│   ├── __init__.py
│   └── test_analysis.py
├── scripts/                # Optional: Analysis workflows
│   └── run_analysis.py
├── manuscript/             # Optional: Research content
│   ├── 01_introduction.md
│   └── config.yaml
└── pyproject.toml          # Project metadata
```

## Integration with Pipeline

### Script Discovery

The project module integrates with the analysis pipeline:

```python
# scripts/02_run_analysis.py uses project discovery
from infrastructure.project import discover_projects

def run_analysis_pipeline():
    projects = discover_projects(repo_root)

    for project in projects:
        if project.name == args.project:
            scripts = discover_analysis_scripts(project.path)
            # Execute scripts...
```

### Test Execution

Project tests are executed through the test pipeline:

```python
# scripts/01_run_tests.py uses project validation
from infrastructure.project import validate_project_structure

def run_project_tests(project_name: str):
    project_dir = repo_root / "projects" / project_name

    is_valid, message = validate_project_structure(project_dir)
    if not is_valid:
        logger.error(f"Invalid project: {message}")
        return False

    # Run pytest on project tests...
```

## Configuration

### pyproject.toml

Projects can include standard Python project metadata:

```toml
[project]
name = "my_research"
version = "0.1.0"
description = "Novel research on X"
authors = [
    {name = "Dr. Researcher", email = "researcher@uni.edu"}
]
dependencies = ["numpy", "scipy", "matplotlib"]
```

### Manuscript Config

Research projects can include manuscript configuration:

```yaml
paper:
  title: "My Research Title"
  subtitle: "Optional Subtitle"

authors:
  - name: "Dr. Researcher"
    email: "researcher@uni.edu"
    affiliation: "University Name"
```

## Testing

The project module includes tests:

```bash
# Test project discovery functionality
pytest tests/infra_tests/test_project_discovery.py -v

# Test with real project structures
pytest tests/infra_tests/test_project_discovery.py::test_discover_projects -v
```

## Error Handling

### Common Validation Errors

**Missing src/ directory:**
```python
(False, "Missing required directory: src")
# Solution: Create src/ directory with Python files
```

**Empty src/ directory:**
```python
(False, "src/ directory contains no Python files")
# Solution: Add Python modules to src/
```

**Project not found:**
```python
(False, "Project directory does not exist: projects/myproject")
# Solution: Create project or check spelling
```

## Best Practices

### Project Organization

- **Consistent naming**: Use descriptive project names
- **Independent scope**: Keep projects focused on single research questions
- **Standard structure**: Follow template conventions for compatibility
- **Documentation**: Include README.md in each project

### Development Workflow

- **Validation first**: Check project structure before development
- **Incremental building**: Start with minimal structure, expand as needed
- **Regular testing**: Run project tests frequently during development
- **Clean commits**: Keep project and template changes separate

## Architecture

```mermaid
graph TD
    A[Project Module] --> B[Discovery]
    A --> C[Validation]
    A --> D[Metadata]

    B --> E[discover_projects()]
    C --> F[validate_project_structure()]
    D --> G[get_project_metadata()]

    E --> H[ProjectInfo dataclass]
    F --> I[Validation results]
    G --> J[Metadata dictionary]

    H --> K[Pipeline Integration]
    I --> K
    J --> K
```

## See Also

- [AGENTS.md](AGENTS.md) - technical documentation
- [manuscript/README.md](manuscript/README.md) - Manuscript utilities
- [../../scripts/AGENTS.md](../../scripts/AGENTS.md) - Pipeline integration
- [../../projects/AGENTS.md](../../projects/AGENTS.md) - Multi-project overview