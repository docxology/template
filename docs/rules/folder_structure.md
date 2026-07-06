# Folder Structure Documentation Standard

## Overview

This document establishes the mandatory folder structure documentation pattern that applies to every directory in the Research Project Template. Every directory must follow this pattern to ensure consistent, documentation across the entire codebase.

## Core Documentation Pattern

### Mandatory Files

Every directory **must** contain at least two documentation files:

1. **`AGENTS.md`** — technical documentation (REQUIRED)
2. **`README.md`** — quick human reference guide (REQUIRED)

Per-subdirectory specialization files **may** also appear when the
content warrants them — these are not optional decorations, they are
load-bearing for the conventions they encode:

| File | Where it appears | Purpose |
|------|------------------|---------|
| `STYLE.md` | `src/` | Source-code style + design conventions for the module |
| `PATTERNS.md` | `tests/` | Copy-pasteable test patterns (fixtures, parametrize, error-paths) |
| `CONVENTIONS.md` | `scripts/` | Thin-orchestrator rules + CLI / output / exit-code contracts |

The code and prose exemplars (`projects/templates/template_code_project/`,
`projects/templates/template_prose_project/`) ship all three at the appropriate
locations as of the May 2026 sibling-parity hardening pass; new
projects should mirror that layout when they need the full docs/style pattern.

### Pattern Enforcement

The two-mandatory-file (AGENTS.md + README.md) rule is universal. The
specialization files above are recommended at the `src/`/`tests/`/`scripts/`
level. The drift checker (`scripts/audit/check_template_drift.py`,
`missing_canonical_file` detector) gates the mandatory files; the
specialization files are AESTHETIC and enforced by audit only.

```mermaid
flowchart LR
    DIR[directory/]
    DIR --> AG[AGENTS.md<br/>REQUIRED · technical documentation]
    DIR --> RD[README.md<br/>REQUIRED · quick reference + Mermaid diagrams]
    DIR --> OPT[OPTIONAL.md<br/>specialized documentation]
    DIR --> CODE[code files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef req fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef opt fill:#0f766e,stroke:#0f172a,color:#fff
    class DIR d
    class AG,RD req
    class OPT,CODE opt
```

**Violation of this pattern** is considered a documentation standard breach and must be corrected immediately.

## AGENTS.md Requirements

### AGENTS.md - Purpose
- **technical documentation** for understanding and working with directory contents
- **AI agent friendly** - structured for automated parsing and comprehension
- **Developer reference** - details for implementation and maintenance
### AGENTS.md - Content Structure

1. **Overview** (50-100 words) - What this directory does, why it exists, who uses it
2. **Key Concepts** (optional) - Terminology, architecture, important principles
3. **Directory Structure** - File organization and purpose of each file
4. **Installation/Setup** (if applicable) - Prerequisites, installation steps, configuration
5. **Usage Examples** - Common tasks, real-world scenarios, copy-paste ready examples
6. **Configuration** (if applicable) - All options, environment variables, config files
7. **Testing** (for directories with tests) - How to run tests, test structure, writing tests
8. **API Reference** (for modules) - Key classes, functions, import statements, parameters, returns
9. **Troubleshooting** - Common issues, solutions, debug tips
10. **Best Practices** - Do's and don'ts, performance tips, security considerations
11. **See Also / References** - Related documentation, external resources, cross-references

### AGENTS.md - Length Guidelines
- **Minimum**: 100 lines for simple directories
- **Typical**: 200-500 lines for most directories
- **Maximum**: 600 lines (split into specialized files if exceeded)

## README.md Requirements

### Purpose
- **Quick human reference** - fast lookup of common tasks and key information
- **Signposting** - clear navigation to detailed documentation
- **Visual elements** - Mermaid diagrams for architecture and workflows

### Content Structure
1. **Title** - One-line description of directory purpose
2. **Quick Start** - Minimal working example (5-10 lines)
3. **Key Features** - 3-5 bullet points highlighting capabilities
4. **Installation** - Copy-paste ready commands (if applicable)
5. **Common Commands** - 3-5 most frequently used operations
6. **More Information** - Link to AGENTS.md for details

### Length Guidelines
- **Typical**: 50-150 lines
- **Focus**: Concise, actionable information
- **Diagrams**: Include Mermaid diagrams for complex workflows or architectures

## Directory Structure Standards

### Root Level Directories

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| `infrastructure/` | ✅ module documentation | ✅ Quick reference | Generic build/validation tools |
| `scripts/` | ✅ Entry point documentation | ✅ Quick reference | Orchestration scripts |
| `tests/` | ✅ Testing philosophy | ✅ Quick reference | Test suites |
| `projects/` | ✅ Project structure guide | ✅ Quick reference | Research code |
| `docs/` | ✅ Documentation organization | ✅ Quick reference | Documentation hub |
| Root `.cursorrules` | — | — | Cursor IDE rule file (repository root) |
| `docs/rules/` | ✅ Standards overview | ✅ Quick reference | Development guidelines (Markdown corpus) |

### Infrastructure Subdirectories

All `infrastructure/` subdirectories follow the pattern:

```mermaid
flowchart LR
    M[infrastructure/module/]
    M --> INIT[__init__.py<br/>Public API exports]
    M --> AG[AGENTS.md<br/>REQUIRED · technical documentation]
    M --> RD[README.md<br/>REQUIRED · quick reference]
    M --> CORE[core.py<br/>Core functionality]
    M --> CLI[cli.py<br/>CLI · optional]
    M --> CFG[config.py<br/>Configuration · optional]
    M --> OTHER[other files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef req fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef opt fill:#0f766e,stroke:#0f172a,color:#fff
    class M d
    class INIT,AG,RD,CORE req
    class CLI,CFG,OTHER opt
```

### Project Subdirectories

All `projects/` subdirectories follow the pattern:

```mermaid
flowchart LR
    P[projects/&lt;name&gt;/]
    P --> AG[AGENTS.md<br/>REQUIRED · directory documentation]
    P --> RD[README.md<br/>REQUIRED · quick reference]
    P --> CODE[code files]
    P --> CFG[config files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef req fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef opt fill:#0f766e,stroke:#0f172a,color:#fff
    class P d
    class AG,RD req
    class CODE,CFG opt
```

### Documentation Subdirectories

All `docs/` subdirectories follow the pattern:

```mermaid
flowchart LR
    D[docs/section/]
    D --> AG[AGENTS.md<br/>REQUIRED · section documentation]
    D --> RD[README.md<br/>REQUIRED · quick reference]
    D --> TOPICS[topic files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef req fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef opt fill:#0f766e,stroke:#0f172a,color:#fff
    class D d
    class AG,RD req
    class TOPICS opt
```

## Integration with Development Standards

### Cross-References

This standard integrates with:

- [`documentation_standards.md`](documentation_standards.md) — AGENTS.md/README.md writing guidelines
- [`AGENTS.md`](AGENTS.md) — Standards hub overview (this directory)
- [Root `AGENTS.md`](../AGENTS.md) - Directory-level documentation section

### Quality Assurance

Documentation quality is verified through:

1. **Manual review** - Pull request reviews check for AGENTS.md/README.md presence
2. **Automated checks** - Pre-commit hooks can validate documentation structure
3. **Consistency audits** - Regular reviews ensure standards compliance

### Update Triggers

Update documentation when:

- **Architecture changes** - New directories, file reorganization
- **API changes** - New functions, parameters, return types
- **Feature additions** - New capabilities, usage patterns
- **Breaking changes** - API modifications, migration requirements
- **Bug fixes** - Important fixes with changed behavior

## Optional Specialized Documentation

### When to Add Additional .md Files

Additional documentation files should only be added when:

1. **Content exceeds reasonable length** (>600 lines in AGENTS.md)
2. **Specialized audience needs** (e.g., API.md for external users)
3. **Maintenance benefits** (e.g., CHANGELOG.md for versioned modules)

### Recommended Optional Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `CHANGELOG.md` | Version history, migration notes | Versioned infrastructure modules |
| `examples.md` | Extended usage examples | Complex modules with many use cases |
| `TROUBLESHOOTING.md` | Detailed troubleshooting | Error-prone modules (LLM, rendering) |
| `API.md` | API reference | Large public-facing modules |
| `DESIGN.md` | Design decisions, rationale | Complex architectural decisions |
| `DEPENDENCIES.md` | External dependencies | Modules with complex requirements |

## Mermaid Diagram Standards

### README.md Diagram Requirements

README.md files should include Mermaid diagrams for:

- **Architecture diagrams** - showing relationships between components
- **Workflow diagrams** - illustrating processes and data flow
- **Decision trees** - for complex conditional logic

### Diagram Guidelines

```mermaid
graph TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E[End]
```

- Use descriptive node names (no spaces in IDs)
- Include clear labels for decision points
- Use consistent arrow styles
- Keep diagrams focused and readable

## Examples from Repository

### Infrastructure Module Example

```mermaid
flowchart TB
    LLM[infrastructure/llm/]
    LLM --> META[__init__.py · AGENTS.md · README.md]
    LLM --> CORE[core]
    LLM --> TPL[templates]
    LLM --> OTHER[other subdirs]

    CORE --> CORE_F[__init__.py · AGENTS.md ·<br/>README.md · python files]
    TPL --> TPL_F[AGENTS.md · README.md ·<br/>python files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef pkg fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class LLM d
    class CORE,TPL,OTHER pkg
    class META,CORE_F,TPL_F f
```

### Project Directory Example

```mermaid
flowchart LR
    SRC[projects/&lt;name&gt;/src/]
    SRC --> META[__init__.py · AGENTS.md · README.md<br/>research code documentation]
    SRC --> DP[data_processing.py]
    SRC --> SIM[simulation.py]
    SRC --> VIZ[visualization.py]
    SRC --> OTHER[other files]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef code fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef doc fill:#0f766e,stroke:#0f172a,color:#fff
    class SRC d
    class DP,SIM,VIZ,OTHER code
    class META doc
```

## Quality Checklist

Before committing folder structure changes:

- [ ] Every directory has `AGENTS.md` and `README.md`
- [ ] AGENTS.md follows standard section structure
- [ ] README.md includes Mermaid diagrams where appropriate
- [ ] Cross-references are accurate and working
- [ ] Optional files have clear justification
- [ ] Documentation is up-to-date with code changes
- [ ] No orphaned documentation files

## See Also

- [documentation_standards.md](documentation_standards.md) - Detailed AGENTS.md/README.md writing guidelines
- [AGENTS.md](AGENTS.md) - Overview of all development standards
- [../AGENTS.md](../AGENTS.md) - Root documentation structure
- [docs/](../) - Main documentation hub

---

**Version**: 1.0.0
**Last Updated**: 2025-01-01
**Status**: Active standard - mandatory compliance
**Maintainer**: Template Team
