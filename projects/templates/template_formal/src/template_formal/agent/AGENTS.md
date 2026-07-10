# `src/template_formal/agent/` — Agent Guide

`Agent[StateT]` — one storage session, one protocol endpoint, one free-energy
decision loop. See `README.md` for the full contract.

**Contents.** `agent.py` — `Agent`, `BeliefState`, `GaussianBelief`,
`CandidateAction`, `DecisionError`, and the free-energy functions.

**Contract.** Never add a public method or attribute to `Agent` that returns
or accepts a `Path`, `sqlite3.Connection`, or `Database` — that is the exact
structural-isolation guarantee `tests/agent/test_agent_isolation.py` checks by
reflection (ISC-30), and it breaks silently (no type error) if violated,
since `Path`/`Connection` are ordinary types mypy has no reason to flag. Any
new `StateT` implementation must satisfy `GaussianBelief` structurally
(read-only `mean`/`variance` properties) — a plain mutable `float` attribute
on a `frozen=True` dataclass will not satisfy the Protocol under mypy
--strict.

Any new numeric field feeding `expected_free_energy` (directly or via a new
`GaussianBelief` implementation) needs the same construction-time
finite-and-positive-variance guard `BeliefState.__post_init__` already
enforces (ISC-81) — three adversarial rounds independently found this exact
class of gap (unvalidated numeric field feeding a downstream `math.log`/
division), so a new belief type skipping it is a regression, not a new
finding.

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
