# 📚 Documentation Index

This index provides an overview of all documentation files in the Research Project Template, organized by category and purpose.

## 🎯 **Quick Start by Persona**

### 👤 **New User / Content Creator**

1. **[README.md](../README.md)** - Project overview
2. **[guides/getting-started.md](guides/getting-started.md)** - Write your first document (Levels 1-3)
3. **[reference/quick-start-cheatsheet.md](reference/quick-start-cheatsheet.md)** - Essential commands
4. **[reference/common-workflows.md](reference/common-workflows.md)** - Step-by-step recipes
5. **[reference/faq.md](reference/faq.md)** - Common questions

### 👨‍💻 **Developer / Researcher**

1. **[core/how-to-use.md](core/how-to-use.md)** - Usage guide (all 12 levels)
2. **[guides/figures-and-analysis.md](guides/figures-and-analysis.md)** - Figures and automation (Levels 4-6)
3. **[core/architecture.md](core/architecture.md)** - System design overview
4. **[architecture/thin-orchestrator-summary.md](architecture/thin-orchestrator-summary.md)** - Pattern implementation
5. **[core/workflow.md](core/workflow.md)** - Development process

### 🏗️ **Contributor / Maintainer**

1. **[development/contributing.md](development/contributing.md)** - Contribution guidelines
2. **[rules/AGENTS.md](rules/AGENTS.md)** - Development standards
3. **[guides/testing-and-reproducibility.md](guides/testing-and-reproducibility.md)** - TDD workflow (Levels 7-9)
4. **[development/testing/testing-guide.md](development/testing/testing-guide.md)** - Testing requirements
5. **[development/code-of-conduct.md](development/code-of-conduct.md)** - Community standards

### 🔍 **Troubleshooter**

1. **[operational/troubleshooting/](operational/troubleshooting/)** - Troubleshooting guides
2. **[reference/faq.md](reference/faq.md)** - Common questions and solutions
3. **[operational/build/build-system.md](operational/build/build-system.md)** - Build system details
4. **[operational/config/performance-optimization.md](operational/config/performance-optimization.md)** - Performance issues
5. **[operational/troubleshooting/common-errors.md](operational/troubleshooting/common-errors.md#️-project-packages-missing-from-root-venv--silent-stage-4-failure)** - ⚠️ Silent Stage 4 failure pattern

---

> [!IMPORTANT]
> **Critical Rules for Multi-Project Pipelines (March 2026)**
>
> 1. **Root Venv Dependency Coverage** — If `projects/<name>/.venv` does NOT exist, every package in that project's `pyproject.toml` must also be in the root `pyproject.toml`. Violation: Stage 4 fails silently in < 1s. Fix: `uv sync` after adding to root deps.
> 2. **`matplotlib` in Core Deps** — Must be in `[project.dependencies]`, not `[project.optional-dependencies]`. `uv sync` without flags skips optional groups.
> 3. **`project_config:` Namespace** — Project-specific `config.yaml` keys that aren't in the `ManuscriptConfig` schema cause WARNING spam. Nest them under `project_config:` to suppress warnings.
> 4. **Idempotency** — Analysis scripts must skip network calls when output data files already exist.
>
> Details: [docs/AGENTS.md](AGENTS.md) | [guides/new-project-setup.md](guides/new-project-setup.md#pitfall-6-project-specific-packages-absent-from-root-venv--silent-stage-4-failure)

---

## 🏗️ **Development Rules**

Development standards (formerly in `.cursorrules/`) are documented in the `rules/` directory:

- **[`rules/AGENTS.md`](rules/AGENTS.md)** - Overview and navigation guide
- **[`rules/README.md`](rules/README.md)** - Quick reference and patterns
- **[`rules/error_handling.md`](rules/error_handling.md)** - Exception handling patterns
- **[`rules/security.md`](rules/security.md)** - Security standards
- **[`rules/python_logging.md`](rules/python_logging.md)** - Logging standards
- **[`rules/infrastructure_modules.md`](rules/infrastructure_modules.md)** - Infrastructure module development
- **[`rules/testing_standards.md`](rules/testing_standards.md)** - Testing patterns
- **[`rules/documentation_standards.md`](rules/documentation_standards.md)** - Documentation writing guide
- **[`rules/type_hints_standards.md`](rules/type_hints_standards.md)** - Type annotation patterns
- **[`rules/llm_standards.md`](rules/llm_standards.md)** - LLM/Ollama integration
- **[`rules/code_style.md`](rules/code_style.md)** - Code formatting
- **[`rules/git_workflow.md`](rules/git_workflow.md)** - Git workflow
- **[`rules/api_design.md`](rules/api_design.md)** - API design
- **[`rules/manuscript_style.md`](rules/manuscript_style.md)** - Manuscript formatting
- **[`rules/reporting.md`](rules/reporting.md)** - Reporting module standards
- **[`rules/refactoring.md`](rules/refactoring.md)** - Refactoring standards
- **[`rules/folder_structure.md`](rules/folder_structure.md)** - Folder structure

---

## 🎯 **Core Documentation**

- **[README.md](../README.md)** - Main project overview and quick start
- **[AGENTS.md](../AGENTS.md)** - System documentation
- **[CLOUD_DEPLOY.md](CLOUD_DEPLOY.md)** - **Headless / cloud server deployment guide** ☁️
- **[PAI.md](PAI.md)** - **Personal AI Infrastructure (PAI)** 🤖
- **[RUN_GUIDE.md](RUN_GUIDE.md)** - **Run guide and pipeline reference** 🚀
- **[core/how-to-use.md](core/how-to-use.md)** - Usage guide (all 12 levels)

### Quick Reference

- **[reference/copypasta.md](reference/copypasta.md)** - Ready-to-use sharing content
- **[reference/faq.md](reference/faq.md)** - FAQs
- **[reference/quick-start-cheatsheet.md](reference/quick-start-cheatsheet.md)** - Essential commands
- **[reference/common-workflows.md](reference/common-workflows.md)** - Step-by-step recipes
- **[reference/glossary.md](reference/glossary.md)** - Glossary of terms

---

## 🏗️ **Architecture & Design**

- **[core/architecture.md](core/architecture.md)** - System design overview
- **[architecture/two-layer-architecture.md](architecture/two-layer-architecture.md)** - Two-layer architecture guide
- **[architecture/thin-orchestrator-summary.md](architecture/thin-orchestrator-summary.md)** - Thin orchestrator pattern
- **[architecture/decision-tree.md](architecture/decision-tree.md)** - Code placement decisions
- **[core/workflow.md](core/workflow.md)** - Development workflow

---

## 📝 **Usage Guides**

### Skill-Level Guides

- **[guides/getting-started.md](guides/getting-started.md)** - Levels 1-3 (Beginner)
- **[guides/figures-and-analysis.md](guides/figures-and-analysis.md)** - Levels 4-6 (Intermediate)
- **[guides/testing-and-reproducibility.md](guides/testing-and-reproducibility.md)** - Levels 7-9 (Advanced)
- **[guides/extending-and-automation.md](guides/extending-and-automation.md)** - Levels 10-12 (Expert)
- **[guides/new-project-setup.md](guides/new-project-setup.md)** - New project checklist (all learnings)

### Content Authoring

- **[usage/examples.md](usage/examples.md)** - Project customization examples
- **[usage/examples-showcase.md](usage/examples-showcase.md)** - Real-world examples
- **[usage/template-description.md](usage/template-description.md)** - Template overview
- **[usage/markdown-template-guide.md](usage/markdown-template-guide.md)** - Markdown authoring
- **[usage/manuscript-numbering-system.md](usage/manuscript-numbering-system.md)** - Section numbering
- **[usage/style-guide.md](usage/style-guide.md)** - Equations, figures, tables
- **[usage/image-management.md](usage/image-management.md)** - Image handling
- **[usage/visualization-guide.md](usage/visualization-guide.md)** - Publication-quality figures

### Scientific Computing

- **[modules/scientific-simulation-guide.md](modules/scientific-simulation-guide.md)** - Simulation system

---

## 🔧 **Development & Maintenance**

- **[development/contributing.md](development/contributing.md)** - Contribution guidelines
- **[development/code-of-conduct.md](development/code-of-conduct.md)** - Community standards
- **[development/security.md](development/security.md)** - Security policy
- **[development/roadmap.md](development/roadmap.md)** - Development roadmap
- **[development/coverage-gaps.md](development/coverage-gaps.md)** - Coverage analysis
- **[development/testing/testing-guide.md](development/testing/testing-guide.md)** - Testing framework
- **[development/testing/testing-with-credentials.md](development/testing/testing-with-credentials.md)** - Credential testing

---

## 🧪 **Advanced Modules**

- **[modules/modules-guide.md](modules/modules-guide.md)** - All 10 infrastructure modules
- **[reference/api-reference.md](reference/api-reference.md)** - Unified API documentation
- **[modules/pdf-validation.md](modules/pdf-validation.md)** - PDF validation system

### Per-Module Guides (`modules/guides/`)

- **[modules/guides/integrity-module.md](modules/guides/integrity-module.md)**
- **[modules/guides/llm-module.md](modules/guides/llm-module.md)**
- **[modules/guides/publishing-module.md](modules/guides/publishing-module.md)**
- **[modules/guides/rendering-module.md](modules/guides/rendering-module.md)**
- **[modules/guides/reporting-module.md](modules/guides/reporting-module.md)**
- **[modules/guides/scientific-module.md](modules/guides/scientific-module.md)**

---

## ⚙️ **Operational Guides**

### Build & CI/CD (`operational/build/`)

- **[operational/build/build-system.md](operational/build/build-system.md)** - Build pipeline
- **[operational/build/build-history.md](operational/build/build-history.md)** - Build changelog
- **[operational/build/build-performance.md](operational/build/build-performance.md)** - Build performance tuning
- **[operational/build/ci-cd-integration.md](operational/build/ci-cd-integration.md)** - GitHub Actions
- **[operational/build/dependency-management.md](operational/build/dependency-management.md)** - uv package manager

### Configuration & Performance (`operational/config/`)

- **[operational/config/configuration.md](operational/config/configuration.md)** - Configuration system
- **[operational/config/checkpoint-resume.md](operational/config/checkpoint-resume.md)** - Checkpoint system
- **[operational/config/performance-optimization.md](operational/config/performance-optimization.md)** - Performance tuning

### Logging (`operational/logging/`)

- **[operational/logging/](operational/logging/)** - Comprehensive logging guide
- **[operational/logging/python-logging.md](operational/logging/python-logging.md)** - Python logging
- **[operational/logging/bash-logging.md](operational/logging/bash-logging.md)** - Bash logging
- **[operational/logging/logging-patterns.md](operational/logging/logging-patterns.md)** - Cross-language patterns

### Troubleshooting (`operational/troubleshooting/`)

- **[operational/troubleshooting/](operational/troubleshooting/)** - Diagnostic flowchart and approach
- **[operational/troubleshooting/common-errors.md](operational/troubleshooting/common-errors.md)** - Error patterns
- **[operational/troubleshooting/build-tools.md](operational/troubleshooting/build-tools.md)** - Build tool issues
- **[operational/troubleshooting/test-failures.md](operational/troubleshooting/test-failures.md)** - Test debugging
- **[operational/troubleshooting/environment-setup.md](operational/troubleshooting/environment-setup.md)** - Environment setup
- **[operational/troubleshooting/recovery-procedures.md](operational/troubleshooting/recovery-procedures.md)** - Recovery
- **[operational/troubleshooting/llm-review.md](operational/troubleshooting/llm-review.md)** - LLM review issues
- **[operational/troubleshooting/llm-diagnostics.md](operational/troubleshooting/llm-diagnostics.md)** - LLM diagnostics

### Other Operational Guides

- **[operational/reporting-guide.md](operational/reporting-guide.md)** - Reporting system
- **[operational/error-handling-guide.md](operational/error-handling-guide.md)** - Error handling patterns

---

## 📚 **Reference Materials**

- **[best-practices/best-practices.md](best-practices/best-practices.md)** - Consolidated best practices
- **[best-practices/version-control.md](best-practices/version-control.md)** - Git workflows
- **[best-practices/multi-project-management.md](best-practices/multi-project-management.md)** - Multi-project setup
- **[best-practices/migration-guide.md](best-practices/migration-guide.md)** - Migration from other templates
- **[best-practices/backup-recovery.md](best-practices/backup-recovery.md)** - Backup strategies

---

## 🔒 **Security & Provenance**

- **[security/README.md](security/README.md)** - Security overview
- **[security/steganography.md](security/steganography.md)** - Alpha-channel watermarking and QR codes
- **[security/hashing_and_manifests.md](security/hashing_and_manifests.md)** - SHA-256/512 hashing and manifests
- **[security/secure_execution.md](security/secure_execution.md)** - `secure_run.sh` orchestration and threat model

---

## 🤖 **AI Prompt Templates**

- **[prompts/README.md](prompts/README.md)** - Navigation guide
- **[prompts/manuscript_creation.md](prompts/manuscript_creation.md)** - Manuscript creation
- **[prompts/code_development.md](prompts/code_development.md)** - Code development
- **[prompts/test_creation.md](prompts/test_creation.md)** - Test creation
- **[prompts/feature_addition.md](prompts/feature_addition.md)** - Feature addition
- **[prompts/refactoring.md](prompts/refactoring.md)** - Refactoring
- **[prompts/documentation_creation.md](prompts/documentation_creation.md)** - Documentation creation
- **[prompts/infrastructure_module.md](prompts/infrastructure_module.md)** - Infrastructure modules
- **[prompts/validation_quality.md](prompts/validation_quality.md)** - Validation and QA
- **[prompts/comprehensive_assessment.md](prompts/comprehensive_assessment.md)** - Assessment and review

---

## 📁 **Directory Structure**

```text
docs/
├── README.md                           # Docs entry point
├── AGENTS.md                           # Documentation hub guide
├── documentation-index.md              # This index
│
├── core/                               # Essential documentation
│   ├── how-to-use.md                   # Usage guide (12 levels)
│   ├── architecture.md                 # System design overview
│   └── workflow.md                     # Development workflow
│
├── guides/                             # Skill-level guides
│   ├── getting-started.md              # Levels 1-3
│   ├── figures-and-analysis.md         # Levels 4-6
│   ├── testing-and-reproducibility.md  # Levels 7-9
│   ├── extending-and-automation.md     # Levels 10-12
│   └── new-project-setup.md            # Setup checklist + pitfalls
│
├── architecture/                       # Architecture documentation
│   ├── two-layer-architecture.md       # Full architecture guide
│   ├── thin-orchestrator-summary.md    # Pattern implementation
│   └── decision-tree.md               # Code placement decisions
│
├── usage/                              # Content authoring & patterns
│   ├── examples.md, examples-showcase.md
│   ├── markdown-template-guide.md, style-guide.md
│   ├── manuscript-numbering-system.md
│   ├── image-management.md, visualization-guide.md
│   └── template-description.md
│
├── operational/                        # Operational workflows
│   ├── build/                          # Build pipeline & CI/CD
│   │   ├── build-system.md, build-history.md
│   │   ├── build-performance.md
│   │   ├── ci-cd-integration.md
│   │   └── dependency-management.md
│   ├── config/                         # Configuration & performance
│   │   ├── configuration.md
│   │   ├── checkpoint-resume.md
│   │   └── performance-optimization.md
│   ├── logging/                        # Logging guides
│   │   ├── README.md (comprehensive guide)
│   │   ├── python-logging.md, bash-logging.md
│   │   └── logging-patterns.md
│   ├── troubleshooting/                # Troubleshooting guides
│   │   ├── README.md (flowchart)
│   │   ├── common-errors.md, build-tools.md
│   │   ├── test-failures.md, environment-setup.md
│   │   ├── recovery-procedures.md
│   │   ├── llm-review.md
│   │   └── llm-diagnostics.md
│   ├── reporting-guide.md
│   └── error-handling-guide.md
│
├── reference/                          # Reference materials
│   ├── api-reference.md (unified)
│   ├── glossary.md, faq.md
│   ├── quick-start-cheatsheet.md
│   ├── common-workflows.md
│   └── copypasta.md
│
├── modules/                            # Infrastructure modules
│   ├── modules-guide.md
│   ├── scientific-simulation-guide.md
│   ├── pdf-validation.md
│   └── guides/ (6 per-module guides)
│
├── development/                        # Development & contribution
│   ├── contributing.md, code-of-conduct.md
│   ├── security.md, roadmap.md
│   ├── coverage-gaps.md
│   └── testing/
│       ├── testing-guide.md
│       └── testing-with-credentials.md
│
├── best-practices/                     # Best practices
│   ├── best-practices.md
│   ├── version-control.md
│   ├── multi-project-management.md
│   ├── migration-guide.md
│   └── backup-recovery.md
│
├── prompts/                            # AI prompt templates (9)
│   ├── manuscript_creation.md, code_development.md
│   ├── test_creation.md, feature_addition.md
│   ├── refactoring.md, documentation_creation.md
│   ├── infrastructure_module.md
│   ├── validation_quality.md
│   └── comprehensive_assessment.md
│
├── security/                           # Security & provenance
│   ├── README.md
│   ├── steganography.md
│   ├── hashing_and_manifests.md
│   └── secure_execution.md
│
└── audit/                              # Audit reports
    ├── documentation-review-report.md
    ├── documentation-review-summary.md
    └── filepath-audit-report.md
```

---

## 📋 Documentation Maintenance Notes

- All documentation is maintained as evergreen content (no time-sensitive dates).
- Each sub-directory has a `README.md` (user-facing) and `AGENTS.md` (technical guide).
- Documentation is verified for accuracy and completeness on an ongoing basis.

For the most up-to-date information, see the individual documentation files linked above.
