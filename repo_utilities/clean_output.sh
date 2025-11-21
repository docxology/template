#!/bin/bash

# Generic Project Output Cleanup Script
# Safely removes all generated output since everything is regenerated from markdown

set -euo pipefail
export LANG="${LANG:-C.UTF-8}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$REPO_ROOT/project"
OUTPUT_DIR="$PROJECT_DIR/output"
LATEX_DIR="$PROJECT_DIR/output/tex"

# Source unified logging library
LOGGING_SCRIPT="$REPO_ROOT/repo_utilities/logging.sh"
if [ -f "$LOGGING_SCRIPT" ]; then
    source "$LOGGING_SCRIPT"
else
    # Fallback basic logging
    log_info() { echo "[INFO] $1"; }
    log_success() { echo "✅ $1"; }
    log_warn() { echo "⚠️ $1" >&2; }
    log_header() { echo ""; echo "$1"; echo ""; }
fi

log_header "🧹 CLEANING PROJECT OUTPUT DIRECTORIES"

log_info "Repository root: $REPO_ROOT"

# Clean output directory (all disposable)
if [ -d "$OUTPUT_DIR" ]; then
    log_info "Removing output directory: $OUTPUT_DIR"
    rm -rf "$OUTPUT_DIR"
    log_success "Output directory cleaned"
else
    log_warn "Output directory not found: $OUTPUT_DIR"
fi

# Clean latex directory (all disposable)
if [ -d "$LATEX_DIR" ]; then
    log_info "Removing latex directory: $LATEX_DIR"
    rm -rf "$LATEX_DIR"
    log_success "Latex directory cleaned"
else
    log_warn "Latex directory not found: $LATEX_DIR"
fi

echo ""
log_success "All output directories cleaned!"
log_info "Run 'repo_utilities/render_pdf.sh' to regenerate everything from manuscript sources"
echo ""
log_info "Preserved directories:"
log_dim "  📁 Project:    $PROJECT_DIR/"
log_dim "  📁 Manuscript: $PROJECT_DIR/manuscript/"
log_dim "  🔧 Scripts:    $PROJECT_DIR/scripts/"
log_dim "  📚 Source:     $PROJECT_DIR/src/"
log_dim "  🧪 Tests:      $PROJECT_DIR/tests/"
