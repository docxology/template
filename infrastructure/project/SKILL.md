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

## Optional CodeGraph Helpers

CodeGraph is a local-only agent navigation index. Use these helpers to print
safe commands and verify that a template-root index did not include private
symlinked projects:

```python
from pathlib import Path
from infrastructure.project import build_codegraph_init_command, verify_codegraph_scope_payload

print(build_codegraph_init_command(Path(".")).display)
offenders = verify_codegraph_scope_payload(codegraph_files_json)
```

The index directory `.codegraph/` is generated local state and must remain
untracked.

## Rendered vs Non-Rendered Subfolders

- **Rendered:** `projects/templates/` (public exemplars) and optional `projects/active/` (hot-seat) — discovered and executed by infrastructure when present.
- **Non-rendered:** `projects/working/` and `projects/archive/` in the simplified sidecar; optional legacy `projects/published/` and `projects/other/` are also preserved but not executed.

```bash
# Retire a sidecar working project
mv projects/working/{name}/ projects/archive/{name}/

# Resume a sidecar archived project
mv projects/archive/{name}/ projects/working/{name}/

# Render explicitly from the template checkout
uv run python scripts/pipeline/stage_03_render.py --project working/{name}
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
uv run python -c "
from infrastructure.project import discover_projects
from pathlib import Path
for p in discover_projects(Path('.')):
    print(f'{p.name}: {p.path}')
"
```

## Public API Summary (`__init__.py`)

| Export | Type |
|--------|------|
| `CodeGraphCommand` | Dataclass |
| `PUBLIC_PROJECT_NAMES` | Constant (tuple) |
| `ProjectInfo` | Dataclass |
| `build_codegraph_files_command` | Function |
| `build_codegraph_init_command` | Function |
| `build_scope_check_command` | Function |
| `discover_projects` | Function |
| `find_setup_hook` | Function |
| `get_project_metadata` | Function |
| `preflight_setup_hook` | Function |
| `public_ci_source_paths` | Function |
| `public_project_infos` | Function |
| `public_project_names` | Function |
| `resolve_project_root` | Function |
| `run_project_setup_hook` | Function |
| `validate_project_structure` | Function |
| `verify_codegraph_scope_payload` | Function |
