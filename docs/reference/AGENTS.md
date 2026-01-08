# Reference Documentation

## Overview

The `docs/reference/` directory contains reference materials, quick lookups, and supplementary information for the Research Project Template. These documents provide fast access to essential information without requiring extensive reading.

## Directory Structure

```
docs/reference/
├── AGENTS.md                       # This technical documentation
├── API_REFERENCE.md                # API documentation
├── ../reference/COMMON_WORKFLOWS.md             # Step-by-step workflow recipes
├── COPYPASTA.md                    # Reusable documentation snippets
├── FAQ.md                          # Frequently asked questions
├── GLOSSARY.md                     # Terms and definitions
├── QUICK_START_CHEATSHEET.md       # Essential commands reference
└── README.md                       # Quick reference overview
```

## Key Documentation Files

### API Reference (`API_REFERENCE.md`)

**API documentation for all modules:**

**Infrastructure APIs:**
- Core utilities (logging, configuration, exceptions)
- Validation APIs (PDF, Markdown, integrity checking)
- Rendering APIs (PDF, HTML, slide generation)
- Publishing APIs (Zenodo, arXiv, GitHub integration)

**Project APIs:**
- Analysis modules and algorithms
- Data processing utilities
- Visualization functions
- Custom research workflows

### Common Workflows (`../reference/COMMON_WORKFLOWS.md`)

**Step-by-step recipes for frequent tasks:**

**Research Workflows:**
- Initial project setup and configuration
- Manuscript development and organization
- Analysis execution and validation
- Output generation and publishing

**Maintenance Workflows:**
- Dependency updates and system maintenance
- Backup and recovery procedures
- Performance monitoring and optimization
- Troubleshooting common issues

### FAQ (`FAQ.md`)

**Frequently asked questions organized by category:**

**Getting Started:**
- Installation and setup questions
- Basic configuration issues
- First project creation problems

**Usage Questions:**
- Common operational issues
- Configuration problems
- Output generation questions

**Troubleshooting:**
- Build failures and error resolution
- Performance issues and optimization
- Integration problems and workarounds

### Glossary (`GLOSSARY.md`)

**Terminology and concept definitions:**

**System Concepts:**
- Two-layer architecture explanation
- Thin orchestrator pattern definition
- Infrastructure vs project layer distinctions

**Technical Terms:**
- LaTeX compilation terminology
- PDF validation concepts
- API glossary generation
- Publishing platform terms

### Quick Start Cheatsheet (`QUICK_START_CHEATSHEET.md`)

**Essential commands and quick references:**

**Command Reference:**
```bash
# pipeline execution
python3 scripts/execute_pipeline.py --core-only

# Individual stage execution
python3 scripts/00_setup_environment.py  # Environment check
python3 scripts/01_run_tests.py          # Test suite
python3 scripts/02_run_analysis.py       # Analysis execution
python3 scripts/03_render_pdf.py         # PDF generation
python3 scripts/04_validate_output.py    # Quality validation
python3 scripts/05_copy_outputs.py       # Deliverable copying

# Interactive menu
./run.sh  # Main interactive interface
```

**Configuration Quick Reference:**
```bash
# Essential environment variables
export AUTHOR_NAME="Dr. Researcher"
export PROJECT_TITLE="Research Project"
export LOG_LEVEL=1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

# Optional service tokens
export ZENODO_TOKEN="your-zenodo-token"
export OLLAMA_HOST="http://localhost:11434"
```

### Copypasta (`COPYPASTA.md`)

**Reusable documentation snippets and templates:**

**Common Configurations:**
```yaml
# project/manuscript/config.yaml template
paper:
  title: "Research Paper Title"
  version: "1.0"

authors:
  - name: "Dr. Primary Author"
    orcid: "0000-0000-0000-1234"
    email: "author@university.edu"
    affiliation: "Research University"

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"
```

**Standard Commands:**
```bash
# System health check
python3 -c "
from infrastructure.core import environment
status = environment.check_system_requirements()
print('System Status:')
for component, info in status.items():
    print(f'  {component}: {\"✓\" if info[\"available\"] else \"✗\"}')
"

# Quick test run
python3 scripts/01_run_tests.py --tb=short

# Fast PDF generation
python3 scripts/03_render_pdf.py --quiet
```

## Reference Material Standards

### Quick Access Design

**Immediate Information Access:**
- No lengthy introductions or background
- Direct answers to common questions
- Copy-paste ready code snippets
- Tabular format for comparisons

**Example Structure:**
```markdown
## Command: Generate PDF Output

**Quick Use:**
```bash
python3 scripts/03_render_pdf.py
```

**With Custom Config:**
```bash
export LOG_LEVEL=0  # Debug output
python3 scripts/03_render_pdf.py --config custom.yaml
```

**Common Issues:**
- LaTeX not found → Install MacTeX/BasicTeX
- Missing packages → `tlmgr install multirow cleveref`
- Memory errors → Reduce `PDF_MEMORY_LIMIT`
```

### Coverage

**Command Reference:**
```markdown
## All Pipeline Stages

| Stage | Script | Purpose | Duration |
|-------|--------|---------|----------|
| 00 | `setup_environment.py` | System validation | < 1 min |
| 01 | `run_tests.py` | Test execution | 2-5 min |
| 02 | `run_analysis.py` | Research analysis | 5-30 min |
| 03 | `render_pdf.py` | PDF generation | 2-10 min |
| 04 | `validate_output.py` | Quality checks | < 1 min |
| 05 | `copy_outputs.py` | File delivery | < 1 min |
```

**Configuration Options Table:**
```markdown
## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `1` | Logging verbosity (0-3) |
| `AUTHOR_NAME` | `""` | Primary author name |
| `PROJECT_TITLE` | `""` | Research project title |
| `OLLAMA_HOST` | `"http://localhost:11434"` | LLM service endpoint |
| `ZENODO_TOKEN` | `""` | Zenodo publishing token |
| `MAX_PARALLEL_SUMMARIES` | `1` | Parallel LLM operations |
```

## Maintenance and Updates

### Content Freshness

**Regular Updates:**
- Update command examples with features
- Refresh version-specific information
- Validate all code snippets regularly
- Update FAQ based on user questions

**Validation Procedures:**
```bash
# Validate all commands in cheatsheet
./validate_cheatsheet_commands.sh docs/reference/QUICK_START_CHEATSHEET.md

# Check FAQ answers accuracy
./validate_faq_answers.sh docs/reference/FAQ.md

# Test API reference examples
python3 validate_api_examples.py docs/reference/API_REFERENCE.md
```

### User Feedback Integration

**FAQ Evolution:**
- Track common user questions
- Add answers to FAQ when repeated
- Update existing answers based on new information
- Remove outdated questions

**Copypasta Enhancement:**
- Collect frequently requested code snippets
- Standardize common configuration patterns
- Update snippets with best practices
- Remove deprecated patterns

## Content Organization

### Information Architecture

**Progressive Information Access:**
```
QUICK_START_CHEATSHEET.md → ../reference/COMMON_WORKFLOWS.md → FAQ.md
          ↓                        ↓
    Immediate Actions       Step-by-Step Guides    Problem Solving
```

**Reference Hierarchy:**
- **Cheatsheet**: Immediate command reference
- **Common Workflows**: task procedures
- **FAQ**: Problem-specific solutions
- **API Reference**: Technical implementation details
- **Glossary**: Concept definitions

### Cross-Reference System

**Internal Linking:**
```markdown
## Related Information

- **Setup**: See [`../core/HOW_TO_USE.md`](../core/HOW_TO_USE.md)
- **Troubleshooting**: See [`../operational/TROUBLESHOOTING_GUIDE.md`](../operational/TROUBLESHOOTING_GUIDE.md)
- **Configuration**: See [`../operational/CONFIGURATION.md`](../operational/CONFIGURATION.md)
- **API Details**: See [`API_REFERENCE.md`](API_REFERENCE.md)
```

**External Resources:**
```markdown
## External Links

- [Pandoc Manual](https://pandoc.org/MANUAL.html) - Document conversion
- [LaTeX Wikibook](https://en.wikibooks.org/wiki/LaTeX) - LaTeX documentation
- [Python Testing](https://docs.pytest.org/) - Testing framework
- [Git Documentation](https://git-scm.com/doc) - Version control
```

## Quality Assurance

### Content Accuracy

**Technical Validation:**
- Test all command examples in clean environments
- Validate configuration examples with schema checking
- Verify API signatures against actual code
- Cross-reference information accuracy

**Example Testing:**
```bash
# Test cheatsheet commands
for cmd in $(grep "^\`\`\`bash" QUICK_START_CHEATSHEET.md | sed 's/```bash//'); do
    echo "Testing: $cmd"
    eval "$cmd --dry-run" 2>/dev/null || echo "Command failed: $cmd"
done

# Validate configuration examples
python3 -c "
import yaml
with open('config_example.yaml') as f:
    config = yaml.safe_load(f)
    print('Configuration syntax valid')
"
```

### Consistency Standards

**Formatting Consistency:**
- Use consistent code block languages
- Standardize table formats
- Maintain consistent heading hierarchy
- Use uniform link formatting

**Content Standards:**
- Use active voice in instructions
- Provide, working examples
- Include error handling in code snippets
- Document prerequisites and assumptions

## Usage Analytics

### Content Effectiveness

**Usage Tracking:**
- Monitor which references are most accessed
- Track FAQ question popularity
- Measure cheatsheet command usage
- Analyze workflow completion rates

**Improvement Metrics:**
- User feedback on reference usefulness
- Time to find information
- Error rates in copied commands
- Update frequency requirements

### Continuous Improvement

**Content Optimization:**
```python
# Analyze reference usage patterns
def analyze_reference_usage():
    """Analyze which reference materials are most used."""
    usage_stats = {
        'cheatsheet_commands': count_command_usage(),
        'faq_questions': count_faq_searches(),
        'workflow_steps': track_workflow_completion(),
        'api_references': track_api_lookups()
    }

    # Generate improvement recommendations
    recommendations = []
    if usage_stats['faq_questions']['setup'] > usage_stats['faq_questions']['advanced']:
        recommendations.append("Add more setup-focused FAQ answers")

    if usage_stats['cheatsheet_commands']['pdf_generation'] > usage_stats['cheatsheet_commands']['testing']:
        recommendations.append("Expand PDF generation command examples")

    return recommendations
```

## Special Content Types

### Code Snippet Management

**Copypasta Best Practices:**
```python
# Well-documented reusable snippets
"""
Environment Health Check
Copy this to quickly verify system status
"""
from infrastructure.core import environment

def check_system_health():
    """Check all system components health."""
    status = environment.check_system_requirements()

    healthy = []
    issues = []

    for component, info in status.items():
        if info['available']:
            healthy.append(f"✓ {component}: {info['version']}")
        else:
            issues.append(f"✗ {component}: {info.get('error', 'Not available')}")

    return healthy, issues

# Usage
healthy, issues = check_system_health()
print("System Health Check:")
print("\n".join(healthy))
if issues:
    print("\nIssues found:")
    print("\n".join(issues))
```

### Configuration Templates

**Standardized Templates:**
```yaml
# project configuration template
# Copy and customize for new projects

paper:
  title: "Your Research Paper Title"
  subtitle: ""  # Optional subtitle
  version: "1.0"

authors:
  - name: "Dr. Primary Author"
    orcid: "0000-0000-0000-1234"  # Get from https://orcid.org/
    email: "author@university.edu"
    affiliation: "Research University"
    corresponding: true

  - name: "Co-Author Name"
    affiliation: "Another University"

publication:
  doi: ""  # Will be filled after publication
  journal: ""  # Optional
  volume: ""  # Optional
  pages: ""  # Optional

keywords:
  - "research"
  - "methodology"
  - "analysis"

metadata:
  license: "Apache-2.0"
  language: "en"

# LLM integration (optional)
llm:
  enabled: true
  translations:
    enabled: true
    languages:
      - zh  # Chinese
      - es  # Spanish
      - fr  # French
```

## Future Enhancements

### Planned Improvements

**Reference Materials:**
- Interactive command reference
- Video tutorials for complex workflows
- API playground for testing calls
- Configuration wizard/generator

**Content Automation:**
- Auto-generated command references
- Dynamic FAQ from issue tracking
- Usage-based content prioritization
- Automated example validation

### Community Contributions

**Reference Enhancement Process:**
1. **Identify Gap**: Find missing or unclear reference information
2. **Gather Examples**: Collect real usage examples and common questions
3. **Create Content**: Write clear, concise reference material
4. **Validate**: Test all examples and commands
5. **Review**: Get feedback from maintainers and users
6. **Publish**: Add to appropriate reference document

## See Also

**Reference Documentation:**
- [`QUICK_START_CHEATSHEET.md`](QUICK_START_CHEATSHEET.md) - Essential commands
- [`../reference/COMMON_WORKFLOWS.md`](../reference/COMMON_WORKFLOWS.md) - Step-by-step procedures
- [`FAQ.md`](FAQ.md) - Problem-solving answers
- [`API_REFERENCE.md`](API_REFERENCE.md) - Technical API details

**System Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - system overview
- [`../DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md) - Documentation index
- [`../../AGENTS.md`](../../AGENTS.md) - Root system documentation