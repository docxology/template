# `src/`

Layer-2 engine: deterministic self-organizing agent-team coordination.

**Contents.** `search.py`/`ranking.py`/`state.py` the coordination core; `agents.py` team agents; `confirmation.py` + `dead_ends.py` + `stagnation.py` the honest-testbed controls; `objective.py` the synthetic objective.

**Contract.** All compute lives here (incl. ablation/comparison runners); scripts only orchestrate. No mocks; deterministic; 90% coverage.

See the project [`../AGENTS.md`](../AGENTS.md).
