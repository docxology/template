\newpage

# Appendices

## Appendix: Pipeline Stage Reference {#appendix-pipeline}

\begin{table}[h]
\caption{Single-project DAG exported from default \texttt{pipeline.yaml} (names shown in topological order). Scripts live under \texttt{scripts/}.}
\label{tab:pipeline-stages}
\end{table}

| Stage name | Script / method | Primary inputs | Outputs / artefacts | Failure mode |
|-----------|-----------------|---------------|----------------------|--------------|
| Clean Output Directories | `_run_clean_outputs` | prior `projects/<name>/output/`, mirrored `output/<name>/` targets | emptied trees | Blocking |
| Environment Setup | `00_setup_environment.py` | toolchain probes | scaffold dirs, env exports | Blocking |
| Infrastructure Tests | `01_run_tests.py --infra-only --infra-scope pipeline-smoke` | `tests/infra_tests/` | coverage + junit-style logs | tolerant ceilings |
| Project Tests | `01_run_tests.py --project-only` | `projects/<name>/tests/` | coverage artefacts | blocking by default |
| Project Analysis | `02_run_analysis.py` | thin scripts | `figures/`, `data/`, reports | Blocking |
| Connector Search | `08_connector_search.py` | `manuscript/config.yaml` | `output/data/connector_search/` | opt-in (`science` tag); skipped if not configured |
| Provenance Record | `09_provenance_record.py --stage "Connector Search"` | prior stage outputs | `.provenance/graph.json` | opt-in (`provenance` tag); skipped if not configured |
| PDF Rendering | `03_render_pdf.py` | `manuscript/`, placeholders | `.pdf`/`.tex` bundles | Blocking |
| Output Validation | `04_validate_output.py` | render tree | Markdown + PDF diagnostics JSON | Blocking / downgrade |
| LLM Scientific Review | `06_llm_review.py --reviews-only` | resolved manuscript artefacts | textual reviews | Optional skip (`allow_skip`) |
| LLM Translations | `06_llm_review.py --translations-only` | abstract metadata | multilingual snippets | Optional skip (`allow_skip`) |
| Copy Outputs | `05_copy_outputs.py` | validated tree | mirrored `output/<name>/…` | soft fail logged |
| Ebook Generation | `11_ebook_generation.py` | rendered combined markdown | `output/ebook/` (EPUB/MOBI/DOCX) | opt-in (`ebook` tag); soft fail |
| Metadata Package | `12_metadata_package.py` | `manuscript/config.yaml` | `output/metadata/` (ONIX/JSON/OPF) | opt-in (`metadata` tag); soft fail |
| Executable Bundle | `08_executable_bundle.py` | project tree + outputs | container bundle manifest | opt-in (`bundle` tag) |
| Archival Publication | `09_archive_publication.py` | bundle + deliverables | archival deposit manifest | opt-in (`archival` tag) |

`scripts/pipeline/stage_07_executive_report.py` is invoked **outside** this DAG whenever `execute_multi_project.py` aggregates pipelines—supplying cross-project KPI dashboards absent from lone-project checkpoints.
