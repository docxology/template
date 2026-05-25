# Project Module

> **Multi-project discovery, validation, and metadata extraction**

**Location:** `infrastructure/project/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **Project Discovery**: Finds valid projects under `projects/` by applying the
  same structure validator used by the pipeline
- **Structure Validation**: Verifies required `src/` and `tests/` directories;
  `src/` must contain Python files. `scripts/` and `manuscript/` are optional
  but expected for normal pipeline/rendering workflows.
- **Metadata Extraction**: Reads project configuration (title, authors, DOI, testing thresholds)
- **Multi-Project Support**: Enables N independent projects within a single repository

---

## Usage Examples

### Discover Active Projects

```python
from pathlib import Path
from infrastructure.project import discover_projects

# Discover all projects under projects/
projects = discover_projects(Path("."))
for project in projects:
    print(f"{project.name}: {project.path}")
```

### Validate Project Structure

```python
from pathlib import Path
from infrastructure.project import validate_project_structure

is_valid, message = validate_project_structure(Path("projects/template_code_project"))
if is_valid:
    print("Project structure is valid")
else:
    print(f"Issue: {message}")
```

### Extract Project Metadata

```python
from pathlib import Path
from infrastructure.project import get_project_metadata

metadata = get_project_metadata(Path("projects/template_code_project"))
print(f"Title: {metadata.title}")
print(f"Authors: {metadata.authors}")
```

---

## Discovery Rules

A directory is a valid project if and only if:

1. It exists as a subdirectory of `projects/`
2. It does not start with `_` or `.`
3. It contains `src/` with at least one Python file
4. It contains `tests/`

Projects in `projects_in_progress/` and `projects_archive/` are **not** discovered.
`manuscript/config.yaml` is still required for rendering metadata and normal
project workflows, but it is not the low-level discovery predicate.

---

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `ProjectInfo` | Dataclass | Project metadata container |
| `discover_projects` | Function | Find all valid projects |
| `get_project_metadata` | Function | Extract config.yaml metadata |
| `validate_project_structure` | Function | Verify directory structure |

---

## Related Documentation

- **[Modules Guide](../modules-guide.md)** — Module overview
- **[Multi-Project Management](../../best-practices/multi-project-management.md)** — Multi-project workflows
- **[Infrastructure AGENTS.md](../../../infrastructure/project/AGENTS.md)** — Machine-readable API spec
