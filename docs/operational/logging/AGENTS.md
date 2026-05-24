## docs/operational/logging/ — Logging System

### Scope

Logging standards and operational patterns across bash + Python:

- Logging levels and conventions
- Structured context and error reporting
- Cross-language consistency

### Files

| File | Purpose |
| --- | --- |
| `README.md` | Primary entry point for logging guidance |
| `python-logging.md` | Python logging patterns and APIs |
| `bash-logging.md` | Bash logging patterns for operational scripts (`bash_utils.sh`; not used by `run.sh`) |
| `logging-patterns.md` | Cross-language conventions and examples |
| `output-design.md` | Visual contract — terminal vs file, summary schema, verbosity dial |

### See also

- [`docs/rules/python_logging.md`](../../rules/python_logging.md)
- [`infrastructure/core/logging/utils.py`](../../../infrastructure/core/logging/utils.py)
