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

echo "🎉 PDF regeneration complete!"
echo "📁 Check output/pdf/ for all generated files"
echo "📖 Main document: output/pdf/project_combined.pdf"
