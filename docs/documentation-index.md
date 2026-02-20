# 📚 Documentation Index

This index provides an overview of all documentation files in the Research Project Template, organized by category and purpose.

## 🎯 **Quick Start by Persona**

### 👤 **New User / Content Creator**

**Goal:** Write documents and generate PDFs without programming

1. **[README.md](../README.md)** - Project overview
2. **[guides/getting-started.md](guides/getting-started.md)** - Write your first document (Levels 1-3)
3. **[reference/quick-start-cheatsheet.md](reference/quick-start-cheatsheet.md)** - Essential commands
4. **[reference/common-workflows.md](reference/common-workflows.md)** - Step-by-step recipes
5. **[reference/faq.md](reference/faq.md)** - Common questions

### 👨‍💻 **Developer / Researcher**

**Goal:** Add figures, data analysis, and automation

1. **[core/how-to-use.md](core/how-to-use.md)** - usage guide (all 12 levels)
2. **[guides/figures-and-analysis.md](guides/figures-and-analysis.md)** - Add figures and automation (Levels 4-6)
3. **[core/architecture.md](core/architecture.md)** - Understand system design
4. **[architecture/thin-orchestrator-summary.md](architecture/thin-orchestrator-summary.md)** - Learn the pattern
5. **[core/workflow.md](core/workflow.md)** - Development process

### 🏗️ **Contributor / Maintainer**

**Goal:** Contribute code and understand standards

1. **[development/contributing.md](development/contributing.md)** - Contribution guidelines
2. **[.cursorrules/AGENTS.md](../.cursorrules/AGENTS.md)** - Development standards
3. **[guides/testing-and-reproducibility.md](guides/testing-and-reproducibility.md)** - TDD workflow (Levels 7-9)
4. **[development/testing-guide.md](development/testing-guide.md)** - Testing requirements
5. **[development/code-of-conduct.md](development/code-of-conduct.md)** - Community standards

### 🔍 **Troubleshooter**

**Goal:** Fix issues and understand problems

1. **[operational/troubleshooting-guide.md](operational/troubleshooting-guide.md)** - troubleshooting
2. **[reference/faq.md](reference/faq.md)** - Common questions and solutions
3. **[operational/build-system.md](operational/build-system.md)** - Build system details
4. **[operational/performance-optimization.md](operational/performance-optimization.md)** - Performance issues

---

## 🏗️ **Development Rules**

Development standards are documented in the `.cursorrules/` directory:

- **[`.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md)** - Overview and navigation guide
- **[`.cursorrules/README.md`](../.cursorrules/README.md)** - Quick reference and patterns
- **[`.cursorrules/error_handling.md`](../.cursorrules/error_handling.md)** - Exception handling patterns
- **[`.cursorrules/security.md`](../.cursorrules/security.md)** - Security standards and guidelines
- **[`.cursorrules/python_logging.md`](../.cursorrules/python_logging.md)** - Logging standards and best practices
- **[`.cursorrules/infrastructure_modules.md`](../.cursorrules/infrastructure_modules.md)** - Infrastructure module development
- **[`.cursorrules/testing_standards.md`](../.cursorrules/testing_standards.md)** - Testing patterns and coverage standards
- **[`.cursorrules/documentation_standards.md`](../.cursorrules/documentation_standards.md)** - AGENTS.md and README.md writing guide
- **[`.cursorrules/type_hints_standards.md`](../.cursorrules/type_hints_standards.md)** - Type annotation patterns
- **[`.cursorrules/llm_standards.md`](../.cursorrules/llm_standards.md)** - LLM/Ollama integration patterns
- **[`.cursorrules/code_style.md`](../.cursorrules/code_style.md)** - Code formatting and style standards
- **[`.cursorrules/git_workflow.md`](../.cursorrules/git_workflow.md)** - Git workflow and commit standards
- **[`.cursorrules/api_design.md`](../.cursorrules/api_design.md)** - API design and interface standards
- **[`.cursorrules/manuscript_style.md`](../.cursorrules/manuscript_style.md)** - Manuscript formatting and style standards
- **[`.cursorrules/reporting.md`](../.cursorrules/reporting.md)** - Reporting module standards and outputs
- **[`.cursorrules/refactoring.md`](../.cursorrules/refactoring.md)** - Refactoring and modularization standards
- **[`.cursorrules/folder_structure.md`](../.cursorrules/folder_structure.md)** - Folder structure and organization standards

**Note**: Use `.cursorrules/` files as quick reference during development. Corresponding `docs/` files provide guides.

## 🎯 **Core Documentation**

### **Primary Entry Points**

- **[`README.md`](../README.md)** - **Main project overview** and quick start guide
- **[`AGENTS.md`](../AGENTS.md)** - **system documentation** - Everything you need to know
- **[`docs/core/how-to-use.md`](core/how-to-use.md)** - **usage guide** from basic to advanced levels

### **Quick Reference**

- **[`docs/reference/copypasta.md`](reference/copypasta.md)** - Ready-to-use content for sharing the template
- **[`docs/reference/faq.md`](reference/faq.md)** - Frequently asked questions and common issues
- **[`docs/reference/quick-start-cheatsheet.md`](reference/quick-start-cheatsheet.md)** - One-page essential commands reference
- **[`docs/reference/common-workflows.md`](reference/common-workflows.md)** - Step-by-step workflow recipes
- **[`docs/reference/glossary.md`](reference/glossary.md)** - glossary of terms
- **[`scripts/README.md`](../scripts/README.md)** - Detailed utility documentation
- **[`tests/README.md`](../tests/README.md)** - Test suite guide and commands
- **[`tests/AGENTS.md`](../tests/AGENTS.md)** - Testing philosophy and structure

## 🏗️ **Architecture & Design**

### **System Architecture**

- **[`docs/core/architecture.md`](core/architecture.md)** - system design overview
- **[`docs/architecture/two-layer-architecture.md`](architecture/two-layer-architecture.md)** - two-layer architecture guide
- **[`docs/architecture/thin-orchestrator-summary.md`](architecture/thin-orchestrator-summary.md)** - Thin orchestrator pattern implementation
- **[`docs/core/workflow.md`](core/workflow.md)** - Development workflow and build pipeline

### **Technical Implementation**

- **[`docs/modules/pdf-validation.md`](modules/pdf-validation.md)** - PDF validation system documentation
- **[`docs/operational/reporting-guide.md`](operational/reporting-guide.md)** - Reporting system guide and report interpretation

## 📝 **Usage Guides**

### **Getting Started**

- **[`docs/guides/getting-started.md`](guides/getting-started.md)** - Basic usage guide (Levels 1-3)
- **[`docs/usage/examples.md`](usage/examples.md)** - Project renaming and customization examples
- **[`docs/usage/examples-showcase.md`](usage/examples-showcase.md)** - Real-world usage examples
- **[`docs/usage/template-description.md`](usage/template-description.md)** - Template overview and features

### **Skill-Level Guides**

- **[`docs/guides/figures-and-analysis.md`](guides/figures-and-analysis.md)** - Intermediate usage guide (Levels 4-6)
- **[`docs/guides/testing-and-reproducibility.md`](guides/testing-and-reproducibility.md)** - Advanced usage guide (Levels 7-9)
- **[`docs/guides/extending-and-automation.md`](guides/extending-and-automation.md)** - Expert usage guide (Levels 10-12)
- **[`docs/guides/intermediate-usage.md`](guides/intermediate-usage.md)** - Backward-compatible redirect to Figures and Analysis

### **Advanced Usage**

- **[`docs/usage/markdown-template-guide.md`](usage/markdown-template-guide.md)** - Markdown and cross-referencing guide
- **[`docs/usage/manuscript-numbering-system.md`](usage/manuscript-numbering-system.md)** - Manuscript section numbering system
- **[`docs/development/coverage-gaps.md`](development/coverage-gaps.md)** - Test coverage gap analysis and improvement plans
- **[`scripts/README.md`](../scripts/README.md)** - Thin orchestrator pattern guide

### **Scientific Computing Guides**

- **[`docs/modules/scientific-simulation-guide.md`](modules/scientific-simulation-guide.md)** - Scientific simulation and analysis system guide
- **[`docs/usage/visualization-guide.md`](usage/visualization-guide.md)** - Visualization system for publication-quality figures
- **[`docs/usage/image-management.md`](usage/image-management.md)** - Image insertion, captioning, and cross-referencing guide

## 🔧 **Development & Maintenance**

### **Contributing**

- **[`docs/development/contributing.md`](development/contributing.md)** - Contribution guidelines and process
- **[`docs/development/code-of-conduct.md`](development/code-of-conduct.md)** - Community standards and behavior
- **[`docs/development/security.md`](development/security.md)** - Security policy and vulnerability reporting

### **Future Development**

- **[`docs/development/roadmap.md`](development/roadmap.md)** - Development roadmap and future plans

## 🧪 **Advanced Modules**

### **Module Guides**

- **[`docs/modules/modules-guide.md`](modules/modules-guide.md)** - Guide for all 9 infrastructure modules
- **[`docs/reference/api-reference.md`](reference/api-reference.md)** - API documentation for all src/ modules

### **Per-Module Guides** (`modules/guides/`)

- **[`docs/modules/guides/integrity-module.md`](modules/guides/integrity-module.md)** - Integrity module guide
- **[`docs/modules/guides/llm-module.md`](modules/guides/llm-module.md)** - LLM module guide
- **[`docs/modules/guides/publishing-module.md`](modules/guides/publishing-module.md)** - Publishing module guide
- **[`docs/modules/guides/rendering-module.md`](modules/guides/rendering-module.md)** - Rendering module guide
- **[`docs/modules/guides/reporting-module.md`](modules/guides/reporting-module.md)** - Reporting module guide
- **[`docs/modules/guides/scientific-module.md`](modules/guides/scientific-module.md)** - Scientific module guide

## ⚙️ **Operational Guides**

### **Dependency & Build Management**

- **[`docs/operational/dependency-management.md`](operational/dependency-management.md)** - guide for uv package manager
- **[`docs/operational/build-history.md`](operational/build-history.md)** - Build history and changelog
- **[`docs/operational/build-system.md`](operational/build-system.md)** - build system reference
- **[`docs/operational/performance-optimization.md`](operational/performance-optimization.md)** - Build time optimization and caching strategies

### **CI/CD & Automation**

- **[`docs/operational/ci-cd-integration.md`](operational/ci-cd-integration.md)** - GitHub Actions and CI/CD integration guide

### **Pipeline Orchestration**

- **[`../RUN_GUIDE.md`](../RUN_GUIDE.md)** - pipeline orchestration guide (run.sh)

### **Reporting**

- **[`docs/operational/reporting-guide.md`](operational/reporting-guide.md)** - Reporting system and report interpretation guide

### **Troubleshooting & Support**

- **[`docs/operational/troubleshooting-guide.md`](operational/troubleshooting-guide.md)** - troubleshooting guide
- **[`docs/reference/faq.md`](reference/faq.md)** - Frequently asked questions and common issues
- **[`docs/operational/llm-review-troubleshooting.md`](operational/llm-review-troubleshooting.md)** - LLM-specific troubleshooting
- **[`docs/operational/checkpoint-resume.md`](operational/checkpoint-resume.md)** - Checkpoint and resume system
- **[`docs/operational/error-handling-guide.md`](operational/error-handling-guide.md)** - Error handling patterns
- **[`docs/operational/logging-guide.md`](operational/logging-guide.md)** - Logging system guide
- **[`docs/development/testing-guide.md`](development/testing-guide.md)** - Testing framework guide
- **[`docs/development/testing-with-credentials.md`](development/testing-with-credentials.md)** - Testing with external service credentials
- **[`docs/operational/configuration.md`](operational/configuration.md)** - Configuration system guide

### **Logging Guides** (`operational/logging/`)

- **[`docs/operational/logging/bash-logging.md`](operational/logging/bash-logging.md)** - Bash logging patterns
- **[`docs/operational/logging/python-logging.md`](operational/logging/python-logging.md)** - Python logging patterns
- **[`docs/operational/logging/logging-patterns.md`](operational/logging/logging-patterns.md)** - Cross-language logging patterns

### **Troubleshooting Guides** (`operational/troubleshooting/`)

- **[`docs/operational/troubleshooting/build-tools.md`](operational/troubleshooting/build-tools.md)** - Build tool troubleshooting
- **[`docs/operational/troubleshooting/common-errors.md`](operational/troubleshooting/common-errors.md)** - Common error patterns and fixes
- **[`docs/operational/troubleshooting/environment-setup.md`](operational/troubleshooting/environment-setup.md)** - Environment setup troubleshooting
- **[`docs/operational/troubleshooting/recovery-procedures.md`](operational/troubleshooting/recovery-procedures.md)** - Recovery procedures
- **[`docs/operational/troubleshooting/test-failures.md`](operational/troubleshooting/test-failures.md)** - Test failure troubleshooting

## 📚 **Reference Materials**

### **Best Practices & Guidelines**

- **[`docs/best-practices/best-practices.md`](best-practices/best-practices.md)** - Consolidated best practices compilation
- **[`docs/best-practices/version-control.md`](best-practices/version-control.md)** - Git workflows and version control best practices
- **[`docs/architecture/decision-tree.md`](architecture/decision-tree.md)** - Decision tree for code placement

### **Project Management**

- **[`docs/best-practices/multi-project-management.md`](best-practices/multi-project-management.md)** - Managing multiple projects using the template
- **[`docs/best-practices/migration-guide.md`](best-practices/migration-guide.md)** - Step-by-step migration from other templates
- **[`docs/best-practices/backup-recovery.md`](best-practices/backup-recovery.md)** - Backup strategies and recovery procedures

### **Changelog**

## 🤖 **AI Prompt Templates**

### **Prompt Categories**

#### **Core Development Prompts**

- **[`docs/prompts/README.md`](prompts/README.md)** - Navigation guide for all prompt templates
- **[`docs/prompts/AGENTS.md`](prompts/AGENTS.md)** - Technical documentation for prompt templates
- **[`docs/prompts/manuscript_creation.md`](prompts/manuscript_creation.md)** - manuscript creation from research description
- **[`docs/prompts/code_development.md`](prompts/code_development.md)** - Standards-compliant code development
- **[`docs/prompts/test_creation.md`](prompts/test_creation.md)** - test creation (no mocks policy)
- **[`docs/prompts/feature_addition.md`](prompts/feature_addition.md)** - feature development with architecture compliance

#### **Advanced Development Prompts**

- **[`docs/prompts/refactoring.md`](prompts/refactoring.md)** - Clean break code refactoring
- **[`docs/prompts/documentation_creation.md`](prompts/documentation_creation.md)** - AGENTS.md and README.md creation
- **[`docs/prompts/infrastructure_module.md`](prompts/infrastructure_module.md)** - Generic infrastructure module development
- **[`docs/prompts/validation_quality.md`](prompts/validation_quality.md)** - Quality assurance and validation procedures
- **[`docs/prompts/comprehensive_assessment.md`](prompts/comprehensive_assessment.md)** - Comprehensive assessment and review procedures

## 📁 **File Organization**

### **Directory Structure**

```text
docs/
├── README.md                           # Main docs entry point
├── AGENTS.md                           # Directory documentation guide
├── documentation-index.md              # documentation index (this file)
│
├── core/                               # Essential documentation
│   ├── README.md                       # Core docs overview
│   ├── AGENTS.md                       # Core docs technical guide
│   ├── how-to-use.md                   # usage guide
│   ├── architecture.md                 # System design
│   └── workflow.md                     # Development workflow
│
├── guides/                             # Usage guides by skill level
│   ├── README.md                       # Guides overview
│   ├── AGENTS.md                       # Guides technical guide
│   ├── getting-started.md              # Levels 1-3
│   ├── figures-and-analysis.md         # Levels 4-6
│   ├── intermediate-usage.md           # Redirect to Figures and Analysis
│   ├── testing-and-reproducibility.md  # Levels 7-9
│   └── extending-and-automation.md     # Levels 10-12
│
├── architecture/                       # Architecture documentation
│   ├── README.md                       # Architecture overview
│   ├── AGENTS.md                       # Architecture technical guide
│   ├── two-layer-architecture.md       # architecture guide
│   ├── thin-orchestrator-summary.md    # Pattern implementation
│   └── decision-tree.md                # Code placement decisions
│
├── usage/                              # Usage examples and patterns
│   ├── README.md                       # Usage docs overview
│   ├── AGENTS.md                       # Usage technical guide
│   ├── examples.md                     # Basic examples
│   ├── examples-showcase.md            # Real-world examples
│   ├── template-description.md         # Template overview
│   ├── markdown-template-guide.md      # Markdown authoring
│   ├── manuscript-numbering-system.md  # Section numbering
│   ├── image-management.md             # Image handling
│   └── visualization-guide.md          # Visualization system
│
├── operational/                        # Operational workflows
│   ├── README.md                       # Operational docs overview
│   ├── AGENTS.md                       # Operational technical guide
│   ├── build-history.md                # Build history and changelog
│   ├── build-system.md                 # Build system reference
│   ├── ci-cd-integration.md            # CI/CD setup
│   ├── dependency-management.md        # Package management
│   ├── performance-optimization.md     # Performance tuning
│   ├── configuration.md                # Configuration guide
│   ├── checkpoint-resume.md            # Checkpoint system
│   ├── reporting-guide.md              # Reporting system guide
│   ├── troubleshooting-guide.md        # Troubleshooting
│   ├── llm-review-troubleshooting.md   # LLM-specific issues
│   ├── error-handling-guide.md         # Error patterns
│   ├── logging-guide.md                # Logging system
│   ├── logging/                        # Detailed logging guides
│   │   ├── README.md                   # Logging overview
│   │   ├── bash-logging.md             # Bash logging patterns
│   │   ├── python-logging.md           # Python logging patterns
│   │   └── logging-patterns.md         # Cross-language patterns
│   └── troubleshooting/                # Detailed troubleshooting
│       ├── README.md                   # Troubleshooting overview
│       ├── build-tools.md              # Build tool issues
│       ├── common-errors.md            # Common error patterns
│       ├── environment-setup.md        # Environment setup
│       ├── recovery-procedures.md      # Recovery procedures
│       └── test-failures.md            # Test failure guides
│
├── reference/                          # Reference materials
│   ├── README.md                       # Reference docs overview
│   ├── AGENTS.md                       # Reference technical guide
│   ├── api-reference.md                # API docs
│   ├── glossary.md                     # Terms and definitions
│   ├── faq.md                          # Common questions
│   ├── quick-start-cheatsheet.md       # Quick reference
│   ├── common-workflows.md             # Step-by-step recipes
│   └── copypasta.md                    # Sharing content
│
├── modules/                            # Advanced modules
│   ├── README.md                       # Modules overview
│   ├── AGENTS.md                       # Modules technical guide
│   ├── modules-guide.md                # Modules guide
│   ├── scientific-simulation-guide.md  # Simulation system
│   ├── pdf-validation.md               # PDF validation
│   └── guides/                         # Per-module guides
│       ├── README.md                   # Module guides overview
│       ├── integrity-module.md         # Integrity module
│       ├── llm-module.md              # LLM module
│       ├── publishing-module.md        # Publishing module
│       ├── rendering-module.md         # Rendering module
│       ├── reporting-module.md         # Reporting module
│       └── scientific-module.md        # Scientific module
│
├── development/                        # Development & contribution
│   ├── README.md                       # Development docs overview
│   ├── AGENTS.md                       # Development technical guide
│   ├── contributing.md                 # Contribution guide
│   ├── code-of-conduct.md              # Community standards
│   ├── security.md                     # Security policy
│   ├── roadmap.md                      # Future plans
│   ├── testing-guide.md                # Testing framework
│   ├── testing-with-credentials.md     # Credential testing
│   └── coverage-gaps.md                # Coverage analysis
│
├── best-practices/                     # Best practices
│   ├── README.md                       # Best practices overview
│   ├── AGENTS.md                       # Best practices technical guide
│   ├── best-practices.md               # Consolidated practices
│   ├── version-control.md              # Git workflows
│   ├── multi-project-management.md     # Multi-project setup
│   ├── migration-guide.md              # Migration from other templates
│   └── backup-recovery.md              # Backup strategies
│
├── prompts/                            # AI prompt templates
│   ├── README.md                       # Prompts overview
│   ├── AGENTS.md                       # Prompts technical guide
│   ├── manuscript_creation.md          # Manuscript creation
│   ├── code_development.md             # Code development
│   ├── test_creation.md                # Test creation
│   ├── feature_addition.md             # Feature addition
│   ├── refactoring.md                  # Refactoring
│   ├── documentation_creation.md       # Documentation creation
│   ├── infrastructure_module.md        # Infrastructure modules
│   ├── validation_quality.md           # Validation and QA
│   └── comprehensive_assessment.md     # Assessment and review
│
└── audit/                              # Audit reports
    ├── README.md                       # Audit overview
    ├── AGENTS.md                       # Audit technical guide
    ├── documentation-review-report.md  # Documentation review
    ├── documentation-review-summary.md # Review summary
    └── filepath-audit-report.md        # Filepath audit
```

### **Documentation Categories**

| Category | Directory | Purpose |
|----------|-----------|---------|
| **Core** | `core/` | Essential documentation for all users (how-to-use.md, architecture.md, workflow.md) |
| **Guides** | `guides/` | Usage guides by skill level (getting-started.md, figures-and-analysis.md, testing-and-reproducibility.md, extending-and-automation.md) |
| **Architecture** | `architecture/` | System design and implementation (two-layer-architecture.md, thin-orchestrator-summary.md, decision-tree.md) |
| **Usage** | `usage/` | Usage examples and patterns (examples.md, markdown-template-guide.md, visualization-guide.md) |
| **Development** | `development/` | Contributing and future development (contributing.md, code-of-conduct.md, roadmap.md, testing-guide.md) |
| **Reference** | `reference/` | Quick reference and sharing content (faq.md, api-reference.md, glossary.md, quick-start-cheatsheet.md) |
| **Modules** | `modules/` | Module documentation (modules-guide.md, scientific-simulation-guide.md, pdf-validation.md, guides/) |
| **Operational** | `operational/` | Operational workflows and guides (build-system.md, reporting-guide.md, troubleshooting-guide.md, configuration.md, logging/, troubleshooting/) |
| **Best Practices** | `best-practices/` | Best practices and project management (best-practices.md, version-control.md, migration-guide.md) |
| **AI Prompts** | `prompts/` | AI prompt templates for development tasks (manuscript_creation.md, code_development.md, test_creation.md, comprehensive_assessment.md) |
| **Audit** | `audit/` | Audit reports and validation findings (documentation-review-report.md, documentation-review-summary.md, filepath-audit-report.md) |

## 🔗 **Cross-Referencing System**

All documentation files include cross-references:

- **README.md** → Links to all major documentation directories
- **core/how-to-use.md** → usage guide with all sections
- **core/architecture.md** → System design with related documentation links
- **All files** → Include context about related information

## 📖 **Detailed Reading Paths**

### **New Users - Learning Path**

1. **[README.md](../README.md)** - Project overview (5 min)
2. **[guides/getting-started.md](guides/getting-started.md)** - Write first document (30 min)
3. **[reference/quick-start-cheatsheet.md](reference/quick-start-cheatsheet.md)** - Essential commands reference
4. **[reference/common-workflows.md](reference/common-workflows.md)** - Common tasks step-by-step
5. **[usage/examples-showcase.md](usage/examples-showcase.md)** - See real-world usage

### **Developers - Architecture & Patterns**

1. **[core/architecture.md](core/architecture.md)** - System design overview (15 min)
2. **[architecture/two-layer-architecture.md](architecture/two-layer-architecture.md)** - architecture guide (30 min)
3. **[architecture/thin-orchestrator-summary.md](architecture/thin-orchestrator-summary.md)** - Pattern implementation (20 min)
4. **[core/workflow.md](core/workflow.md)** - Development process (20 min)
5. **[guides/figures-and-analysis.md](guides/figures-and-analysis.md)** - Add figures and automation

### **Contributors - Standards & Process**

1. **[development/contributing.md](development/contributing.md)** - Contribution guidelines (10 min)
2. **[.cursorrules/AGENTS.md](../.cursorrules/AGENTS.md)** - Development standards (30 min)
3. **[guides/testing-and-reproducibility.md](guides/testing-and-reproducibility.md)** - TDD workflow (45 min)
4. **[development/testing-guide.md](development/testing-guide.md)** - Testing requirements (20 min)
5. **[development/code-of-conduct.md](development/code-of-conduct.md)** - Community standards (5 min)

## 🎯 **Documentation Quality**

### **Standards Applied**

- ✅ **coverage** - All features and workflows documented
- ✅ **Cross-referencing** - All files include links to related content
- ✅ **Professional structure** - Clear organization and navigation
- ✅ **Practical examples** - Real-world usage patterns included
- ✅ **Troubleshooting** - Common issues and solutions documented
- ✅ **Best practices** - Established patterns and guidelines included

### **Build System**

- **[`docs/operational/build-system.md`](operational/build-system.md)** - build system reference (status, performance, fixes)

### **Documentation Completeness**

- ✅ **100+ documentation files** across 14 directories covering all aspects (including root-level guides)
- ✅ **cross-referencing** system
- ✅ **Real-world examples** and showcase projects
- ✅ **Technical implementation** details
- ✅ **Build system analysis** and performance metrics
- ✅ **Troubleshooting** and FAQ sections
- ✅ **Advanced modules** guides
- ✅ **Operational workflows** (CI/CD, dependencies, performance)
- ✅ **Reference materials** (API, best practices, migration)
- ✅ **Future development** roadmap

---

## 📋 Documentation Maintenance Notes

- Historical review reports have been removed to keep the index current and focused.
- All documentation is maintained as evergreen content (no time-sensitive dates).
- Documentation is verified for accuracy and completeness on an ongoing basis.

**This documentation ecosystem provides everything needed to understand, use, and contribute to the Research Project Template effectively! 🚀**

For the most up-to-date information, see the individual documentation files linked above.
