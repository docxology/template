# 🧠 PAI.md - Infrastructure Context

## 📍 Purpose
This directory contains the **Layer 1** generic tools that power the research template. Code here is **project-agnostic** and strictly separated from domain-specific logic.

## 🛠️ Components
- **Core**: Logging, config, environment management.
- **Validation**: File integrity, PDF/Markdown checking (`output_validator.py`, `audit_orchestrator.py`).
- **Rendering**: PDF generation logic.
- **LLM**: Local model integration for reviews.

## 🤖 Agent Guidelines
- **Import Rules**: Can import from standard libs. **Cannot** import from `projects/` (prevents circular dependency).
- **Testing**: Must be tested in `tests/infra_tests/`.
- **Modifications**: Changes here affect ALL projects. Exercise caution.
