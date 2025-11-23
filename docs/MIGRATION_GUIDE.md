# Migration Guide

> **Step-by-step guide** for migrating from other templates and projects

**Quick Reference:** [Getting Started](GETTING_STARTED.md) | [Architecture](ARCHITECTURE.md) | [Common Workflows](COMMON_WORKFLOWS.md)

This guide provides comprehensive instructions for migrating existing projects to the Research Project Template structure, ensuring a smooth transition while preserving your work.

## Overview

Migration involves adapting your existing project structure to match the template's architecture while preserving your code, data, and documentation. This guide covers common migration scenarios and provides step-by-step procedures.

## Pre-Migration Assessment

### Evaluate Your Current Project

**Before migrating, assess:**

1. **Current structure** - Directory layout
2. **Dependencies** - Python packages and versions
3. **Code organization** - Module structure
4. **Testing** - Test coverage and framework
5. **Documentation** - Format and organization
6. **Build system** - Current build process

### Identify Migration Requirements

**Determine what needs to migrate:**

- Source code modules
- Test files
- Documentation/manuscript files
- Configuration files
- Dependencies
- Build scripts

## Migration Strategy

### Phase 1: Preparation

**Before starting migration:**

1. **Backup everything** - Full project backup
2. **Create migration branch** - Isolated migration work
3. **Document current state** - Note current structure
4. **Plan migration steps** - Detailed plan

### Phase 2: Structure Setup

**Set up template structure:**

1. **Create directories** - src/, tests/, scripts/, etc.
2. **Copy template files** - Build scripts, configs
3. **Set up dependencies** - Install uv, configure pyproject.toml

### Phase 3: Code Migration

**Migrate your code:**

1. **Move source code** - To src/ directory
2. **Move tests** - To tests/ directory
3. **Adapt scripts** - Convert to thin orchestrators
4. **Update imports** - Fix import paths

### Phase 4: Documentation Migration

**Migrate documentation:**

1. **Move manuscript files** - To manuscript/ directory
2. **Update references** - Fix cross-references
3. **Adapt formatting** - Match template format
4. **Update metadata** - Author, project info

### Phase 5: Validation

**Validate migration:**

1. **Run tests** - Ensure all tests pass
2. **Check coverage** - Verify 100% coverage
3. **Build PDFs** - Generate outputs
4. **Validate outputs** - Check PDF quality

## Common Migration Scenarios

### Scenario 1: Simple Python Project

**From:** Basic Python project with scripts

**Steps:**

1. **Create template structure:**
   ```bash
   mkdir -p src tests scripts manuscript docs
   ```

2. **Move code to src/:**
   ```bash
   # Move modules
   mv *.py src/
   # Keep only orchestration scripts in root
   ```

3. **Create tests:**
   ```bash
   # Create test files
   for module in src/*.py; do
     test_file="tests/test_$(basename $module)"
     # Create test template
   done
   ```

4. **Adapt scripts:**
   ```python
   # Convert scripts to thin orchestrators
   # Old: Script with business logic
   # New: Script that imports from src/
   ```

5. **Update dependencies:**
   ```bash
   # Create pyproject.toml
   uv init
   uv add existing-dependencies
   ```

### Scenario 2: Research Paper Project

**From:** LaTeX or Word document project

**Steps:**

1. **Convert to Markdown:**
   ```bash
   # Convert LaTeX to Markdown
   pandoc document.tex -o manuscript/01_introduction.md
   
   # Or convert Word
   pandoc document.docx -o manuscript/01_introduction.md
   ```

2. **Organize sections:**
   ```bash
   # Create numbered sections
   mv introduction.md manuscript/02_introduction.md
   mv methods.md manuscript/03_methodology.md
   ```

3. **Add cross-references:**
   ```markdown
   # Update references
   # Old: See Section 2
   # New: See \ref{sec:methodology}
   ```

4. **Set up build system:**
   ```bash
   # Copy template build scripts
   cp template/repo_utilities/* repo_utilities/
   ```

### Scenario 3: Jupyter Notebook Project

**From:** Jupyter notebooks with analysis

**Steps:**

1. **Extract code:**
   ```python
   # Convert notebooks to scripts
   jupyter nbconvert --to script notebook.ipynb
   ```

2. **Separate logic from presentation:**
   ```python
   # Business logic → src/
   # Visualization → scripts/
   ```

3. **Create tests:**
   ```python
   # Extract test cases from notebooks
   # Create test files
   ```

4. **Convert outputs:**
   ```bash
   # Export figures
   # Convert markdown cells to manuscript/
   ```

### Scenario 4: Existing Template Fork

**From:** Previous version of template

**Steps:**

1. **Compare structures:**
   ```bash
   # Identify differences
   diff -r old_template/ new_template/
   ```

2. **Update configuration:**
   ```bash
   # Update pyproject.toml
   # Update build scripts
   # Update dependencies
   ```

3. **Migrate customizations:**
   ```bash
   # Preserve custom code
   # Preserve custom scripts
   # Preserve custom documentation
   ```

4. **Test compatibility:**
   ```bash
   # Run full test suite
   # Verify build works
   # Check outputs
   ```

## Step-by-Step Migration Process

### Step 1: Backup and Preparation

**Create backup:**
```bash
# Full project backup
tar -czf project_backup_$(date +%Y%m%d).tar.gz project/

# Or use git
git tag backup-before-migration
git push origin backup-before-migration
```

**Create migration branch:**
```bash
git checkout -b migration/template-upgrade
```

### Step 2: Set Up Template Structure

**Clone template structure:**
```bash
# Create directories
mkdir -p src tests scripts manuscript docs repo_utilities output

# Copy template files
cp template/repo_utilities/* repo_utilities/
cp template/pyproject.toml .
cp template/.cursorrules .
```

**Set up dependencies:**
```bash
# Initialize uv
uv init

# Add existing dependencies
uv add package1 package2 package3
```

### Step 3: Migrate Source Code

**Move code to src/:**
```bash
# Move modules
mv existing_modules/*.py src/

# Update imports in moved files
# Fix relative imports
```

**Create test structure:**
```bash
# Create test files
for module in src/*.py; do
    module_name=$(basename $module .py)
    cat > tests/test_${module_name}.py << EOF
"""Tests for ${module_name} module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ${module_name} import *

def test_example():
    """Example test."""
    pass
EOF
done
```

### Step 4: Adapt Scripts

**Convert to thin orchestrators:**
```python
# Old script (business logic included)
def process_data(data):
    result = sum(data) / len(data)  # Business logic
    return result

# New script (thin orchestrator)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from statistics import calculate_average  # Import from src/

def process_data(data):
    result = calculate_average(data)  # Use src/ method
    return result
```

### Step 5: Migrate Documentation

**Organize manuscript files:**
```bash
# Move documents
mv papers/*.md manuscript/

# Rename to numbered format
mv introduction.md manuscript/02_introduction.md
mv methods.md manuscript/03_methodology.md
```

**Update cross-references:**
```markdown
# Update reference format
# Old: See Section 2
# New: See \ref{sec:methodology}

# Add section labels
# Introduction {#sec:introduction}
```

### Step 6: Update Configuration

**Set environment variables:**
```bash
# Create .env file
cat > .env << EOF
AUTHOR_NAME="Your Name"
AUTHOR_EMAIL="your.email@example.com"
AUTHOR_ORCID="0000-0000-0000-0000"
PROJECT_TITLE="Your Project Title"
EOF
```

**Update pyproject.toml:**
```toml
[project]
name = "your-project-name"
version = "0.1.0"
description = "Your project description"
authors = [{name = "Your Name", email = "your.email@example.com"}]
```

### Step 7: Test Migration

**Run test suite:**
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ --cov=src

# Fix any import errors
# Add missing tests
```

**Build outputs:**
```bash
# Clean outputs
# Pipeline automatically handles cleanup

# Run build
python3 scripts/run_all.py

# Verify outputs
ls -la output/pdf/
```

## Common Migration Challenges

### Challenge 1: Import Path Issues

**Problem:** Import errors after moving files

**Solution:**
```python
# Add src/ to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Or use absolute imports
from src.module import function
```

### Challenge 2: Test Coverage Gaps

**Problem:** Coverage below 100% after migration

**Solution:**
```bash
# Identify missing coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Add tests for uncovered code
# Look for lines marked ">>>>>"
```

### Challenge 3: Build Script Compatibility

**Problem:** Existing build scripts don't work

**Solution:**
```bash
# Adapt scripts to template structure
# Use template build scripts as reference
# Update paths and commands
```

### Challenge 4: Documentation Format

**Problem:** Documentation doesn't match template format

**Solution:**
```markdown
# Update to template format
# Add section labels: {#sec:section_name}
# Update cross-references: \ref{sec:section_name}
# Use equation environments: \begin{equation}...\end{equation}
```

## Data Preservation

### Preserving Code

**Ensure nothing is lost:**
```bash
# Before migration
git add -A
git commit -m "Pre-migration backup"

# After migration
git diff HEAD~1  # Verify nothing missing
```

### Preserving Data

**Backup data files:**
```bash
# Backup data
cp -r data/ data_backup/

# Restore after migration
cp -r data_backup/* output/data/
```

### Preserving Outputs

**Save existing outputs:**
```bash
# Backup outputs
tar -czf outputs_backup.tar.gz output/

# Reference for comparison
# Verify new outputs match
```

## Testing After Migration

### Validation Checklist

**Verify migration success:**

- [ ] All tests pass
- [ ] 100% code coverage achieved
- [ ] Build completes successfully
- [ ] PDFs generate correctly
- [ ] Cross-references work
- [ ] Figures display properly
- [ ] All functionality preserved

### Comparison Testing

**Compare old vs new:**
```bash
# Run old build
cd old_project && ./build.sh

# Run new build
cd new_project && python3 scripts/run_all.py

# Compare outputs
diff -r old_project/output/ new_project/output/
```

## Rollback Procedures

### If Migration Fails

**Rollback steps:**

1. **Restore from backup:**
   ```bash
   # Restore files
   tar -xzf project_backup.tar.gz
   
   # Or use git
   git checkout backup-before-migration
   ```

2. **Investigate issues:**
   ```bash
   # Review error logs
   # Identify problems
   # Fix issues
   ```

3. **Retry migration:**
   ```bash
   # Apply fixes
   # Retry migration steps
   ```

## Migration from Specific Templates

### From QuadMath

**The template was adapted from QuadMath:**
```bash
# Copy utilities
cp quadmath/repo_utilities/* repo_utilities/

# Adapt structure
# Update paths
# Update dependencies
```

**See:** [README.md Migration Section](../README.md#migration-from-quadmath)

### From Other Research Templates

**Generic migration steps:**

1. **Identify differences** - Compare structures
2. **Map components** - Match old to new
3. **Migrate code** - Move and adapt
4. **Update configs** - Adapt settings
5. **Test thoroughly** - Verify everything works

## Post-Migration

### Optimization

**After successful migration:**

1. **Optimize structure** - Clean up unnecessary files
2. **Improve tests** - Enhance test coverage
3. **Update documentation** - Align with template
4. **Performance tuning** - Optimize build times

### Documentation

**Update project documentation:**

1. **Update README** - Reflect new structure
2. **Update guides** - Align with template
3. **Add examples** - Show new patterns
4. **Document changes** - Note what changed

## Summary

Migration checklist:

1. **Preparation** - Backup, plan, branch
2. **Structure** - Set up template directories
3. **Code** - Move and adapt source code
4. **Tests** - Create comprehensive tests
5. **Scripts** - Convert to thin orchestrators
6. **Documentation** - Migrate and format
7. **Configuration** - Update settings
8. **Validation** - Test everything
9. **Optimization** - Improve and refine

For detailed guidance, see:
- [Getting Started](GETTING_STARTED.md) - Template basics
- [Architecture](ARCHITECTURE.md) - System structure
- [Workflow](WORKFLOW.md) - Development process

---

**Related Documentation:**
- [Getting Started](GETTING_STARTED.md) - Template basics
- [Architecture](ARCHITECTURE.md) - Understanding structure
- [Common Workflows](COMMON_WORKFLOWS.md) - Step-by-step guides


