# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project.

## Purpose

To provide a machine-readable and human-readable blueprint of the repository's value proposition as a research environment.

## Key Subsystems

### 1. Visualization Service

- **Source**: `scripts/generate_architecture_viz.py`
- **Output**: `figures/architecture_viz.png`
- **Dependency**: `matplotlib`
- **Pattern**: Standard Stage 02 extraction.

### 2. Manuscript Compilation

- **Source**: `manuscript/01_*.md` through `06_*.md`
- **Reference Management**: Handled by the root `scientific` and `rendering` modules.
- **Metadata**: Injected from `manuscript/config.yaml`.

### 3. Verification Gaps

- This project currently focuses on structural description rather than algorithm execution.
- Tests are provided in `tests/` to ensure the visualization logic remains functional across Python updates.
