---
name: template-pipeline
version: 1.1.0
description: >
  Numbered pipeline stage orchestrators (stages 00–13) for the template
  research framework.  Each stage_NN_*.py is a thin orchestrator that wires
  the repo root onto sys.path and delegates to infrastructure/ modules.
tags:
  - pipeline
  - orchestration
  - stages
  - template
trigger: "run a pipeline stage|stage_0[0-9]|stage_1[0-3]|connector_search|provenance_record|research_workflow"
---

# template-pipeline

Numbered pipeline stage scripts in `scripts/pipeline/`.

## When to use

Load this skill when you need to:
- Run or debug a specific pipeline stage
- Add a new stage script
- Understand the stage → infrastructure module mapping
- Work with opt-in stages (08 connector_search, 09 provenance_record, 10 research_workflow)

## Stage inventory

| Script | Infrastructure module |
|--------|-----------------------|
| `stage_00_setup.py` | `infrastructure.core.runtime.setup_checks` |
| `stage_01_test.py` | `infrastructure.core.pytest_orchestration`, `infrastructure.core.test_runner`, `infrastructure.reporting.pipeline_test_runner` |
| `stage_02_analysis.py` | `infrastructure.core.analysis_pipeline`, `infrastructure.core.script_discovery` |
| `stage_03_render.py` | `infrastructure.rendering.pipeline` (all enabled formats; historical YAML label `PDF Rendering`) |
| `stage_04_validate.py` | `infrastructure.validation.output.pipeline`, `infrastructure.validation.publication.rendered_provenance` |
| `stage_05_copy.py` | `infrastructure.core.files`, `infrastructure.validation.output.render_formats`, `infrastructure.validation.output.validator`, `infrastructure.reporting.output_statistics` |
| `stage_06_llm_review.py` | `infrastructure.llm.review.pipeline_runner` |
| `stage_07_executive_report.py` | `infrastructure.reporting.multi_project_reporter`, `infrastructure.reporting.output_organizer` |
| `stage_08_connector_search.py` | `infrastructure.search.connectors` (opt-in) |
| `stage_09_provenance_record.py` | `infrastructure.provenance` (opt-in) |
| `stage_10_research_workflow.py` | `infrastructure.research.ResearchWorkflow` (opt-in) |
| `stage_11_ebook.py` | `infrastructure.rendering.ebook_stage` |
| `stage_12_metadata.py` | `infrastructure.publishing.metadata_stage` |

## Bootstrap pattern

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path
ensure_repo_root_on_path()
```

## Pitfalls

- Always use `parents[2]` (not `parent.parent`) — scripts live at depth 3.
- Opt-in stages (08–10) should exit 2 when backend is absent, not 1.
- Never add business logic to stage scripts — keep them thin orchestrators.
