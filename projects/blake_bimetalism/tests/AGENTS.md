# 🤖 AGENTS.md - Test Validation Subsystem

## 🎯 Subsystem Overview
The `tests/` folder ensures the mathematical integrity and deterministic execution rules of the Blake Bimetallism project. Extending the master `infrastructure/` package into `Layer 2`, it enforces structural assertions against the 18-chapter corpus, the `src/viz/` visual rendering engine, and the quantitative bimetallic gap matrices.

## 🏗️ Technical Constraints

### 1. Absolute Zero-Mock Policy
The tests must interact with the *real* outputs and methods located in `src/`. The use of `unittest.mock` to artificially bypass analysis engines or fake the presence of data files is an absolute violation of the thesis integrity.
- If testing the 3D Topological Gresham's Law chart, the test must verify the presence of the actual `matplotlib/networkx` generated elements on disk.
- If testing the textual assertions, the file references must strictly point to the real files (`00_abstract.md` through `06_conclusion.md`).

### 2. Coverage Minimums
The `blake_bimetalism/tests/` bounds demand at least `90%` statement coverage by the infrastructure validators. Tests must traverse:
- Historical boundaries (e.g., verifying that Newton's ratio does not fall below 15.21).
- Script orchestrators (ensuring `scripts/analyze.py` properly triggers the DAG pipeline structure).

### 3. Execution Context Isolation
All tests must verify conditions cleanly without creating persisting filesystem garbage or corrupting the global state of the user. `tmp_path` fixtures must be used for all I/O boundary tests.
