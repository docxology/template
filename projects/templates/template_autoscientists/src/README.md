# `src/`

Layer-2 engine: deterministic self-organizing agent-team coordination.

**Contents.** `search.py`/`ranking.py`/`state.py` the coordination core; `agents.py` team agents; `confirmation.py` + `dead_ends.py` + `stagnation.py` the honest-testbed controls; `objective.py` the synthetic objective; `ablation.py` and `comparison.py` the exact experiment definitions used by scripts and tests; `figures.py` the figure-rendering helpers scripts call into; `transcript.py` the offline transcript validation/replay contract for the opt-in live-agent path.

**Contract.** All compute lives here (incl. ablation/comparison runners); scripts only orchestrate. No mocks; deterministic; 90% coverage.

See the project [`../AGENTS.md`](../AGENTS.md).
