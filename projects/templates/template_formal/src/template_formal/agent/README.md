# `src/template_formal/agent/` — `Agent[StateT]`: one colony member

An `Agent` owns exactly two resources and nothing else: one real, on-disk
SQLite storage session and one protocol endpoint (a
`template_formal.protocol.session.SessionEndpoint` phase object). Everything
about "decentralized, no shared global state" in this template's framing
lives here — see `agent.py`'s module docstring for the full rationale.

## Modules

| File | Responsibility |
| --- | --- |
| `agent.py` | `Agent[StateT]` itself, plus its `GaussianBelief` Protocol, `BeliefState` reference implementation, `CandidateAction`, `DecisionError`, and the free-energy functions (`gaussian_kl_divergence`, `gaussian_differential_entropy`, `expected_free_energy`) the decision loop scores candidates with. |

## Public API (`__init__.py`)

```python
from template_formal.agent import (
    Agent, AnyProtocolPhase, BeliefState, CandidateAction, DecisionError,
    GaussianBelief, StateT, expected_free_energy,
    gaussian_differential_entropy, gaussian_kl_divergence,
)
```

## Core invariants

**Structural isolation (ISC-27, ISC-30).** No public attribute or method on
`Agent` ever returns or accepts a `Path`, `sqlite3.Connection`, or `Database`.
One agent's storage file is therefore unreachable through a *second* agent's
API — not merely unreached in practice. `tests/agent/test_agent_isolation.py`
proves this by reflection over `Agent`'s own public surface, not by
inspecting one call site.

**Construction-time belief validation (ISC-81).** `BeliefState.__post_init__`
rejects a non-finite or non-positive `variance` immediately. Without this
guard a `BeliefState(mean=0.0, variance=0.0)` would construct silently and
only fail three calls later, deep inside `gaussian_kl_divergence`/
`gaussian_differential_entropy`, with an undocumented `ZeroDivisionError` or
`math domain error` — far from the real defect, and feeding this template's
headline Active-Inference claim through an unguarded numeric boundary. Both a
FirstPrinciples pass and a security review independently converged on this
gap in the third adversarial round.

**Free-energy decision loop.** `Agent.decide()` scores each `CandidateAction`
by `expected_free_energy = KL[Q(o) || P(o)] + H[Q(o)]` — closed-form Gaussian
KL divergence (the "risk" term, how far a candidate's predicted outcome is
from this agent's fixed preference) plus closed-form Gaussian differential
entropy (the "ambiguity" term). It returns the candidate that minimizes `G`,
breaking ties by `min`'s documented first-occurrence behavior — exploited
deliberately by the colony integration test's symmetry-breaking, not
incidentally. This borrows only the general framing from Friston 2005 (behavior
as free-energy minimization over a belief distribution); see the module
docstring and `manuscript` §"Active Inference framing" for exactly what is
and isn't claimed. `Agent.tick()` composes `decide()` with
`record_observation()` in one call, folding a storage failure into a
`DecisionError` rather than discarding it.

`GaussianBelief` declares `mean`/`variance` as read-only `@property` members
specifically because mypy --strict treats a plain `attr: float` Protocol
member as read-write, which a `frozen=True` dataclass can never satisfy — see
`tests/mypy_fixtures/good_agent_belief_instantiation.py` for the positive
control proving `Agent[BeliefState]` itself type-checks against this Protocol.

`Agent.__init__` requires a `NewType`-wrapped `AgentId`, not a bare `str`/`UUID`
(ISC-31); the `isinstance(agent_id, UUID)` check is the runtime half of that
proof, reachable only if a caller bypasses mypy.

## Tests

`tests/agent/` — three files:

- `test_agent_lifecycle.py` — `record_observation`/`tick`/`observation_count`
  against a real SQLite file, the handshake-initiation guard (raises on a
  second `initiate_handshake`), and `agent_id`/`protocol_phase` observability.
- `test_agent_isolation.py` — the structural-isolation proofs above (ISC-30),
  plus the `AgentId`-construction runtime guard (ISC-31).
- `test_agent_free_energy.py` — hand-derived numeric expectations for
  `gaussian_kl_divergence`/`gaussian_differential_entropy`/`expected_free_energy`
  (ISC-29), and the `BeliefState.variance` construction-time guard's boundary
  cases: `0.0`, `-1.0`, `math.nan`, `math.inf` each raise; `1e-9` still
  constructs (ISC-81).

## ISA cross-reference

ISC-27, ISC-28, ISC-29, ISC-30, ISC-31, ISC-81. See `ISA.md` for full criteria
text.
