# Manuscript — `template/` Meta-Project

## Overview

Self-referential publication describing `template/`; sources live under `projects/templates/template_template/` alongside the other public exemplars. Tokens such as `${module_count}` hydrate from `projects/templates/template_template/scripts/generate_manuscript_metrics.py` before PDF rendering (`output/manuscript/`). Long-form facts that rotate with repository layout belong in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); link instead of copying counts.

## Chapters (numbered segments + appendix set)

| File | Section |
|------|---------|
| `01_abstract.md` | Abstract |
| `02_introduction.md` | Introduction |
| `03a_architecture.md` | Methods: Architecture |
| `03b_pipeline.md` | Methods: Pipeline DAG + orchestrators (`run.sh` / secure path) |
| `03c_documentation.md` | Methods: Documentation duality |
| `03d_fair_iac.md` | Methods: FAIR + IaC |
| `03e_quality.md` | Methods: QA + visualization |
| `04_results.md` | Results |
| `05a_zeromock_tradeoff.md` | Discussion: Zero-Mock |
| `05b_scalability.md` | Discussion: Scaling |
| `05c_comparison.md` | Discussion: Comparative landscape |
| `05d_ai_collaboration.md` | Discussion: AI collaboration |
| `05e_future_conclusion.md` | Discussion: Futures + conclusions |
| `06_infrastructure_modules.md` | Module reference |
| `07_security_provenance.md` | Security |
| `08a_appendix_pipeline.md` | Appendix · Pipeline DAG (12 YAML rows) |
| `08b_appendix_config.md` | Appendix · Configuration |
| `08c_appendix_directory.md` | Appendix · Directory sketch |
| `08d_appendix_exemplars.md` | Appendix · Public exemplars |
| `08e_appendix_docs.md` | Appendix · Documentation inventory |
| `08f_appendix_matrix.md` | Appendix · Matrix |

Supporting assets: `preamble.md`, `config.yaml`, `references.bib`.

## Token catalog (selected)

| Token | Meaning |
|-------|---------|
| `${module_count}` | Infrastructure subdirectories from live discovery |
| `${importable_package_count}` | Subdirectories that are importable Python packages (carry `__init__.py`) |
| `${pipeline_stages_declared}` | YAML stage count (12) |
| `${pipeline_stages_default_full}` | Default full run (10) |
| `${pipeline_stages_core_only}` | `--core-only` run (8) |
| `${stage_count}` | Numbered `scripts/NN_*.py` files only |
| `${public_exemplar_list}` | Git-tracked exemplars from `public_scope` |
| `${project_template_*}` | Meta-project metrics from `projects/templates/template_template` |
| `${project_template_code_project_*}` | Code exemplar |
| `${project_template_prose_project_*}` | Prose exemplar |
| `${project_template_autoresearch_project_*}` | AutoResearch exemplar |
| `${project_template_search_project_*}` | Literature-search exemplar |
