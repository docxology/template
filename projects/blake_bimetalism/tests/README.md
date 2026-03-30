# Test Framework: Blake Bimetallism

The `tests/` directory bounds the computational execution of the Blake Bimetallism metrics. It runs alongside the master `template/tests/` infrastructure but focuses solely on validating the structural and mathematical logic defined in the `src/` directory.

## Architecture
This folder contains `pytest` execution units structurally asserting:
* **`test_analysis.py`**: Validates the mathematical bounds of the Historical Gresham's Law entropy equations and prophetic inversions.
* **`test_analyze_script.py`**: Verifies that the Deep Orchestrator outputs the `metastability_results.json` correctly mapped to the DAG pipeline.
* **`test_manuscript.py`**: Verifies the dynamic LaTeX injection bounds against the 18-chapter (`00_` to `06_`) markdown repository architecture.

### Execution Command
The template CI/CD automatically runs these tests upon commit at **Stage 03: Run Tests** of the root pipeline.
To explicitly trigger them independently in CLI:
```bash
uv run pytest projects/blake_bimetalism/tests/ -v
```
