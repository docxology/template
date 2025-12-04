# Project - Ways of Knowing Analysis Research Unit

## Overview

This is a complete, self-contained research project focused on the analysis of ways of knowing using Andrius Kulikauskas's philosophical framework. Everything needed for the research is in this folder:

- **src/** - Ways of knowing analysis algorithms and frameworks
- **tests/** - Comprehensive test suite (70% minimum coverage)
- **scripts/** - Analysis workflows and database setup
- **manuscript/** - Research manuscript on ways of knowing
- **docs/** - Project documentation
- **output/** - Generated results (figures, data, PDFs)

This folder can be copied as a complete unit to start new research based on ways of knowing analysis.

## Architecture

### Scientific Code (src/)

Pure Python implementations of ways of knowing analysis algorithms:

```
src/
├── database.py             # Ways database ORM and initialization
├── sql_queries.py          # SQL queries for ways data
├── models.py               # Ways data models (Way, Room, Question, Example)
├── ways_analysis.py        # Main ways analysis framework
├── house_of_knowledge.py   # House of Knowledge analysis
├── network_analysis.py     # Network analysis for ways relationships
├── statistics.py           # Ways-specific statistical analysis
└── metrics.py              # Ways coverage and balance metrics
```

**Requirements:**
- 70% minimum test coverage for project/src/ modules
- Type hints on all public APIs
- Comprehensive docstrings
- No mock testing (real data analysis only)
- Pure functions where possible

### Tests (tests/)

Comprehensive test suite validating ways of knowing analysis code:

- **70% minimum coverage required** for project/src/ modules
- **Real data testing** - Use actual ways database data, not mocks
- **Integration tests** - Test ways analysis workflow
- **Database tests** - Validate SQL queries and ORM operations

**Running tests:**
```bash
pytest tests/ --cov=src --cov-fail-under=70
pytest tests/ --cov=src --cov-report=html
```

### Scripts (scripts/)

Thin orchestrators that use ways analysis modules:

```
scripts/
└── db_setup.py             # Database initialization and setup
```

**Pattern:**
1. Import modules from src/
2. Call ways analysis functions
3. Orchestrate ways data workflows
4. Generate ways analysis outputs

### Manuscript (manuscript/)

Ways of knowing research manuscript in Markdown:

```
manuscript/
├── 01_abstract.md
├── 02_introduction.md
├── 03_methodology.md
├── 04_experimental_results.md
├── 05_discussion.md
├── 06_conclusion.md
├── 08_acknowledgments.md
├── 09_appendix.md
├── config.yaml              # Metadata
├── references.bib           # Bibliography
└── preamble.md              # LaTeX preamble
```

### Output (output/)

Generated results (disposable):

```
output/
├── figures/                 # PNG/PDF figures
├── data/                    # CSV/NPZ data files
├── pdf/                     # Generated PDFs
├── latex_temp/              # LaTeX temporary files
└── reports/                 # Generated reports
```

These files are regenerated on each build and can be deleted safely.

## Development Workflow

### 1. Extend Ways Analysis

**Step 1: Implement in src/**
```python
# src/new_ways_analysis.py
from ways_analysis import WaysAnalyzer

def analyze_ways_patterns(analyzer: WaysAnalyzer):
    """Analyze patterns in ways of knowing.

    Args:
        analyzer: Initialized WaysAnalyzer instance

    Returns:
        Pattern analysis results
    """
    characterization = analyzer.characterize_ways()
    return extract_patterns(characterization)
```

**Step 2: Add comprehensive tests**
```python
# tests/test_new_ways_analysis.py
def test_analyze_ways_patterns():
    """Test ways patterns analysis."""
    analyzer = WaysAnalyzer()
    result = analyze_ways_patterns(analyzer)
    assert result is not None
    assert 'patterns' in result
```

**Step 3: Ensure coverage requirements met**
```bash
pytest tests/test_new_ways_analysis.py --cov=src/new_ways_analysis --cov-fail-under=70
```

**Step 4: Integrate into analysis pipeline**
```python
# scripts/extended_analysis.py
from new_ways_analysis import analyze_ways_patterns
from ways_analysis import WaysAnalyzer

analyzer = WaysAnalyzer()
patterns = analyze_ways_patterns(analyzer)
save_patterns_to_file(patterns)
```

**Step 5: Document in manuscript**
```markdown
# Methodology

We extended our ways analysis using src/new_ways_analysis.py...

![Ways Patterns](../output/figures/ways_patterns.png){fig:patterns width=0.8}
```

### 2. Generate Figures

Scripts generate figures that are integrated into the manuscript:

```python
# scripts/generate_results.py
from plots import plot_convergence
from infrastructure.documentation import FigureManager

fig = plot_convergence(results)
fm = FigureManager()
fm.register_figure(
    filename="results.png",
    caption="Convergence results visualization",
    label="fig:results"
)
```

Figures are automatically referenced:
```markdown
See [Figure @fig:results] for detailed results.
```

### 3. Build Manuscript

From template root:
```bash
./repo_utilities/render_pdf.sh
```

This:
1. Runs all project tests
2. Executes all scripts
3. Generates all figures
4. Builds manuscript PDFs
5. Validates quality

## Module Guide

### Core Ways Analysis

- **ways_analysis.py** - Main ways analysis framework and characterization
- **database.py** - Ways database ORM and initialization
- **sql_queries.py** - SQL queries for ways data access
- **models.py** - Data models for Way, Room, Question, Example entities

### Specialized Analysis

- **house_of_knowledge.py** - House of Knowledge structure analysis
- **network_analysis.py** - Network relationships between ways
- **statistics.py** - Ways-specific statistical analysis and distributions
- **metrics.py** - Ways coverage, completeness, and balance metrics

## Testing

### Test Structure

```python
"""Tests for src/ways_analysis.py"""
import pytest
from ways_analysis import WaysAnalyzer, WaysCharacterization

class TestWaysAnalyzer:
    """Test suite for WaysAnalyzer class."""

    def test_characterize_ways(self):
        """Test ways characterization functionality."""
        analyzer = WaysAnalyzer()
        result = analyzer.characterize_ways()
        assert isinstance(result, WaysCharacterization)
        assert result.total_ways > 0

    def test_analyze_dialogue_types(self):
        """Test dialogue type analysis."""
        analyzer = WaysAnalyzer()
        result = analyzer.analyze_dialogue_types()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_error_handling(self):
        """Test error conditions."""
        analyzer = WaysAnalyzer()
        with pytest.raises(Exception):
            analyzer.analyze_nonexistent_data()

class TestWaysCharacterization:
    """Test suite for WaysCharacterization dataclass."""

    def test_initialization(self):
        """Test dataclass initialization."""
        char = WaysCharacterization(
            total_ways=12,
            dialogue_types={'question': 5, 'statement': 7}
        )
        assert char.total_ways == 12
        assert char.most_common_type == 'statement'
```

### Running Tests

```bash
# All project tests with coverage
pytest tests/ --cov=src --cov-fail-under=70

# Specific ways analysis tests
pytest tests/test_ways_analysis.py -v

# Specific test class/function
pytest tests/test_ways_analysis.py::TestWaysAnalyzer::test_characterize_ways -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Best Practices

### Code Quality

✅ **Do:**
- Write clear, documented ways analysis code
- Use type hints on all public APIs
- Test everything thoroughly with real ways data
- Document ways analysis algorithms clearly
- Handle database and analysis errors gracefully

❌ **Don't:**
- Skip tests or coverage requirements
- Use mocks (test real ways database data)
- Leave undocumented ways analysis logic
- Hardcode database paths or queries
- Ignore edge cases in ways analysis

### Testing

✅ **Do:**
- Write tests first (TDD) for ways analysis
- Test with real ways database data
- Cover all ways analysis edge cases
- Test database query error handling
- Maintain 70% coverage for ways modules

❌ **Don't:**
- Use mocks for ways data
- Skip database error condition tests
- Leave ways analysis untested
- Test implementation details over behavior
- Accept coverage below 70% threshold

### Scripts

✅ **Do:**
- Import ways analysis from src/
- Orchestrate ways data workflows
- Generate ways analysis figures/tables
- Handle database I/O operations
- Provide clear ways analysis output

❌ **Don't:**
- Implement ways analysis algorithms in scripts
- Duplicate ways analysis logic from src/
- Skip database connection error handling
- Hardcode ways database paths
- Mix ways computation and orchestration

## Deployment

### Standalone Project

Copy this folder to use independently for ways of knowing research:

```bash
cp -r /path/to/template/project /path/to/my_ways_research
cd /path/to/my_ways_research
pytest tests/ --cov=src --cov-fail-under=70
python scripts/db_setup.py  # Initialize ways database
```

The project works completely independently - no template infrastructure needed.

### Integration with Template

To build the ways manuscript with template infrastructure:

```bash
cd /path/to/template
./repo_utilities/render_pdf.sh
```

This uses the template's build system while your ways analysis code remains in `project/`.

## Documentation

- This file (AGENTS.md) - Ways analysis architecture and guidelines
- README.md - Quick start and overview for ways research
- docs/ - Additional ways analysis documentation
- Docstrings - In-code ways analysis documentation

## See Also

- Root AGENTS.md - Template architecture
- Root README.md - Template overview
- repo_utilities/ - Build scripts
- infrastructure/ - Generic validation tools






