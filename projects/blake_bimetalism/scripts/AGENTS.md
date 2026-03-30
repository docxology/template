# 🤖 AGENTS.md - `projects/blake_bimetalism/scripts/`

## 🎯 Directory Overview
This directory acts as the execution bridge between the `blake_bimetalism` mathematical domain logic (in `src/`) and the root-level 10-stage template DAG pipeline. Agents working here must strictly enforce the **Thin Orchestrator Pattern**.

## 🏗️ Architecture Rules

### 1. The Thin Orchestrator Pattern
- Files in this directory (e.g., `analyze.py`, `generate_figures.py`) MUST NOT contain any business logic, historical data arrays, or mathematical rendering code.
- Their exclusive purpose is to:
  1. Boot up the logger.
  2. Setup the output directories (e.g., `../output/data/` or `../output/figures/`).
  3. Import the heavy-lifting functions from `projects.blake_bimetalism.src`.
  4. Invoke those functions to generate finalized JSONs, SVGs, or PNGs.
  5. Save the output to disk for the next DAG stage to ingest.

### 2. DAG Execution Interface
- These scripts are automatically invoked during Stage 3: **Project Analysis** (`02_run_analysis.py`) of the root 10-stage pipeline.
- The root orchestrator expects these scripts to exit with code `0`. If any script here fails, the entire manuscript PDF compilation is aborted.

### 3. File Responsibilities
- `analyze.py`: Ingests the `MetaStabilityMetrics` class from `src/analysis.py` to serialize the "Gresham Entropy Gap" and "Visionary Inversion Gap" metrics into `output/data/metastability_results.json`.
- `generate_figures.py`: Ingests the 6 topological/mathematical rendering endpoints from `src/figures.py` and actively writes their PNG/SVG visual outputs to `output/figures/`.
