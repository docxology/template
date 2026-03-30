# 🤖 AGENTS.md - `projects/blake_bimetalism/src/`

## 🎯 Directory Overview
This directory contains the core mathematical, topological, and quantitative business logic for the `blake_bimetalism` manuscript. Following the **Two-Layer Architecture**, all substantive programmatic work supporting the historical arguments must reside here, encapsulated within dedicated namespaces (e.g., `src.viz`).

## 🏗️ Architecture Rules

### 1. Mathematical Rigor & Zero-Mock Policy
- The models implemented here (such as the calculations backing Gresham's Law visualizations or bimetallic ratio divergences) MUST not be stubbed or dummied. They reflect verifiable calculations based on 18th and 19th-century historical monetary datasets (e.g., Hamilton's 1792 ratio vs. Newton's 1717 ratio).
- All functions declared here are strictly unit-tested in the `/projects/blake_bimetalism/tests/` directory under absolute Zero-Mock assertions. 

### 2. The `src/viz/` Graphics Engine
- Advanced, programmatic visualizations are handled by the `src/viz/` subpackage.
- These visualizations use `matplotlib` to programmatically export SVG representations of bimetallic models (e.g., The 3D Topological Fracture of Gresham's Law).
- `src.figures.py` acts as a facade pattern, bubbling up the visualization rendering methods from the deep `src.viz` architecture so that `scripts/generate_figures.py` can invoke them cleanly.

### 3. File Responsibilities
- `__init__.py`: Package initialization; exposes high-level analysis routines.
- `analysis.py`: Contains dataclasses and logic to compute the structural mismatch (Entropy Gap) between legal fiat mint ratios and Euclidean market realities.
- `figures.py`: Maps and exports rendering functions from the `viz/` engine.
- `manuscript.py`: Interfaces with the LaTeX template and manages variable injections from the analysis engines.

## 🚀 Execution limits
Do not place script execution blocks (e.g., `if __name__ == "__main__":`) in these files. All executions are driven by `scripts/` calling into `src/`.
