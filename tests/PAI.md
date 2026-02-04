# 🧠 PAI.md - Tests Context

## 📍 Purpose
This directory contains **Infrastructure Tests** (`tests/infra_tests/`). Project-specific tests live in `projects/{name}/tests/`.

## 🛡️ Testing Standards
- **Zero Mocks**: Real filesystem operations (via `tmp_path`), real network calls (via local fixtures), or deterministic inputs.
- **Coverage**: Repository aims for 100% pass rate.
- **Isolation**: Infrastructure tests should not depend on specific project content.

## 🤖 Agent Guidelines
- **Running**: Use `scripts/01_run_tests.py` (runs both infra and project tests) or `pytest tests/`.
- **Verification**: Use `scripts/verify_no_mocks.py` to ensure compliance.
