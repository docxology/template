# 🧠 PAI.md - Projects Context

## 📍 Purpose

This directory contains the **Layer 2** domain-specific research projects. Each subdirectory is a self-contained research environment.

## 📂 Structure Per Project

- `src/`: Pure scientific logic and self-contained execution.
- `tests/`: Zero-Mock test suite guaranteeing 100% testability.
- `scripts/`: Thin Orchestrators handling side-effects and coordination.
- `manuscript/`: Markdown source and configuration.
- `docs/`: Modular documentation hub.
- `output/`: Working directory for generated artifacts.

## 🤖 Agent Guidelines

- **Isolation**: Projects should not import from each other.
- **Infrastructure Usage**: Projects can and should import from `infrastructure/`.
- **Creation**: To create a new project, copy an existing project under `projects/` as a template.
