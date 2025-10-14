#!/bin/bash

# Simple PDF regeneration script
# This script clears the output folder and fully regenerates all PDFs

set -euo pipefail

echo "🚀 Starting complete PDF regeneration from scratch..."
echo

# Clean all previous outputs
echo "🧹 Step 1: Cleaning output directory..."
./repo_utilities/clean_output.sh
echo "✅ Output directory cleaned"
echo

# Generate everything fresh
echo "🔄 Step 2: Regenerating all PDFs..."
./repo_utilities/render_pdf.sh
echo

# Validate the generated PDF
echo "🔍 Step 3: Validating PDF output quality..."
uv run python repo_utilities/validate_pdf_output.py --words 200
VALIDATION_EXIT=$?
echo

# Handle validation results
if [ $VALIDATION_EXIT -eq 0 ]; then
    echo "✅ PDF validation passed - no issues detected"
elif [ $VALIDATION_EXIT -eq 1 ]; then
    echo "⚠️  PDF validation found rendering issues - see report above"
    echo "   Review and fix unresolved references or citations"
else
    echo "❌ PDF validation encountered an error"
fi
echo

echo "🎉 PDF regeneration complete!"
echo "📁 Check output/pdf/ for all generated files"
echo "📖 Main document: output/pdf/project_combined.pdf"
