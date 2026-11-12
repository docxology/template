# Frozen health-gate fixture

This dependency-free Python project supplies the real `pyproject.toml` and
matching `uv.lock` copied by the stage-table controls in
[`test_health.py`](../../infra_tests/core/test_health.py). The controls run the
actual health registry under frozen dependency resolution; they do not generate
a lock or replace the gate implementation.

The project is virtual (`package = false`) and declares an empty standalone
workspace, so a temporary test repository cannot inherit the parent workspace.
No provider, downloaded data or third-party package belongs in this fixture.

Keep metadata and lock changes together. Approved Source preparation may use
`uv lock --project tests/fixtures/health_gate --offline` with a supported Root
interpreter; ordinary tests only copy the committed pair.

See [fixture conventions](../README.md) and [agent guidance](AGENTS.md).
