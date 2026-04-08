\newpage

# Appendices

## Appendix: Pipeline Stage Reference {#appendix-pipeline}

\begin{table}[h]
\caption{Pipeline stage reference showing each stage's script, inputs, outputs, and failure handling.}
\label{tab:pipeline-stages}
\end{table}

| Stage | Script | Input | Output | Failure Mode |
|---|------------|-------|--------|--------------|
| 00 | `00_setup_environment.py` | System environment | Validated env, directories | Hard fail |
| 01 | `01_run_tests.py` | `tests/`, `projects/*/tests/` | Coverage JSON, test reports | Configurable |
| 02 | `02_run_analysis.py` | `projects/*/scripts/*.py` | Figures, data files | Hard fail |
| 03 | `03_render_pdf.py` | `manuscript/*.md`, `config.yaml` | PDF in `output/` | Hard fail |
| 04 | `04_validate_output.py` | `output/` contents | Validation report | Warning |
| 05 | `05_copy_outputs.py` | `output/` artifacts | Organized copies | Soft fail |
| 06 | `06_llm_review.py` | Rendered manuscript | Executive summary, reviews | Skippable |
| 07 | `07_generate_executive_report.py` | All stage outputs | JSON + Markdown report | Soft fail |
