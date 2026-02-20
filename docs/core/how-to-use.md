# 🚀 HOW TO USE: Research Project Template

> **Usage Guide** - Navigation hub for all skill levels

This is the **master navigation guide** for using the Research Project Template. Whether you're just getting started or building advanced research workflows, this guide will direct you to the right resources.

## 📚 Guide Organization

The guide is organized into **skill-level focused documents**:

- **[Levels 1-3](#levels-1-3-getting-started)**: Just write documents (no programming)
- **[Levels 4-6](#levels-4-6-intermediate-usage)**: Add figures and automation
- **[Levels 7-9](#levels-7-9-advanced-usage)**: Test-driven development
- **[Levels 10-12](#levels-10-12-expert-usage)**: Custom architectures

Plus:

- **[Quick Start Cheatsheet](#quick-reference-documents)**: One-page essential commands
- **[Common Workflows](#quick-reference-documents)**: Step-by-step recipes
- **[Glossary](#quick-reference-documents)**: Terms and definitions

## 🎯 Find Your Starting Point

**New to the template?**
→ Start with **[Quick Start](#quick-start)** below or **[Getting Started Guide](../guides/getting-started.md)**

**Know what you want to do?**
→ Check **[Common Workflows](../reference/common-workflows.md)** for step-by-step recipes

**Need a specific term explained?**
→ Check the **[Glossary](../reference/glossary.md)**

**Want essential commands only?**
→ Check the **[Quick Start Cheatsheet](../reference/quick-start-cheatsheet.md)**

## 🚀 Quick Start

### For Everyone: Use This Template

1. **Click "Use this template"** on the [GitHub repository](https://github.com/docxology/template)
2. **Clone your new repository**
3. **Install dependencies**: `uv sync`
4. **Generate your first document**: `python3 scripts/execute_pipeline.py --core-only`

That's it! You now have a research project structure.

### What You Get Immediately

- ✅ **project structure** with clear organization
- ✅ **Professional PDF generation** from markdown
- ✅ **Cross-referencing system** for equations and figures
- ✅ **Automated testing** framework (2118 tests: 1796 infrastructure [2 skipped] + 320 project, all passing)
- ✅ **Build pipeline** that validates everything (58-second builds)
- ✅ **Terminal output logging** - all pipeline output saved to timestamped log files
- ✅ **25+ guides** for all skill levels

## 📖 Guides by Skill Level

### Levels 1-3: Getting Started

**for**: Users who just want to write documents without programming

**[📘 Read Getting Started Guide](../guides/getting-started.md)**

**What you'll learn**:

- Set up the template
- Write and format professional documents
- Add equations and cross-references
- Generate publication-ready PDFs
- Customize project metadata

**Time**: 2-3 hours

**Skills required**: Basic computer skills, text editor

---

### Levels 4-6: Intermediate Usage

**for**: Users ready to add custom figures and automation

**[📗 Read Figures and Analysis Guide](../guides/figures-and-analysis.md)**

**What you'll learn**:

- Generate figures from data using scripts
- Understand the thin orchestrator pattern
- Add new Python modules with testing
- Create data analysis pipelines
- Automate workflows

**Time**: 1-2 days

**Skills required**: Basic Python, matplotlib knowledge

**Prerequisites**: [Getting Started Guide](../guides/getting-started.md)

---

### Levels 7-9: Advanced Usage

**for**: Developers ready for test-driven development

**[📕 Read Testing and Reproducibility Guide](../guides/testing-and-reproducibility.md)**

**What you'll learn**:

- Practice test-driven development (TDD)
- Achieve and maintain test coverage
- Build complex mathematical workflows
- Implement testing strategies
- Ensure reproducible research results

**Time**: 1-2 weeks

**Skills required**: Strong Python, testing knowledge

**Prerequisites**: [Figures and Analysis Guide](../guides/figures-and-analysis.md)

---

### Levels 10-12: Expert Usage

**for**: Expert developers building custom systems

**[📙 Read Extending and Automation Guide](../guides/extending-and-automation.md)**

**What you'll learn**:

- Extend the template architecture
- Create custom build pipelines
- Integrate external tools and systems
- Implement continuous integration
- Build automated documentation systems
- Create research workflow integrations

**Time**: 1-2 months

**Skills required**: Expert Python, DevOps, system design

**Prerequisites**: [Testing and Reproducibility Guide](../guides/testing-and-reproducibility.md)

---

## 🎯 Quick Reference Documents

### Quick Start Cheatsheet

**[📋 One-page essential commands](../reference/quick-start-cheatsheet.md)**

Essential commands, quick syntax reference, troubleshooting, and decision tree. for bookmarking.

### Common Workflows

**[📝 Step-by-step recipes](../reference/common-workflows.md)**

workflows for common tasks:

- Write your first document
- Add a new section
- Create a figure with data
- Add mathematical equations
- Cross-reference sections
- Add new Python module
- Write tests
- Debug failures
- Fix coverage
- Generate PDFs
- Customize metadata
- Add supplemental materials
- Contribute to template

### Glossary

**[📖 Terms and definitions](../reference/glossary.md)**

glossary of all terms and concepts used in the template. Alphabetically organized with cross-references.

---

## 🗺️ Learning Path

```
Level 1-3: Getting Started (2-3 hours)
    ↓
Level 4-6: Intermediate Usage (1-2 days)
    ↓
Level 7-9: Advanced Usage (1-2 weeks)
    ↓
Level 10-12: Expert Usage (1-2 months)
```

**Total Time**: 1-3 months to master all levels

**Estimated time to productivity**:

- Basic documents: 2-3 hours
- With figures: 1-2 days
- With testing: 1-2 weeks
- Production systems: 1-2 months

## 📊 What Each Level Covers

| Level | Focus | Time | Prerequisites |
|-------|-------|------|---------------|
| **1** | Write documents | 30-45 min | None |
| **2** | Equations & references | 45-60 min | Level 1 |
| **3** | Customization | 30-45 min | Level 2 |
| **4** | Basic figures | 3-4 hours | Level 3, Basic Python |
| **5** | Data analysis | 4-6 hours | Level 4, Python |
| **6** | Automation | 2-3 hours | Level 5 |
| **7** | Test-driven dev | 3-5 days | Level 6, Testing |
| **8** | Complex workflows | 1 week | Level 7 |
| **9** | Reproducibility | 2-3 days | Level 8 |
| **10** | Custom architectures | 1-2 weeks | Level 9, System design |
| **11** | CI/CD automation | 1-2 weeks | Level 10, DevOps |
| **12** | Research integration | 1-2 weeks | Level 11 |

## 🎓 Recommended Learning Sequences

### For Academic Researchers

1. **[Getting Started](../guides/getting-started.md)** - Write your paper
2. **[Figures and Analysis](../guides/figures-and-analysis.md)** - Add figures and analysis
3. **[Testing and Reproducibility](../guides/testing-and-reproducibility.md)** - Ensure reproducibility

### For Software Developers

1. **[Quick Start Cheatsheet](../reference/quick-start-cheatsheet.md)** - Get oriented fast
2. **[Figures and Analysis](../guides/figures-and-analysis.md)** - Understand the pattern
3. **[Testing and Reproducibility](../guides/testing-and-reproducibility.md)** - Master TDD approach
4. **[Extending and Automation](../guides/extending-and-automation.md)** - Build custom systems

### For Contributors

1. **[Getting Started](../guides/getting-started.md)** - Understand basics
2. **[Testing and Reproducibility](../guides/testing-and-reproducibility.md)** - Learn TDD workflow
3. **[Contributing Guide](../development/contributing.md)** - Contribution process
4. **[Code of Conduct](../development/code-of-conduct.md)** - Community standards

## 📚 Related Documentation

### Core Documentation

- **[AGENTS.md](../AGENTS.md)** - system reference
- **[Architecture](../core/architecture.md)** - System design
- **[Thin Orchestrator Pattern](../architecture/thin-orchestrator-summary.md)** - Core pattern
- **[Workflow](../core/workflow.md)** - Development process

### Build System

- **[Build System](../operational/build-system.md)** - reference (status, performance, fixes)
- **[PDF Validation](../modules/pdf-validation.md)** - Quality checks

### Writing & Formatting

- **[Markdown Template Guide](../usage/markdown-template-guide.md)** - formatting reference
- **[Manuscript Numbering](../usage/manuscript-numbering-system.md)** - Section organization
- **[LaTeX Preamble](../../projects/act_inf_metaanalysis/manuscript/preamble.md)** - Styling configuration example

### Examples & Help

- **[Examples](../usage/examples.md)** - Usage patterns
- **[Examples Showcase](../usage/examples-showcase.md)** - Real-world applications
- **[FAQ](../reference/faq.md)** - Frequently asked questions
- **[Template Description](../usage/template-description.md)** - Overview

### Community

- **[Contributing](../development/contributing.md)** - How to contribute
- **[Code of Conduct](../development/code-of-conduct.md)** - Community standards
- **[Security](../development/security.md)** - Security policy
- **[Roadmap](../development/roadmap.md)** - Future plans

### Reference

- **[Documentation Index](../documentation-index.md)** - index
- **[Copypasta](../reference/copypasta.md)** - Shareable content
- **[API Reference](../reference/api-reference.md)** - API documentation
- **[Best Practices](../best-practices/best-practices.md)** - Consolidated best practices

### Advanced Topics

- **[Two-Layer Architecture](../architecture/two-layer-architecture.md)** - architecture guide
- **[Modules Guide](../modules/modules-guide.md)** - Using all 9 infrastructure modules
- **[Dependency Management](../operational/dependency-management.md)** - uv package manager guide
- **[CI/CD Integration](../operational/ci-cd-integration.md)** - GitHub Actions setup
- **[Performance Optimization](../operational/performance-optimization.md)** - Build time optimization
- **[Migration Guide](../best-practices/migration-guide.md)** - Migrating from other templates

## 🆘 Troubleshooting

Having issues? Here's where to look:

1. **[Troubleshooting Guide](../operational/troubleshooting-guide.md)** - troubleshooting
2. **[FAQ](../reference/faq.md)** - Common questions and solutions
3. **[Common Workflows](../reference/common-workflows.md)** - Step-by-step help
4. **[Quick Start Cheatsheet](../reference/quick-start-cheatsheet.md)** - Quick troubleshooting section
5. **[Glossary](../reference/glossary.md)** - Term definitions
6. **[Build System](../operational/build-system.md)** - Build system details

**Common Issues**:

- Tests fail → [Testing and Reproducibility Guide](../guides/testing-and-reproducibility.md#level-7-test-driven-development)
- Coverage below requirements → [Common Workflows](../reference/common-workflows.md#fix-coverage-below-requirements)
- PDF generation fails → [FAQ](../reference/faq.md#q-my-pdfs-arent-generating-correctly)
- Figures not appearing → [Figures and Analysis](../guides/figures-and-analysis.md#level-4-add-basic-figures)

## 🎯 Your Next Steps

**Choose your path**:

- 📘 **New to template** → [Getting Started Guide](../guides/getting-started.md)
- 📗 **Ready for figures** → [Figures and Analysis Guide](../guides/figures-and-analysis.md)
- 📕 **Want to test properly** → [Testing and Reproducibility Guide](../guides/testing-and-reproducibility.md)
- 📙 **Building custom systems** → [Extending and Automation Guide](../guides/extending-and-automation.md)

**Need quick help**:

- 📋 **Essential commands** → [Quick Start Cheatsheet](../reference/quick-start-cheatsheet.md)
- 📝 **Specific task** → [Common Workflows](../reference/common-workflows.md)
- 📖 **Term definition** → [Glossary](../reference/glossary.md)
- ❓ **Common question** → [FAQ](../reference/faq.md)

---

**Ready to start?** Choose your skill level above and dive in!

**System Status**: ✅ All operational | **Build Time**: 84s (without optional LLM review) | **Coverage**: 100%/90% (project), 83.33%/60% (infra) | **Tests**: 2118 passing

**Need help?** Start with **[Getting Started Guide](../guides/getting-started.md)** or check the **[FAQ](../reference/faq.md)**
