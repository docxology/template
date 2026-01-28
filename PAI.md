# 🧠 PAI.md - Personal AI Infrastructure Context

## 🆔 Identity
- **System**: Research Project Template
- **Role**: Standardized Research Execution Environment
- **Type**: Core Infrastructure / Skill
- **Signposting**: Linked to [PAI Core](../../.gemini/antigravity/knowledge/personal_ai_infrastructure_pai_system/artifacts/overview.md)

## 📍 Purpose
This repository serves as the **canonical template** for all research projects within the Personal AI Infrastructure. It enforces:

1.  **Standardized Structure**: Separation of generic `infrastructure/` and domain-specific `projects/`.
2.  **Thin Orchestration**: Scripts that orchestrate logic defined in `src/` modules.
3.  **Zero-Mock Testing**: Absolute prohibition on mocks; validation via real execution.
4.  **Agent-Friendly Documentation**: Comprehensive `AGENTS.md` and `PAI.md` coverage.

## 🛠️ Usage for Agents
Agents operating within this repository should:

- **Discover**: Use `infrastructure.project.discovery` to find active projects.
- **Execute**: Prefer `scripts/` entry points (e.g., `01_run_tests.py`, `02_run_analysis.py`).
- **Verify**: Always run tests before making changes: `scripts/01_run_tests.py`.
- **Document**: Update `AGENTS.md` when architectural patterns change.

## 🔗 Architecture Linkage
- **Infrastructure**: Provides generic build, validation, and rendering tools.
- **Projects**: Contain domain-specific science and logic.
- **Output**: Tethered to the `output/` directory (ignored by git, validated for integrity).

## ⚠️ Constraints
- **No Legacy**: Legacy methods are actively removed.
- **Real Tests**: No mocks allowed. Use `scripts/verify_no_mocks.py` to check.
