# Build Tools Troubleshooting

> **Solutions** for pandoc, LaTeX, and PDF generation issues

**Quick Reference:** [Main Troubleshooting](README.md) | [Environment](environment-setup.md) | [Pipeline Orchestration](../../RUN_GUIDE.md)

---

## Build Tool Availability

### Missing pandoc or xelatex

**Symptom:**

```text
'pandoc' not found (Document conversion)
'xelatex' not found (LaTeX compilation)
```

**Solution - Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu
```

**Solution - macOS (BasicTeX - ~100MB):**

```bash
brew install pandoc
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar
```

**Solution - macOS (MacTeX - ~4GB):**

```bash
brew install pandoc
brew install --cask mactex
```

**PATH Setup (macOS):**

```bash
export PATH="/Library/TeX/texbin:$PATH"
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## LaTeX Compilation Errors

### Missing LaTeX Packages

**Symptom:** `LaTeX Error: File '*.sty' not found`

**Solution:**

```bash
# Check which packages are missing
uv run python scripts/03_render_pdf.py --project project 2>&1 | grep "File.*not found"

# Install missing packages
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar bm subcaption
```

---

### Document Structure Errors

**Symptom:** `*** (job aborted, no legal \end found)`

**Diagnosis:**

```bash
# Check LaTeX log (use your project name)
tail -20 projects/{name}/output/pdf/_combined_manuscript.log

# Common causes:
# - Missing \end{document}
# - Unmatched \begin{}/\end{} pairs
# - Malformed figure environments

# Check generated LaTeX file
head -50 projects/{name}/output/pdf/_combined_manuscript.tex
tail -20 projects/{name}/output/pdf/_combined_manuscript.tex
```

---

### Figure Path Issues

**Symptom:** Figures not appearing in PDF or `Figure file not found`

**Diagnosis:**

```bash
# Verify figures exist
ls -la projects/{name}/output/figures/

# Check figure references
grep "includegraphics" projects/{name}/output/pdf/_combined_manuscript.tex | head -5

# Check LaTeX log for graphics errors
tail -150 projects/{name}/output/pdf/_combined_manuscript.log | grep -A2 -B2 "graphics\|Error"
```

**Solutions:**

1. Generate missing figures: `uv run python scripts/02_run_analysis.py`
2. Verify graphicx package: `grep "usepackage{graphicx}" projects/{name}/output/pdf/_combined_manuscript.tex`
3. Fix figure paths: `sed -i 's|{figures/|{../output/figures/|g' projects/{name}/manuscript/*.md`
4. Run full rebuild: `uv run python scripts/execute_pipeline.py --project {name} --core-only --clean`

---

### Empty PDF Generation

**Symptom:** 0.0 KB PDFs generated

**Diagnosis:**

```bash
ls -lh projects/{name}/output/pdf/*.pdf | grep "0.0"
grep "Fatal error" projects/{name}/output/pdf/_combined_manuscript.log
grep "Emergency stop" projects/{name}/output/pdf/_combined_manuscript.log
```

---

## Title Page Issues

### Title Page Not Appearing

**Symptom:** PDF renders but title page missing

**Solution:** Create/verify `projects/{name}/manuscript/config.yaml`:

```yaml
paper:
  title: "Your Paper Title"
  subtitle: ""
  date: ""

authors:
  - name: "Dr. Your Name"
    email: "your@email.edu"
    affiliation: "Your Institution"
    corresponding: true
```

---

## Pandoc Issues

### Pandoc Conversion Failed

**Diagnosis:**

```bash
pandoc --version
pandoc input.md -o output.pdf --verbose
```

---

## Expected Warnings (Safe to Ignore)

### BibTeX `openout_any = p`

```text
Warning: Can't open "..." for writing. (openout_any = p)
```

This is normal - BibTeX security configuration.

### LaTeX Rerun Suggestions

```text
Rerun to get cross-references right
```

Normal - pipeline handles this automatically.

### pypdf Warnings

```text
Ignoring wrong pointing object 0 0 (offset 0)
```

Normal - pypdf gracefully handles malformed PDF objects.

---

## Cross-Reference Issues

### References Show ?? in PDF

**Symptom:** Section/figure/equation references display as `??`

**Diagnosis:**

```bash
# Check labels exist
grep -r "\\label{" projects/<name>/manuscript/

grep -r "\\ref{" projects/<name>/manuscript/
```

**Solutions:**

1. Ensure label defined: `\label{sec:name}` after section heading
2. Check reference matches: `\ref{sec:name}` matches label
3. Rebuild (multiple passes needed): `uv run python scripts/execute_pipeline.py --project {name} --core-only`

---

**Related:** [Environment Setup](environment-setup.md) | [Common Errors](common-errors.md) | [Main Guide](README.md)
