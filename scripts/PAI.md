# 🧠 PAI.md - Scripts Context

## 📍 Purpose
This directory contains the **Entry Point Orchestrators**. This directory holds role-specific entry-point orchestrators: `pipeline/` (stage scripts), `runner/` (pipeline, matrix, bundle and archival runners), `audit/` (documentation, drift, tracked-resource and publication-output gates), `docgen/` (`docs/_generated/` writers), `publish/` (release helpers), `gates/` (opt-in gates plus the offline local gate), `maintenance/`, `shell/` and `fixtures/`. Business logic stays in `infrastructure/`.

## PAI v5 Operations

The template pipeline remains separate from the local PAI daemon. PAI v5 operational checks use Pulse on `http://localhost:31337`, especially `GET /api/pulse/health` and `POST /notify`. Do not add Pulse lifecycle work to these scripts unless the template pipeline itself needs it.

## ⚡ Design Pattern
- **Thin Orchestration**: Scripts should primarily coordinate. Heavy logic belongs in `projects/{name}/src/` or `infrastructure/`.
- **Project Discovery**: Scripts use `infrastructure.project.discovery` to find and execute project-specific code.

## 🤖 Agent Guidelines
- **Usage**: Use these scripts to run tasks (e.g., `uv run python scripts/pipeline/stage_01_test.py`).
- **New Stages**: If adding a pipeline stage, ensure it follows the `XX_name.py` naming convention and supports the `--project` flag.
