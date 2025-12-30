# 🚀 Getting Started Guide

> **Complete beginner's guide** to using the Research Project Template

**Quick Reference:** [Cheatsheet](../reference/QUICK_START_CHEATSHEET.md) | [Common Workflows](../reference/COMMON_WORKFLOWS.md) | [FAQ](../reference/FAQ.md)

This guide covers **Levels 1-3** of the Research Project Template. Perfect for users who just want to write documents without programming.

## 📚 What You'll Learn

By the end of this guide, you'll be able to:

- ✅ Set up the template on your computer
- ✅ Write and format professional documents
- ✅ Add equations and cross-references
- ✅ Generate publication-ready PDFs
- ✅ Customize project metadata

**Estimated Time:** 2-3 hours

## 🎯 Prerequisites

- Basic computer skills
- Text editor (any will work)
- No programming knowledge required

## 📖 Table of Contents

- [Quick Start](#quick-start)
- [Level 1: Write Your First Document](#level-1-write-your-first-document)
- [Level 2: Add Equations and References](#level-2-add-equations-and-references)
- [Level 3: Basic Customization](#level-3-basic-customization)
- [What to Read Next](#what-to-read-next)

---

## Quick Start

### Step 1: Get the Template

1. **Click "Use this template"** on [GitHub](https://github.com/docxology/template)
2. **Name your repository** (e.g., "my-research-project")
3. **Clone your new repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/your-repo-name.git
   cd your-repo-name
   ```

### Step 2: Install Dependencies

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install pandoc
brew install --cask mactex

# Install Python dependencies
pip install uv
uv sync
```

**Ubuntu/Debian:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu python3-pip

# Install Python dependencies
pip3 install uv
uv sync
```

### Step 3: Generate Your First PDF

```bash
# Generate everything (runs all 6 pipeline stages)
python3 scripts/execute_pipeline.py --core-only

# Or use unified interactive menu
./run.sh

# Open the result
open output/project_combined.pdf  # macOS (top-level output/)
xdg-open output/project_combined.pdf  # Linux
```

**🎉 Success!** You should see a professional PDF document.

---

## Level 1: Write Your First Document

**Goal**: Create professional documents without programming

**Time**: 30-45 minutes

### Understanding the Manuscript Structure

The template provides pre-structured manuscript files in the `manuscript/` directory:

```
manuscript/
├── preamble.md              # LaTeX styling (don't edit yet)
├── 01_abstract.md           # Research overview
├── 02_introduction.md       # Project introduction
├── 03_methodology.md        # Methods and approach
├── 04_experimental_results.md  # Results and findings
├── 05_discussion.md         # Analysis
├── 06_conclusion.md         # Summary
└── 99_references.md         # Bibliography
```

### Edit the Abstract

1. **Open the abstract file**
   ```bash
   vim manuscript/01_abstract.md
   # Or use your preferred text editor
   ```

2. **You'll see**:
   ```markdown
   # Abstract {#sec:abstract}
   
   This template demonstrates...
   ```

3. **Replace with your content**:
   ```markdown
   # Abstract {#sec:abstract}
   
   This research investigates the impact of machine learning on climate 
   prediction accuracy. We developed a novel ensemble method combining 
   neural networks with traditional models...
   ```

4. **Save the file**

### Edit the Introduction

1. **Open the introduction**
   ```bash
   vim manuscript/02_introduction.md
   ```

2. **Add your content**:
   ```markdown
   # Introduction {#sec:introduction}
   
   ## Background
   
   Climate change poses significant challenges...
   
   ## Motivation
   
   Current prediction methods have limitations...
   
   ## Objectives
   
   This research aims to:
   1. Develop improved prediction models
   2. Validate accuracy across multiple datasets
   3. Provide actionable recommendations
   ```

3. **Save the file**

### Generate Your PDF

1. **Run complete pipeline**
   ```bash
   # Runs all 6 stages including cleanup
   python3 scripts/execute_pipeline.py --core-only
   
   # Or use unified interactive menu
   ./run.sh
   ```

3. **View the result**
   ```bash
   open output/project_combined.pdf  # Top-level output (after stage 5)
   ```

**What You Get**:
- ✅ Professional formatting
- ✅ Automatic section numbering
- ✅ Table of contents
- ✅ Proper academic style

### Edit Multiple Sections

Continue editing other sections:

- **Methodology** (`03_methodology.md`): Your research methods
- **Results** (`04_experimental_results.md`): Your findings
- **Discussion** (`05_discussion.md`): Analysis and interpretation
- **Conclusion** (`06_conclusion.md`): Summary and future work

**After each major change**, regenerate the PDF to see your progress.

---

## Level 2: Add Equations and References

**Goal**: Add mathematical equations and cross-references

**Time**: 45-60 minutes

### Adding Mathematical Equations

#### Simple Inline Math

For math within text, use dollar signs:

```markdown
The quadratic formula $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$ solves...
```

#### Numbered Equations

For important equations you'll reference later:

```markdown
\begin{equation}\label{eq:quadratic}
x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}
\end{equation}
```

**Key Parts**:
- `\begin{equation}` - Start equation
- `\label{eq:quadratic}` - Unique name for referencing
- `\end{equation}` - End equation

#### Referencing Equations

To refer to an equation elsewhere:

```markdown
Using the quadratic formula \eqref{eq:quadratic}, we can solve...
```

### Common Math Symbols

| Symbol | LaTeX | Example |
|--------|-------|---------|
| Fraction | `\frac{a}{b}` | $\frac{a}{b}$ |
| Square root | `\sqrt{x}` | $\sqrt{x}$ |
| Superscript | `x^2` | $x^2$ |
| Subscript | `x_1` | $x_1$ |
| Sum | `\sum_{i=1}^{n}` | $\sum_{i=1}^{n}$ |
| Integral | `\int_0^1` | $\int_0^1$ |
| Greek letters | `\alpha, \beta` | $\alpha, \beta$ |

### Cross-Referencing Sections

#### Add Section Labels

When creating a section heading, add a label:

```markdown
# Methodology {#sec:methodology}

## Data Collection {#sec:data_collection}
```

#### Reference Sections

To refer to a section:

```markdown
As described in Section \ref{sec:methodology}, we collected...

The data collection process (Section \ref{sec:data_collection}) involved...
```

### Adding Figures

Even though you're not generating figures yet, you can reference existing ones:

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/example_figure.png}
\caption{Example visualization showing convergence behavior}
\label{fig:example}
\end{figure}

Figure \ref{fig:example} demonstrates the algorithm's performance.
```

**Figure Anatomy**:
- `[h]` - Place here (h = here, t = top, b = bottom)
- `width=0.8\textwidth` - 80% of text width
- `caption{}` - Description below figure
- `label{}` - Unique name for referencing

### Complete Example

Here's a complete methodology section with equations and references:

```markdown
# Methodology {#sec:methodology}

## Mathematical Framework

Our approach is based on the optimization problem:

\begin{equation}\label{eq:objective}
\min_{x \in \mathbb{R}^n} f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
\end{equation}

where $w_i$ are weights and $\phi_i$ are basis functions.

## Algorithm

The iterative update follows:

\begin{equation}\label{eq:update}
x_{k+1} = x_k - \alpha_k \nabla f(x_k)
\end{equation}

As shown in Equation \eqref{eq:update}, we use gradient descent with 
step size $\alpha_k$.

## Convergence Analysis

From equations \eqref{eq:objective} and \eqref{eq:update}, we can prove 
convergence under standard assumptions (see Section \ref{sec:results}).
```

---

## Level 3: Basic Customization

**Goal**: Personalize your project

**Time**: 30-45 minutes

### Customize Project Metadata

#### Method 1: Environment Variables

```bash
# Set your information
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_EMAIL="jane.smith@university.edu"
export AUTHOR_ORCID="0000-0001-2345-6789"
export PROJECT_TITLE="Impact of Machine Learning on Climate Prediction"

# Optional: Add DOI if published
export DOI="10.5281/zenodo.12345678"

# Generate with your metadata
python3 scripts/execute_pipeline.py --core-only
```

#### Method 2: Create .env File

1. **Copy template**
   ```bash
   cp .env.template .env
   ```

2. **Edit .env**
   ```bash
   vim .env
   ```

3. **Add your information**
   ```bash
   AUTHOR_NAME="Dr. Jane Smith"
   AUTHOR_EMAIL="jane.smith@university.edu"
   AUTHOR_ORCID="0000-0001-2345-6789"
   PROJECT_TITLE="Impact of Machine Learning on Climate Prediction"
   DOI=""  # Leave empty if not published yet
   ```

4. **Source and build**
   ```bash
   source .env
   python3 scripts/execute_pipeline.py --core-only
   ```

**What Gets Updated**:
- ✅ PDF title page
- ✅ PDF metadata
- ✅ Author information
- ✅ Document properties

### Customize LaTeX Styling

**Note**: This is optional and more advanced. Skip if you're satisfied with defaults.

The template uses `manuscript/preamble.md` for styling. You can modify:

- **Colors**: Change link colors, heading colors
- **Fonts**: Modify font families and sizes
- **Spacing**: Adjust line spacing and margins
- **Headers/Footers**: Customize page headers

**Basic color customization**:

1. **Open preamble**
   ```bash
   vim manuscript/preamble.md
   ```

2. **Find color definitions** (around line 97-103):
   ```latex
   \definecolor{codebg}{RGB}{248, 248, 248}
   \definecolor{codeborder}{RGB}{200, 200, 200}
   ```

3. **Add your colors**:
   ```latex
   \definecolor{myblue}{RGB}{0, 114, 178}
   \definecolor{mygreen}{RGB}{0, 158, 115}
   ```

4. **Use in hyperlinks** (around line 54-60):
   ```latex
   \hypersetup{
       colorlinks=true,
       linkcolor=myblue,
       citecolor=mygreen,
       ...
   }
   ```

**See [project/manuscript/preamble.md](../../projects/project/manuscript/preamble.md) for the LaTeX preamble configuration.**

### Add Bibliography

1. **Edit references.bib**
   ```bash
   vim manuscript/references.bib
   ```

2. **Add entries**:
   ```bibtex
   @article{smith2020climate,
     title={Machine Learning for Climate Prediction},
     author={Smith, Jane and Doe, John},
     journal={Nature Climate Change},
     volume={10},
     pages={123--130},
     year={2020}
   }
   
   @book{jones2019ai,
     title={Artificial Intelligence in Environmental Science},
     author={Jones, Alice},
     publisher={Academic Press},
     year={2019}
   }
   ```

3. **Cite in manuscript**:
   ```markdown
   Recent advances \cite{smith2020climate} demonstrate...
   
   For comprehensive review, see \cite{jones2019ai}.
   ```

4. **Rebuild to see citations**
   ```bash
   python3 scripts/execute_pipeline.py --core-only
   ```

---

## Quick Tips

### Writing Tips

1. **Keep sections focused**: One main idea per section
2. **Use clear headings**: Help readers navigate
3. **Add labels consistently**: `{#sec:descriptive_name}`
4. **Reference liberally**: Connect ideas across sections
5. **Preview frequently**: Regenerate PDF to see changes

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| **Forgot section label** | Add `{#sec:name}` after heading |
| **Reference shows ??** | Check label spelling matches |
| **Equation not numbered** | Use `\begin{equation}...\end{equation}` |
| **Figure not found** | Check path is `../output/figures/` |
| **PDF won't build** | Run `python3 scripts/execute_pipeline.py --core-only` (includes cleanup) |

### Keyboard Shortcuts

**Most text editors**:
- Save: `Ctrl+S` (Linux/Windows) or `Cmd+S` (macOS)
- Find: `Ctrl+F` or `Cmd+F`
- Replace: `Ctrl+H` or `Cmd+Option+F`

**Vim users**:
- Save and quit: `:wq`
- Quit without saving: `:q!`
- Search: `/searchterm`

---

## Troubleshooting

### Build Fails

**Problem**: PDF generation fails

**Solutions**:
1. Check pandoc installed: `pandoc --version`
2. Check xelatex installed: `xelatex --version`
3. Clean and rebuild:
   ```bash
   python3 scripts/execute_pipeline.py --core-only
   ```

### References Show ??

**Problem**: Cross-references display as `??`

**Solutions**:
1. Check label exists: Search for `{#sec:labelname}`
2. Check spelling matches exactly
3. Rebuild (references need multiple passes):
   ```bash
   python3 scripts/execute_pipeline.py --core-only
   ```

### Math Not Rendering

**Problem**: Equations display as plain text

**Solutions**:
1. Check equation environment syntax
2. Use `\begin{equation}` not `$$`
3. Check for unescaped special characters
4. Rebuild PDF

### Can't Find File

**Problem**: Figure or reference not found

**Solutions**:
1. Check relative path: `../output/figures/name.png`
2. Verify file exists: `ls project/output/figures/`
3. Run complete pipeline (includes script execution): `python3 scripts/execute_pipeline.py --core-only`

---

## What to Read Next

### If you're ready to...

**Add your own figures and data**
→ Read **[Intermediate Usage Guide](../guides/INTERMEDIATE_USAGE.md)** (Levels 4-6)

**Learn test-driven development**
→ Read **[Advanced Usage Guide](../guides/ADVANCED_USAGE.md)** (Levels 7-9)

**Understand the system architecture**
→ Read **[Architecture Guide](../core/ARCHITECTURE.md)**

**See real-world examples**
→ Read **[Examples Showcase](../usage/EXAMPLES_SHOWCASE.md)**

**Find answers to common questions**
→ Read **[FAQ](../reference/FAQ.md)**

### Related Documentation

- **[Quick Start Cheatsheet](../reference/QUICK_START_CHEATSHEET.md)** - One-page reference
- **[Common Workflows](../reference/COMMON_WORKFLOWS.md)** - Step-by-step recipes
- **[Glossary](../reference/GLOSSARY.md)** - Terms and definitions
- **[Markdown Template Guide](../usage/MARKDOWN_TEMPLATE_GUIDE.md)** - Complete formatting reference
- **[Documentation Index](../DOCUMENTATION_INDEX.md)** - All documentation

---

## Success Checklist

After completing this guide, you should be able to:

- [x] Install the template and dependencies
- [x] Edit manuscript sections
- [x] Add mathematical equations with labels
- [x] Create cross-references between sections
- [x] Generate professional PDFs
- [x] Customize project metadata
- [x] Add bibliography entries

**Congratulations!** You've mastered the basics. Ready for more? Check out **[Intermediate Usage](../guides/INTERMEDIATE_USAGE.md)**.

---

**Need help?** Check the **[FAQ](../reference/FAQ.md)** or **[Common Workflows](../reference/COMMON_WORKFLOWS.md)**

**Quick Reference**: [Cheatsheet](../reference/QUICK_START_CHEATSHEET.md) | [Glossary](../reference/GLOSSARY.md)


