# 🏗️ Expert Usage Guide

> **Custom architectures and advanced automation**

**Previous**: [Advanced Usage](ADVANCED_USAGE.md) (Levels 7-9)

This guide covers **Levels 10-12** of the Research Project Template. Perfect for expert developers ready to extend the template, create custom architectures, and build advanced automation systems.

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

- Completed [Advanced Usage Guide](ADVANCED_USAGE.md)
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
# Create custom project structure
mkdir -p custom_projects/machine_learning
mkdir -p custom_projects/simulation
mkdir -p custom_projects/data_science

# Copy and adapt base structure
cp -r src tests scripts custom_projects/machine_learning/
```

### Custom Build Pipelines

**Create specialized build script**:

```bash
#!/bin/bash
# custom_projects/machine_learning/ml_build.sh

set -e

echo "ML Project Build Pipeline"

# 1. Run ML-specific tests
pytest tests/ --cov=src --cov-report=html \
    --markers="ml"  # Only ML tests

# 2. Train models
python3 scripts/train_models.py

# 3. Evaluate models
python3 scripts/evaluate_models.py

# 4. Generate model cards
python3 scripts/generate_model_cards.py

# 5. Build documentation
pandoc docs/*.md -o output/ml_docs.pdf \
    --template=templates/ml_template.tex

echo "ML build complete!"
```

### Integration with External Tools

**Example: External simulation tool**:

```python
# scripts/external_simulation.py
#!/usr/bin/env python3
"""Integrate external simulation tool."""
import subprocess
import json
import os

from analysis import process_simulation_results  # From src/

def run_external_tool(config_file):
    """Run external simulation tool."""
    
    # Prepare configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Run external tool
    result = subprocess.run(
        ['external_simulator', '--config', config_file, '--output', 'raw_results.json'],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Load raw results
    with open('raw_results.json', 'r') as f:
        raw_data = json.load(f)
    
    # Use src/ methods for analysis
    processed = process_simulation_results(raw_data)
    
    # Generate visualization
    create_simulation_plots(processed)
    
    return processed

def main():
    configs = ['config1.json', 'config2.json', 'config3.json']
    
    for config in configs:
        print(f"Running simulation: {config}")
        results = run_external_tool(config)
        save_results(results, config)

if __name__ == '__main__':
    main()
```

**See [ARCHITECTURE.md](ARCHITECTURE.md) for architecture principles.**

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
        uv run pytest tests/ --cov=src --cov-report=xml
    
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
        python3 scripts/run_all.py
    
    - name: Upload PDFs
      uses: actions/upload-artifact@v3
      with:
        name: pdfs
        path: output/pdf/*.pdf
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
    """Generate documentation for all src/ modules."""
    src_dir = 'src'
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

---

## Level 12: Research Workflow Integration

**Goal**: Integrate with research tools and workflows

### Literature Review Integration

```python
# scripts/literature_analysis.py
#!/usr/bin/env python3
"""Analyze research trends from literature."""
import requests
from collections import Counter

# Import from src/ (implement these as needed)
from text_analysis import extract_keywords, analyze_trends

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
    
    # Use src/ methods for analysis
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
vim src/new_algorithm.py
vim tests/test_new_algorithm.py

# Ensure coverage requirements met
pytest tests/ --cov=src --cov-report=term-missing

# Commit with conventional commit messages
git add src/new_algorithm.py tests/test_new_algorithm.py
git commit -m "feat: add new optimization algorithm

- Implements gradient-free optimization
- Includes comprehensive tests (meets coverage requirements)
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

## Related Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - System design
- **[Workflow Guide](WORKFLOW.md)** - Development process
- **[Build System](BUILD_SYSTEM.md)** - Performance and status
- **[Contributing Guide](CONTRIBUTING.md)** - Contribution process
- **[Roadmap](ROADMAP.md)** - Future plans

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

**Need help?** Check the **[FAQ](FAQ.md)** or **[Documentation Index](DOCUMENTATION_INDEX.md)**

**Quick Reference**: [Cheatsheet](QUICK_START_CHEATSHEET.md) | [Glossary](GLOSSARY.md)


