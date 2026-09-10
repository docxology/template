# tests/infra_tests/audit/ — Tests for the `scripts/audit/` gates

## Purpose

Contract tests for the thin audit CLIs: every script under `scripts/audit/` is a
thin orchestrator over `infrastructure/` logic, and this folder pins both the
observable CLI behavior (exit codes, finding shapes) and the underlying logic
modules directly.

## Files

- `test_check_doc_module_refs.py` — contract for
  `scripts/audit/check_doc_module_refs.py` and its logic module
  `infrastructure.documentation.doc_module_refs`: positive findings for
  unresolvable `infrastructure.*` dotted references in `docs/`, `README.md`,
  and `AGENTS.md`; negative control on real references; front-door link
  contract; thin-CLI wiring.

## Conventions

- Real filesystem fixtures under `tmp_path` (the no-mocks policy applies).
- Negative controls are mandatory: each detector must be proven to fire on an
  injected violation, not merely pass on a clean tree.

## See Also

- [`README.md`](README.md)
- [`../../../infrastructure/documentation/AGENTS.md`](../../../infrastructure/documentation/AGENTS.md)
