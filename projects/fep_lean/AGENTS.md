# FEP Lean Agents — projects/fep_lean

**Version**: v0.3.0 | **Status**: Active | **Last Updated**: March 2026

## Purpose

Orchestrator project formalizing 25 FEP/Active Inference/Bayesian Mechanics topics via OpenGauss sessions. Each topic → one **4-or-5-turn** Lean4 formalization session (NL → Lean4 → validate-request → Hermes explanation → [optional Lean compile check]), logged, artifact-saved, and reported as a modular per-run subfolder.

**Maturity Distribution** (March 2026): 1 real, 16 partial, 8 aspirational.

## Active Components

| File/Dir | Purpose |
| -------- | ------- |
| `config/settings.yaml` | GAUSS_HOME, model, Hermes AI layer, fallback models, Lean verify config |
| `config/topics.yaml` | 25 FEP formalization topics catalogue with mathlib_status |
| `src/fep_topics.py` | FEPTopic + FEPTopicCatalogue typed dataclasses |
| `src/gauss_runner.py` | GaussRunner — 4/5-turn OpenGauss session orchestrator |
| `src/hermes_explainer.py` | HermesExplainer — FEP-domain system prompt + model fallback chain via OpenRouter |
| `src/lean_verifier.py` | LeanVerifier — native Lean 4 / `lake env lean` compilation check |
| `src/fep_visualizer.py` | 4 publication-quality figures (area dist, maturity heatmap, timing, Mathlib coverage) |
| `src/open_gauss_client.py` | OpenGaussClient — SQLite session management, artifact export, validation |
| `src/pipeline.py` | 6-step DAG pipeline |
| `src/reporter.py` | Modular subfolder report generator |
| `src/orchestrator.py` | CLI entry point: `--list`, `--topic`, `--area`, `--pipeline`, `--stats`, `--force-refresh` |
| `scripts/` | Shell orchestration scripts (setup, run, test, clean, view, setup_lean) |
| `tests/` | 7 test suites, **113 tests**, zero mocks |
| `run_demo.py` | Full orchestration demo |
| `pyproject.toml` | uv-managed Python package |
| `manuscript/` | Research manuscript (§1–§7 + 25 per-topic appendices) |

## Operating Contracts

1. **Modularity**: Each src/ module has one responsibility; pipeline composes them.
2. **OpenGauss Only**: All formalization sessions MUST go through `GaussRunner` (no direct DB access in orchestrator or reporter).
3. **Zero-Mock**: All tests use real SQLite, real file I/O, isolated `tmp_path` GAUSS_HOME.
4. **Artifact Saving**: Every topic run MUST export a session artifact JSON.
5. **Structured Logging**: All GaussRunner operations log to `operations.jsonl`.
6. **Config Priority**: env vars > `~/.gauss/.env` > `settings.yaml` > code defaults.
7. **4-or-5-Turn Sessions**: Each topic produces 4 OpenGauss messages by default (user NL, asst Lean4, user validate, asst Hermes). When `verify_lean: true`, a 5th message with native Lean compilation results is added.
8. **Modular Output**: Reporter MUST write to `run_YYYYMMDD_HHMMSS/` subfolder; never flat files.
9. **Hermes Fallback**: HermesExplainer MUST always return a result even on API failure (stub mode). Model fallback chain is tried before falling back to stub. Pipeline must never fail due to Hermes errors.

## Key Commands

```bash
# Tests
uv run pytest tests/ -v --no-cov

# Full demo (25 topics, modular output subfolder)
uv run python run_demo.py

# Force fresh sessions (re-create all)
uv run python run_demo.py --force --no-prompt

# Orchestrator CLI
uv run python -m src.orchestrator --list              # list all topics
uv run python -m src.orchestrator --list --area FEP    # list FEP topics only
uv run python -m src.orchestrator --stats              # maturity distribution table
uv run python -m src.orchestrator --pipeline           # full 6-step pipeline
uv run python -m src.orchestrator --pipeline --area FEP  # pipeline for one area
uv run python -m src.orchestrator --topic fep-001      # single topic
```

## Dependencies

- `pyyaml>=6.0`
- `matplotlib>=3.7`
- `requests>=2.28`

## Navigation

- **Human Docs**: [README.md](README.md)
- **Functional Spec**: [SPEC.md](SPEC.md)
- **AI Context**: [PAI.md](PAI.md)
- **Parent**: [../AGENTS.md](../AGENTS.md)
- **Root**: [../../AGENTS.md](../../AGENTS.md)

## Directory AGENTS.md Files

| Directory | AGENTS.md | Purpose |
| --------- | --------- | ------- |
| **src/** | [src/AGENTS.md](src/AGENTS.md) | Module map, interfaces, data flow |
| **tests/** | [tests/AGENTS.md](tests/AGENTS.md) | Test suites, zero-mock policy |
| **config/** | [config/AGENTS.md](config/AGENTS.md) | Config schema, env overrides |
| **scripts/** | [scripts/AGENTS.md](scripts/AGENTS.md) | Script inventory, workflows |
| **docs/** | [docs/AGENTS.md](docs/AGENTS.md) | Documentation hub |
