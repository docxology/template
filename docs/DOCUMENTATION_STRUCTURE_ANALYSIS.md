# Documentation Structure Analysis

**Generated**: 2025-01-XX  
**Purpose**: Analysis of documentation structure patterns and required sections

## AGENTS.md Structure Pattern

### Standard Sections (Recommended Order)

Based on `.cursorrules/documentation_standards.md` and analysis of existing files:

1. **Title** - `# [Module/Directory Name] Documentation`
2. **Overview** (Required)
   - What is this module/directory?
   - Why does it exist?
   - Who should use it?
   - 50-100 words
3. **Key Concepts** (Optional)
   - Terminology specific to this module
   - Architecture overview
   - Important principles
4. **File Organization** / **Directory Structure** (Required for directories)
   - Directory structure
   - Purpose of each file
5. **Installation/Setup** (If applicable)
   - Prerequisites
   - Installation steps
   - Configuration
6. **Usage Examples** / **Quick Example** (Required)
   - Common tasks with code samples
   - Real-world scenarios
   - Copy-paste ready examples
7. **Configuration** (If applicable)
   - All configuration options
   - Environment variables
   - Config file format
8. **API Reference** (For modules with code)
   - Key classes and functions
   - Import statements
   - Parameters and returns
9. **Testing** (For modules with tests)
   - How to run tests
   - Test structure
   - Writing new tests
10. **Troubleshooting** (Optional but recommended)
    - Common issues
    - Solutions
    - Debug tips
11. **Best Practices** (Optional)
    - Do's and don'ts
    - Performance tips
    - Security considerations
12. **See Also** / **References** (Required)
    - Related documentation
    - External resources
    - Cross-references

### Observed Variations

**Root AGENTS.md:**
- System Overview
- Table of Contents
- Core Architecture
- Repository Structure
- Directory-Level Documentation
- Configuration System
- Rendering Pipeline
- Validation Systems
- Testing Framework
- Output Formats
- Advanced Modules
- Troubleshooting
- Maintenance
- References
- Best Practices
- System Status

**Infrastructure Module AGENTS.md:**
- Overview
- New Modular Architecture
- Key Design Principles
- Module Organization
- Design Principles
- Integration with Build Pipeline
- Configuration
- Usage Examples
- Testing
- Troubleshooting
- Migration Guide
- Architecture Advantages
- Future Enhancements
- See Also

**Project Module AGENTS.md:**
- Purpose
- Architectural Role (Layer 2)
- Module Organization
- Module Descriptions
- Usage Examples
- Testing
- See Also

## README.md Structure Pattern

### Standard Sections (Recommended Order)

1. **Title** - `# [Module Name]`
2. **One-line description** (Required)
   - Brief description of purpose
3. **Quick Start** (Required)
   - Minimal working example
   - 5-10 lines of code
4. **Key Features** / **Overview** (Optional)
   - 3-5 bullet points
   - Key capabilities
5. **Installation** (If applicable)
   - Copy-paste commands
6. **Common Commands** / **Usage** (Required)
   - 3-5 most used tasks
   - Command examples
7. **Modules** / **Components** (For directories with submodules)
   - List of key modules/components
8. **More Information** / **See Also** (Required)
   - Link to AGENTS.md
   - Related documentation

### Observed Variations

**Root README.md:**
- Project overview
- What This Template Provides
- Choose Your Path (user type navigation)
- Documentation Navigation Map
- Quick Start
- System Health & Metrics
- Learning Paths
- Project Structure
- Key Architectural Principles
- Key Features
- Installation & Setup
- Customization
- Testing
- Output
- How It Works
- Complete Documentation Index
- Contributing
- License
- Citation
- Troubleshooting
- Migration
- Architecture Benefits
- Quick Links by User Type

**Infrastructure Module README.md:**
- Title with one-line description
- Quick Start (code examples)
- Modules (list)
- Key Classes & Functions
- Environment Variables
- Testing
- Link to AGENTS.md

**Project Module README.md:**
- Title with one-line description
- What's Here
- Quick Start
- Modules (table)
- Key Concepts
- File Organization
- Testing
- See Also
- Quick Facts

## Required Sections Checklist

### AGENTS.md Required Sections

- [ ] **Title** - `# [Name] Documentation`
- [ ] **Overview** - What, why, who
- [ ] **Usage Examples** - At least one working example
- [ ] **See Also** - Links to related documentation

### AGENTS.md Optional but Recommended

- [ ] **File Organization** - For directories
- [ ] **Configuration** - If configurable
- [ ] **API Reference** - For code modules
- [ ] **Testing** - If tests exist
- [ ] **Troubleshooting** - Common issues
- [ ] **Best Practices** - Guidelines

### README.md Required Sections

- [ ] **Title** - `# [Name]`
- [ ] **One-line description**
- [ ] **Quick Start** - Minimal example
- [ ] **Common Commands** - 3-5 most used tasks
- [ ] **More Information** - Link to AGENTS.md

### README.md Optional Sections

- [ ] **Key Features** - Bullet points
- [ ] **Installation** - If needed
- [ ] **Modules** - For directories
- [ ] **Environment Variables** - If applicable

## Terminology Standards

### Layer Terminology

**Consistent Terms:**
- **Layer 1** = Infrastructure (generic, reusable)
- **Layer 2** = Project (project-specific, customizable)
- **Infrastructure** = Generic tools (Layer 1)
- **Project** = Research-specific code (Layer 2)

**Should NOT mix:**
- ❌ "Generic layer" vs "Layer 1"
- ❌ "Project layer" vs "Layer 2"
- ❌ "Infrastructure layer" vs "Layer 1"

### Pipeline Terminology

**Consistent Terms:**
- **Stage 0-8** = Extended pipeline (run.sh, displayed as [1/9] to [8/9])
- **Stage 00-05** = Core pipeline (run_all.py, zero-padded)
- **./run.sh** = Interactive menu orchestrator
- **run_all.py** = Python orchestrator

**Should clarify:**
- Which entry point is being discussed
- Stage numbering convention used

### Coverage Terminology

**Consistent Terms:**
- **Infrastructure**: 49% minimum (currently 55.89%)
- **Project**: 70% minimum (currently 99.88%)
- **Test counts**: 878 tests (558 infrastructure + 320 project)

## Formatting Standards

### Code Blocks

**Required:**
- Language tag must be specified
- `bash` for shell commands
- `python` for Python code
- `markdown` for markdown examples
- `yaml` for configuration files

**Example:**
```bash
python3 scripts/00_setup_environment.py
```

### Links

**Internal Links:**
- Use relative paths: `[text](path/to/file.md)`
- Link to AGENTS.md from README.md: `[AGENTS.md](AGENTS.md)`
- Link to parent docs: `[../README.md](../README.md)`

**External Links:**
- Use descriptive text: `[Pandoc Manual](https://pandoc.org/MANUAL.html)`
- Never use bare URLs

### Tables

**Format:**
- Use markdown tables with alignment
- Include headers
- Use consistent column widths

### Emphasis

**Consistent Usage:**
- **Bold** for UI elements, commands, file names
- *Italic* for emphasis, terms being defined
- `Code` for inline code, file paths, functions
- > Blockquotes for important notes

## Cross-Reference Patterns

### Standard Cross-References

**From README.md to AGENTS.md:**
```markdown
See [AGENTS.md](AGENTS.md) for comprehensive documentation.
```

**From AGENTS.md to related docs:**
```markdown
## See Also

- [`../README.md`](../README.md) - Quick reference
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) - Architecture guide
```

**From docs/ to other docs/:**
```markdown
See [`ARCHITECTURE.md`](ARCHITECTURE.md) for system design.
```

## Documentation Completeness Matrix

| File Type | Required Sections | Recommended Sections | Optional Sections |
|-----------|------------------|----------------------|-------------------|
| **AGENTS.md** | Overview, Usage Examples, See Also | File Organization, Configuration, API Reference, Testing, Troubleshooting | Key Concepts, Best Practices, Migration Guide |
| **README.md** | Title, Description, Quick Start, Common Commands, Link to AGENTS.md | Key Features, Installation, Modules | Environment Variables, Testing |

## Structure Validation Checklist

For each AGENTS.md file:
- [ ] Has Overview section
- [ ] Has at least one Usage Example
- [ ] Has See Also section with links
- [ ] Uses consistent terminology
- [ ] Code blocks have language tags
- [ ] Links use relative paths
- [ ] Tables are properly formatted

For each README.md file:
- [ ] Has one-line description
- [ ] Has Quick Start section
- [ ] Has Common Commands section
- [ ] Links to AGENTS.md
- [ ] Uses consistent terminology
- [ ] Code blocks have language tags
- [ ] Links use relative paths

