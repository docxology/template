# `scripts/` Block: Orchestration

This directory houses the "Thin Orchestrators" for the **Blake Bimetallism** project. Following the root Two-Layer Architecture, these scripts contain absolutely zero business logic or markdown text. They merely act as CLI endpoints bridging the domain layer (`src/`) with the output layer (`output/`).

## Core Endpoints

1. **`analyze.py`**: Interacts with the programmatic models of Gresham's Law. It passes explicit reserve figures (e.g., Hamilton's baseline) into the `MetaStabilityMetrics` object and serializes the resulting "Entropy Gap" into a JSON file, guaranteeing that the mathematical assertions in the manuscript are dynamically generated.
2. **`generate_figures.py`**: Bootstraps the `src/viz/` topological mathematical engine. It invokes the 6 specific visualizations (e.g., 3D fracture planes, historic time series) and saves them as artifact images to be embedded in the PDF via LaTeX.

### Execution
While you can run these individually (e.g., `python3 scripts/generate_figures.py`), they are purposefully built to be executed automatically by the template's root DAG pipeline:
```bash
./run.sh --pipeline --project blake_bimetalism
```
