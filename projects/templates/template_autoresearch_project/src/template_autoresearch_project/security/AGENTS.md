# Security package

| Module | Role |
| --- | --- |
| `constants.py` | `SECURITY_ARTIFACTS` paths |
| `payloads.py` | Threat model, inventory, attestation payload builders |
| `render.py` | Markdown review packet rendering |
| `artifacts.py` | `write_security_artifacts` orchestration |
| `__init__.py` | Test-facing re-exports |

Import via `from src.security import …` (no root `security.py` stub).
