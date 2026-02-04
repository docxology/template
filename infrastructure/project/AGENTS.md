# infrastructure/project/ - Project Management Module

## Purpose

The `infrastructure/project/` module provides project discovery, validation, and metadata extraction for multi-project support. This enables the template to manage multiple independent research projects within a single repository.

## Key Components

### Project Discovery (`discovery.py`)

**Core Functions:**

- `discover_projects(repo_root)` - Find all valid projects in `projects/` directory
- `validate_project_structure(project_dir)` - Validate required directories exist
- `get_project_metadata(project_dir)` - Extract configuration from pyproject.toml and config.yaml
- `get_default_project(repo_root)` - Get the default template project

**ProjectInfo Dataclass:**
```python
@dataclass
class ProjectInfo:
    name: str              # Project directory name
    path: Path             # Absolute path to project
    has_src: bool          # Has src/ directory
    has_tests: bool        # Has tests/ directory  
    has_scripts: bool      # Has scripts/ directory
    has_manuscript: bool   # Has manuscript/ directory
    metadata: dict         # Extracted metadata
    
    @property
    def is_valid(self) -> bool:
        """Check if project has minimum required structure."""
```

## Project Structure Requirements

### Required Directories

A valid project **must** have:
- `src/` - Source code with Python modules
- `tests/` - Test suite

### Optional Directories

Recommended but not required:
- `scripts/` - Analysis scripts (discovered by `02_run_analysis.py`)
- `manuscript/` - Research manuscript markdown files
- `output/` - Generated outputs (created automatically)

### Example Project Structure

```
projects/
├── project/              # Default template project
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   ├── manuscript/
│   ├── output/           # Generated (not in git)
│   └── pyproject.toml
├── myresearch/           # Custom project 1
│   ├── src/
│   ├── tests/
│   ├── manuscript/
│   └── pyproject.toml
└── experiment2/          # Custom project 2
    ├── src/
    ├── tests/
    └── pyproject.toml
```

## Discovery Scope and Project Organization

### Active vs Archived Projects

The infrastructure distinguishes between **active projects** and **archived projects**:

#### ✅ **Active Projects (`projects/`)**
- **Scanned** by `discover_projects()` function
- **Validated** for structure requirements
- **Listed** in `run.sh` interactive menu
- **Executed** by pipeline scripts

#### ❌ **Archived Projects (`projects_archive/`)**
- **NOT scanned** by `discover_projects()` function
- **NOT validated** by infrastructure
- **NOT listed** in `run.sh` menu
- **NOT executed** by pipeline scripts
- **Preserved** for historical reference

### Discovery Behavior

```python
# discover_projects() only scans projects/ directory
def discover_projects(repo_root: Path | str) -> list[ProjectInfo]:
    """Discover all valid projects in projects/ directory.

    This function intentionally excludes projects_archive/ directory.
    Only projects in projects/ are discovered and executed by infrastructure.
    """
    projects_dir = repo_root / "projects"  # Only this directory is scanned
    # projects_archive/ is intentionally excluded
```

## Usage

### Discovering All Projects

```python
from infrastructure.project import discover_projects

repo_root = Path("/path/to/template")
projects = discover_projects(repo_root)

for project in projects:
    print(f"Found: {project.name} at {project.path}")
    print(f"  Valid: {project.is_valid}")
    print(f"  Has manuscript: {project.has_manuscript}")
```

### Validating a Project

```python
from infrastructure.project import validate_project_structure

project_dir = Path("projects/myresearch")
is_valid, message = validate_project_structure(project_dir)

if is_valid:
    print(f"✓ {message}")
else:
    print(f"✗ {message}")
```

### Extracting Project Metadata

```python
from infrastructure.project import get_project_metadata

metadata = get_project_metadata(Path("projects/project"))

print(f"Name: {metadata['name']}")
print(f"Version: {metadata['version']}")
print(f"Description: {metadata['description']}")
print(f"Authors: {', '.join(metadata['authors'])}")
```

## Integration with Pipeline

### Script Discovery (02_run_analysis.py)

```python
from infrastructure.project import discover_projects

# Discover all projects
projects = discover_projects(repo_root)

# Run analysis for specific project
project_name = args.project
project_root = repo_root / "projects" / project_name

scripts = discover_analysis_scripts(project_root)
```

### Test Execution (01_run_tests.py)

```python
from infrastructure.project import validate_project_structure

project_root = repo_root / "projects" / args.project

# Validate before running tests
is_valid, message = validate_project_structure(project_root)
if not is_valid:
    logger.error(f"Invalid project: {message}")
    return 1

# Run tests
cmd = [sys.executable, "-m", "pytest", str(project_root / "tests")]
```

## Metadata Sources

Metadata is extracted from multiple sources in priority order:

### 1. pyproject.toml (Primary)

```toml
[project]
name = "myresearch"
version = "0.1.0"
description = "Novel optimization framework"
authors = [
    {name = "Dr. Jane Smith", email = "jane@example.com"}
]
```

### 2. manuscript/config.yaml (Secondary)

```yaml
paper:
  title: "Novel Optimization Framework"
  
authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-0000"
```

### 3. Default Values (Fallback)

If no configuration files found:
```python
{
    "name": "{project_directory_name}",
    "description": "",
    "version": "0.1.0",
    "authors": []
}
```

## Validation Rules

### Project Discovery

Projects are discovered if:
- Located in `projects/` directory
- Not hidden (doesn't start with `.`)
- Has valid structure (passes `validate_project_structure()`)

### Structure Validation

A project is valid if:
- ✅ Directory exists and is readable
- ✅ Has `src/` directory
- ✅ Has `tests/` directory
- ✅ `src/` contains at least one `.py` file

A project is invalid if:
- ❌ Missing `src/` or `tests/` directories
- ❌ `src/` directory is empty (no Python files)
- ❌ Directory is not accessible

## Creating New Projects

### Option 1: Copy Template

```bash
# Copy the default template project
cp -r projects/project projects/myresearch

# Customize pyproject.toml
vim projects/myresearch/pyproject.toml

# Add your code
vim projects/myresearch/src/mymodule.py
```

### Option 2: Manual Creation

```bash
# Create project structure
mkdir -p projects/myresearch/{src,tests,scripts,manuscript}

# Create pyproject.toml
cat > projects/myresearch/pyproject.toml << EOF
[project]
name = "myresearch"
version = "0.1.0"
description = "My research project"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF

# Add initial module
touch projects/myresearch/src/__init__.py
touch projects/myresearch/src/mymodule.py

# Add initial test
touch projects/myresearch/tests/__init__.py
touch projects/myresearch/tests/test_mymodule.py
```

### Option 3: Migration Script

```bash
# Use the provided migration helper
python3 -c "
from infrastructure.project import validate_project_structure
from pathlib import Path

project_dir = Path('projects/myresearch')
is_valid, message = validate_project_structure(project_dir)
print(f'Project validation: {message}')
"
```

## Best Practices

### Do's ✅

- Keep each project independent (no cross-project imports)
- Use consistent directory structure across projects
- Include pyproject.toml with project metadata
- Add README.md to each project explaining its purpose
- Use meaningful project names (not `project1`, `project2`)

### Don'ts ❌

- Don't create projects without required `src/` and `tests/` directories
- Don't share code between projects (use infrastructure/ for shared utilities)
- Don't commit `output/` directories (added to `.gitignore`)
- Don't use spaces or special characters in project names

## Error Handling

### Common Validation Errors

**Missing src/ directory:**
```python
(False, "Missing required directory: src")
```
**Solution:** Create `src/` directory with at least one `.py` file

**No Python files in src/:**
```python
(False, "src/ directory contains no Python files")
```
**Solution:** Add Python modules to `src/`

**Project not found:**
```python
(False, "Project directory does not exist: projects/myproject")
```
**Solution:** Check project name spelling or create project

### Debug Mode

Enable debug logging to see project discovery details:

```python
import logging
logging.getLogger("infrastructure.project.discovery").setLevel(logging.DEBUG)

projects = discover_projects(repo_root)
# Outputs:
#   DEBUG: Discovered project: project at /path/to/projects/project
#   DEBUG: Discovered project: myresearch at /path/to/projects/myresearch
#   DEBUG: Skipping invalid: Missing required directory: src
```

## Testing

The module includes tests in `tests/infra_tests/test_project_discovery.py`:

```bash
# Run project discovery tests
python3 -m pytest tests/infra_tests/test_project_discovery.py -v

# Expected tests:
# test_discover_projects - Finds all valid projects
# test_validate_project_structure - Validates required directories
# test_get_project_metadata - Extracts metadata correctly
# test_invalid_project_handling - Handles invalid projects gracefully
```

## See Also

- [`infrastructure/core/script_discovery.py`](../core/script_discovery.py) - Analysis script discovery
- [`infrastructure/core/file_operations.py`](../core/file_operations.py) - File operations with project support
- [`scripts/AGENTS.md`](../../scripts/AGENTS.md) - Generic entry point orchestrators
- [`AGENTS.md`](../../AGENTS.md) - system documentation

## Summary

The `infrastructure/project/` module enables multi-project support by:
- ✅ Discovering valid projects in `projects/` directory
- ✅ Validating project structure requirements
- ✅ Extracting metadata from configuration files
- ✅ Providing ProjectInfo dataclass for project information
- ✅ Supporting both default and custom projects
- ✅ Enabling project selection in pipeline scripts
