# Quickstart — template_sia

## From repository root

```bash
# Tests
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only

# Analysis only
uv run python scripts/02_run_analysis.py --project templates/template_sia

# Core pipeline (tests → analysis → PDF → validate → copy)
uv run python scripts/execute_pipeline.py --project templates/template_sia --core-only --skip-infra
```

## From project directory

```bash
cd projects/templates/template_sia
uv run python scripts/run_sia_loop.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Live mode (optional)

Requires local Ollama:

```bash
ollama serve
ollama pull gemma3:4b
uv run python scripts/run_sia_loop.py --live-sia
```

The LLM model is read from `manuscript/config.yaml` (`sia.llm_model`), not a CLI flag.
Set `sia.llm_model: "gemma3:4b"` in `manuscript/config.yaml` first — it ships empty
(`llm_model: ""`), and an empty value produces **no LLM feedback note** even with Ollama
running and a model pulled.

Default pipeline and CI use fixture replay (`live: false` in `manuscript/config.yaml`).

## Deliverables

- Combined PDF: `output/templates/template_sia/pdf/template_sia_combined.pdf`
- Loop report: `projects/templates/template_sia/output/reports/sia_loop_report.md`
