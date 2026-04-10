# Multi-Project Management Guide

> **Strategies for managing multiple projects** using the template

**Quick Reference:** [Getting Started](../guides/getting-started.md) | [Architecture](../core/architecture.md) | [Best Practices](../best-practices/best-practices.md)

This guide provides strategies and best practices for managing multiple research projects that all use the Research Project Template, enabling efficient workflows and maintaining consistency across projects.

## Overview

When managing multiple research projects, you can leverage the template's structure to:

- Maintain consistency across projects
- Share common configurations
- Update templates efficiently
- Manage dependencies across projects
- Automate common workflows

## 3-Directory Project Lifecycle

The repository uses three sibling directories to manage projects at different stages:

| Directory | Purpose | Rendered by `./run.sh`? |
|-----------|---------|------------------------|
| `projects/` | **Active** – ready for the pipeline | ✅ Yes |
| `projects_in_progress/` | **Work-in-progress** – not yet publication-ready | ❌ No |
| `projects_archive/` | **Completed / paused** – kept for reference | ❌ No |

**Rules:**

- `./run.sh` only discovers projects under `projects/`. Archive and in-progress directories are ignored.
- A project retains its full structure (src/, manuscript/, tests/, output/) in any directory, so it can be moved back to `projects/` at any time without modification.
- Use `projects_in_progress/` while actively writing; move to `projects/` only when ready for a full pipeline render.
- Use `projects_archive/` for completed or low-priority projects so they do not increase pipeline runtime.

**Authoritative roster:** [`docs/_generated/active_projects.md`](../_generated/active_projects.md) from `discover_projects()`. Default path examples in docs use [`projects/code_project/`](../../projects/code_project/); an active project may also maintain its own reference hub (for example [`projects/fep_lean/docs/`](../../projects/fep_lean/docs/)).

**Moving a project:**

```bash
# Promote a WIP project to active
mv projects_in_progress/my_paper projects/my_paper

# Archive a completed project
mv projects/finished_paper projects_archive/finished_paper

# Return an archived project for revisions
mv projects_archive/old_paper projects_in_progress/old_paper
```

**Advanced: running the pipeline against a different directory:**

```python
from infrastructure.core.pipeline.pipeline import PipelineConfig, PipelineExecutor
from pathlib import Path

# Test an in-progress project without moving it
config = PipelineConfig(
    project_name="draft_paper",
    repo_root=Path("."),
    projects_dir="projects_in_progress",   # override default "projects"
)
PipelineExecutor(config).execute_core_pipeline()
```

Infrastructure modules (`discovery.py`, `script_discovery.py`, `config_loader.py`,
`checkpoint.py`, and the reporting layer) accept a `projects_dir` string (or resolve paths via `PipelineConfig`, whose **`project_dir`** property is the computed `repo_root / projects_dir / project_name` path), so this configuration propagates throughout the pipeline.

## Organizing Multiple Projects

### Directory Structure

**Recommended organization:**

```text
research/
├── project1/
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   └── ...
├── project2/
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   └── ...
└── shared/
    ├── templates/
    ├── utilities/
    └── configs/
```

**Benefits:**

- Clear project separation
- Shared resources accessible
- Easy to navigate
- Consistent structure

### Naming Conventions

**Use consistent naming:**

- Project names: `project-name` (kebab-case)
- Branch names: `project-name-feature`
- Tag names: `project-name-v1.0.0`

**Example:**

```text
climate-analysis/
optimization-study/
ml-benchmarking/
```

## Shared Dependencies

### Common Dependencies

**Identify shared packages:**

```toml
# shared/pyproject.toml.template
[project]
dependencies = [
    "numpy>=1.22",
    "matplotlib>=3.7",
    "pypdf>=5.0",
    # Common packages
]
```

**Manage shared dependencies:**

```bash
# Create shared dependency file
cat > shared/requirements-common.txt << EOF
numpy>=1.22
matplotlib>=3.7
pypdf>=5.0
EOF

# Install in each project
uv pip install -r ../shared/requirements-common.txt
```

### Dependency Version Management

**Keep versions consistent:**

```bash
# Update all projects
for project in */; do
    cd "$project"
    uv sync --upgrade-package numpy
    cd ..
done
```

**Version synchronization script:**

```bash
#!/bin/bash
# sync-dependencies.sh

PACKAGE="$1"
VERSION="$2"

for project in */; do
    if [ -f "$project/pyproject.toml" ]; then
        echo "Updating $project..."
        cd "$project"
        uv add "${PACKAGE}==${VERSION}"
        cd ..
    fi
done
```

## Template Updates Across Projects

### Updating Template Structure

**When template improves:**

```bash
# 1. Update template repository
cd template-repo
git pull origin main

# 2. For each project
for project in ../../projects/*/; do
    cd "$project"
    
    # Copy updated files
    cp -r ../../template/scripts/* scripts/
    cp ../../template/pyproject.toml pyproject.toml.new
    
    # Review changes
    diff pyproject.toml pyproject.toml.new
    
    # Apply if compatible
    # mv pyproject.toml.new pyproject.toml
done
```

### Selective Updates

**Update specific components:**

```bash
# Update only build scripts
cp -r template/scripts/* projects/{name}/scripts/

# Update only documentation structure
cp -r template/docs/* project/docs/

# Update only test configuration
cp template/pyproject.toml project/pyproject.toml  # Review first
```

## Common Configurations

### Shared Configuration Files

**Create shared configs:**

```bash
# Shared .env template
cat > shared/.env.template << EOF
AUTHOR_NAME="Your Name"
AUTHOR_EMAIL="your.email@example.com"
AUTHOR_ORCID="0000-0000-0000-0000"
PROJECT_TITLE="Project Title"
EOF

# Copy to each project
for project in */; do
    cp shared/.env.template "$project/.env.template"
done
```

### Environment Variables

**Consistent environment setup:**

```bash
# Shared environment script
cat > shared/setup-env.sh << 'EOF'
#!/bin/bash
export AUTHOR_NAME="Your Name"
export AUTHOR_EMAIL="your.email@example.com"
export AUTHOR_ORCID="0000-0000-0000-0000"
export PROJECT_TITLE="Project Title"
EOF

# Source in each project
source ../shared/setup-env.sh
```

## Automation Strategies

### Batch Operations

**Run commands across projects:**

```bash
#!/bin/bash
# run-all-projects.sh

COMMAND="$@"

for project in */; do
    if [ -f "$project/pyproject.toml" ]; then
        echo "Running in $project..."
        cd "$project"
        eval "$COMMAND"
        cd ..
    fi
done
```

**Usage:**

```bash
# Run tests in all projects
./run-all-projects.sh "uv run pytest tests/"

# Build all projects
./run-all-projects.sh "uv run python scripts/execute_multi_project.py"

# Update dependencies
./run-all-projects.sh "uv sync --upgrade"
```

### Status Monitoring

**Check status of all projects:**

```bash
#!/bin/bash
# project-status.sh

for project in */; do
    if [ -d "$project/.git" ]; then
        echo "=== $project ==="
        cd "$project"
        git status --short
        echo "Tests: $(uv run pytest tests/ --collect-only -q 2>/dev/null | tail -1)"
        cd ..
        echo
    fi
done
```

## Project-Specific Customizations

### Preserving Customizations

**Document project-specific changes:**

```markdown
# PROJECT_CUSTOMIZATIONS.md

## Custom Scripts
- scripts/custom_analysis.py - Project-specific analysis

## Modified Files
- scripts/03_render_pdf.py - Added custom validation step

## Additional Dependencies
- scipy>=1.10 - For advanced analysis
```

### Template Compatibility

**Ensure customizations remain compatible:**

```bash
# Before template updates
git diff template-repo/scripts/03_render_pdf.py \
          scripts/03_render_pdf.py

# Review changes
# Apply selectively
# Test thoroughly
```

## Dependency Management

### Project-Specific Dependencies

**Isolate project dependencies:**

```toml
# pyproject.toml
[project]
dependencies = [
    # Shared dependencies (from template)
    "numpy>=1.22",
    "matplotlib>=3.7",
    # Project-specific
    "scipy>=1.10",
    "pandas>=2.0",
]
```

### ⚠️ Root Venv Dependency Coverage (Critical Rule)

Each project in `projects/` may have its own `pyproject.toml` listing extra dependencies. However, **analysis scripts run with the root `.venv`** (via `02_run_analysis.py`) unless the project has a local `.venv/` directory.

**The rule:** If `projects/<name>/.venv` does **not** exist, all packages in `projects/<name>/pyproject.toml#dependencies` must **also** be declared in the root `pyproject.toml`.

**How to verify:**

```bash
# For each project without a local venv:
for project in projects/*/; do
    if [ ! -d "$project/.venv" ]; then
        echo "=== $project (uses ROOT venv) ==="
        grep -A 20 '^dependencies' "$project/pyproject.toml" 2>/dev/null
    fi
done

# Verify all needed packages are in root venv:
.venv/bin/python -c "
import scipy, pandas, networkx, rdflib, wordcloud, sklearn, requests
print('All OK')
"
```

**Symptoms when violated:**

- `❌ project_name: 4 stages, 7.7s` in multi-project summary (Stage 4 fails in < 1s)
- No visible import error in console (swallowed by subprocess capture)
- Project passes when analysis scripts are run standalone (because environment differs)

**Fix:** Add missing packages to root `pyproject.toml`'s core `dependencies`, then `uv sync`.

**Venv selection logic in `02_run_analysis.py`:**

```text
project has .venv/ + uv available  →  uv run --directory project/ python script.py
project has .venv/ + no uv        →  get_python_command() + script.py  (warning logged)
project has no .venv/             →  get_python_command() + script.py  (root venv)
```

### Dependency Conflicts

**Resolve conflicts:**

```bash
# Check for conflicts
uv tree

# Resolve version conflicts
uv add "package>=1.0,<2.0"  # Compatible version

# Document resolution
# Add note in pyproject.toml
```

## Workflow Best Practices

### Project Initialization

**Standardize new projects:**

```bash
#!/bin/bash
# new-project.sh

PROJECT_NAME="$1"

# Create from template
git clone template-repo "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Customize (edit config.yaml or set environment variables)
cp projects/{name}/manuscript/config.yaml.example projects/{name}/manuscript/config.yaml
vim projects/{name}/manuscript/config.yaml

# Initialize
uv sync
uv run pytest tests/
```

### Regular Maintenance

**Maintenance tasks:**

```bash
# Weekly: Update dependencies
for project in */; do
    cd "$project"
    uv sync --upgrade
    cd ..
done

# Monthly: Review and cleanup
# Remove unused dependencies
# Update documentation
# Review test coverage
```

### Cross-Project Testing

**Test across projects:**

```bash
# Ensure all projects build
for project in */; do
    cd "$project"
    uv run python scripts/execute_pipeline.py --project "$project" --core-only || echo "$project failed"
    cd ..
done
```

## Best Practices

### Organization

1. **Consistent structure** - Same layout across projects
2. **Clear naming** - Descriptive project names
3. **Shared resources** - Common utilities and configs
4. **Documentation** - Document project-specific changes

### Maintenance

1. **Regular updates** - Keep template current
2. **Dependency sync** - Consistent versions
3. **Testing** - Verify all projects work
4. **Backup** - Regular backups of all projects

### Collaboration

1. **Shared standards** - Consistent practices
2. **Communication** - Share improvements
3. **Documentation** - Document shared patterns
4. **Review** - Review across projects

## Troubleshooting

### Common Issues

#### Issue: Template updates break projects

**Solution:**

- Review changes before applying
- Test in one project first
- Preserve customizations
- Update gradually

#### Issue: Dependency conflicts

**Solution:**

- Use compatible versions
- Document constraints
- Test thoroughly
- Consider virtual environments

#### Issue: Inconsistent structure

**Solution:**

- Standardize on template structure
- Use scripts to enforce
- Document deviations
- Regular audits

#### Issue: Multi-project pipeline Stage 4 fails silently in < 1s

**Symptom:** `❌ project_name: 4 stages, 7.7s` with 3 stages obviously fast (clean + setup + tests) and Stage 4 (analysis) never producing output.

**Most common root cause:** Project-specific packages missing from root `.venv` (see [Root Venv Dependency Coverage](#root-venv-dependency-coverage-critical-rule) above).

**Diagnosis checklist:**

```bash
# 1. Check project pipeline log directly:
cat projects/<name>/output/logs/pipeline.log

# 2. Run analysis stage standalone to see errors:
python3 scripts/02_run_analysis.py --project <name>

# 3. Run first analysis script directly with root Python:
.venv/bin/python projects/<name>/scripts/01_*.py

# 4. Check all imports from project's src:
.venv/bin/python -c "import scipy, pandas, wordcloud" 2>&1
```

**Other causes to rule out:**

- Script syntax error (run `python -m py_compile script.py`)
- Missing `conftest.py` adding `src/` to path
- Data file not found (e.g., `corpus.jsonl` was cleaned)

## Automation Scripts

### Project Initialization Script

**Template for new projects:**

```bash
#!/bin/bash
# init-project.sh

PROJECT_NAME="$1"
TEMPLATE_DIR="../template"

# Copy template
cp -r "$TEMPLATE_DIR" "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Remove git history
rm -rf .git

# Initialize new repo
git init
git add .
git commit -m "Initial commit from template"

# Customize
echo "Customize project: $PROJECT_NAME"
```

### Batch Updates

**Update all projects:**

```bash
#!/bin/bash
# update-all-projects.sh

TEMPLATE_DIR="../template"

for project in */; do
    echo "Updating $project..."
    cd "$project"
    
    # Backup
    git tag backup-before-update
    
    # Update files
    cp -r "$TEMPLATE_DIR/scripts/" scripts/
    
    # Test
    uv run python scripts/execute_pipeline.py --project "$project" --core-only || echo "Failed: $project"
    
    cd ..
done
```

## Summary

Multi-project management strategies:

1. **Organization** - Consistent structure and naming
2. **Shared resources** - Common dependencies and configs
3. **Template updates** - Selective and careful updates
4. **Automation** - Scripts for common tasks
5. **Maintenance** - Regular updates and testing

**Benefits:**

- Consistency across projects
- Efficient maintenance
- Shared improvements
- Reduced duplication

---

**See Also:**

- [Getting Started](../guides/getting-started.md) - Setting up projects
- [Architecture](../core/architecture.md) - Project structure
- [Best Practices](../best-practices/best-practices.md) - Management practices
