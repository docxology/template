# Standards Compliance Matrix

This document maps current project practices to `.cursorrules/` development standards, providing a compliance checklist and quick reference for developers.

## Overview

The project follows comprehensive development standards defined in the `.cursorrules/` directory. This document shows how project practices align with these standards and provides compliance verification.

## Standards Compliance Matrix

### Code Quality Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Code Style** ([`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md)) | Black formatting, isort imports, flake8 linting | ✅ Full | Automated in CI |
| **Type Hints** ([`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md)) | All public APIs typed, comprehensive annotations | ✅ Full | mypy validation |
| **Error Handling** ([`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md)) | Custom exceptions, proper chaining, context | ✅ Full | Exception hierarchy |
| **Logging** ([`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md)) | Unified logging system, structured messages | ✅ Full | `get_logger(__name__)` |
| **API Design** ([`.cursorrules/api_design.md`](../../../.cursorrules/api_design.md)) | Consistent signatures, keyword-only params | ✅ Full | Function patterns |

### Testing Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **No Mocks Policy** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md)) | Real data testing, no MagicMock/pytest-mock | ✅ Full | `verify_no_mocks.py` |
| **Coverage Requirements** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md)) | 90% project, 60% infrastructure coverage | ✅ Full | pytest-cov validation |
| **Test Organization** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md)) | Clear structure, fixtures, parameterized tests | ✅ Full | Test directory structure |
| **TDD Approach** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md)) | Tests written before/ alongside code | ✅ Full | Test-first development |

### Documentation Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **AGENTS.md Structure** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md)) | Comprehensive docs with all required sections | ✅ Full | All AGENTS.md files |
| **README.md Pattern** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md)) | Quick reference with Mermaid diagrams | ✅ Full | All README.md files |
| **Code Documentation** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md)) | Google-style docstrings, examples | ✅ Full | All public functions |
| **Cross-References** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md)) | Proper linking between documents | ✅ Full | "See Also" sections |

### Git Workflow Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Branch Naming** ([`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md)) | `type/description` format (feature/, bugfix/, etc.) | ✅ Full | Branch creation |
| **Commit Messages** ([`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md)) | `<type>(<scope>): <description>` format | ✅ Full | Commit standards |
| **Pull Requests** ([`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md)) | Template with testing, breaking changes | ✅ Full | PR process |
| **Pre-commit Hooks** ([`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md)) | Automated formatting, linting, testing | ✅ Full | CI/CD pipeline |

### Refactoring Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Clean Break Approach** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md)) | No backward compatibility, full migration | ✅ Full | Refactoring procedures |
| **Modularization** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md)) | Clear separation of concerns, single responsibility | ✅ Full | Module boundaries |
| **Testing During Refactor** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md)) | Full coverage before changes, validate after | ✅ Full | Refactor playbook |

### Infrastructure Module Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Generic Focus** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md)) | Reusable across projects, domain-independent | ✅ Full | Infrastructure layer |
| **60% Coverage** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md)) | Minimum 60% test coverage achieved | ✅ Full | Coverage reports |
| **Public API** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md)) | Clear `__init__.py` exports, comprehensive docs | ✅ Full | Module organization |
| **Error Handling** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md)) | Custom exceptions, proper context | ✅ Full | Exception patterns |

## Project-Specific Standards

### Architecture Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Two-Layer Architecture** ([`.cursorrules/AGENTS.md`](../../../.cursorrules/AGENTS.md)) | Clear separation: infrastructure (generic) vs project (specific) | ✅ Full | Layer organization |
| **Thin Orchestrator Pattern** ([`.cursorrules/AGENTS.md`](../../../.cursorrules/AGENTS.md)) | Scripts coordinate, modules compute | ✅ Full | Script structure |
| **Project Layer Focus** ([`.cursorrules/AGENTS.md`](../../../.cursorrules/AGENTS.md)) | Domain-specific algorithms, 90% coverage | ✅ Full | Scientific modules |

### Manuscript Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Equation Formatting** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | equation environment, proper labels | ✅ Full | LaTeX equations |
| **Cross-References** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | ref and eqref commands | ✅ Full | Reference system |
| **Figure Standards** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | Relative paths, proper captions, labels | ✅ Full | Figure management |
| **Citation Format** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | `\cite{key}` before punctuation | ✅ Full | Bibliography system |
| **Section Numbering** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | 01-09 main, S01-S0N supplemental, 98-99 reference | ✅ Full | File naming system |
| **Table Formatting** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | LaTeX tabular with borders and captions | ✅ Full | Table structures |
| **Heading Hierarchy** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | # ## ### with section labels | ✅ Full | Document structure |
| **Configuration Management** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md)) | YAML config files with metadata | ✅ Full | Paper metadata |

#### Detailed Manuscript Examples

**Equation Definitions for Examples:**
```latex
% Convergence equation referenced in examples
\begin{equation}\label{eq:convergence}
\|x_k - x^*\| \leq C \rho^k
\end{equation}
```

**Equation Formatting Examples:**
```latex
% From 03_methodology.md - Display equations with labels
\begin{equation}\label{eq:objective_compliance}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x) + \lambda R(x)
\end{equation}

% From S01_supplemental_methods.md - Multi-line equations
\begin{equation}\label{eq:iterations_bound_compliance}
\|x_k - x^*\| \leq C \rho^k \leq \epsilon \Rightarrow k \geq \frac{\log(C/\epsilon)}{\log(1/\rho)} = O(\kappa \log(1/\epsilon))
\end{equation}
```

**Cross-Reference Examples:**
```markdown
% Section references from 04_experimental_results.md
Our experimental evaluation follows the methodology described in Section \ref{sec:methodology}.

% Equation references from 04_experimental_results.md
The results demonstrate that our approach achieves the theoretical convergence rate \eqref{eq:convergence}.

% Figure references from 02_introduction.md
Figure \ref{fig:example_figure} shows a mathematical function.
```

**Figure Integration Examples:**
```markdown
% From 03_methodology.md - Figure with proper sizing and paths
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/experimental_setup.png}
\caption{Experimental pipeline showing the complete workflow}
\label{fig:experimental_setup}
\end{figure}

% From 04_experimental_results.md - Multiple figures
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Algorithm convergence comparison showing performance improvement}
\label{fig:convergence_plot}
\end{figure}
```

**Citation Style Examples:**
```markdown
% Single citations from 01_abstract.md
building on foundational work in convex optimization \cite{boyd2004, nesterov2018}

% Multiple citations from 03_methodology.md
extending classical convex optimization methods \cite{boyd2004, nesterov2018} with modern adaptive strategies \cite{kingma2014, duchi2011}.
```

**Table Formatting Examples:**
```latex
% From 04_experimental_results.md - Complex table with borders
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Method} & \textbf{Convergence Rate} & \textbf{Memory Usage} & \textbf{Success Rate (\%)} \\
\hline
Our Method & 0.85 & $O(n)$ & 94.3 \\
Gradient Descent & 0.9 & $O(n^2)$ & 85.0 \\
Adam & 0.9 & $O(n^2)$ & 85.0 \\
L-BFGS & 0.9 & $O(n^2)$ & 85.0 \\
\hline
\end{tabular}
\caption{Performance comparison with state-of-the-art methods}
\label{tab:performance_comparison}
\end{table}
```

**Section Structure Examples:**
```markdown
% From 02_introduction.md - Main sections with labels
# Introduction {#sec:introduction}

## Overview

## Project Structure

# Methodology {#sec:methodology}

## Mathematical Framework

### Optimization Problem

# Experimental Results {#sec:experimental_results}

## Experimental Setup
```

**Configuration Examples:**
```yaml
# From config.yaml.example - Complete metadata structure
paper:
  title: "Novel Optimization Framework for Machine Learning"
  subtitle: "A Comprehensive Approach to Large-Scale Problems"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "Department of Computer Science, University of Example"
    corresponding: true

publication:
  doi: ""
  journal: "Journal of Example Research"
  volume: "42"
  pages: ""
  year: ""
```

### LLM Integration Standards

| Standard | Project Practice | Compliance | Reference |
|----------|------------------|------------|-----------|
| **Local-First Approach** ([`.cursorrules/llm_standards.md`](../../../.cursorrules/llm_standards.md)) | Ollama integration, privacy-focused | ✅ Full | LLM infrastructure |
| **Template System** ([`.cursorrules/llm_standards.md`](../../../.cursorrules/llm_standards.md)) | Reusable prompts for research tasks | ✅ Full | Prompt templates |
| **Error Handling** ([`.cursorrules/llm_standards.md`](../../../.cursorrules/llm_standards.md)) | Graceful degradation, fallback handling | ✅ Full | LLM robustness |

## Compliance Verification

### Automated Checks

```bash
# Code quality (CI/CD)
black --check .                    # Code formatting
isort --check-only .              # Import sorting
flake8 .                          # Linting
mypy .                            # Type checking

# Testing (CI/CD)
pytest --cov=. --cov-fail-under=90  # Coverage requirements
python3 scripts/verify_no_mocks.py  # No mocks policy

# Documentation (CI/CD)
python3 -m infrastructure.validation.cli markdown docs/ --strict
```

### Manual Verification

#### Pre-Commit Checklist
- [ ] Code follows formatting standards (Black, isort)
- [ ] Type hints on all public APIs
- [ ] Tests written for new functionality
- [ ] Documentation updated (AGENTS.md, README.md)
- [ ] No mocks used in tests
- [ ] Commit message follows standards

#### Code Review Checklist
- [ ] Two-layer architecture respected
- [ ] Thin orchestrator pattern followed
- [ ] Error handling uses custom exceptions
- [ ] Logging uses unified system
- [ ] Test coverage requirements met
- [ ] Documentation standards followed

## Standards Quick Reference

### For New Code
1. **Write tests first** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md))
2. **Add type hints** ([`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md))
3. **Handle errors properly** ([`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md))
4. **Use unified logging** ([`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md))
5. **Format with Black** ([`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md))
6. **Document thoroughly** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md))

### For Refactoring
1. **No backward compatibility** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md))
2. **Clean break approach** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md))
3. **Maintain test coverage** ([`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md))
4. **Update all imports** ([`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md))
5. **Update documentation** ([`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md))

### For Infrastructure Development
1. **Generic and reusable** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md))
2. **60% minimum coverage** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md))
3. **Clear public API** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md))
4. **Comprehensive documentation** ([`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md))

### For Manuscript Writing
1. **Use equation environment** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md))
2. **Proper cross-references** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md))
3. **Figure standards** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md))
4. **Citation formatting** ([`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md))

## Compliance Status

### Current Status: ✅ FULLY COMPLIANT

**All major standards implemented:**
- ✅ **Code Quality**: Black, isort, flake8, mypy
- ✅ **Testing**: No mocks, 90% project coverage, 60% infrastructure coverage
- ✅ **Documentation**: AGENTS.md + README.md pattern, comprehensive cross-references
- ✅ **Git Workflow**: Proper branching, conventional commits, PR templates
- ✅ **Architecture**: Two-layer separation, thin orchestrator pattern
- ✅ **Error Handling**: Custom exception hierarchy, proper context
- ✅ **Logging**: Unified system with structured messages
- ✅ **Type Safety**: Comprehensive type hints on all APIs

### Continuous Compliance

**Automated Enforcement:**
- Pre-commit hooks for formatting and basic checks
- CI/CD pipeline with comprehensive validation
- Coverage requirements enforced
- Documentation validation in build process

**Manual Oversight:**
- Code reviews check standards compliance
- Documentation reviews ensure completeness
- Regular audits of standards alignment

## Common Compliance Issues

### Most Common Issues
1. **Missing type hints** - All public APIs must be typed
2. **Mock usage** - Never use mocks, test with real data
3. **Low coverage** - Must meet 90% project, 60% infrastructure requirements
4. **Poor documentation** - All changes need AGENTS.md/README.md updates
5. **Inconsistent formatting** - Always use Black and isort

### Quick Fixes
```bash
# Fix formatting
black file.py
isort file.py

# Check types
mypy file.py

# Run tests with coverage
pytest --cov=file --cov-report=html

# Validate docs
python3 -m infrastructure.validation.cli markdown docs/
```

## Standards Evolution

### Updating Standards
1. **Review current practices** against new requirements
2. **Update .cursorrules/ files** with new standards
3. **Update this compliance matrix** to reflect changes
4. **Provide migration guides** for breaking changes
5. **Update CI/CD** to enforce new standards

### Version Compatibility
- Standards are versioned with the template
- Breaking changes require migration documentation
- Backward compatibility maintained where possible
- Clear upgrade paths provided

## See Also

**Development Standards:**
- [`.cursorrules/AGENTS.md`](../../../.cursorrules/AGENTS.md) - Development standards overview
- [`.cursorrules/README.md`](../../../.cursorrules/README.md) - Quick standards reference
- [`.cursorrules/folder_structure.md`](../../../.cursorrules/folder_structure.md) - Documentation structure standards

**Project Documentation:**
- [`AGENTS.md`](AGENTS.md) - Complete project documentation
- [`README.md`](README.md) - Quick reference
- [`development_workflow.md`](development_workflow.md) - Complete development workflow

**Template Documentation:**
- [`../../AGENTS.md`](../../AGENTS.md) - Complete template documentation
- [`../../docs/core/ARCHITECTURE.md`](../../docs/core/ARCHITECTURE.md) - System architecture
- [`../../docs/best-practices/BEST_PRACTICES.md`](../../docs/best-practices/BEST_PRACTICES.md) - Code quality best practices

---

**Last Updated:** 2025-01-01
**Compliance Status:** ✅ Fully Compliant
**Next Review:** Monthly automated checks