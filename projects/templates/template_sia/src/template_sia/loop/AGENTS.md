# template_sia/loop/ — agent contract

Self-improvement loop cluster: the Layer-2 project adapter for the shared SIA
harness (`loop.py`), typed settings from `manuscript/config.yaml`
(`loop_config.py`), the fail-closed approval contract for live forks
(`approval.py`), and the deterministic reference target agent
(`reference_agent.py`).

`live_proposals.py` owns the separate bounded numeric proposal lane.
`proposal_domain.py` limits mutation and independently scores exact case
membership; `proposal_transport.py` permits only credential-free loopback
Ollama requests; `proposal_sandbox.py` requires an immutable existing image,
restricted Docker execution, and verified container cleanup. The held-out data
never enters proposer prompts. Retain failed-run evidence and exact rollback;
source application remains unsupported.

## Files

- `README.md` — scope of this cluster.

## See also

- [`../AGENTS.md`](../AGENTS.md) — package-level module map.
- [`../../AGENTS.md`](../../AGENTS.md) — exemplar agent guide.
