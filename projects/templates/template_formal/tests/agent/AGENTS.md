# `tests/agent/` — Agent Guide

Tests `src/template_formal/agent/agent.py`. See [`README.md`](README.md)
for the full test breakdown.

## Contract

- **Speed:** fast. Every test is one or two `Agent` instances against a
  tiny real SQLite file. Should stay well under a second for the whole
  directory.
- **Free-energy numbers must be hand-derived, never self-referential.**
  Any new `gaussian_kl_divergence`/`gaussian_differential_entropy`/
  `expected_free_energy` test must compute its expected value from the
  closed-form formula independently (by hand, in the test, with the
  derivation shown in a comment) — not by calling the function under test
  twice and asserting it equals itself. See `test_agent_free_energy.py`'s
  module docstring for the standard this directory holds.
- **`BeliefState` validates numeric fields at construction.** If you add a
  new numeric field to `BeliefState` or a sibling belief type, guard it in
  `__post_init__` and add both a construction-time-rejection test here and
  a comment explaining what deep-inside failure it prevents (the existing
  variance guard prevents an undocumented `ZeroDivisionError`/`math domain
  error` three calls downstream — that's the bar for "why this guard
  matters," not just "guards are good").
- **Isolation tests must stay structural.** If `Agent` grows a new public
  attribute or method, `test_agent_isolation.py`'s introspection loops
  (`_public_members`, the `inspect.signature` walk) will automatically
  include it — but if the new member's type or parameter annotation is a
  storage/connection type not already in the forbidden set, add it
  explicitly; the tests only catch what they know to look for.
- **`Agent`'s public surface is asserted as an exact set** in
  `tests/colony/test_colony_integration.py::test_colony_coordinator_never_touches_an_agents_internal_storage_or_protocol_handle`.
  Adding or removing a public `Agent` method requires updating that set
  too, in the `colony/` directory, not just here.

## Running just this directory

```bash
uv run pytest projects/templates/template_formal/tests/agent/ -v
```
