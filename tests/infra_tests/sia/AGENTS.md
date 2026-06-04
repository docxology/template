# tests/infra_tests/sia/

Layer 1 tests for the SIA harness (`infrastructure/sia/`).

## Coverage

| Module | Test file |
| --- | --- |
| `task_layout.py` | `test_task_layout.py` |
| `loop_runner.py` | `test_loop_runner.py` |
| `evaluation_runner.py` | `test_evaluation_runner.py` |
| `context_ledger.py` | `test_context_ledger.py` |
| `execution_logs.py` | `test_execution_logs.py` |
| `cli.py` | `test_cli.py`, `test_cli_inspect_run.py` |
| `live_llm.py` | `test_live_llm.py` (`requires_ollama` when live) |

## Policy

Real subprocesses, fixture files, and temp directories only — no mocks.
