# 🤖 AGENTS.md - `projects/blake_bimetalism/`

## 🎯 Directory Overview

This directory houses the `blake_bimetalism` research project, an 18-chapter scholarly manuscript that synthesizes William Blake's mystical-poetic critique of atomistic materialism with macroeconomic monetary history. The project traces a 500-year arc—from the 1558 Elizabethan debasement through the 1971 Nixon Shock to the 2026 American "Monetary Federalism" movement—mapping structural Bimetallism (Gresham's Law, Newtonian ratios) directly onto Blake's cosmology of Urizen (centralized abstraction) and Orc (tangible, earthly rebellion).

This project strictly adheres to the repository's **Two-Layer Architecture**, **Thin Orchestrator Pattern**, **Zero-Mock Policy**, and is verified by deep academic scholarship (Friedman, Flandreau, Redish).

## 🏗️ Architecture Rules

### 1. Two-Layer Architecture Compliance
- **Generic Tools**: Do not write project-agnostic build/render code here. Rely exclusively on root `/infrastructure/`.
- **Domain Logic**: All business logic (quantitative mathematical analysis, topological Gresham's Law rendering) lives in `/src/` and its highly specialized `/src/viz/` programmatic engine.
- **Test Suite**: Located in `/tests/`, ensuring that all mathematical and manuscript assertions are functionally verifiable without stubs.
- **Workflow Orchestration**: Lives in `/scripts/`, driving domain tasks before the 10-stage root pipeline converts outputs to the final publication artifacts.

### 2. Thin Orchestrators (`scripts/`)
- Scripts (e.g., `scripts/analyze.py`, `scripts/generate_figures.py`) MUST NOT contain business logic.
- They must import from `projects.blake_bimetalism.src.*` to orchestrate operations.
- They output serialized results (e.g., 6 mathematical `.svg` figures) to `output/` so that the DAG pipeline can ingest and normalize them for LaTeX.

### 3. Zero-Mock Testing (`tests/`)
- All tests in `tests/test_*.py` operate without mocking core business logic.
- Mathematical models (e.g., fractional reserve deflation limits, 15:1 vs 15.21:1 structural bounds) and manuscript file extraction (18 explicit `.md` files) are rigorously asserted.

## 📁 Directory Structure
- `src/`: Domain-specific analysis, including the `viz/` subpackage powering the programmatic visualizations.
- `tests/`: 100% Zero-Mock tests.
- `scripts/`: Thin scripts handling CLI ingestion and triggering the visualization generation.
- `manuscript/`: The 18 structured scholarly Markdown chapters (`00_` to `06_`) and the BibTeX database (`references.bib`).
- `doc/`: Deep technical documentation of the modules.
- `output/`: Ephemeral output directory where charts and analysis metrics are deposited prior to finalizing root outputs.

## 🚀 Execution

This project is automatically discovered and processed by the root 10-stage pipeline, which will sequentially assemble the 18 files, resolve bibliography, and produce LaTeX, PDF, and HTML targets:
```bash
# Run the complete manuscript processing pipeline
./secure_run.sh --project blake_bimetalism
# Or bypass the interactive menu:
./run.sh --pipeline --project blake_bimetalism
```
