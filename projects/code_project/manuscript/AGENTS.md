---
title: "Agentic Protocol: Code Project Exemplar"
type: "system_prompt"
version: "2.0"
---

## `code_project` AI Instructions

This document defines the strict behavioral standards for any AI agent interacting with the `code_project` directory. This project is the **master exemplar** for the Generalized Research Template.

## 1. Project Identity

This is not an isolated python script; it is a heavily-integrated, production-grade optimization study.

* **Primary Objective**: To demonstrate how a theoretical mathematical algorithm (Gradient Descent) is implemented, validated, and published using the `infrastructure`, `tests`, and `docs` layers of the repository.
* **Operating Principle**: Do not invent parallel systems. You must utilize the existing repository infrastructure.

## 2. The Zero-Mock Testing Policy

This is the most critical constraint in the repository.

1. **NO MOCKS**: You are strictly forbidden from using `unittest.mock` or generating synthetic "fake" data to bypass tests.
2. **Real Execution Only**: All tests in `tests/` must execute the actual scientific logic against real configurations.
3. **100% Coverage Gate**: The CI pipeline will reject any push that drops branch or statement coverage below 100%. If you write a line of code, you must execute it with a test.
4. **Hermetic Boundaries**: Execution must be contained by the fixtures in `tests/conftest.py`.

## 3. Infrastructure Coupling

When modifying python logic in `scripts/`, you must route functionality through the `infrastructure` modules:

* **Logging**: Use `infrastructure.core.logging_utils.ProjectLogger`. NEVER use print().
* **Validation**: Use `infrastructure.scientific.stability.check_numerical_stability` instead of manual NaN checks.
* **Benchmarking**: Use `infrastructure.scientific.benchmarking.benchmark_function` instead of manual `time.time()` tracking.
* **Configuration**: Rely on `infrastructure.core.config_loader.load_config()`.

## 4. Manuscript & Rendering (RASP Standard)

This project strictly adheres to the Rigorous Agentic Scientific Protocol (RASP) for documentation.

1. **No Extraneous Summaries**: Do not add "In summary" or "In conclusion" to the ends of markdown sections.
2. **LaTeX Integration**: Assume the manuscript files (`00_abstract.md`, etc.) are pre-processed by `preamble.md` and `config.yaml` before pandoc conversion.
3. **Visualization Coupling**: If you change a visualization in `scripts/optimization_analysis.py`, you MUST update the corresponding caption in `03_results.md` to reflect the exact data shown.

## 5. Development Workflow

If tasked to add a new algorithm or feature, follow this exact sequence:

1. Read the relevant `infrastructure` code first (`view_file`).
2. Update the mathematical model in `02_methodology.md`.
3. Write the failing test in `tests/integration/` demonstrating the requirement.
4. Implement the logic in `scripts/`, utilizing `infrastructure.scientific`.
5. Execute `pytest` locally to verify zero-mock success.
6. Regenerate visualizations via `python3 scripts/optimization_analysis.py`.
7. Update `03_results.md` and `04_conclusion.md`.
8. Re-render the manuscript via `python3 scripts/03_render_pdf.py` to ensure pandoc compatibility.

**Failure to adhere to these protocol standards will result in immediate rejection by the infrastructure validation gates.**
