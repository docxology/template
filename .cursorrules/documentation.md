# Documentation Standards

## Documentation Requirements by Directory Type

### Source and Configuration Directories

Each source directory level MUST have:

### AGENTS.md - Comprehensive Documentation
- Detailed architecture and design
- Purpose and organization
- Implementation patterns
- Usage examples
- Troubleshooting guide
- Best practices
- Cross-references to related documentation

### README.md - Quick Reference
- One-page quick start
- Essential commands
- Key file descriptions
- Common workflows
- Links to detailed docs
- Target: Answer questions in 30 seconds

## AGENTS.md Structure

### Header and Purpose
```markdown
# directory/ - Short Description

## Purpose

One paragraph explaining what this directory does and why it's organized this way.

## Organization
```

### Content Sections
- Architecture/Design
- File Organization
- Usage Patterns
- Integration Points
- Best Practices
- Troubleshooting
- See Also/Cross-references

### Length and Depth
- Comprehensive (500-2000+ lines)
- Answer all "how", "what", "why" questions
- Include code examples
- Real-world patterns
- Multiple use cases

## README.md Structure

### Header
```markdown
# directory/ - Quick Reference

> One-line summary of the directory's purpose.
```

### Sections
- Overview (2-3 sentences)
- Quick usage examples
- Key files (table format)
- Common operations (code blocks)
- Link to detailed docs
- See Also

### Length and Depth
- Concise (100-300 lines)
- Answer most common questions
- Minimal but sufficient detail
- Links to AGENTS.md for depth

## Exception: Generated Output Directories

The `output/` directory and its subdirectories are **disposable** and regenerated on every build. They do NOT contain AGENTS.md or README.md files because:

- They are cleaned by `clean_output.sh` at the start of each build
- All contents are regenerated from source during the pipeline
- Persistent documentation files would be deleted every build cycle
- Documentation for output types lives in source directories (`src/`, `scripts/`, `docs/`)

### Directories Exempt from Documentation Requirement

- `output/` and all subdirectories (pdf/, figures/, data/, tex/, reports/, simulations/)
- Any other generated/temporary directories marked as disposable in `.gitignore`

### Directories That MUST Have Documentation

- `src/` - Source code modules
- `scripts/` - Script orchestrators
- `tests/` - Test suites
- `docs/` - Documentation
- `manuscript/` - Manuscript sections
- `repo_utilities/` - Build utilities
- All other source or configuration directories

## Code Comments

### In-File Documentation

```python
def analyze_convergence(data: np.ndarray, threshold: float = 1e-6) -> Dict[str, Any]:
    """Analyze data convergence patterns.
    
    Examines input data for convergence characteristics and returns
    detailed metrics for algorithm evaluation.
    
    Args:
        data: Input array with convergence trajectory
        threshold: Convergence detection threshold (default: 1e-6)
    
    Returns:
        Dictionary with keys:
            'converged': Boolean indicating convergence
            'iterations': Number of iterations to converge
            'rate': Estimated convergence rate
            'error': Final error value
    
    Raises:
        ValueError: If data is empty or invalid
        TypeError: If data is not array-like
    
    Example:
        >>> data = np.array([1.0, 0.5, 0.1, 0.01, 0.001])
        >>> result = analyze_convergence(data)
        >>> result['converged']
        True
    """
    if len(data) == 0:
        raise ValueError("Empty data array")
    
    # Core algorithm
    converged = check_convergence(data, threshold)  # Key logic
    iterations = find_convergence_point(data, threshold)
    
    return {
        'converged': converged,
        'iterations': iterations,
        'rate': estimate_rate(data),
        'error': data[-1] if len(data) > 0 else None
    }
```

### Bash Script Documentation

```bash
#!/bin/bash

# Script: render_pdf.sh
# Purpose: Generate PDF manuscripts from markdown sources
# Usage: ./render_pdf.sh [--clean] [--validate]
# Environment: LOG_LEVEL, REPO_ROOT, AUTHOR_NAME

set -euo pipefail

# =============================================================================
# CONFIGURATION SECTION
# Defines all paths and constants used throughout the script
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/output"

# =============================================================================
# CORE FUNCTIONS
# Main logic organized by responsibility
# =============================================================================

check_dependencies() {
    # Verify required tools (pandoc, xelatex) are available
    # Exit with error if any missing
    ...
}
```

## Cross-Referencing

### Link Format
```markdown
See [AGENTS.md](AGENTS.md) for detailed documentation.
See [README.md](README.md) for quick reference.
See [../parent/AGENTS.md](../parent/AGENTS.md) for parent documentation.
See [../../AGENTS.md](../../AGENTS.md) for root documentation.
```

### In Code
```python
# See ../AGENTS.md for overview of repository structure
# See src/AGENTS.md for source module documentation
```

## Documentation Examples

### Well-Documented src/ Module
```
src/AGENTS.md (800 lines)
- Architecture overview
- Each public function documented
- Usage patterns
- Common mistakes
- Testing approach

src/README.md (200 lines)
- Quick overview
- Import examples
- Common operations
- Link to AGENTS.md
```

### Well-Documented Directory
```
scripts/AGENTS.md (600 lines)
- Orchestration pattern
- Each script documented
- Integration with src/
- Output organization
- Troubleshooting

scripts/README.md (150 lines)
- Quick start
- List of scripts
- Common commands
- Link to detailed docs
```

## Documentation Consistency

### Terminology
- Use consistent terms across all docs
- Define acronyms on first use
- Refer to components by standard names

### Formatting
- Code in backticks: `filename.py`
- Headers with `#` consistently
- Bullet lists for clarity
- Tables for comparisons

### Examples
- Include executable examples
- Show both good and bad patterns
- Real file paths from repo
- Actual command lines

## Auto-Generated Documentation

### Glossary Generation
```bash
# Generates src/api_glossary.md from src/ docstrings
python3 repo_utilities/generate_glossary.py

# Output: manuscript/98_symbols_glossary.md
# Auto-injected into build
```

### Coverage Reports
```bash
# Generates HTML coverage report
python3 -m pytest tests/ --cov=src --cov-report=html

# Output: htmlcov/index.html
```

## Documentation Review Checklist

- [ ] Source directories have AGENTS.md and README.md
- [ ] Generated directories (output/) are excluded from documentation requirement
- [ ] AGENTS.md is comprehensive (500+ lines)
- [ ] README.md is concise (100-300 lines)
- [ ] Cross-references are accurate
- [ ] Code examples are correct
- [ ] Links work (relative paths)
- [ ] Terminology is consistent
- [ ] Structure follows standard format
- [ ] Updated when code changes
- [ ] No references to output/ documentation in rules

## Comprehensive Documentation

For complete documentation standards and guides, see:

- [`docs/AGENTS.md`](../docs/AGENTS.md) - Documentation philosophy and organization
- [`docs/DOCUMENTATION_INDEX.md`](../docs/DOCUMENTATION_INDEX.md) - Complete documentation index
- [`docs/MARKDOWN_TEMPLATE_GUIDE.md`](../docs/MARKDOWN_TEMPLATE_GUIDE.md) - Markdown writing standards

## See Also

- [../AGENTS.md](../AGENTS.md) - Root documentation
- [../README.md](../README.md) - Project overview
- [../docs/](../docs/) - Documentation hub
- [core_architecture.md](core_architecture.md) - System design

