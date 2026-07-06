# scripts/pipeline/

Numbered pipeline stage orchestrators (stages 00–12).

## Quick reference

| Stage | Script | One-liner |
|-------|--------|-----------|
| 00 | `stage_00_setup.py` | Environment + deps |
| 01 | `stage_01_test.py` | Run tests |
| 02 | `stage_02_analysis.py` | Project analysis |
| 03 | `stage_03_render.py` | Render PDF |
| 04 | `stage_04_validate.py` | Validate outputs |
| 05 | `stage_05_copy.py` | Copy outputs |
| 06 | `stage_06_llm_review.py` | LLM review |
| 07 | `stage_07_executive_report.py` | Executive report |
| 08 | `stage_08_connector_search.py` | Connector search (opt-in) |
| 09 | `stage_09_provenance_record.py` | Provenance record (opt-in) |
| 10 | `stage_10_research_workflow.py` | Research workflow (opt-in) |
| 11 | `stage_11_ebook.py` | Ebook generation (opt-in) |
| 12 | `stage_12_metadata.py` | Metadata package (opt-in) |

## Usage

```bash
# Run a single stage
uv run python scripts/pipeline/stage_00_setup.py --project my_project

# Opt-in stages — print help
uv run python scripts/pipeline/stage_08_connector_search.py --help
uv run python scripts/pipeline/stage_09_provenance_record.py --help
uv run python scripts/pipeline/stage_10_research_workflow.py --help
```

## Notes

- Each script is a **thin orchestrator** — all logic lives in `infrastructure/`.
- Bootstrap uses `parents[2]` to reach the repo root from `scripts/pipeline/`.
- Opt-in stages (08, 09, 10) exit 2 (graceful skip) when infrastructure is absent.
- The full pipeline is orchestrated by [`scripts/runner/execute_pipeline.py`](../runner/execute_pipeline.py).
- Stage ordering is canonical in [`infrastructure/core/pipeline/pipeline.yaml`](../../infrastructure/core/pipeline/pipeline.yaml).
