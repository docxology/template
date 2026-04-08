# 🏗️ Extending and Automation Guide

> **Custom architectures and automation**

**Previous**: [Testing and Reproducibility](../guides/testing-and-reproducibility.md) (Levels 7-9)

This guide covers **Levels 10-12** of the Research Project Template. for expert developers ready to extend the template, create custom architectures, and build advanced automation systems.

## 📚 What You'll Learn

By the end of this guide, you'll be able to:

- ✅ Extend the template architecture
- ✅ Create custom build pipelines
- ✅ Integrate external tools and systems
- ✅ Implement continuous integration
- ✅ Build automated documentation systems
- ✅ Create research workflow integrations

**Estimated Time:** 1-2 months

## 🎯 Prerequisites

- Completed [Testing and Reproducibility Guide](../guides/testing-and-reproducibility.md)
- Expert Python programming skills
- Understanding of system design and DevOps
- Experience with CI/CD systems

## 📖 Table of Contents

- [Level 10: Custom Architectures](#level-10-custom-architectures)
- [Level 11: Advanced Automation](#level-11-advanced-automation)
- [Level 12: Research Workflow Integration](#level-12-research-workflow-integration)

---

## Level 10: Custom Architectures

**Goal**: Extend and customize the template architecture

### Extending the Template

**Create specialized project types**:

```bash
# Prefer a real project tree under projects/{name}/ (discovered by ./run.sh).
# Scaffold from the exemplar layout:
mkdir -p projects/my_research/src projects/my_research/tests projects/my_research/scripts projects/my_research/manuscript
cp projects/code_project/manuscript/config.yaml projects/my_research/manuscript/
```

### Custom Build Pipelines

**Create specialized build script** (example aligned with this repo; save under `projects/{name}/scripts/` if project-specific):

```bash
#!/bin/bash
set -e

echo "Project build pipeline (exemplar: code_project)"

uv run pytest projects/code_project/tests/ \
  --cov=projects/code_project/src --cov-report=html

uv run python projects/code_project/scripts/optimization_analysis.py

uv run python scripts/execute_pipeline.py --project code_project --core-only

echo "Build complete."
```

### Integration with External Tools

**Example: External simulation tool**:

```python
#!/usr/bin/env python3
"""Thin orchestrator sketch: subprocess for an external binary; computation in src/."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_external_tool(config_file: Path, raw_out: Path) -> dict:
    subprocess.run(
        ["external_simulator", "--config", str(config_file), "--output", str(raw_out)],
        capture_output=True,
        text=True,
        check=True,
    )
    with open(raw_out, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    # Implement domain analysis in projects/{name}/src/; import it here.
    # config_file = Path("…")  # your inputs
    # raw_out = Path("…")
    # data = run_external_tool(config_file, raw_out)
    # processed = your_src_module.process(data)
    pass


if __name__ == "__main__":
    main()
```

**See [../core/architecture.md](../core/architecture.md) for architecture principles.**

---

## Level 11: Advanced Automation

**Goal**: Implement CI/CD and automated documentation

### Continuous Integration

**GitHub Actions workflow**:

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync
    
    - name: Run tests
      run: |
        uv run pytest projects/code_project/tests/ --cov=projects/code_project/src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
  
  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y pandoc texlive-xetex
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install Python dependencies
      run: |
        pip install uv
        uv sync
    
    - name: Run build pipeline
      run: |
        uv run python scripts/execute_pipeline.py --project {name} --core-only
    
    - name: Upload PDFs
      uses: actions/upload-artifact@v3
      with:
        name: pdfs
        path: output/*/pdf/*.pdf
```

### Automated Documentation

**Generate API docs from source**:

```python
# scripts/auto_documentation.py
#!/usr/bin/env python3
"""Automatically generate API documentation."""
import inspect
import ast
import os

def extract_module_info(module_path):
    """Extract documentation from Python module."""
    with open(module_path, 'r') as f:
        tree = ast.parse(f.read())
    
    functions = []
    classes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                functions.append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'args': [arg.arg for arg in node.args.args],
                })
        
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                classes.append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'methods': [m.name for m in node.body 
                               if isinstance(m, ast.FunctionDef) 
                               and not m.name.startswith('_')]
                })
    
    return {'functions': functions, 'classes': classes}

def generate_markdown_docs(module_name, info):
    """Generate markdown documentation."""
    md = f"# {module_name} API Reference\n\n"
    
    if info['classes']:
        md += "## Classes\n\n"
        for cls in info['classes']:
            md += f"### `{cls['name']}`\n\n"
            if cls['docstring']:
                md += f"{cls['docstring']}\n\n"
            if cls['methods']:
                md += "**Methods:**\n"
                for method in cls['methods']:
                    md += f"- `{method}()`\n"
                md += "\n"
    
    if info['functions']:
        md += "## Functions\n\n"
        for func in info['functions']:
            args = ', '.join(func['args'])
            md += f"### `{func['name']}({args})`\n\n"
            if func['docstring']:
                md += f"{func['docstring']}\n\n"
    
    return md

def main():
    """Generate documentation for all projects/{name}/src/ modules."""
    src_dir = 'projects/code_project/src'
    output_dir = 'output/api_docs'
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(src_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_path = os.path.join(src_dir, filename)
            module_name = filename[:-3]
            
            print(f"Documenting {module_name}...")
            info = extract_module_info(module_path)
            md = generate_markdown_docs(module_name, info)
            
            output_path = os.path.join(output_dir, f'{module_name}.md')
            with open(output_path, 'w') as f:
                f.write(md)
            
            print(output_path)

if __name__ == '__main__':
    main()
```

**Note**: The template ships with a production CI configuration at [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) with 8 jobs: lint, verify-no-mocks, test-infra (matrix), test-project (matrix), validate manuscripts, security scan, and performance check. Study it as a reference for your own CI setup.

---

## Level 12: Research Workflow Integration

**Goal**: Integrate with research tools and workflows

### LLM-Assisted Review

Use local LLMs for automated manuscript review and translation:

```bash
# Ensure Ollama is running with a model
ollama serve && ollama pull gemma3:4b

# Run pipeline with LLM review
./run.sh --pipeline  # Stage 06 generates reviews automatically
```

See the [LLM Integration Guide](llm-integration-guide.md) for programmatic usage.

### Publishing and DOI

Generate citations, mint DOIs, and publish to Zenodo:

```python
from infrastructure.publishing import generate_citation_bibtex, extract_publication_metadata
from pathlib import Path

metadata = extract_publication_metadata(Path("projects/code_project/manuscript/config.yaml"))
print(generate_citation_bibtex(metadata))
```

See the [Publishing Guide](publishing-guide.md) for the full workflow.

### Literature Review Integration

```python
# projects/code_project/scripts/literature_analysis.py
#!/usr/bin/env python3
"""Analyze research trends from literature."""
import requests
from collections import Counter

# Import from projects/{name}/src/ (implement these as needed)
from projects.code_project.src.text_analysis import extract_keywords, analyze_trends

def fetch_papers(query, max_results=100):
    """Fetch papers from API (e.g., arXiv, PubMed)."""
    # Implement API calls
    pass

def analyze_research_trends(query):
    """Analyze trends in research literature."""
    
    # Fetch papers
    papers = fetch_papers(query)
    
    # Extract abstracts
    abstracts = [p['abstract'] for p in papers]
    
    # Use projects/{name}/src/ methods for analysis
    all_keywords = []
    for abstract in abstracts:
        keywords = extract_keywords(abstract)
        all_keywords.extend(keywords)
    
    # Analyze trends
    keyword_counts = Counter(all_keywords)
    trends = analyze_trends(keyword_counts, papers)
    
    return trends

def generate_trend_report(trends):
    """Generate trend analysis report."""
    # Create visualizations
    # Generate markdown report
    pass
```

### Collaborative Research

**Set up Git workflow**:

```bash
# Feature branch workflow
git checkout -b feature/new-algorithm

# Make changes
vim projects/code_project/src/new_algorithm.py
vim projects/code_project/tests/test_new_algorithm.py

# Ensure coverage requirements met
pytest projects/code_project/tests/ --cov=projects.code_project.src --cov-report=term-missing

# Commit with conventional commit messages
git add projects/code_project/src/new_algorithm.py projects/code_project/tests/test_new_algorithm.py
git commit -m "feat: add new optimization algorithm

- Implements gradient-free optimization
- Includes tests (meets coverage requirements)
- Adds examples in scripts/

Closes #123"

# Push and create pull request
git push origin feature/new-algorithm
```

---

## Best Practices

### Architecture Extensions

1. **Maintain thin orchestrator pattern**
2. **Maintain required test coverage**
3. **Document all extensions**
4. **Preserve backward compatibility**
5. **Use semantic versioning**

### CI/CD Best Practices

1. **Test on multiple Python versions**
2. **Cache dependencies for speed**
3. **Fail fast on test failures**
4. **Upload artifacts for inspection**
5. **Monitor build times**

### Integration Best Practices

1. **Handle external tool failures gracefully**
2. **Validate external data thoroughly**
3. **Log all external interactions**
4. **Use timeouts for external calls**
5. **Document integration requirements**

---

## Troubleshooting

### CI/CD Pipeline Fails

**Symptom**: GitHub Actions workflow fails

**Solution**:
- Check Python version compatibility in workflow matrix
- Verify pytest-cov installed: `pip install pytest-cov`
- Check coverage thresholds match project settings

### External Tool Integration Fails

**Symptom**: `subprocess.run` fails with external tool

**Solution**:
- Verify tool is installed: `which external_tool`
- Add error handling for missing tool
- Use absolute paths for tool execution

### Artifact Upload Fails

**Symptom**: `actions/upload-artifact` fails

**Solution**:
- Check file paths exist before upload
- Verify no file size limits exceeded
- Use correct artifact path patterns

---

## Related Documentation

- **[Architecture Guide](../core/architecture.md)** - System design
- **[Workflow Guide](../core/workflow.md)** - Development process
- **[Pipeline Orchestration](../RUN_GUIDE.md)** - Stages, flags, and common invocations
- **[Contributing Guide](../development/contributing.md)** - Contribution process
- **[Roadmap](../development/roadmap.md)** - Future plans

---

## Success Checklist

After completing this guide, you should be able to:

- [x] Extend template architecture for custom needs
- [x] Create specialized build pipelines
- [x] Integrate external tools and systems
- [x] Implement continuous integration
- [x] Build automated documentation
- [x] Create research workflow integrations

**Congratulations!** You've mastered all 12 levels of the Research Project Template. You're now ready to build production-grade research systems.

---

**Need help?** Check the **[FAQ](../reference/faq.md)** or **[Documentation Index](../documentation-index.md)**

**Quick Reference**: [Cheatsheet](../reference/quick-start-cheatsheet.md) | [Glossary](../reference/glossary.md)


