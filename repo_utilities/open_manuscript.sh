#!/bin/bash

# Manuscript Viewer - Opens different versions of the manuscript
# Usage: ./open_manuscript.sh [version]
# Versions: pdf, html, ide (default: pdf)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/output"
PDF_DIR="$OUTPUT_DIR/pdf"

# Default version
VERSION="${1:-pdf}"

# Function to detect available applications
detect_app() {
    local app_type="$1"
    
    case "$app_type" in
        "browser")
            if command -v xdg-open >/dev/null 2>&1; then
                echo "xdg-open"
            elif command -v firefox >/dev/null 2>&1; then
                echo "firefox"
            elif command -v google-chrome >/dev/null 2>&1; then
                echo "google-chrome"
            else
                echo "xdg-open"
            fi
            ;;
        "pdf")
            if command -v xdg-open >/dev/null 2>&1; then
                echo "xdg-open"
            elif command -v evince >/dev/null 2>&1; then
                echo "evince"
            elif command -v okular >/dev/null 2>&1; then
                echo "okular"
            else
                echo "xdg-open"
            fi
            ;;
    esac
}

# Function to open file
open_file() {
    local file_path="$1"
    local app_type="$2"
    
    if [ ! -f "$file_path" ]; then
        echo "❌ File not found: $file_path"
        return 1
    fi
    
    local app=$(detect_app "$app_type")
    echo "🚀 Opening $file_path with $app..."
    
    case "$app" in
        "xdg-open")
            xdg-open "$file_path"
            ;;
        "firefox"|"google-chrome")
            "$app" "$file_path"
            ;;
        "evince"|"okular")
            "$app" "$file_path" &
            ;;
        *)
            xdg-open "$file_path"
            ;;
    esac
}

# Main logic
case "$VERSION" in
    "pdf"|"standard")
        echo "📖 Opening standard PDF version..."
        open_file "$PDF_DIR/project_combined.pdf" "pdf"
        ;;
    "html"|"web")
        echo "🖥️  Opening HTML version (best for IDEs)..."
        open_file "$OUTPUT_DIR/project_combined.html" "browser"
        ;;
    "ide")
        echo "💻 Opening IDE-friendly version..."
        if [ -f "$PDF_DIR/project_combined_ide_friendly.pdf" ]; then
            open_file "$PDF_DIR/project_combined_ide_friendly.pdf" "pdf"
        else
            echo "⚠️  IDE-friendly PDF not found, opening HTML version instead..."
            open_file "$OUTPUT_DIR/project_combined.html" "browser"
        fi
        ;;
    "list"|"ls")
        echo "📚 Available manuscript versions:"
        echo ""
        echo "📖 Standard PDF: $PDF_DIR/project_combined.pdf"
        if [ -f "$PDF_DIR/project_combined_ide_friendly.pdf" ]; then
            echo "💻 IDE-friendly PDF: $PDF_DIR/project_combined_ide_friendly.pdf"
        fi
        if [ -f "$PDF_DIR/project_combined_web.pdf" ]; then
            echo "🌐 Web-optimized PDF: $PDF_DIR/project_combined_web.pdf"
        fi
        echo "🖥️  HTML version: $OUTPUT_DIR/project_combined.html"
        echo ""
        echo "💡 Usage: ./open_manuscript.sh [pdf|html|ide|list]"
        echo "   - pdf/html: Open specific version"
        echo "   - ide: Open IDE-friendly version (falls back to HTML)"
        echo "   - list: Show all available versions"
        ;;
    *)
        echo "❌ Unknown version: $VERSION"
        echo ""
        echo "Available versions:"
        echo "  pdf    - Standard PDF (default)"
        echo "  html   - HTML version (best for IDEs)"
        echo "  ide    - IDE-friendly version"
        echo "  list   - Show all available versions"
        echo ""
        echo "Usage: ./open_manuscript.sh [version]"
        exit 1
        ;;
esac

echo "✅ Manuscript opened successfully!"
