# tests/helpers/

Shared test helper modules — imported by tests in `tests/integration/` and `tests/infra_tests/`, not collected by pytest. Currently provides `log_parser.py` for typed assertions against structured JSON log output.

See [`AGENTS.md`](AGENTS.md) for the public API.

## Owned process controls

`owned_process.py` supplies `owned_process_fixture` and `OwnedProcessFixture` for
real ordinary-group and detached-session process controls. Its child publishes
actual startup/PID/session/clock records; the parent requires a native live
observation. `assert_cleaned` requires exact native absence or a genuine zombie
before accepting the delayed-write condition. Missing or failing native tools
fail the positive control. The context manager attempts cleanup only for the
observed PID whose untruncated native argv retains its unique owned token; it
preserves the original test/operator exception. It never treats a missing startup
receipt as proof of cleanup, changes a production deadline, or replaces a provider.
