# docs/ - Documentation

## Purpose

The `docs/` directory contains comprehensive project documentation organized by purpose and audience. This is the central hub for all project documentation beyond code comments.

## Documentation Organization

### Core Guides (Essential Reading)

| File | Purpose | Audience |
|------|---------|----------|
| `HOW_TO_USE.md` | Complete usage guide from basic to advanced | New users, developers |
| `ARCHITECTURE.md` | System design and structure | Developers, architects |
| `WORKFLOW.md` | Development workflow and best practices | Developers |

### Template Information

| File | Purpose | Audience |
|------|---------|----------|
| `TEMPLATE_DESCRIPTION.md` | Template overview and features | New users |
| `EXAMPLES.md` | Usage examples and patterns | All users |
| `EXAMPLES_SHOWCASE.md` | Real-world usage examples | Advanced users |

### Development & Contribution

| File | Purpose | Audience |
|------|---------|----------|
| `CONTRIBUTING.md` | How to contribute to the project | Contributors |
| `CODE_OF_CONDUCT.md` | Community guidelines | All participants |
| `SECURITY.md` | Security policies and reporting | All users |
| `ROADMAP.md` | Future development plans | Maintainers, contributors |

### Advanced Topics

| File | Purpose | Audience |
|------|---------|----------|
| `THIN_ORCHESTRATOR_SUMMARY.md` | Architecture pattern details | Developers |
| `PDF_VALIDATION.md` | PDF validation documentation | Developers |
| `MARKDOWN_TEMPLATE_GUIDE.md` | Markdown authoring guide | Content creators |

### Reference & Navigation

| File | Purpose | Audience |
|------|---------|----------|
| `DOCUMENTATION_INDEX.md` | Complete documentation index | All users |
| `FAQ.md` | Frequently asked questions | All users |
| `COPYPASTA.md` | Reusable documentation snippets | Documentation writers |

### Supporting Files

| File | Purpose |
|------|---------|
| `00_preamble.md` | Documentation preamble and styling |

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
- **HOW_TO_USE.md**: Step-by-step usage
- **AGENTS.md**: Complete technical reference
- **Specialized docs**: Deep dives into specific topics

### Keep Current
Documentation must stay synchronized with code:
- Update docs when changing features
- Validate examples regularly
- Review docs during code review
- Archive outdated information

## When to Update Which Docs

### Adding a Feature
1. Update `ROADMAP.md` (remove from planned)
2. Update `HOW_TO_USE.md` (usage instructions)
3. Update relevant `AGENTS.md` (technical details)
4. Add example to `EXAMPLES.md`

### Changing Architecture
1. Update `ARCHITECTURE.md` (design changes)
2. Update `THIN_ORCHESTRATOR_SUMMARY.md` (if pattern affected)
3. Update `WORKFLOW.md` (if workflow changes)
4. Update root `AGENTS.md` (system overview)

### Bug Fixes
1. Update `FAQ.md` (if commonly encountered)
2. Update troubleshooting sections
3. Add preventive guidance if relevant

### Deprecating Features
1. Mark as deprecated in `ROADMAP.md`
2. Update `HOW_TO_USE.md` (migration guide)
3. Update `CONTRIBUTING.md` (don't use deprecated features)
4. Remove examples from `EXAMPLES.md`

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
See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

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
===== 100% coverage =====
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
README.md → HOW_TO_USE.md → ARCHITECTURE.md
    ↓            ↓                ↓
EXAMPLES.md  WORKFLOW.md    Technical Docs
```

### Cross-References
- **HOW_TO_USE.md** references:
  - EXAMPLES.md (usage examples)
  - ARCHITECTURE.md (design understanding)
  - WORKFLOW.md (development process)
  - FAQ.md (troubleshooting)

- **ARCHITECTURE.md** references:
  - THIN_ORCHESTRATOR_SUMMARY.md (pattern details)
  - WORKFLOW.md (how to work with architecture)
  - ../src/AGENTS.md (implementation details)

- **WORKFLOW.md** references:
  - CONTRIBUTING.md (contribution process)
  - ARCHITECTURE.md (understanding structure)
  - ../tests/AGENTS.md (testing approach)

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

### 00_preamble.md
Documentation-specific LaTeX preamble (if generating docs as PDFs):
- Not rendered standalone
- Provides styling for documentation PDFs
- Similar to `manuscript/preamble.md` but for docs

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
2. Read `HOW_TO_USE.md` (complete guide)
3. Review `EXAMPLES.md` (usage patterns)
4. Check `FAQ.md` (common questions)

### For Developers
1. Review `ARCHITECTURE.md` (system design)
2. Read `THIN_ORCHESTRATOR_SUMMARY.md` (pattern)
3. Follow `WORKFLOW.md` (development process)
4. Check `CONTRIBUTING.md` (contribution guide)

### For Advanced Users
1. Deep dive into `ARCHITECTURE.md`
2. Review `PDF_VALIDATION.md`
3. Study `EXAMPLES_SHOWCASE.md`
4. Explore `ROADMAP.md` (future features)

## See Also

- [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - Complete documentation index
- [`HOW_TO_USE.md`](HOW_TO_USE.md) - Comprehensive usage guide
- [`../AGENTS.md`](../AGENTS.md) - Root system documentation
- [`../README.md`](../README.md) - Project overview

