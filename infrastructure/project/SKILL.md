---
name: infrastructure-project
description: Skill for the project management infrastructure module providing multi-project discovery, structure validation, and metadata extraction. Use when discovering active projects, validating project directory structure, or extracting project configuration metadata.
---

# Project Module

Multi-project discovery, validation, and metadata management.

## Project Discovery (`discovery.py`)

```python
from infrastructure.project import discover_projects, ProjectInfo

# Discover all valid projects in the repository
projects = discover_projects(repo_root)

for project in projects:
    print(f"{project.name}: {project.path}")
    print(f"  Has tests: {project.has_tests}")
    print(f"  Has manuscript: {project.has_manuscript}")
```

## Structure Validation

```python
from infrastructure.project import validate_project_structure

# Validate that a project has all required directories
is_valid, message = validate_project_structure(project_path)
```

**Required directories:**

- `src/` — Project source code
- `tests/` — Test suite

**Optional (recommended) directories:**

- `scripts/` — Analysis scripts (thin orchestrators)
- `manuscript/` — Markdown manuscript sections

## Metadata Extraction

```python
from infrastructure.project import get_project_metadata

# Extract project metadata from pyproject.toml and/or manuscript/config.yaml
metadata = get_project_metadata(project_path)
print(metadata.get("title"), metadata["version"], metadata["authors"])
```

## Active vs Archived Projects

- **Active:** `projects/` — Discovered and executed by infrastructure
- **Archived:** `projects_archive/` — Preserved but not executed

```bash
# Archive a project
mv projects/{name}/ projects_archive/{name}/

# Reactivate a project
mv projects_archive/{name}/ projects/{name}/
```

## Multi-Project Pipeline Usage

Multi-project orchestration lives in `infrastructure.core`, not this module:

```python
from infrastructure.project import discover_projects
from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator

# Discover and run all projects
projects = discover_projects(repo_root)
config = MultiProjectConfig(projects=[p.name for p in projects])
orchestrator = MultiProjectOrchestrator(config)
result = orchestrator.run()
```

**CLI:**

```bash
# Run all projects
./run.sh --all-projects --pipeline

# List available projects
python3 -c "
from infrastructure.project import discover_projects
from pathlib import Path
for p in discover_projects(Path('.')):
    print(f'{p.name}: {p.path}')
"
```

## Public API Summary (`__init__.py`)

| Export | Type |
|--------|------|
| `discover_projects` | Function |
| `validate_project_structure` | Function |
| `get_project_metadata` | Function |
| `ProjectInfo` | Dataclass |
