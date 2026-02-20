# docs/ - Documentation

> **Documentation hub** for the Research Project Template

**Quick Reference:** [Documentation Index](documentation-index.md) | [How To Use](core/how-to-use.md) | [Architecture](core/architecture.md) | [FAQ](reference/faq.md)

## Purpose

The `docs/` directory contains project documentation organized by purpose and audience. This is the central hub for all project documentation beyond code comments.

## Documentation Organization

Documentation is organized into modular subdirectories by purpose and audience:

### Core Documentation (`core/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `core/how-to-use.md` | usage guide from basic to advanced | New users, developers |
| `core/architecture.md` | System design and structure | Developers, architects |
| `core/workflow.md` | Development workflow and best practices | Developers |

### Usage Guides (`guides/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `guides/getting-started.md` | Basic usage guide (Levels 1-3) | Beginners |
| `guides/figures-and-analysis.md` | Intermediate usage (Levels 4-6) | Intermediate users |
| `guides/testing-and-reproducibility.md` | Advanced usage (Levels 7-9) | Advanced users |
| `guides/extending-and-automation.md` | Expert usage (Levels 10-12) | Expert users |

### Architecture Documentation (`architecture/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `architecture/two-layer-architecture.md` | two-layer architecture guide | Developers, architects |
| `architecture/thin-orchestrator-summary.md` | Architecture pattern details | Developers |
| `architecture/decision-tree.md` | Code placement decisions | Developers |

### Usage Examples (`usage/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `usage/template-description.md` | Template overview and features | New users |
| `usage/examples.md` | Usage examples and patterns | All users |
| `usage/examples-showcase.md` | Real-world usage examples | Advanced users |
| `usage/markdown-template-guide.md` | Markdown authoring guide | Content creators |
| `usage/manuscript-numbering-system.md` | Manuscript section numbering system | Content creators |

### Operational Guides (`operational/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `operational/build-history.md` | Build history and changelog | Developers |
| `operational/build-system.md` | Build pipeline and execution details | Developers |
| `operational/ci-cd-integration.md` | CI/CD setup and GitHub Actions | Developers |
| `operational/dependency-management.md` | Package management with uv | Developers |
| `operational/performance-optimization.md` | Build time optimization and caching | Developers |
| `operational/configuration.md` | Configuration system guide | All users |
| `operational/checkpoint-resume.md` | Checkpoint and resume system | Developers |
| `operational/reporting-guide.md` | Reporting system and report interpretation | Developers |
| `operational/troubleshooting-guide.md` | troubleshooting | All users |
| `operational/llm-review-troubleshooting.md` | LLM-specific troubleshooting | Developers |
| `operational/error-handling-guide.md` | Error handling patterns | Developers |
| `operational/logging-guide.md` | Logging system guide | Developers |

### Reference Materials (`reference/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `reference/faq.md` | Frequently asked questions | All users |
| `reference/api-reference.md` | API documentation | Developers |
| `reference/glossary.md` | Terms and definitions | All users |
| `reference/quick-start-cheatsheet.md` | Essential commands reference | All users |
| `reference/common-workflows.md` | Step-by-step workflow recipes | All users |
| `reference/copypasta.md` | Reusable documentation snippets | Documentation writers |

### Advanced Modules (`modules/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `modules/modules-guide.md` | Guide for all 9 infrastructure modules | Developers |
| `modules/pdf-validation.md` | PDF validation documentation | Developers |
| `modules/scientific-simulation-guide.md` | Scientific simulation system | Researchers |

### Per-Module Guides (`modules/guides/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `modules/guides/integrity-module.md` | Integrity module guide | Developers |
| `modules/guides/llm-module.md` | LLM module guide | Developers |
| `modules/guides/publishing-module.md` | Publishing module guide | Developers |
| `modules/guides/rendering-module.md` | Rendering module guide | Developers |
| `modules/guides/reporting-module.md` | Reporting module guide | Developers |
| `modules/guides/scientific-module.md` | Scientific module guide | Developers |

### Logging Guides (`operational/logging/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `operational/logging/bash-logging.md` | Bash logging patterns | Developers |
| `operational/logging/python-logging.md` | Python logging patterns | Developers |
| `operational/logging/logging-patterns.md` | Cross-language logging patterns | Developers |

### Troubleshooting Guides (`operational/troubleshooting/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `operational/troubleshooting/build-tools.md` | Build tool troubleshooting | Developers |
| `operational/troubleshooting/common-errors.md` | Common error patterns and fixes | All users |
| `operational/troubleshooting/environment-setup.md` | Environment setup issues | All users |
| `operational/troubleshooting/recovery-procedures.md` | Recovery procedures | Developers |
| `operational/troubleshooting/test-failures.md` | Test failure troubleshooting | Developers |

### Development & Contribution (`development/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `development/contributing.md` | How to contribute to the project | Contributors |
| `development/code-of-conduct.md` | Community guidelines | All participants |
| `development/security.md` | Security policies and reporting | All users |
| `development/roadmap.md` | Future development plans | Maintainers, contributors |
| `development/testing-guide.md` | Testing framework guide | Developers |
| `development/testing-with-credentials.md` | Testing with external service credentials | Developers |
| `development/coverage-gaps.md` | Test coverage gap analysis | Developers |

### Best Practices (`best-practices/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `best-practices/best-practices.md` | Consolidated best practices | All users |
| `best-practices/version-control.md` | Git workflows and best practices | Developers |
| `best-practices/migration-guide.md` | Migration from other templates | Developers |
| `best-practices/multi-project-management.md` | Managing multiple projects | Developers |
| `best-practices/backup-recovery.md` | Backup strategies and recovery | All users |

### AI Prompt Templates (`prompts/`)

| File | Purpose | Audience |
| ------ | --------- | ---------- |
| `prompts/README.md` | Quick reference guide for all prompts | All users |
| `prompts/AGENTS.md` | Technical documentation for prompt templates | Developers |
| `prompts/manuscript_creation.md` | manuscript creation from research description | Researchers |
| `prompts/code_development.md` | Standards-compliant code development | Developers |
| `prompts/test_creation.md` | test creation (no mocks) | Developers |
| `prompts/refactoring.md` | Clean break code refactoring | Developers |
| `prompts/feature_addition.md` | feature development with architecture compliance | Developers |
| `prompts/documentation_creation.md` | AGENTS.md and README.md creation | Technical writers |
| `prompts/infrastructure_module.md` | Generic infrastructure module development | Architects |
| `prompts/validation_quality.md` | Quality assurance and validation | QA engineers |
| `prompts/comprehensive_assessment.md` | Comprehensive assessment and review | QA engineers |

## Development Rules

The `.cursorrules/` directory contains modular development rules that complement this documentation. Each rule file covers specific development standards:

| Rule Module | Focus Area |
| ------------- | ----------- |
| [`../.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md) | Overview and navigation guide |
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
| [`../.cursorrules/reporting.md`](../.cursorrules/reporting.md) | Reporting module standards and outputs |
| [`../.cursorrules/refactoring.md`](../.cursorrules/refactoring.md) | Refactoring and modularization standards |
| [`../.cursorrules/folder_structure.md`](../.cursorrules/folder_structure.md) | Folder structure and organization standards |

**Quick Access**: Use `.cursorrules/` files for rule reference during development; consult `docs/` files for guides.

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
- **core/how-to-use.md**: Step-by-step usage
- **AGENTS.md**: technical reference
- **Specialized docs**: Deep dives into specific topics (organized by subdirectory)

### Keep Current

Documentation must stay synchronized with code:

- Update docs when changing features
- Validate examples regularly
- Review docs during code review
- Archive outdated information

## When to Update Which Docs

### Adding a Feature

1. Update `development/roadmap.md` (remove from planned)
2. Update `core/how-to-use.md` (usage instructions)
3. Update relevant `AGENTS.md` (technical details)
4. Add example to `usage/examples.md`

### Changing Architecture

1. Update `core/architecture.md` (design changes)
2. Update `architecture/thin-orchestrator-summary.md` (if pattern affected)
3. Update `core/workflow.md` (if workflow changes)
4. Update root `AGENTS.md` (system overview)

### Bug Fixes

1. Update `reference/faq.md` (if commonly encountered)
2. Update `operational/troubleshooting-guide.md` troubleshooting sections
3. Add preventive guidance if relevant

### Deprecating Features

1. Mark as deprecated in `development/roadmap.md`
2. Update `core/how-to-use.md` (migration guide)
3. Update `development/contributing.md` (don't use deprecated features)
4. Remove examples from `usage/examples.md`

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

```text

### Links
```markdown
# Internal links (relative paths)
See [core/architecture.md](core/architecture.md) for details.

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

Always include, runnable examples:

```bash
# Bad: Incomplete example
pytest tests/

# Good: with output
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

```text
README.md → core/how-to-use.md → core/architecture.md
    ↓            ↓                      ↓
usage/examples.md  core/workflow.md    Technical Docs
```

### Cross-References

- **core/how-to-use.md** references:
  - usage/examples.md (usage examples)
  - core/architecture.md (design understanding)
  - core/workflow.md (development process)
  - reference/faq.md (troubleshooting)

- **core/architecture.md** references:
  - architecture/two-layer-architecture.md (architecture guide)
  - architecture/thin-orchestrator-summary.md (pattern details)
  - core/workflow.md (how to work with architecture)
  - ../../infrastructure/AGENTS.md (infrastructure implementation details)
  - ../../projects/act_inf_metaanalysis/src/AGENTS.md (project implementation details)

- **core/workflow.md** references:
  - development/contributing.md (contribution process)
  - core/architecture.md (understanding structure)
  - ../../tests/AGENTS.md (testing approach)

## Contributing to Documentation

### Adding New Documentation

1. Determine appropriate file or create new one
2. Follow style guide
3. Add to documentation-index.md
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
- [ ] Examples are and runnable
- [ ] Links use relative paths for internal docs
- [ ] Code blocks specify language
- [ ] Headings are hierarchical
- [ ] No bare URLs (use link text)
- [ ] Spell-checked
- [ ] Added to documentation-index.md
- [ ] Cross-referenced from related docs

## Special Files

### copypasta.md

Reusable documentation snippets:

- Common command sequences
- Standard explanations
- Installation instructions
- Troubleshooting steps
- Reduces duplication across docs

### documentation-index.md

Master index of all documentation:

- Organized by category
- Links to all docs
- Brief description of each
- Updated with every new doc

## Quick Navigation

### For New Users

1. Start with `../README.md` (project overview)
2. Read `core/how-to-use.md` (guide)
3. Review `usage/examples.md` (usage patterns)
4. Check `reference/faq.md` (common questions)

### For Developers

1. Review `core/architecture.md` (system design)
2. Read `architecture/thin-orchestrator-summary.md` (pattern)
3. Follow `core/workflow.md` (development process)
4. Check `development/contributing.md` (contribution guide)

### For Advanced Users

1. Deep dive into `core/architecture.md`
2. Review `modules/pdf-validation.md`
3. Study `usage/examples-showcase.md`
4. Explore `development/roadmap.md` (future features)

## See Also

- [`documentation-index.md`](documentation-index.md) - documentation index
- [`core/how-to-use.md`](core/how-to-use.md) - usage guide
- [`../AGENTS.md`](../AGENTS.md) - Root system documentation
- [`../README.md`](../README.md) - Project overview
