# 📋 Common Workflows

> **Step-by-step recipes** for common tasks

**New to the template?** Start with **[Quick Start Cheatsheet](QUICK_START_CHEATSHEET.md)** | **[Getting Started](GETTING_STARTED.md)**

## 🎯 "I Want To..." Quick Index

- [Write my first document](#write-my-first-document)
- [Add a new section to manuscript](#add-a-new-section-to-manuscript)
- [Create a figure with data](#create-a-figure-with-data)
- [Add mathematical equations](#add-mathematical-equations)
- [Cross-reference sections and figures](#cross-reference-sections-and-figures)
- [Add a new Python module](#add-a-new-python-module)
- [Write tests for my code](#write-tests-for-my-code)
- [Debug test failures](#debug-test-failures)
- [Fix coverage below 100%](#fix-coverage-below-100)
- [Generate PDF of manuscript](#generate-pdf-of-manuscript)
- [Customize project metadata](#customize-project-metadata)
- [Add supplemental materials](#add-supplemental-materials)
- [Contribute to the template](#contribute-to-the-template)

---

## Write My First Document

**Goal**: Create your first professional document from scratch

**Prerequisites**: Template cloned and dependencies installed

**Steps**:

1. **Edit the abstract**
   ```bash
   vim manuscript/01_abstract.md
   ```

2. **Add your content**
   ```markdown
   # Abstract {#sec:abstract}
   
   Your research summary goes here. Keep it concise (150-250 words).
   ```

3. **Generate the PDF**
   ```bash
   ./repo_utilities/clean_output.sh
   ./repo_utilities/render_pdf.sh
   ```

4. **View the result**
   ```bash
   open output/pdf/01_abstract.pdf
   ```

**Expected Result**: Professional PDF with your content formatted

**Next Steps**: Read [Getting Started Guide](GETTING_STARTED.md) for more details

---

## Add a New Section to Manuscript

**Goal**: Add a new numbered section to your manuscript

**Prerequisites**: Basic understanding of markdown

**Steps**:

1. **Determine section number**
   - Main sections: 01-09 (e.g., `07_limitations.md`)
   - Supplemental: S01-S99 (e.g., `S03_additional_data.md`)
   - See [Manuscript Numbering](MANUSCRIPT_NUMBERING_SYSTEM.md)

2. **Create the file**
   ```bash
   vim manuscript/07_limitations.md
   ```

3. **Add section header with label**
   ```markdown
   # Limitations {#sec:limitations}
   
   ## Study Limitations
   
   This research has several limitations...
   ```

4. **Rebuild manuscript**
   ```bash
   ./repo_utilities/render_pdf.sh
   ```

5. **Reference from other sections**
   ```markdown
   See Section \ref{sec:limitations} for discussion of constraints.
   ```

**Expected Result**: New section appears in correct order in combined PDF

**Troubleshooting**: 
- Section not appearing? Check filename starts with number/S-number
- Wrong order? See [Manuscript Numbering](MANUSCRIPT_NUMBERING_SYSTEM.md)

---

## Create a Figure with Data

**Goal**: Generate a figure from data using the thin orchestrator pattern

**Prerequisites**: Understanding of Python and matplotlib

**Steps**:

1. **Create business logic in `src/`**
   ```bash
   vim src/data_analysis.py
   ```
   
   ```python
   def analyze_data(values):
       """Analyze data and return statistics."""
       return {
           'mean': sum(values) / len(values),
           'max': max(values),
           'min': min(values)
       }
   ```

2. **Create tests (100% coverage required)**
   ```bash
   vim tests/test_data_analysis.py
   ```
   
   ```python
   from data_analysis import analyze_data
   
   def test_analyze_data():
       result = analyze_data([1, 2, 3, 4, 5])
       assert result['mean'] == 3.0
       assert result['max'] == 5
       assert result['min'] == 1
   ```

3. **Run tests**
   ```bash
   pytest tests/test_data_analysis.py --cov=src.data_analysis
   ```

4. **Create thin orchestrator script**
   ```bash
   vim scripts/my_analysis_figure.py
   ```
   
   ```python
   #!/usr/bin/env python3
   import os
   import matplotlib.pyplot as plt
   from data_analysis import analyze_data  # Import from src/
   
   # Use src/ method for computation
   data = [1, 2, 3, 4, 5]
   stats = analyze_data(data)
   
   # Script handles visualization only
   fig, ax = plt.subplots()
   ax.bar(['Mean', 'Max', 'Min'], 
          [stats['mean'], stats['max'], stats['min']])
   ax.set_title('Data Analysis')
   
   # Save to output
   output_path = 'output/figures/my_analysis.png'
   os.makedirs(os.path.dirname(output_path), exist_ok=True)
   fig.savefig(output_path)
   print(output_path)  # Print for manifest
   ```

5. **Run script**
   ```bash
   python3 scripts/my_analysis_figure.py
   ```

6. **Add to manuscript**
   ```markdown
   \begin{figure}[h]
   \centering
   \includegraphics[width=0.8\textwidth]{../output/figures/my_analysis.png}
   \caption{Statistical analysis of dataset}
   \label{fig:my_analysis}
   \end{figure}
   ```

**Expected Result**: Figure appears in manuscript with professional formatting

**Key Principle**: Business logic in `src/`, visualization in `scripts/`

**See Also**: [Thin Orchestrator Pattern](THIN_ORCHESTRATOR_SUMMARY.md)

---

## Add Mathematical Equations

**Goal**: Add numbered equations with cross-references

**Prerequisites**: Basic LaTeX knowledge

**Steps**:

1. **Write equation with label**
   ```markdown
   \begin{equation}\label{eq:quadratic}
   f(x) = ax^2 + bx + c
   \end{equation}
   ```

2. **Reference equation in text**
   ```markdown
   The quadratic function \eqref{eq:quadratic} has two solutions.
   ```

3. **For multiple equations**
   ```markdown
   \begin{align}
   f(x) &= x^2 + 2x + 1 \label{eq:first} \\
   g(x) &= x^3 - x \label{eq:second}
   \end{align}
   
   Equations \eqref{eq:first} and \eqref{eq:second} are related.
   ```

4. **Rebuild**
   ```bash
   ./repo_utilities/render_pdf.sh
   ```

**Expected Result**: Numbered equations with clickable references

**Troubleshooting**:
- Equation shows (??) → Check label spelling
- Numbering wrong → Ensure unique labels
- Not rendering → Check LaTeX syntax

**See Also**: [Markdown Template Guide](MARKDOWN_TEMPLATE_GUIDE.md)

---

## Cross-Reference Sections and Figures

**Goal**: Create internal links between document parts

**Prerequisites**: Basic markdown understanding

**Types of References**:

### Section References
```markdown
# Methodology {#sec:methodology}

As described in Section \ref{sec:methodology}...
```

### Equation References
```markdown
\begin{equation}\label{eq:important}
E = mc^2
\end{equation}

From Equation \eqref{eq:important}, we see...
```

### Figure References
```markdown
\begin{figure}[h]
\centering
\includegraphics{../output/figures/plot.png}
\caption{Results}
\label{fig:results}
\end{figure}

Figure \ref{fig:results} shows...
```

### Table References
```markdown
\begin{table}[h]
\caption{Performance metrics}
\label{tab:performance}
...
\end{table}

Table \ref{tab:performance} summarizes...
```

**Validation**:
```bash
python3 repo_utilities/validate_markdown.py
```

**See Also**: [Markdown Template Guide](MARKDOWN_TEMPLATE_GUIDE.md)

---

## Add a New Python Module

**Goal**: Add new functionality following the thin orchestrator pattern

**Prerequisites**: Python programming knowledge

**Steps**:

1. **Create module in `src/`**
   ```bash
   vim src/statistics.py
   ```
   
   ```python
   """Statistical analysis functions."""
   
   def calculate_variance(values):
       """Calculate sample variance."""
       mean = sum(values) / len(values)
       return sum((x - mean) ** 2 for x in values) / (len(values) - 1)
   
   def calculate_std_dev(values):
       """Calculate standard deviation."""
       return calculate_variance(values) ** 0.5
   ```

2. **Create comprehensive tests**
   ```bash
   vim tests/test_statistics.py
   ```
   
   ```python
   from statistics import calculate_variance, calculate_std_dev
   
   def test_calculate_variance():
       values = [1, 2, 3, 4, 5]
       var = calculate_variance(values)
       assert abs(var - 2.5) < 1e-10
   
   def test_calculate_std_dev():
       values = [1, 2, 3, 4, 5]
       std = calculate_std_dev(values)
       assert abs(std - 1.5811388) < 1e-6
   ```

3. **Ensure 100% coverage**
   ```bash
   pytest tests/test_statistics.py --cov=src.statistics --cov-report=term-missing
   ```

4. **Use in scripts (thin orchestrator)**
   ```python
   from statistics import calculate_std_dev
   
   data = [1, 2, 3, 4, 5]
   std = calculate_std_dev(data)  # Use src/ method
   # Script handles visualization...
   ```

**Expected Result**: Fully tested module ready for use

**Key Rules**:
- ALL business logic in `src/`
- 100% test coverage required
- Scripts only orchestrate, never implement algorithms

**See Also**: [Thin Orchestrator Pattern](THIN_ORCHESTRATOR_SUMMARY.md)

---

## Write Tests for My Code

**Goal**: Achieve 100% test coverage for src/ modules

**Prerequisites**: Understanding of pytest

**Steps**:

1. **Create test file**
   ```bash
   vim tests/test_my_module.py
   ```

2. **Import module to test**
   ```python
   from my_module import my_function
   ```

3. **Write test cases**
   ```python
   def test_my_function_basic():
       """Test basic functionality."""
       result = my_function([1, 2, 3])
       assert result == expected_value
   
   def test_my_function_edge_cases():
       """Test edge cases."""
       assert my_function([]) == default_value
       assert my_function([1]) == single_value
   
   def test_my_function_errors():
       """Test error handling."""
       with pytest.raises(ValueError):
           my_function(invalid_input)
   ```

4. **Run tests with coverage**
   ```bash
   pytest tests/test_my_module.py --cov=src.my_module --cov-report=term-missing
   ```

5. **Check for missing lines**
   - Lines marked with `>>>>>` are not covered
   - Add tests to cover all branches

6. **Repeat until 100%**

**Expected Result**: All code paths tested, 100% coverage achieved

**Requirements**:
- Statement coverage: 100%
- Branch coverage: 100%
- No mocks: Use real data

**See Also**: [Testing Guide](../tests/AGENTS.md) | [Workflow](WORKFLOW.md)

---

## Debug Test Failures

**Goal**: Identify and fix failing tests

**Steps**:

1. **Run tests verbosely**
   ```bash
   pytest tests/ -v
   ```

2. **Run specific test**
   ```bash
   pytest tests/test_my_module.py::test_specific_function -v
   ```

3. **Use debugger**
   ```bash
   pytest tests/test_my_module.py --pdb
   ```

4. **Check detailed output**
   ```bash
   pytest tests/ -vv --tb=long
   ```

5. **Common issues**:
   - Import errors → Check `PYTHONPATH`
   - Assertion failures → Check expected vs actual values
   - Coverage failures → Add tests for missing lines

**Troubleshooting Commands**:
```bash
# Show test discovery
pytest --collect-only

# Run with maximum verbosity
pytest -vvv

# Show local variables on failure
pytest -l

# Stop at first failure
pytest -x
```

**See Also**: [FAQ](FAQ.md#q-how-do-i-debug-test-failures)

---

## Fix Coverage Below 100%

**Goal**: Achieve required 100% test coverage

**Steps**:

1. **Generate coverage report**
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

2. **Identify missing lines**
   - Look for lines marked `>>>>>` 
   - Note which functions/branches aren't covered

3. **Analyze uncovered code**
   ```bash
   pytest tests/ --cov=src --cov-report=html
   open htmlcov/index.html
   ```

4. **Add tests for uncovered paths**
   - Test all conditional branches (if/else)
   - Test exception handling
   - Test edge cases

5. **Verify improvement**
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

**Example - Covering Conditional**:
```python
# Code with uncovered branch
def process(value):
    if value > 0:  # Covered
        return value * 2
    else:  # Not covered - need test
        return 0

# Add test for uncovered branch
def test_process_negative():
    assert process(-5) == 0
```

**Expected Result**: 100% coverage achieved

**See Also**: [Test Improvements](TEST_IMPROVEMENTS_SUMMARY.md)

---

## Generate PDF of Manuscript

**Goal**: Build professional PDF from markdown sources

**Steps**:

1. **Clean previous outputs**
   ```bash
   ./repo_utilities/clean_output.sh
   ```

2. **Run complete build**
   ```bash
   ./repo_utilities/render_pdf.sh
   ```

3. **Check for errors**
   - Tests must pass (320/322)
   - Scripts must succeed
   - Markdown validation must pass
   - PDF compilation must succeed

4. **View output**
   ```bash
   open output/pdf/project_combined.pdf
   ```

5. **Validate PDF quality**
   ```bash
   python3 repo_utilities/validate_pdf_output.py
   ```

**Build Pipeline Stages**:
1. Test validation (27s)
2. Script execution (1s)
3. Repository utilities (1s)
4. Individual PDFs (32s)
5. Combined PDF (10s)
6. Validation (1s)

**Total Time**: ~75 seconds

**Troubleshooting**:
- Tests fail → Fix coverage issues
- Scripts fail → Check imports from src/
- PDF fails → Check pandoc/xelatex installation
- References show ?? → Check label spelling

**See Also**: [Build System](BUILD_SYSTEM.md) | [PDF Validation](PDF_VALIDATION.md)

---

## Customize Project Metadata

**Goal**: Personalize project with your information

**Steps**:

1. **Set environment variables**
   ```bash
   export AUTHOR_NAME="Dr. Jane Smith"
   export AUTHOR_EMAIL="jane.smith@university.edu"
   export AUTHOR_ORCID="0000-0001-2345-6789"
   export PROJECT_TITLE="My Research Project"
   export DOI="10.5281/zenodo.12345678"  # Optional
   ```

2. **Or create `.env` file**
   ```bash
   cp .env.template .env
   vim .env
   ```
   
   Add:
   ```bash
   AUTHOR_NAME="Dr. Jane Smith"
   AUTHOR_EMAIL="jane.smith@university.edu"
   AUTHOR_ORCID="0000-0001-2345-6789"
   PROJECT_TITLE="My Research Project"
   DOI="10.5281/zenodo.12345678"
   ```

3. **Source environment**
   ```bash
   source .env
   ```

4. **Generate with custom metadata**
   ```bash
   ./repo_utilities/render_pdf.sh
   ```

**Applied To**:
- PDF metadata (title, author, date)
- LaTeX document properties
- Generated file headers
- Cross-reference systems

**See Also**: [AGENTS.md Configuration](../AGENTS.md#configuration-system)

---

## Add Supplemental Materials

**Goal**: Add supplemental sections to manuscript

**Steps**:

1. **Create supplemental file**
   ```bash
   vim manuscript/S03_supplemental_figures.md
   ```

2. **Add content**
   ```markdown
   # Supplemental Figures {#sec:supplemental_figures}
   
   ## Additional Visualizations
   
   This section contains extended visualizations...
   ```

3. **Reference from main text**
   ```markdown
   See Section \ref{sec:supplemental_figures} for additional figures.
   ```

4. **Rebuild**
   ```bash
   ./repo_utilities/render_pdf.sh
   ```

**Naming Convention**:
- Main sections: `01-09`
- Supplemental sections: `S01-S99`
- Glossary: `98`
- References: `99`

**Order in PDF**:
1. Main sections (01-09)
2. Supplemental sections (S01-S99)
3. Glossary (98)
4. References (99)

**See Also**: [Manuscript Numbering](MANUSCRIPT_NUMBERING_SYSTEM.md)

---

## Contribute to the Template

**Goal**: Improve the template for everyone

**Steps**:

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork"
   git clone https://github.com/YOUR_USERNAME/template.git
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/my-improvement
   ```

3. **Make changes**
   - Follow thin orchestrator pattern
   - Maintain 100% test coverage
   - Update documentation

4. **Run tests**
   ```bash
   pytest tests/ --cov=src --cov-report=term-missing
   ```

5. **Run complete build**
   ```bash
   ./generate_pdf_from_scratch.sh
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/my-improvement
   # On GitHub, create Pull Request
   ```

**Contribution Checklist**:
- [ ] Tests pass (320/322+)
- [ ] Coverage maintained/improved
- [ ] Documentation updated
- [ ] Thin orchestrator pattern followed
- [ ] Commit messages clear
- [ ] PR description complete

**See Also**: [Contributing Guide](CONTRIBUTING.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 🔗 Related Documentation

- **[Quick Start Cheatsheet](QUICK_START_CHEATSHEET.md)** - One-page reference
- **[Getting Started](GETTING_STARTED.md)** - Comprehensive beginner guide
- **[FAQ](FAQ.md)** - Common questions
- **[Glossary](GLOSSARY.md)** - Terms and definitions
- **[Complete Guide](HOW_TO_USE.md)** - All 12 skill levels

---

**Need more help?** Check the **[FAQ](FAQ.md)** or **[Documentation Index](DOCUMENTATION_INDEX.md)**


