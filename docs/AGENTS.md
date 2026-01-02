# docs/ - Documentation

> **Documentation hub** for the Research Project Template

**Quick Reference:** [Documentation Index](DOCUMENTATION_INDEX.md) | [How To Use](core/HOW_TO_USE.md) | [Architecture](core/ARCHITECTURE.md) | [FAQ](reference/FAQ.md)

## Purpose

The `docs/` directory contains comprehensive project documentation organized by purpose and audience. This is the central hub for all project documentation beyond code comments.

## Documentation Organization

Documentation is organized into modular subdirectories by purpose and audience:

### Core Documentation (`core/`)

| File | Purpose | Audience |
|------|---------|----------|
| `core/HOW_TO_USE.md` | Complete usage guide from basic to advanced | New users, developers |
| `core/ARCHITECTURE.md` | System design and structure | Developers, architects |
| `core/WORKFLOW.md` | Development workflow and best practices | Developers |

### Usage Guides (`guides/`)

| File | Purpose | Audience |
|------|---------|----------|
| `guides/GETTING_STARTED.md` | Basic usage guide (Levels 1-3) | Beginners |
| `guides/FIGURES_AND_ANALYSIS.md` | Intermediate usage (Levels 4-6) | Intermediate users |
| `guides/TESTING_AND_REPRODUCIBILITY.md` | Advanced usage (Levels 7-9) | Advanced users |
| `guides/EXTENDING_AND_AUTOMATION.md` | Expert usage (Levels 10-12) | Expert users |

### Architecture Documentation (`architecture/`)

| File | Purpose | Audience |
|------|---------|----------|
| `architecture/TWO_LAYER_ARCHITECTURE.md` | Complete two-layer architecture guide | Developers, architects |
| `architecture/THIN_ORCHESTRATOR_SUMMARY.md` | Architecture pattern details | Developers |
| `architecture/DECISION_TREE.md` | Code placement decisions | Developers |

### Usage Examples (`usage/`)

| File | Purpose | Audience |
|------|---------|----------|
| `usage/TEMPLATE_DESCRIPTION.md` | Template overview and features | New users |
| `usage/EXAMPLES.md` | Usage examples and patterns | All users |
| `usage/EXAMPLES_SHOWCASE.md` | Real-world usage examples | Advanced users |
| `usage/MARKDOWN_TEMPLATE_GUIDE.md` | Markdown authoring guide | Content creators |
| `usage/MANUSCRIPT_NUMBERING_SYSTEM.md` | Manuscript section numbering system | Content creators |

### Operational Guides (`operational/`)

| File | Purpose | Audience |
|------|---------|----------|
| `operational/BUILD_SYSTEM.md` | Build pipeline and execution details | Developers |
| `operational/TROUBLESHOOTING_GUIDE.md` | Comprehensive troubleshooting | All users |
| `operational/CONFIGURATION.md` | Configuration system guide | All users |

### Reference Materials (`reference/`)

| File | Purpose | Audience |
|------|---------|----------|
| `reference/FAQ.md` | Frequently asked questions | All users |
| `reference/API_REFERENCE.md` | Complete API documentation | Developers |
| `reference/GLOSSARY.md` | Terms and definitions | All users |
| `reference/QUICK_START_CHEATSHEET.md` | Essential commands reference | All users |
| `reference/../reference/COMMON_WORKFLOWS.md` | Step-by-step workflow recipes | All users |
| `reference/COPYPASTA.md` | Reusable documentation snippets | Documentation writers |

### Advanced Modules (`modules/`)

| File | Purpose | Audience |
|------|---------|----------|
| `modules/MODULES_GUIDE.md` | Guide for all 7 modules | Developers |
| `modules/PDF_VALIDATION.md` | PDF validation documentation | Developers |
| `modules/SCIENTIFIC_SIMULATION_GUIDE.md` | Scientific simulation system | Researchers |

### Development & Contribution (`development/`)

| File | Purpose | Audience |
|------|---------|----------|
| `development/CONTRIBUTING.md` | How to contribute to the project | Contributors |
| `development/CODE_OF_CONDUCT.md` | Community guidelines | All participants |
| `development/SECURITY.md` | Security policies and reporting | All users |
| `development/ROADMAP.md` | Future development plans | Maintainers, contributors |
| `development/TESTING_GUIDE.md` | Testing framework guide | Developers |

### Best Practices (`best-practices/`)

| File | Purpose | Audience |
|------|---------|----------|
| `best-practices/BEST_PRACTICES.md` | Consolidated best practices | All users |
| `best-practices/VERSION_CONTROL.md` | Git workflows and best practices | Developers |
| `best-practices/MIGRATION_GUIDE.md` | Migration from other templates | Developers |
| `best-practices/BACKUP_RECOVERY.md` | Backup strategies and recovery | All users |

### AI Prompt Templates (`prompts/`)

| File | Purpose | Audience |
|------|---------|----------|
| `prompts/README.md` | Quick reference guide for all prompts | All users |
| `prompts/AGENTS.md` | Technical documentation for prompt templates | Developers |
| `prompts/manuscript_creation.md` | Complete manuscript creation from research description | Researchers |
| `prompts/code_development.md` | Standards-compliant code development | Developers |
| `prompts/test_creation.md` | Comprehensive test creation (no mocks) | Developers |
| `prompts/refactoring.md` | Clean break code refactoring | Developers |
| `prompts/feature_addition.md` | New feature development with architecture compliance | Developers |
| `prompts/documentation_creation.md` | AGENTS.md and README.md creation | Technical writers |
| `prompts/infrastructure_module.md` | Generic infrastructure module development | Architects |
| `prompts/validation_quality.md` | Quality assurance and validation | QA engineers |

## Development Rules

The `.cursorrules/` directory contains modular development rules that complement this documentation. Each rule file covers specific development standards:

| Rule Module | Focus Area |
|-------------|-----------|
| [`../.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md) | Complete overview and navigation guide |
| [`../.cursorrules/README.md`](../.cursorrules/README.md) | Quick reference and patterns |
| [`../.cursorrules/error_handling.md`](../.cursorrules/error_handling.md) | Exception handling patterns |
| [`../.cursorrules/security.md`](../.cursorrules/security.md) | Security standards and guidelines |
| [`../.cursorrules/python_logging.md`](../.cursorrules/python_logging.md) | Logging standards and best practices |
| [`../.cursorrules/infrastructure_modules.md`](../.cursorrules/infrastructure_modules.md) | Infrastructure module development |
| [`../.cursorrules/testing_standards.md`](../.cursorrules/testing_standards.md) | Testing patterns and coverage standards |
| [`../.cursorrules/documentation_standards.md`](../.cursorrules/documentation_standards.md) | AGENTS.md and README.md writing guide |
| [`../.cursorrules/type_hints_standards.md`](../.cursorrules/type_hints_standards.md) | Type annotation patterns |
| [`../.cursorrules/llm_standards.md`](../.cursorrules/llm_standards.md) | LLM/Ollama integration patterns |
| [`../.cursorrules/code_style.md`](../.cursorrules/code_style.md) | Code formatting and style standards |
| [`../.cursorrules/git_workflow.md`](../.cursorrules/git_workflow.md) | Git workflow and commit standards |
| [`../.cursorrules/api_design.md`](../.cursorrules/api_design.md) | API design and interface standards |
| [`../.cursorrules/manuscript_style.md`](../.cursorrules/manuscript_style.md) | Manuscript formatting and style standards |

**Quick Access**: Use `.cursorrules/` files for rule reference during development; consult `docs/` files for comprehensive guides.

## Documentation Philosophy

### Show, Don't Tell
Documentation should demonstrate through examples rather than lengthy explanations:
- ✅ Code examples with clear outcomes
- ✅ Command sequences with expected results
- ✅ Diagrams and visual aids
- ❌ Excessive prose without examples
- ❌ Theoretical explanations without practical use

### Layered Information
- **README.md**: Quick start, essential links
- **core/HOW_TO_USE.md**: Step-by-step usage
- **AGENTS.md**: Complete technical reference
- **Specialized docs**: Deep dives into specific topics (organized by subdirectory)

### Keep Current
Documentation must stay synchronized with code:
- Update docs when changing features
- Validate examples regularly
- Review docs during code review
- Archive outdated information

## When to Update Which Docs

### Adding a Feature
1. Update `development/ROADMAP.md` (remove from planned)
2. Update `core/HOW_TO_USE.md` (usage instructions)
3. Update relevant `AGENTS.md` (technical details)
4. Add example to `usage/EXAMPLES.md`

### Changing Architecture
1. Update `core/ARCHITECTURE.md` (design changes)
2. Update `architecture/THIN_ORCHESTRATOR_SUMMARY.md` (if pattern affected)
3. Update `core/WORKFLOW.md` (if workflow changes)
4. Update root `AGENTS.md` (system overview)

### Bug Fixes
1. Update `reference/FAQ.md` (if commonly encountered)
2. Update `operational/TROUBLESHOOTING_GUIDE.md` troubleshooting sections
3. Add preventive guidance if relevant

### Deprecating Features
1. Mark as deprecated in `development/ROADMAP.md`
2. Update `core/HOW_TO_USE.md` (migration guide)
3. Update `development/CONTRIBUTING.md` (don't use deprecated features)
4. Remove examples from `usage/EXAMPLES.md`

## Documentation Style Guide

### Headings
- Use ATX-style headings (`#`, `##`, `###`)
- One `#` per document (document title)
- Hierarchical structure (don't skip levels)
- Descriptive, not clever

### Code Blocks
```markdown
# Always specify language
```bash
command --with-flags
```

```python
def example():
    return "formatted"
```
```

### Links
```markdown
# Internal links (relative paths)
See [../core/ARCHITECTURE.md](../core/ARCHITECTURE.md) for details.

# External links (descriptive text)
Check the [Pandoc Manual](https://pandoc.org/MANUAL.html).

# NOT this
See https://pandoc.org/MANUAL.html
```

### Lists
- Use `-` for unordered lists
- Use `1.` for ordered lists (auto-numbering)
- Indent sublists with 2 spaces
- Blank line before and after lists

### Emphasis
- **Bold** for UI elements, commands, file names
- *Italic* for emphasis, terms being defined
- `Code` for inline code, file paths, functions
- > Blockquotes for important notes

### Examples
Always include complete, runnable examples:
```bash
# Bad: Incomplete example
pytest tests/

# Good: Complete with output
$ pytest tests/ --cov=src
===== Coverage: 100% =====
```

## Documentation Maintenance

### Regular Reviews
- Quarterly review of all docs
- Validate all links work
- Run all code examples
- Update version-specific information
- Check for outdated screenshots

### Version Control
- Document changes in commit messages
- Use semantic versioning for doc updates
- Tag major documentation releases
- Maintain changelog for docs

### Quality Checks
```bash
# Check markdown syntax
markdownlint docs/*.md

# Validate links
markdown-link-check docs/*.md

# Check spelling
aspell check docs/*.md
```

## File Relationships

### Documentation Flow
```
README.md → core/HOW_TO_USE.md → core/ARCHITECTURE.md
    ↓            ↓                      ↓
usage/EXAMPLES.md  core/WORKFLOW.md    Technical Docs
```

### Cross-References
- **core/HOW_TO_USE.md** references:
  - usage/EXAMPLES.md (usage examples)
  - core/ARCHITECTURE.md (design understanding)
  - core/WORKFLOW.md (development process)
  - reference/FAQ.md (troubleshooting)

- **core/ARCHITECTURE.md** references:
  - architecture/TWO_LAYER_ARCHITECTURE.md (complete architecture guide)
  - architecture/THIN_ORCHESTRATOR_SUMMARY.md (pattern details)
  - core/WORKFLOW.md (how to work with architecture)
  - ../../infrastructure/AGENTS.md (infrastructure implementation details)
  - ../../projects/code_project/src/AGENTS.md (project implementation details)

- **core/WORKFLOW.md** references:
  - development/CONTRIBUTING.md (contribution process)
  - core/ARCHITECTURE.md (understanding structure)
  - ../../tests/AGENTS.md (testing approach)

## Contributing to Documentation

### Adding New Documentation
1. Determine appropriate file or create new one
2. Follow style guide
3. Add to DOCUMENTATION_INDEX.md
4. Cross-reference from related docs
5. Update this AGENTS.md

### Improving Existing Documentation
1. Identify unclear sections
2. Add examples or clarifications
3. Test all code examples
4. Validate links still work
5. Submit with clear description of improvements

### Documentation Checklist
- [ ] Clear purpose stated at the top
- [ ] Examples are complete and runnable
- [ ] Links use relative paths for internal docs
- [ ] Code blocks specify language
- [ ] Headings are hierarchical
- [ ] No bare URLs (use link text)
- [ ] Spell-checked
- [ ] Added to DOCUMENTATION_INDEX.md
- [ ] Cross-referenced from related docs

## Special Files

### COPYPASTA.md
Reusable documentation snippets:
- Common command sequences
- Standard explanations
- Installation instructions
- Troubleshooting steps
- Reduces duplication across docs

### DOCUMENTATION_INDEX.md
Master index of all documentation:
- Organized by category
- Links to all docs
- Brief description of each
- Updated with every new doc

## Quick Navigation

### For New Users
1. Start with `../README.md` (project overview)
2. Read `core/HOW_TO_USE.md` (complete guide)
3. Review `usage/EXAMPLES.md` (usage patterns)
4. Check `reference/FAQ.md` (common questions)

### For Developers
1. Review `core/ARCHITECTURE.md` (system design)
2. Read `architecture/THIN_ORCHESTRATOR_SUMMARY.md` (pattern)
3. Follow `core/WORKFLOW.md` (development process)
4. Check `development/CONTRIBUTING.md` (contribution guide)

### For Advanced Users
1. Deep dive into `core/ARCHITECTURE.md`
2. Review `modules/PDF_VALIDATION.md`
3. Study `usage/EXAMPLES_SHOWCASE.md`
4. Explore `development/ROADMAP.md` (future features)

## See Also

- [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - Complete documentation index
- [`core/HOW_TO_USE.md`](core/HOW_TO_USE.md) - Comprehensive usage guide
- [`../AGENTS.md`](../AGENTS.md) - Root system documentation
- [`../README.md`](../README.md) - Project overview

