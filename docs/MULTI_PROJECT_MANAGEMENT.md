# Multi-Project Management Guide

> **Strategies for managing multiple projects** using the template

**Quick Reference:** [Getting Started](GETTING_STARTED.md) | [Architecture](ARCHITECTURE.md) | [Best Practices](BEST_PRACTICES.md)

This guide provides strategies and best practices for managing multiple research projects that all use the Research Project Template, enabling efficient workflows and maintaining consistency across projects.

## Overview

When managing multiple research projects, you can leverage the template's structure to:

- Maintain consistency across projects
- Share common configurations
- Update templates efficiently
- Manage dependencies across projects
- Automate common workflows

## Organizing Multiple Projects

### Directory Structure

**Recommended organization:**
```
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
```
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
for project in ../projects/*/; do
    cd "$project"
    
    # Copy updated files
    cp -r ../../template/repo_utilities/* repo_utilities/
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
cp template/repo_utilities/render_pdf.sh project/repo_utilities/

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
./run-all-projects.sh "./repo_utilities/render_pdf.sh"

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
- repo_utilities/render_pdf.sh - Added custom validation step

## Additional Dependencies
- scipy>=1.10 - For advanced analysis
```

### Template Compatibility

**Ensure customizations remain compatible:**
```bash
# Before template updates
git diff template-repo/repo_utilities/render_pdf.sh \
          repo_utilities/render_pdf.sh

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

# Customize
./repo_utilities/rename_project.sh

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
    ./repo_utilities/render_pdf.sh || echo "$project failed"
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

## Automation Scripts

### Project Initialization

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
    cp "$TEMPLATE_DIR/repo_utilities/render_pdf.sh" repo_utilities/
    
    # Test
    ./repo_utilities/render_pdf.sh || echo "Failed: $project"
    
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

For more information, see:
- [Getting Started](GETTING_STARTED.md) - Project setup
- [Architecture](ARCHITECTURE.md) - Understanding structure
- [Best Practices](BEST_PRACTICES.md) - General practices

---

**Related Documentation:**
- [Getting Started](GETTING_STARTED.md) - Setting up projects
- [Architecture](ARCHITECTURE.md) - Project structure
- [Best Practices](BEST_PRACTICES.md) - Management practices

