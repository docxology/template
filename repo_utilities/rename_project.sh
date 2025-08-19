#!/bin/bash

# Project Renaming Script
# Transforms the generic template into a specific project by updating:
# - Configuration files (pyproject.toml, .coveragerc, etc.)
# - Folder names and paths
# - Content references and placeholders
# - README and documentation

set -euo pipefail

# =============================================================================
# CONFIGURATION SECTION - EDIT THESE VALUES FOR YOUR PROJECT
# =============================================================================

# Project Identity
PROJECT_NAME="my-awesome-project"           # Lowercase, kebab-case for URLs
PROJECT_CALLSIGN="MAP"                      # Short acronym/identifier
PROJECT_DESCRIPTION="A revolutionary system for solving complex problems"  # One-line description

# Author Information
AUTHOR_NAME="Dr. Jane Smith"
AUTHOR_ORCID="0000-0000-0000-0000"
AUTHOR_EMAIL="jane.smith@university.edu"
DOI="10.5281/zenodo.12345678"              # Leave empty if not published yet

# Technical Details
PYTHON_VERSION=">=3.10"                     # Minimum Python version
LICENSE="MIT"                               # License type (MIT, Apache-2.0, GPL-3.0, etc.)

# =============================================================================
# SCRIPT LOGIC - DO NOT EDIT BELOW THIS LINE
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get current directory (should be project root)
CURRENT_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info "Starting project renaming process..."
log_info "Current directory: $CURRENT_DIR"
log_info "Project root: $PROJECT_ROOT"
log_info "New project name: $PROJECT_NAME"
log_info "New callsign: $PROJECT_CALLSIGN"

# Validate we're in the right place
if [ ! -f "$PROJECT_ROOT/repo_utilities/rename_project.sh" ]; then
    log_error "This script must be run from the project root directory"
    exit 1
fi

# Check if we're already renamed
if [ "$(basename "$PROJECT_ROOT")" != "project_name" ]; then
    log_warning "This project appears to have already been renamed from 'project_name'"
    log_warning "Current name: $(basename "$PROJECT_ROOT")"
    log_warning "Proceeding with content updates only..."
fi

# =============================================================================
# UPDATE CONFIGURATION FILES
# =============================================================================

log_info "Updating configuration files..."

# Update pyproject.toml
if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    log_info "Updating pyproject.toml..."
    sed -i.bak \
        -e "s/name = \"generic-project-template\"/name = \"$PROJECT_NAME\"/" \
        -e "s/description = \"Generic template for tested code, manuscript editing, and PDF rendering\"/description = \"$PROJECT_DESCRIPTION\"/" \
        -e "s/authors = \[{ name = \"Generic Project Template\" }\]/authors = [{ name = \"$AUTHOR_NAME\" }]/" \
        -e "s/requires-python = \">=3.10\"/requires-python = \"$PYTHON_VERSION\"/" \
        "$PROJECT_ROOT/pyproject.toml"
    rm -f "$PROJECT_ROOT/pyproject.toml.bak"
    log_success "Updated pyproject.toml"
fi

# Update .coveragerc
if [ -f "$PROJECT_ROOT/.coveragerc" ]; then
    log_info "Updating .coveragerc..."
    sed -i.bak \
        -e "s/source = src/source = src/" \
        "$PROJECT_ROOT/.coveragerc"
    rm -f "$PROJECT_ROOT/.coveragerc.bak"
    log_success "Updated .coveragerc"
fi

# Update .cursorrules if it exists
if [ -f "$PROJECT_ROOT/.cursorrules" ]; then
    log_info "Updating .cursorrules..."
    sed -i.bak \
        -e "s/Generic Project Template/$PROJECT_NAME/g" \
        -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
        "$PROJECT_ROOT/.cursorrules"
    rm -f "$PROJECT_ROOT/.cursorrules.bak"
    log_success "Updated .cursorrules"
fi

# =============================================================================
# UPDATE README AND DOCUMENTATION
# =============================================================================

log_info "Updating documentation files..."

# Update main README.md
if [ -f "$PROJECT_ROOT/README.md" ]; then
    log_info "Updating README.md..."
    sed -i.bak \
        -e "s/# Generic Project Template/# $PROJECT_NAME/" \
        -e "s/A generic, reusable template for tested code, manuscript editing, and PDF rendering./$PROJECT_DESCRIPTION/" \
        -e "s/Generic Project Template/$PROJECT_NAME/g" \
        -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
        -e "s/Generic Project Author/$AUTHOR_NAME/g" \
        -e "s/author@example.com/$AUTHOR_EMAIL/g" \
        -e "s/0000-0000-0000-0000/$AUTHOR_ORCID/g" \
        -e "s/Project Title/$PROJECT_NAME/g" \
        "$PROJECT_ROOT/README.md"
    rm -f "$PROJECT_ROOT/README.md.bak"
    log_success "Updated README.md"
fi

# Update repo_utilities README.md
if [ -f "$PROJECT_ROOT/repo_utilities/README.md" ]; then
    log_info "Updating repo_utilities/README.md..."
    sed -i.bak \
        -e "s/Generic Project Template/$PROJECT_NAME/g" \
        -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
        "$PROJECT_ROOT/repo_utilities/README.md"
    rm -f "$PROJECT_ROOT/repo_utilities/README.md.bak"
    log_success "Updated repo_utilities/README.md"
fi

# =============================================================================
# UPDATE MARKDOWN CONTENT
# =============================================================================

log_info "Updating markdown content..."

# Update markdown files
if [ -d "$PROJECT_ROOT/markdown" ]; then
    for md_file in "$PROJECT_ROOT/markdown"/*.md; do
        if [ -f "$md_file" ]; then
            log_info "Updating $(basename "$md_file")..."
            sed -i.bak \
                -e "s/Generic Project Template/$PROJECT_NAME/g" \
                -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
                -e "s/Project Author/$AUTHOR_NAME/g" \
                -e "s/author@example.com/$AUTHOR_EMAIL/g" \
                -e "s/0000-0000-0000-0000/$AUTHOR_ORCID/g" \
                -e "s/Project Title/$PROJECT_NAME/g" \
                "$md_file"
            rm -f "$md_file.bak"
        fi
    done
    log_success "Updated all markdown files"
fi

# =============================================================================
# UPDATE PYTHON FILES
# =============================================================================

log_info "Updating Python files..."

# Update Python files in src/
if [ -d "$PROJECT_ROOT/src" ]; then
    find "$PROJECT_ROOT/src" -name "*.py" -type f | while read -r py_file; do
        log_info "Updating $(basename "$py_file")..."
        sed -i.bak \
            -e "s/Generic Project Template/$PROJECT_NAME/g" \
            -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
            "$py_file"
        rm -f "$py_file.bak"
    done
    log_success "Updated Python files in src/"
fi

# Update Python files in tests/
if [ -d "$PROJECT_ROOT/tests" ]; then
    find "$PROJECT_ROOT/tests" -name "*.py" -type f | while read -r py_file; do
        log_info "Updating $(basename "$py_file")..."
        sed -i.bak \
            -e "s/Generic Project Template/$PROJECT_NAME/g" \
            -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
            "$py_file"
        rm -f "$py_file.bak"
    done
    log_success "Updated Python files in tests/"
fi

# =============================================================================
# UPDATE SCRIPTS
# =============================================================================

log_info "Updating script files..."

# Update Python scripts
if [ -d "$PROJECT_ROOT/scripts" ]; then
    find "$PROJECT_ROOT/scripts" -name "*.py" -type f | while read -r py_file; do
        log_info "Updating $(basename "$py_file")..."
        sed -i.bak \
            -e "s/Generic Project Template/$PROJECT_NAME/g" \
            -e "s/generic project template/$PROJECT_DESCRIPTION/g" \
            "$py_file"
        rm -f "$py_file.bak"
    done
    log_success "Updated Python scripts"
fi

# =============================================================================
# UPDATE ENVIRONMENT VARIABLES IN SCRIPTS
# =============================================================================

log_info "Setting default environment variables in scripts..."

# Update render_pdf.sh with new defaults
if [ -f "$PROJECT_ROOT/repo_utilities/render_pdf.sh" ]; then
    log_info "Updating render_pdf.sh defaults..."
    sed -i.bak \
        -e "s/AUTHOR_NAME=\"\${AUTHOR_NAME:-Project Author}\"/AUTHOR_NAME=\"\${AUTHOR_NAME:-$AUTHOR_NAME}\"/" \
        -e "s/AUTHOR_ORCID=\"\${AUTHOR_ORCID:-0000-0000-0000-0000}\"/AUTHOR_ORCID=\"\${AUTHOR_ORCID:-$AUTHOR_ORCID}\"/" \
        -e "s/AUTHOR_EMAIL=\"\${AUTHOR_EMAIL:-author@example.com}\"/AUTHOR_EMAIL=\"\${AUTHOR_EMAIL:-$AUTHOR_EMAIL}\"/" \
        -e "s|DOI=\"\${DOI:-}\"|DOI=\"\${DOI:-$DOI}\"|" \
        -e "s/PROJECT_TITLE=\"\${PROJECT_TITLE:-Project Title}\"/PROJECT_TITLE=\"\${PROJECT_TITLE:-$PROJECT_NAME}\"/" \
        "$PROJECT_ROOT/repo_utilities/render_pdf.sh"
    rm -f "$PROJECT_ROOT/repo_utilities/render_pdf.sh.bak"
    log_success "Updated render_pdf.sh defaults"
fi

# =============================================================================
# CREATE PROJECT-SPECIFIC FILES
# =============================================================================

log_info "Creating project-specific files..."

# Create a project configuration file
cat > "$PROJECT_ROOT/.project_config" << EOF
# Project Configuration
# Generated by rename_project.sh on $(date)

PROJECT_NAME="$PROJECT_NAME"
PROJECT_CALLSIGN="$PROJECT_CALLSIGN"
PROJECT_DESCRIPTION="$PROJECT_DESCRIPTION"
AUTHOR_NAME="$AUTHOR_NAME"
AUTHOR_ORCID="$AUTHOR_ORCID"
AUTHOR_EMAIL="$AUTHOR_EMAIL"
DOI="$DOI"
PYTHON_VERSION="$PYTHON_VERSION"
LICENSE="$LICENSE"

# Usage:
# source .project_config
# echo "Working on \$PROJECT_NAME"
EOF

log_success "Created .project_config"

# Create a project-specific .env template
cat > "$PROJECT_ROOT/.env.template" << EOF
# Environment variables for $PROJECT_NAME
# Copy this to .env and edit as needed

# Project metadata (can override defaults from rename_project.sh)
AUTHOR_NAME="$AUTHOR_NAME"
AUTHOR_ORCID="$AUTHOR_ORCID"
AUTHOR_EMAIL="$AUTHOR_EMAIL"
DOI="$DOI"
PROJECT_TITLE="$PROJECT_NAME"

# Development settings
LOG_LEVEL=1
MPLBACKEND=Agg
EOF

log_success "Created .env.template"

# =============================================================================
# UPDATE GIT CONFIGURATION
# =============================================================================

log_info "Updating Git configuration..."

# Update .gitignore if it exists
if [ -f "$PROJECT_ROOT/.gitignore" ]; then
    log_info "Updating .gitignore..."
    # Add project-specific entries
    if ! grep -q ".project_config" "$PROJECT_ROOT/.gitignore"; then
        echo "" >> "$PROJECT_ROOT/.gitignore"
        echo "# Project-specific files" >> "$PROJECT_ROOT/.gitignore"
        echo ".project_config" >> "$PROJECT_ROOT/.gitignore"
        echo ".env" >> "$PROJECT_ROOT/.gitignore"
    fi
    log_success "Updated .gitignore"
fi

# =============================================================================
# FINAL STEPS AND INSTRUCTIONS
# =============================================================================

log_success "Project renaming completed successfully!"
echo ""
echo "🎉 Your project has been renamed to: $PROJECT_NAME"
echo ""
echo "📋 Next steps:"
echo "1. Review the changes in the files above"
echo "2. Update any remaining project-specific content manually"
echo "3. Test the build process:"
echo "   ./repo_utilities/clean_output.sh"
echo "   ./repo_utilities/render_pdf.sh"
echo ""
echo "🔧 Configuration:"
echo "   - Project config: .project_config"
echo "   - Environment template: .env.template"
echo "   - Default author info set in render_pdf.sh"
echo ""
echo "📚 Documentation updated:"
echo "   - README.md"
echo "   - All markdown files in markdown/"
echo "   - Python files in src/ and tests/"
echo ""
echo "💡 To customize further:"
echo "   - Edit .project_config for project details"
echo "   - Copy .env.template to .env and modify"
echo "   - Update specific content in markdown files"
echo ""
echo "🚀 Happy coding with $PROJECT_NAME!"
