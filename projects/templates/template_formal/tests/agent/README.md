# `tests/agent/` — decision-loop and isolation tests

Behavioral tests for `src/template_formal/agent/agent.py` — `Agent[StateT]`,
the class combining one `TransactionHandle`-owning storage session and one
protocol endpoint per instantiated agent, plus its free-energy-minimizing
per-tick decision loop.

**Speed:** fast unit-test directory. Every test constructs one or two
`Agent` instances backed by a real but tiny per-agent SQLite file (via
`tmp_path`) and calls a handful of methods — no simulation loops, no
parameter sweeps. The whole directory runs in a fraction of a second.

## Files

| File | Lines | Covers | What it actually tests |
| --- | --- | --- | --- |
| [`test_agent_free_energy.py`](test_agent_free_energy.py) | 136 | ISC-28, ISC-29 | Every expected numeric value is derived independently by hand from the closed-form Gaussian KL-divergence and differential-entropy formulas documented in `agent.py`'s module docstring — never by calling the implementation twice. `gaussian_kl_divergence` of identical distributions is exactly `0.0`; a shifted-mean case matches a hand-derived `2.0`; `gaussian_differential_entropy` of unit variance matches `0.5 * ln(2*pi*e)`, pinned to a literal hand-derived constant (`1.4189385332046727`); `expected_free_energy` (risk + ambiguity) matches hand-computed values for both a matching and a shifted candidate. `Agent.decide` picks the lower-EFE candidate, breaks ties to the first-listed candidate, and returns `Err(DecisionError)` over an empty candidate list. The last block is a third-adversarial-pass regression: `BeliefState(variance=...)` now raises `ValueError` **at construction** for zero, negative, `nan`, or `inf` variance — proving the fix moved the failure from deep inside `gaussian_kl_divergence`/`gaussian_differential_entropy` (an undocumented `ZeroDivisionError`/`math domain error` three calls downstream) to the actual point of misuse. |
| [`test_agent_isolation.py`](test_agent_isolation.py) | 102 | ISC-30 | A structural, not anecdotal, proof that one agent's storage file is unreachable through another agent's public API. `test_no_public_attribute_of_agent_exposes_a_path_or_connection` walks every non-underscore public attribute of a real `Agent` and asserts none is a `Path`, `sqlite3.Connection`, or `Database`. `test_no_public_method_of_agent_accepts_a_path_connection_database_or_agent` inspects every public method's real `inspect.signature()` and asserts no parameter is annotated with one of those same forbidden types — i.e., there is no way to *redirect* an agent at another agent's file, not just no way to read it directly. `test_two_agents_public_apis_never_reference_each_others_file_path` constructs two real agents against two real distinct on-disk files and asserts neither agent's public surface ever equals the other's path. The final test is the runtime half of ISC-31's paired static+dynamic proof: constructing `Agent("not-a-uuid", ...)` raises `TypeError` (the static half is `tests/mypy_fixtures/bad_agent_id_construction.py`). |
| [`test_agent_lifecycle.py`](test_agent_lifecycle.py) | 99 | ISC-27 | `Agent.record_observation` persists a real row, independently verified via a fresh `sqlite3.connect` against the same on-disk file (not the agent's own connection) — including that the stored `value` matches `expected_free_energy` computed independently. `Agent.tick` decides-and-records in one call, incrementing `observation_count()` across repeated ticks. `tick([])` propagates `Err` without recording anything. An agent owns exactly one protocol endpoint, starting `IdleSession`; `initiate_handshake` transitions it to `HandshakingSession` and returns a real `hello` `WireMessage`; a second `initiate_handshake` on the same agent raises `RuntimeError`. `agent_id` returns the identity the agent was constructed with. |

## Why isolation is tested structurally, not just observationally

`test_agent_isolation.py`'s claim is not "agent A happens not to read
agent B's file in this test" — it is "agent A's public API surface has no
attribute or method that *could ever* be used to reach agent B's file,"
checked by introspecting the real public surface (`dir()`,
`inspect.signature()`) rather than trusting a docstring or a single
observed run.
