# 🧠 PAI.md - Projects Context

## 📍 Purpose
This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment.

## 📂 Structure Per Project
- `src/`: Scientific code and business logic.
- `tests/`: Project-specific test suite.
- `scripts/`: Analysis workflows (called by root orchestrators).
- `manuscript/`: Markdown source and configuration.
- `output/`: Working directory for generated artifacts.

## 🤖 Agent Guidelines
- **Isolation**: Projects should not import from each other.
- **Infrastructure Usage**: Projects can and should import from `infrastructure/`.
- **Creation**: To create a new project, copy an existing project under `projects/` as a template.
