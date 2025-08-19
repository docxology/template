# Repository Utilities

This directory contains essential utilities for managing the research project repository.

## Scripts Overview

### Core Utilities

- **`clean_output.sh`** - Cleans all generated output directories
- **`render_pdf.sh`** - Complete PDF generation pipeline with IDE compatibility
- **`rename_project.sh`** - Renames the project and updates all references
- **`generate_glossary.py`** - Generates API glossary from source code
- **`validate_markdown.py`** - Validates markdown files for issues
- **`open_manuscript.sh`** - Opens different manuscript versions for viewing

### New: IDE-Friendly Manuscript Generation

The `render_pdf.sh` script now generates multiple manuscript versions optimized for different viewing contexts:

#### 📖 Standard PDF Version
- **File**: `output/pdf/project_combined.pdf`
- **Use case**: Professional printing, formal viewing
- **Features**: High-quality LaTeX rendering, proper fonts, professional layout

#### 🖥️ HTML Version (Recommended for IDEs)
- **File**: `output/project_combined.html`
- **Use case**: IDE viewing, web browsers, mobile devices
- **Features**: 
  - Responsive design with custom CSS
  - Better text rendering in IDEs
  - Faster loading than PDFs
  - Works in all modern browsers
  - Custom styling for code blocks and tables

#### 💻 IDE-Friendly PDF Version
- **File**: `output/pdf/project_combined_ide_friendly.pdf`
- **Use case**: PDF viewers that struggle with complex LaTeX
- **Features**: Simplified fonts, better compatibility, black links

#### 🌐 Web-Optimized PDF Version
- **File**: `output/pdf/project_combined_web.pdf`
- **Use case**: Web viewing, mobile devices
- **Features**: Optimized for screen viewing, larger fonts

## Quick Start

### Generate All Manuscript Versions
```bash
./repo_utilities/render_pdf.sh
```

### Open Specific Manuscript Version
```bash
# Open HTML version (best for IDEs)
./repo_utilities/open_manuscript.sh html

# Open standard PDF
./repo_utility/open_manuscript.sh pdf

# Open IDE-friendly version
./repo_utilities/open_manuscript.sh ide

# List all available versions
./repo_utilities/open_manuscript.sh list
```

## IDE Compatibility Solutions

### Problem: PDFs Don't Render Well in IDEs
Many IDEs and text editors struggle with complex PDF rendering, especially those with:
- Custom fonts
- Complex mathematical equations
- Embedded graphics
- Advanced LaTeX features

### Solution: Multiple Output Formats
1. **HTML Version**: Guaranteed to work in all IDEs and browsers (now with embedded resources!)
2. **IDE-Friendly PDF**: Simplified LaTeX with better compatibility
3. **Standard PDF**: Professional quality for printing and formal use

### New in Pandoc 3.1.9+
- **`--embed-resources`**: Automatically embeds images and other resources
- **`--self-contained`**: Creates completely standalone HTML files
- **Better LaTeX to HTML conversion**: Improved handling of `\includegraphics` commands
- **Enhanced image support**: Automatic path resolution and embedding

### CSS Styling
The HTML version includes custom CSS (`ide_style.css`) with:
- Professional typography
- Responsive design
- Syntax highlighting for code
- Clean table formatting
- Optimized for screen reading

## Technical Details

### Font Improvements
- **Standard**: Liberation Serif (better than DejaVu for IDEs)
- **Monospace**: Liberation Mono for code blocks
- **Fallbacks**: System fonts for maximum compatibility

### Rendering Engine
- **Standard**: XeLaTeX for professional quality
- **IDE-Friendly**: XeLaTeX with simplified settings
- **HTML**: Pandoc 3.1.9+ with custom CSS and embedded resources

### File Sizes
- **Standard PDF**: ~500KB (full features)
- **HTML**: ~45KB (fast loading)
- **IDE-Friendly**: ~400KB (simplified)

## Troubleshooting

### IDE-Friendly PDF Generation Fails
- Ensure `pdflatex` is installed: `sudo apt-get install texlive-latex-base`
- Check for missing LaTeX packages
- Use HTML version as fallback

### HTML Version Issues
- Verify CSS file exists: `repo_utilities/ide_style.css`
- Check browser console for errors
- Ensure images are in correct paths

### General Issues
- Run `./repo_utilities/clean_output.sh` to reset
- Check dependencies: `./repo_utilities/render_pdf.sh` (will show missing tools)
- Verify markdown files are valid: `./repo_utilities/validate_markdown.py`

## Best Practices

1. **For Development**: Use HTML version in IDEs
2. **For Review**: Use standard PDF
3. **For Sharing**: Use web-optimized PDF
4. **For Printing**: Use standard PDF

## Future Enhancements

- [ ] EPUB generation for e-readers
- [ ] Markdown preview in IDEs
- [ ] Real-time validation
- [ ] Custom theme support
- [ ] Mobile-optimized layouts
