# 🧠 PAI.md - Scripts Context

## 📍 Purpose
This directory contains the **Entry Point Orchestrators**. These scripts drive the execution pipeline (setup, test, analysis, render, validate).

## ⚡ Design Pattern
- **Thin Orchestration**: Scripts should primarily coordinate. Heavy logic belongs in `projects/{name}/src/` or `infrastructure/`.
- **Project Discovery**: Scripts use `infrastructure.project.discovery` to find and execute project-specific code.

## 🤖 Agent Guidelines
- **Usage**: Use these scripts to run tasks (e.g., `python3 scripts/01_run_tests.py`).
- **New Stages**: If adding a pipeline stage, ensure it follows the `XX_name.py` naming convention and supports the `--project` flag.
