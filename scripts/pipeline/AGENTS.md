# scripts/pipeline/ — Numbered Pipeline Stage Orchestrators

## Purpose

This subpackage holds **thin orchestrators** for the numbered build pipeline stages.
Each `stage_NN_*.py` wires the repo root onto `sys.path` and forwards CLI
arguments to the corresponding `infrastructure/` module — no business logic
belongs here.

## Stage scripts

| Script | Stage | Purpose | Tags |
|--------|-------|---------|------|
| `stage_00_setup.py` | 00 | Environment setup (Python, deps, dirs) | `core` |
| `stage_01_test.py` | 01 | Infrastructure + project test orchestration | `core`, `tests` |
| `stage_02_analysis.py` | 02 | Project-script discovery and execution | `core` |
| `stage_03_render.py` | 03 | Manuscript PDF rendering | `core` |
| `stage_04_validate.py` | 04 | Output validation | `core` |
| `stage_05_copy.py` | 05 | Copy outputs to final destination | `core` |
| `stage_06_llm_review.py` | 06 | LLM review and translation | `llm` |
| `stage_07_executive_report.py` | 07 | Multi-project executive reporting | `core` |
| `stage_08_connector_search.py` | 08 | Connector-backed search (opt-in) | `connector_search` |
| `stage_09_provenance_record.py` | 09 | Provenance recording (opt-in) | `provenance` |
| `stage_10_research_workflow.py` | 10 | Research workflow orchestration (opt-in) | `research_workflow` |
| `stage_11_ebook.py` | 11 | Ebook generation (EPUB/MOBI/DOCX; opt-in) | `core`, `ebook` |
| `stage_12_metadata.py` | 12 | Metadata package (ONIX/OPF/JSON; opt-in) | `core`, `metadata` |

## Bootstrap pattern

Every stage script uses the subdirectory-aware bootstrap:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path
ensure_repo_root_on_path()
```

`parents[2]` from `scripts/pipeline/<script>.py` is the repo root.

## Running a stage directly

```bash
# From repo root
uv run python scripts/pipeline/stage_00_setup.py --project my_project
uv run python scripts/pipeline/stage_08_connector_search.py \
    --project my_project --connector exa --query "active inference"
uv run python scripts/pipeline/stage_09_provenance_record.py \
    --project my_project --stage analysis
uv run python scripts/pipeline/stage_10_research_workflow.py \
    --project my_project --describe
```

## Opt-in stages (08, 09, 10)

Stages 08, 09, and 10 are **opt-in** — they exit 2 (graceful skip) when the
backing `infrastructure/` module is not yet configured.  Enable them via tags in
`run.sh` or by running them directly once the infrastructure is ready.

## See also

- [`scripts/runner/`](../runner/) — pipeline execution runners
- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`infrastructure/core/pipeline/pipeline.yaml`](../../infrastructure/core/pipeline/pipeline.yaml) — canonical stage table
