# 🧠 PAI.md - Tests Context

## 📍 Purpose
This directory contains **Infrastructure Tests** (`tests/infra_tests/`). Project-specific tests live in `projects/{name}/tests/`.

## PAI v5 Validation Boundary

Repo tests validate the research template, not the local PAI daemon. PAI v5 smoke checks are external operational probes: system prompt present, Algorithm `v6.3.0` present, ISA skill present, Pulse health on `31337`, and notify delivery. Keep those probes documented instead of folding them into pytest.

## 🛡️ Testing Standards
- **Zero Mocks**: Real filesystem operations (via `tmp_path`), real network calls (via local fixtures), or deterministic inputs.
- **Coverage**: Repository aims for 100% pass rate.
- **Isolation**: Infrastructure tests should not depend on specific project content.

## 🤖 Agent Guidelines
- **Running**: Use `scripts/pipeline/stage_01_test.py` (runs both infra and project tests) or `uv run pytest tests/infra_tests/`.
- **Verification**: Use `scripts/audit/verify_no_mocks.py` to ensure compliance.
