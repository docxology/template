# Private-project promotion package

## Purpose

Keep attestation validation, candidate security scanning, and composite
promotion evaluation independently reusable through the public package API and
explicit CLI subcommands.

## Modules

| Module | Responsibility |
| --- | --- |
| `models.py` | Typed, secret-free attestation, security, and aggregate reports |
| `attestation.py` | Offline attestation parsing and deterministic validation |
| `security_gate.py` | Candidate checks, TODO scanning, and report rendering |
| `composite.py` | Final eligibility composition |
| `cli.py` | Explicit attestation and candidate subcommands |
| `__init__.py` | Stable package-level export API |
| `__main__.py` | `python -m infrastructure.project.promotion` entrypoint |

## Invariants

- Validation is read-only and never prints credential values or candidate data.
- `as_of` is caller-controlled for deterministic expiry decisions.
- Existing imports from `infrastructure.project.promotion` remain valid.
- Retired positional invocations are invalid configurations with exit code 2.
