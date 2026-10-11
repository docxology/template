# `src/`

Layer-2 engine: deterministic self-organizing agent-team coordination.

**Contents.** `search.py`/`ranking.py`/`state.py` the coordination core; `agents.py` team agents; `confirmation.py` + `dead_ends.py` + `stagnation.py` the honest-testbed controls; `objective.py` the synthetic objective; `ablation.py` and `comparison.py` the exact experiment definitions used by scripts and tests; `figures.py` the figure-rendering helpers scripts call into; `transcript.py` the independent offline transcript replay contract; `live_domain.py`, `live_transport.py`, and `live_comparison.py` provide bounded actual local coordination and custody.

**Contract.** All compute lives here (incl. ablation/comparison runners); scripts only orchestrate. No mocks; deterministic core defaults; explicit live mode; 90% coverage.

See the project [`../AGENTS.md`](../AGENTS.md).
