# 📚 Documentation Index

This index provides an overview of all documentation files in the Research Project Template, organized by category and purpose.

## 🎯 **Quick Start by Persona**

### 👤 **New User / Content Creator**
**Goal:** Write documents and generate PDFs without programming

1. **[README.md](../README.md)** - Project overview
2. **[guides/GETTING_STARTED.md](guides/GETTING_STARTED.md)** - Write your first document (Levels 1-3)
3. **[reference/QUICK_START_CHEATSHEET.md](reference/QUICK_START_CHEATSHEET.md)** - Essential commands
4. **[reference/COMMON_WORKFLOWS.md](reference/COMMON_WORKFLOWS.md)** - Step-by-step recipes
5. **[reference/FAQ.md](reference/FAQ.md)** - Common questions

### 👨‍💻 **Developer / Researcher**
**Goal:** Add figures, data analysis, and automation

1. **[core/HOW_TO_USE.md](core/HOW_TO_USE.md)** - Complete usage guide (all 12 levels)
2. **[guides/INTERMEDIATE_USAGE.md](guides/INTERMEDIATE_USAGE.md)** - Add figures and automation (Levels 4-6)
3. **[core/ARCHITECTURE.md](core/ARCHITECTURE.md)** - Understand system design
4. **[architecture/THIN_ORCHESTRATOR_SUMMARY.md](architecture/THIN_ORCHESTRATOR_SUMMARY.md)** - Learn the pattern
5. **[core/WORKFLOW.md](core/WORKFLOW.md)** - Development process

### 🏗️ **Contributor / Maintainer**
**Goal:** Contribute code and understand standards

1. **[development/CONTRIBUTING.md](development/CONTRIBUTING.md)** - Contribution guidelines
2. **[.cursorrules/AGENTS.md](../.cursorrules/AGENTS.md)** - Development standards
3. **[guides/ADVANCED_USAGE.md](guides/ADVANCED_USAGE.md)** - TDD workflow (Levels 7-9)
4. **[development/TESTING_GUIDE.md](development/TESTING_GUIDE.md)** - Testing requirements
5. **[development/CODE_OF_CONDUCT.md](development/CODE_OF_CONDUCT.md)** - Community standards

### 🔍 **Troubleshooter**
**Goal:** Fix issues and understand problems

1. **[operational/TROUBLESHOOTING_GUIDE.md](operational/TROUBLESHOOTING_GUIDE.md)** - Comprehensive troubleshooting
2. **[reference/FAQ.md](reference/FAQ.md)** - Common questions and solutions
3. **[operational/BUILD_SYSTEM.md](operational/BUILD_SYSTEM.md)** - Build system details
4. **[operational/PERFORMANCE_OPTIMIZATION.md](operational/PERFORMANCE_OPTIMIZATION.md)** - Performance issues

---

## 🏗️ **Development Rules**

Development standards are documented in the `.cursorrules/` directory:

- **[`.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md)** - Complete overview and navigation guide
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

**Note**: Use `.cursorrules/` files as quick reference during development. Corresponding `docs/` files provide guides.

## 🎯 **Core Documentation**

### **Primary Entry Points**
- **[`README.md`](../README.md)** - **Main project overview** and quick start guide
- **[`AGENTS.md`](../AGENTS.md)** - **Complete system documentation** - Everything you need to know
- **[`docs/core/HOW_TO_USE.md`](core/HOW_TO_USE.md)** - **Complete usage guide** from basic to advanced levels

### **Quick Reference**
- **[`docs/reference/COPYPASTA.md`](reference/COPYPASTA.md)** - Ready-to-use content for sharing the template
- **[`docs/reference/FAQ.md`](reference/FAQ.md)** - Frequently asked questions and common issues
- **[`docs/reference/QUICK_START_CHEATSHEET.md`](reference/QUICK_START_CHEATSHEET.md)** - One-page essential commands reference
- **[`docs/reference/COMMON_WORKFLOWS.md`](reference/COMMON_WORKFLOWS.md)** - Step-by-step workflow recipes
- **[`docs/reference/GLOSSARY.md`](reference/GLOSSARY.md)** - Comprehensive glossary of terms
- **[`scripts/README.md`](../scripts/README.md)** - Detailed utility documentation
- **[`tests/README.md`](../tests/README.md)** - Test suite guide and commands
- **[`tests/AGENTS.md`](../tests/AGENTS.md)** - Testing philosophy and structure

## 🏗️ **Architecture & Design**

### **System Architecture**
- **[`docs/core/ARCHITECTURE.md`](core/ARCHITECTURE.md)** - Complete system design overview
- **[`docs/architecture/TWO_LAYER_ARCHITECTURE.md`](architecture/TWO_LAYER_ARCHITECTURE.md)** - Complete two-layer architecture guide
- **[`docs/architecture/THIN_ORCHESTRATOR_SUMMARY.md`](architecture/THIN_ORCHESTRATOR_SUMMARY.md)** - Thin orchestrator pattern implementation
- **[`docs/core/WORKFLOW.md`](core/WORKFLOW.md)** - Development workflow and build pipeline

### **Technical Implementation**
- **[`docs/modules/PDF_VALIDATION.md`](modules/PDF_VALIDATION.md)** - PDF validation system documentation

## 📝 **Usage Guides**

### **Getting Started**
- **[`docs/guides/GETTING_STARTED.md`](guides/GETTING_STARTED.md)** - Basic usage guide (Levels 1-3)
- **[`docs/usage/EXAMPLES.md`](usage/EXAMPLES.md)** - Project renaming and customization examples
- **[`docs/usage/EXAMPLES_SHOWCASE.md`](usage/EXAMPLES_SHOWCASE.md)** - Real-world usage examples
- **[`docs/usage/TEMPLATE_DESCRIPTION.md`](usage/TEMPLATE_DESCRIPTION.md)** - Template overview and features

### **Skill-Level Guides**
- **[`docs/guides/INTERMEDIATE_USAGE.md`](guides/INTERMEDIATE_USAGE.md)** - Intermediate usage guide (Levels 4-6)
- **[`docs/guides/ADVANCED_USAGE.md`](guides/ADVANCED_USAGE.md)** - Advanced usage guide (Levels 7-9)
- **[`docs/guides/EXPERT_USAGE.md`](guides/EXPERT_USAGE.md)** - Expert usage guide (Levels 10-12)

### **Advanced Usage**
- **[`docs/usage/MARKDOWN_TEMPLATE_GUIDE.md`](usage/MARKDOWN_TEMPLATE_GUIDE.md)** - Markdown and cross-referencing guide
- **[`docs/usage/MANUSCRIPT_NUMBERING_SYSTEM.md`](usage/MANUSCRIPT_NUMBERING_SYSTEM.md)** - Manuscript section numbering system
- **[`docs/development/COVERAGE_GAPS.md`](development/COVERAGE_GAPS.md)** - Test coverage gap analysis and improvement plans
- **[`scripts/README.md`](../scripts/README.md)** - Thin orchestrator pattern guide

### **Scientific Computing Guides**
- **[`docs/modules/SCIENTIFIC_SIMULATION_GUIDE.md`](modules/SCIENTIFIC_SIMULATION_GUIDE.md)** - Scientific simulation and analysis system guide
- **[`docs/usage/VISUALIZATION_GUIDE.md`](usage/VISUALIZATION_GUIDE.md)** - Visualization system for publication-quality figures
- **[`docs/usage/IMAGE_MANAGEMENT.md`](usage/IMAGE_MANAGEMENT.md)** - Image insertion, captioning, and cross-referencing guide

## 🔧 **Development & Maintenance**

### **Contributing**
- **[`docs/development/CONTRIBUTING.md`](development/CONTRIBUTING.md)** - Contribution guidelines and process
- **[`docs/development/CODE_OF_CONDUCT.md`](development/CODE_OF_CONDUCT.md)** - Community standards and behavior
- **[`docs/development/SECURITY.md`](development/SECURITY.md)** - Security policy and vulnerability reporting

### **Future Development**
- **[`docs/development/ROADMAP.md`](development/ROADMAP.md)** - Development roadmap and future plans

## 🧪 **Advanced Modules**

### **Module Guides**
- **[`docs/modules/ADVANCED_MODULES_GUIDE.md`](modules/ADVANCED_MODULES_GUIDE.md)** - Comprehensive guide for all 7 advanced modules
- **[`docs/reference/API_REFERENCE.md`](reference/API_REFERENCE.md)** - Complete API documentation for all src/ modules

## ⚙️ **Operational Guides**

### **Dependency & Build Management**
- **[`docs/operational/DEPENDENCY_MANAGEMENT.md`](operational/DEPENDENCY_MANAGEMENT.md)** - Complete guide for uv package manager
- **[`docs/operational/BUILD_SYSTEM.md`](operational/BUILD_SYSTEM.md)** - Complete build system reference
- **[`docs/operational/PERFORMANCE_OPTIMIZATION.md`](operational/PERFORMANCE_OPTIMIZATION.md)** - Build time optimization and caching strategies

### **CI/CD & Automation**
- **[`docs/operational/CI_CD_INTEGRATION.md`](operational/CI_CD_INTEGRATION.md)** - GitHub Actions and CI/CD integration guide

### **Pipeline Orchestration**
- **[`../RUN_GUIDE.md`](../RUN_GUIDE.md)** - Complete pipeline orchestration guide (run.sh)

### **Troubleshooting & Support**
- **[`docs/operational/TROUBLESHOOTING_GUIDE.md`](operational/TROUBLESHOOTING_GUIDE.md)** - Comprehensive troubleshooting guide
- **[`docs/reference/FAQ.md`](reference/FAQ.md)** - Frequently asked questions and common issues
- **[`docs/operational/LLM_REVIEW_TROUBLESHOOTING.md`](operational/LLM_REVIEW_TROUBLESHOOTING.md)** - LLM-specific troubleshooting
- **[`docs/operational/CHECKPOINT_RESUME.md`](operational/CHECKPOINT_RESUME.md)** - Checkpoint and resume system
- **[`docs/operational/ERROR_HANDLING_GUIDE.md`](operational/ERROR_HANDLING_GUIDE.md)** - Error handling patterns
- **[`docs/operational/LOGGING_GUIDE.md`](operational/LOGGING_GUIDE.md)** - Logging system guide
- **[`docs/development/TESTING_GUIDE.md`](development/TESTING_GUIDE.md)** - Testing framework guide
- **[`docs/development/TESTING_WITH_CREDENTIALS.md`](development/TESTING_WITH_CREDENTIALS.md)** - Testing with external service credentials
- **[`docs/operational/CONFIGURATION.md`](operational/CONFIGURATION.md)** - Configuration system guide

## 📚 **Reference Materials**

### **Best Practices & Guidelines**
- **[`docs/best-practices/BEST_PRACTICES.md`](best-practices/BEST_PRACTICES.md)** - Consolidated best practices compilation
- **[`docs/best-practices/VERSION_CONTROL.md`](best-practices/VERSION_CONTROL.md)** - Git workflows and version control best practices
- **[`docs/architecture/DECISION_TREE.md`](architecture/DECISION_TREE.md)** - Decision tree for code placement

### **Project Management**
- **[`docs/best-practices/MULTI_PROJECT_MANAGEMENT.md`](best-practices/MULTI_PROJECT_MANAGEMENT.md)** - Managing multiple projects using the template
- **[`docs/best-practices/MIGRATION_GUIDE.md`](best-practices/MIGRATION_GUIDE.md)** - Step-by-step migration from other templates
- **[`docs/best-practices/BACKUP_RECOVERY.md`](best-practices/BACKUP_RECOVERY.md)** - Backup strategies and recovery procedures

### **Changelog**

## 📁 **File Organization**

### **Directory Structure**
```
docs/
├── README.md                           # Main docs entry point
├── AGENTS.md                           # Directory documentation guide
├── DOCUMENTATION_INDEX.md              # Complete documentation index (this file)
│
├── core/                               # Essential documentation
│   ├── README.md                       # Core docs overview
│   ├── HOW_TO_USE.md                   # Complete usage guide
│   ├── ARCHITECTURE.md                 # System design
│   └── WORKFLOW.md                     # Development workflow
│
├── guides/                             # Usage guides by skill level
│   ├── README.md                       # Guides overview
│   ├── GETTING_STARTED.md              # Levels 1-3
│   ├── INTERMEDIATE_USAGE.md           # Levels 4-6
│   ├── ADVANCED_USAGE.md               # Levels 7-9
│   └── EXPERT_USAGE.md                 # Levels 10-12
│
├── architecture/                       # Architecture documentation
│   ├── README.md                       # Architecture overview
│   ├── TWO_LAYER_ARCHITECTURE.md       # Complete architecture guide
│   ├── THIN_ORCHESTRATOR_SUMMARY.md    # Pattern implementation
│   └── DECISION_TREE.md                # Code placement decisions
│
├── usage/                              # Usage examples and patterns
│   ├── README.md                       # Usage docs overview
│   ├── EXAMPLES.md                     # Basic examples
│   ├── EXAMPLES_SHOWCASE.md            # Real-world examples
│   ├── TEMPLATE_DESCRIPTION.md         # Template overview
│   ├── MARKDOWN_TEMPLATE_GUIDE.md      # Markdown authoring
│   ├── MANUSCRIPT_NUMBERING_SYSTEM.md  # Section numbering
│   ├── IMAGE_MANAGEMENT.md             # Image handling
│   └── VISUALIZATION_GUIDE.md          # Visualization system
│
├── operational/                        # Operational workflows
│   ├── README.md                       # Operational docs overview
│   ├── BUILD_SYSTEM.md                 # Build system reference
│   ├── CI_CD_INTEGRATION.md            # CI/CD setup
│   ├── DEPENDENCY_MANAGEMENT.md        # Package management
│   ├── PERFORMANCE_OPTIMIZATION.md      # Performance tuning
│   ├── CONFIGURATION.md                # Configuration guide
│   ├── CHECKPOINT_RESUME.md            # Checkpoint system
│   ├── TROUBLESHOOTING_GUIDE.md        # Troubleshooting
│   ├── LLM_REVIEW_TROUBLESHOOTING.md    # LLM-specific issues
│   ├── ERROR_HANDLING_GUIDE.md         # Error patterns
│   └── LOGGING_GUIDE.md                # Logging system
│
├── reference/                          # Reference materials
│   ├── README.md                       # Reference docs overview
│   ├── API_REFERENCE.md                # Complete API docs
│   ├── GLOSSARY.md                     # Terms and definitions
│   ├── FAQ.md                          # Common questions
│   ├── QUICK_START_CHEATSHEET.md       # Quick reference
│   ├── COMMON_WORKFLOWS.md             # Step-by-step recipes
│   └── COPYPASTA.md                    # Sharing content
│
├── modules/                            # Advanced modules
│   ├── README.md                       # Modules overview
│   ├── ADVANCED_MODULES_GUIDE.md       # Complete modules guide
│   ├── SCIENTIFIC_SIMULATION_GUIDE.md  # Simulation system
│   └── PDF_VALIDATION.md               # PDF validation
│
├── development/                        # Development & contribution
│   ├── README.md                       # Development docs overview
│   ├── CONTRIBUTING.md                 # Contribution guide
│   ├── CODE_OF_CONDUCT.md             # Community standards
│   ├── SECURITY.md                     # Security policy
│   ├── ROADMAP.md                      # Future plans
│   ├── TESTING_GUIDE.md                # Testing framework
│   ├── TESTING_WITH_CREDENTIALS.md     # Credential testing
│   └── COVERAGE_GAPS.md                # Coverage analysis
│
└── best-practices/                     # Best practices
    ├── README.md                       # Best practices overview
    ├── BEST_PRACTICES.md               # Consolidated practices
    ├── VERSION_CONTROL.md              # Git workflows
    ├── MULTI_PROJECT_MANAGEMENT.md     # Multi-project setup
    ├── MIGRATION_GUIDE.md              # Migration from other templates
    └── BACKUP_RECOVERY.md              # Backup strategies
```

### **Documentation Categories**

| Category | Directory | Purpose |
|----------|-----------|---------|
| **Core** | `core/` | Essential documentation for all users (HOW_TO_USE.md, ARCHITECTURE.md, WORKFLOW.md) |
| **Guides** | `guides/` | Usage guides by skill level (GETTING_STARTED.md, INTERMEDIATE_USAGE.md, ADVANCED_USAGE.md, EXPERT_USAGE.md) |
| **Architecture** | `architecture/` | System design and implementation (TWO_LAYER_ARCHITECTURE.md, THIN_ORCHESTRATOR_SUMMARY.md, DECISION_TREE.md) |
| **Usage** | `usage/` | Usage examples and patterns (EXAMPLES.md, MARKDOWN_TEMPLATE_GUIDE.md, VISUALIZATION_GUIDE.md) |
| **Development** | `development/` | Contributing and future development (CONTRIBUTING.md, CODE_OF_CONDUCT.md, ROADMAP.md, TESTING_GUIDE.md) |
| **Reference** | `reference/` | Quick reference and sharing content (FAQ.md, API_REFERENCE.md, GLOSSARY.md, QUICK_START_CHEATSHEET.md) |
| **Modules** | `modules/` | Advanced module documentation (ADVANCED_MODULES_GUIDE.md, SCIENTIFIC_SIMULATION_GUIDE.md, PDF_VALIDATION.md) |
| **Operational** | `operational/` | Operational workflows and guides (BUILD_SYSTEM.md, TROUBLESHOOTING_GUIDE.md, CONFIGURATION.md) |
| **Best Practices** | `best-practices/` | Best practices and project management (BEST_PRACTICES.md, VERSION_CONTROL.md, MIGRATION_GUIDE.md) |

## 🔗 **Cross-Referencing System**

All documentation files include comprehensive cross-references:

- **README.md** → Links to all major documentation directories
- **core/HOW_TO_USE.md** → Complete usage guide with all sections
- **core/ARCHITECTURE.md** → System design with related documentation links
- **All files** → Include context about related information

## 📖 **Detailed Reading Paths**

### **New Users - Complete Learning Path**
1. **[README.md](../README.md)** - Project overview (5 min)
2. **[guides/GETTING_STARTED.md](guides/GETTING_STARTED.md)** - Write first document (30 min)
3. **[reference/QUICK_START_CHEATSHEET.md](reference/QUICK_START_CHEATSHEET.md)** - Essential commands reference
4. **[reference/COMMON_WORKFLOWS.md](reference/COMMON_WORKFLOWS.md)** - Common tasks step-by-step
5. **[usage/EXAMPLES_SHOWCASE.md](usage/EXAMPLES_SHOWCASE.md)** - See real-world usage

### **Developers - Architecture & Patterns**
1. **[core/ARCHITECTURE.md](core/ARCHITECTURE.md)** - System design overview (15 min)
2. **[architecture/TWO_LAYER_ARCHITECTURE.md](architecture/TWO_LAYER_ARCHITECTURE.md)** - Complete architecture guide (30 min)
3. **[architecture/THIN_ORCHESTRATOR_SUMMARY.md](architecture/THIN_ORCHESTRATOR_SUMMARY.md)** - Pattern implementation (20 min)
4. **[core/WORKFLOW.md](core/WORKFLOW.md)** - Development process (20 min)
5. **[guides/INTERMEDIATE_USAGE.md](guides/INTERMEDIATE_USAGE.md)** - Add figures and automation

### **Contributors - Standards & Process**
1. **[development/CONTRIBUTING.md](development/CONTRIBUTING.md)** - Contribution guidelines (10 min)
2. **[.cursorrules/AGENTS.md](../.cursorrules/AGENTS.md)** - Development standards (30 min)
3. **[guides/ADVANCED_USAGE.md](guides/ADVANCED_USAGE.md)** - TDD workflow (45 min)
4. **[development/TESTING_GUIDE.md](development/TESTING_GUIDE.md)** - Testing requirements (20 min)
5. **[development/CODE_OF_CONDUCT.md](development/CODE_OF_CONDUCT.md)** - Community standards (5 min)

## 🎯 **Documentation Quality**

### **Standards Applied**
- ✅ **Comprehensive coverage** - All features and workflows documented
- ✅ **Cross-referencing** - All files include links to related content
- ✅ **Professional structure** - Clear organization and navigation
- ✅ **Practical examples** - Real-world usage patterns included
- ✅ **Troubleshooting** - Common issues and solutions documented
- ✅ **Best practices** - Established patterns and guidelines included

### **Build System**
- **[`docs/operational/BUILD_SYSTEM.md`](operational/BUILD_SYSTEM.md)** - Complete build system reference (status, performance, fixes)

### **Documentation Completeness**
- ✅ **52+ documentation files** covering all aspects (including root-level guides)
- ✅ **Complete cross-referencing** system
- ✅ **Real-world examples** and showcase projects
- ✅ **Technical implementation** details
- ✅ **Build system analysis** and performance metrics
- ✅ **Troubleshooting** and FAQ sections
- ✅ **Advanced modules** comprehensive guides
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
