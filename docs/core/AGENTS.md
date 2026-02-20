# Core Documentation

## Overview

The `docs/core/` directory contains the fundamental documentation that explains how to understand and use the Research Project Template. These documents provide the essential knowledge needed for effective template utilization.

## Directory Structure

```
docs/core/
├── AGENTS.md                   # This technical documentation
├── architecture.md             # System design and structure
├── how-to-use.md               # usage guide
├── README.md                   # Quick reference
└── workflow.md                 # Development workflow
```

## Key Documentation Files

### How To Use (`how-to-use.md`)

**Comprehensive, step-by-step guide for using the Research Project Template:**

**Getting Started:**

- Initial setup and configuration
- Environment preparation
- Basic project structure understanding
- First manuscript generation

**Core Workflows:**

- Writing and organizing research content
- Running analysis scripts
- Generating outputs (PDF, HTML, slides)
- Validation and quality assurance

**Advanced Usage:**

- Custom configuration options
- Extending project functionality
- Integration with external tools
- Performance optimization techniques

**Troubleshooting:**

- Common issues and solutions
- Debug procedures
- Log analysis techniques
- Recovery from failures

### Architecture (`architecture.md`)

**System design and structural overview:**

**Two-Layer Architecture:**

- Infrastructure layer (generic, reusable)
- Project layer (domain-specific, customizable)
- Separation principles and responsibilities
- Inter-layer communication patterns

**Thin Orchestrator Pattern:**

- Business logic placement rules
- Orchestration vs implementation distinction
- Script design principles
- Pattern enforcement mechanisms

**Component Relationships:**

- Module dependencies and interactions
- Data flow patterns
- Configuration management
- Error handling architecture

### Workflow (`workflow.md`)

**Development and operational workflows:**

**Research Development Process:**

- Project initialization
- Iterative development cycles
- Testing and validation procedures
- Documentation maintenance

**Quality Assurance:**

- Code review processes
- Testing requirements and standards
- Performance benchmarking
- Security considerations

**Collaboration Workflows:**

- Multi-developer coordination
- Branch management strategies
- Pull request procedures
- Knowledge sharing practices

## Documentation Philosophy

### Layered Information Architecture

**Progressive Disclosure:**

- **how-to-use.md**: Practical, step-by-step instructions
- **architecture.md**: Design principles and system structure
- **workflow.md**: Operational procedures and best practices

**Information Flow:**

```
how-to-use.md → architecture.md → workflow.md
   ↓               ↓                   ↓
Practical       Design             Operational
Usage         Understanding       Excellence
```

### Show, Don't Tell

**Practical Examples:**

```bash
# Good: command with context
$ python3 scripts/03_render_pdf.py
INFO: Loading manuscript configuration...
INFO: Generating PDF with LaTeX...
INFO: PDF generated successfully: output/{project_name}/pdf/{project_name}_combined.pdf

# View the result
open output/{project_name}/pdf/{project_name}_combined.pdf
```

**Implementation Details:**

```python
# Good: Real, working code examples
from infrastructure.core import load_config

# Load project configuration
config = load_config()

# Access configuration values
author_name = config.get('author_name', 'Default Author')
project_title = config.get('project_title', 'Research Project')

print(f"Author: {author_name}")
print(f"Title: {project_title}")
```

## Core Concepts

### Two-Layer Architecture

**Infrastructure Layer (Generic):**

- Reusable across research projects
- Domain-independent utilities
- testing (60%+ coverage)
- Stable, version-controlled APIs

**Project Layer (Domain-Specific):**

- Custom research algorithms
- Project-specific analysis
- High testing standards (90%+ coverage)
- Flexible and adaptable

**Layer Interaction:**

```python
# Infrastructure provides utilities
from infrastructure.core import get_logger, load_config
from infrastructure.validation import validate_pdf_rendering

# Project implements research logic
from project.src.analysis import run_statistical_analysis
from project.src.visualization import create_research_plots

# Orchestrator coordinates both
def main():
    logger = get_logger(__name__)
    config = load_config()

    # Run project analysis
    results = run_statistical_analysis(config.data_path)

    # Validate outputs
    validation_report = validate_pdf_rendering('output/manuscript.pdf')

    logger.info(f"Analysis: {validation_report}")
```

### Thin Orchestrator Pattern

**Pattern Principles:**

- Business logic in dedicated modules
- Scripts handle coordination only
- Clear separation of concerns
- Testable, maintainable code

**Implementation Example:**

```python
# analysis_pipeline.py (orchestrator script)
from project.src.data_processing import process_research_data
from project.src.statistical_analysis import run_statistical_tests
from infrastructure.core import get_logger

def main():
    """Orchestrate research data analysis."""
    logger = get_logger(__name__)

    # Coordinate analysis steps
    raw_data = load_data()
    processed_data = process_research_data(raw_data)  # Business logic in module
    results = run_statistical_tests(processed_data)   # Business logic in module
    generate_report(results)                          # Output generation

    logger.info("Analysis pipeline completed successfully")

if __name__ == "__main__":
    main()
```

## Usage Workflows

### Basic Research Workflow

**1. Project Setup:**

```bash
# Initialize project structure
mkdir my_research_project
cd my_research_project
cp -r /path/to/template/* .

# Configure project
vim project/manuscript/config.yaml
```

**2. Content Development:**

```bash
# Write research content
vim project/manuscript/01_introduction.md
vim project/manuscript/02_methodology.md

# Develop analysis code
vim project/src/analysis.py
```

**3. Testing and Validation:**

```bash
# Run tests
python3 scripts/01_run_tests.py

# Generate outputs
python3 scripts/03_render_pdf.py

# Validate results
python3 scripts/04_validate_output.py
```

### Advanced Research Workflow

**Parallel Development:**

```bash
# Multiple analysis scripts
python3 project/scripts/data_analysis.py &
python3 project/scripts/statistical_modeling.py &
python3 project/scripts/visualization.py &
wait

# Combined manuscript generation
python3 scripts/03_render_pdf.py
```

**Continuous Integration:**

```bash
# Automated testing
python3 scripts/01_run_tests.py

# Quality validation
python3 scripts/04_validate_output.py

# Output deployment
python3 scripts/05_copy_outputs.py
```

## Configuration Management

### Configuration Hierarchy

**Priority Order:**

1. Environment variables (highest priority)
2. Configuration files (`project/manuscript/config.yaml`)
3. Default values (lowest priority)

**Configuration Example:**

```yaml
# project/manuscript/config.yaml
paper:
  title: "Novel Research Methodology"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"
```

**Environment Override:**

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export PROJECT_TITLE="Updated Research Title"
export LOG_LEVEL=0  # Debug mode
```

## Quality Assurance

### Testing Standards

**Coverage Requirements:**

- Project code: 90% minimum coverage
- Infrastructure code: 60% minimum coverage
- Integration tests for end-to-end workflows
- data analysis (no mocks)

**Testing Workflow:**

```python
# test example
def test_research_algorithm():
    """Test research algorithm with data."""
    # Load actual test dataset
    test_data = load_research_dataset('test_data.csv')

    # Run algorithm
    algorithm = ResearchAlgorithm(config)
    results = algorithm.process(test_data)

    # Validate results
    assert results.accuracy > 0.85
    assert results.convergence_achieved
    assert len(results.predictions) == len(test_data)
```

### Validation Procedures

**Output Validation:**

```python
# PDF validation
from infrastructure.validation import validate_pdf_rendering

report = validate_pdf_rendering('output/manuscript.pdf')
assert report['errors'] == []
assert report['quality_score'] > 0.9

# Content validation
from infrastructure.validation import validate_markdown

issues = validate_markdown('project/manuscript/')
assert len(issues['errors']) == 0
```

## Troubleshooting Guide

### Common Issues

**Configuration Problems:**

```bash
# Check configuration loading
python3 -c "
from infrastructure.core import load_config
config = load_config()
print('Configuration loaded successfully')
print(f'Author: {config.get(\"author_name\")}')
"
```

**Build Failures:**

```bash
# Debug build process
LOG_LEVEL=0 python3 scripts/03_render_pdf.py

# Check LaTeX installation
which xelatex
tlmgr list --only-installed | grep multirow
```

**Test Failures:**

```bash
# Run specific failing test
pytest projects/{name}/tests/test_analysis.py::TestAnalysis::test_algorithm -v

# Check test data integrity
python3 -c "
import pandas as pd
data = pd.read_csv('test_data.csv')
print(f'Data shape: {data.shape}')
print(f'Columns: {list(data.columns)}')
"
```

### Debug Procedures

**System State Inspection:**

```python
# Check system components
from infrastructure.core import environment

status = environment.check_system_requirements()
for component, state in status.items():
    print(f"{component}: {'✓' if state['available'] else '✗'}")
```

**Log Analysis:**

```bash
# Search for errors in logs
grep "ERROR" output/logs/*.log

# Check recent activity
tail -50 output/logs/rendering.log
```

## Performance Optimization

### Profiling Techniques

**Code Profiling:**

```python
import cProfile
from project.src.analysis import run_analysis

# Profile execution
cProfile.run('run_analysis(test_data)', 'profile_output.prof')

# Analyze results
import pstats
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(20)
```

**Memory Optimization:**

```python
from memory_profiler import profile

@profile
def process_large_dataset(data_path):
    """Process large dataset with memory monitoring."""
    data = load_large_dataset(data_path)
    results = analyze_data(data)
    return results

# Run with memory profiling
process_large_dataset('large_dataset.csv')
```

### Performance Monitoring

**System Resources:**

```python
from infrastructure.core import get_system_resources

resources = get_system_resources()
print(f"CPU Usage: {resources['cpu_percent']}%")
print(f"Memory Usage: {resources['memory_percent']}%")
print(f"Available Memory: {resources['memory_available']:.1f}GB")
```

## Integration Examples

### External Tool Integration

**Data Analysis Integration:**

```python
# Integrate with analysis libraries
import numpy as np
import pandas as pd
from scipy import stats

from project.src.statistical_analysis import StatisticalAnalyzer

class AdvancedAnalyzer(StatisticalAnalyzer):
    """Extended analyzer with additional statistical methods."""

    def run_advanced_tests(self, data):
        """Run advanced statistical tests."""
        # Use infrastructure logging
        self.logger.info("Running advanced statistical analysis")

        # Perform analysis
        results = {}
        results['normality_test'] = stats.shapiro(data)
        results['correlation_matrix'] = np.corrcoef(data.T)

        return results
```

### API Integration

**Publishing Integration:**

```python
from infrastructure.publishing import publish_to_zenodo

# Prepare publication metadata
metadata = {
    'title': config.project_title,
    'authors': [{'name': config.author_name, 'orcid': config.author_orcid}],
    'description': 'Research manuscript and analysis results',
    'keywords': ['research', 'analysis', 'methodology']
}

# Publish to Zenodo
files_to_publish = [
    'output/act_inf_metaanalysis/pdf/act_inf_metaanalysis_combined.pdf',
    'output/act_inf_metaanalysis/data/analysis_results.json',
    'projects/act_inf_metaanalysis/src/analysis.py'
]

result = publish_to_zenodo(metadata, files_to_publish, zenodo_token)
print(f"Published with DOI: {result['doi']}")
```

## See Also

**Related Documentation:**

- [`../guides/`](../guides/) - Usage guides for different skill levels
- [`../operational/`](../operational/) - Operational procedures and troubleshooting
- [`../development/`](../development/) - Development and contribution guidelines

**System Documentation:**

- [`../AGENTS.md`](../AGENTS.md) - system overview
- [`../documentation-index.md`](../documentation-index.md) - Documentation index
- [`../../AGENTS.md`](../../AGENTS.md) - Root system documentation
