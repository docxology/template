# Private-project promotion package

## Purpose

Keep attestation validation, candidate security scanning, and composite
promotion evaluation independently reusable while preserving original imports
and the positional CLI.

## Modules

| Module | Responsibility |
| --- | --- |
| `models.py` | Typed, secret-free attestation, security, and aggregate reports |
| `attestation.py` | Offline attestation parsing and deterministic validation |
| `security_gate.py` | Candidate checks, TODO scanning, and report rendering |
| `composite.py` | Final eligibility composition |
| `cli.py` | Explicit subcommands plus legacy positional compatibility |
| `__init__.py` | Stable package-level re-exports for former `promotion.py` callers |
| `__main__.py` | `python -m infrastructure.project.promotion` entrypoint |

## Invariants

- Validation is read-only and never prints credential values or candidate data.
- `as_of` is caller-controlled for deterministic expiry decisions.
- Existing imports from `infrastructure.project.promotion` remain valid.
- The historical positional CLI remains equivalent to `attestation`.
