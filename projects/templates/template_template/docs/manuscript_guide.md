# Manuscript Guide — Template Meta-Project

## Overview

The template meta-project manuscript is a 21-file, modular Markdown document that describes the `template/` architecture. It lives under `projects/templates/template_template/` as a git-tracked public exemplar alongside the other template exemplars. It is the manuscript that uses variable injection — `${variable}` tokens are replaced with live repository metrics at build time.

## File Structure

### Main Sections

| File | Section | Content |
|------|---------|---------|
| `01_abstract.md` | Abstract | Dense single-paragraph summary |
| `02_introduction.md` | §1 Introduction | Reproducibility crisis, related work, gap analysis |

### Methods (5 files)

| File | Subsection | Content |
|------|------------|---------|
| `03a_architecture.md` | §2.1 | Two-Layer Architecture, Standalone Project, Thin Orchestrator |
| `03b_pipeline.md` | §2.2 | Declarative DAG (${pipeline_stages_declared} stages) + orchestrators |
| `03c_documentation.md` | §2.3 | Documentation Duality, Skill Architecture, MCP mapping |
| `03d_fair_iac.md` | §2.4 | FAIR4RS alignment, Infrastructure as Code |
| `03e_quality.md` | §2.5 | Zero-Mock testing, visualization standards |

### Results & Discussion

| File | Section | Content |
|------|---------|---------|
| `04_results.md` | §3 Results | Metrics, benchmarks, comparative matrix |
| `05a_zeromock_tradeoff.md` | §4.1 | Zero-Mock tradeoff analysis |
| `05b_scalability.md` | §4.2 | 1-to-N project scaling |
| `05c_comparison.md` | §4.3 | Tool comparison, FAIR4RS 2024-2026 update |
| `05d_ai_collaboration.md` | §4.4 | AI collaboration, limitations |
| `05e_future_conclusion.md` | §4.5 | Future directions, conclusion |

### Reference & Appendices

| File | Section | Content |
|------|---------|---------|
| `06_infrastructure_modules.md` | §5 | `${module_count}`-module reference |
| `07_security_provenance.md` | §6 | Steganographic provenance |
| `08a_appendix_pipeline.md` | §7 A | Pipeline stage reference |
| `08b_appendix_config.md` | §7 B | Configuration schema reference |
| `08c_appendix_directory.md` | §7 C | Repository directory tree |
| `08d_appendix_exemplars.md` | §7 D | Exemplar project summary |
| `08e_appendix_docs.md` | §7 E | Documentation inventory |
| `08f_appendix_matrix.md` | §7 F | 14×10 comparative matrix |

### Supporting Files

| File | Purpose |
|------|---------|
| `references.bib` | BibTeX entries |
| `config.yaml` | Manuscript metadata (title, authors, DOI, keywords) |
| `preamble.md` | LaTeX preamble (geometry, hyperref) |
| `AGENTS.md` | Machine-readable chapter index + token catalog |
| `README.md` | Human-readable chapter listing |

## Variable Injection

This manuscript uses `${variable}` tokens that are replaced with live values during Stage 02.

### How It Works

1. `scripts/generate_manuscript_metrics.py` runs `build_manuscript_metrics_dict()`
2. Metrics are written to `output/data/metrics.json`
3. `render_all_chapters()` reads each `manuscript/*.md` file
4. `${variable}` tokens are substituted with computed values
5. Rendered files are written to `output/manuscript/*.md`
6. Stage 03 reads from `output/manuscript/` preferentially

### Key Tokens

| Token | Meaning |
|-------|---------|
| `${module_count}` | Infrastructure subpackages discovered live |
| `${pipeline_stages_declared}` | YAML contract stage count (14) |
| `${pipeline_stages_default_full}` | Default full run (10) |
| `${pipeline_stages_core_only}` | `--core-only` run (8) |
| `${stage_count}` | Numbered `scripts/NN_*.py` files only |
| `${public_exemplar_list}` | Git-tracked exemplar slugs from `public_scope` |
| `${docs_file_count}` | Markdown files under `docs/` |
| `${project_template_test_count}` | Meta-project test function count |

Regenerate `output/data/metrics.json` before citing example values in prose.

### Adding New Variables

1. Compute the value in `introspection.py` or `metrics.py`
2. Add the mapping in `build_manuscript_metrics_dict()`
3. Use `${new_variable}` in any manuscript `.md` file
4. Add a test in `test_metrics.py` to verify the new key exists

## Citation Format

Citations use Pandoc-style `[@key]` syntax referencing `references.bib`.

## Cross-References

Figures are referenced by label during rendering; avoid hard-coded figure numbers in source prose when registry tokens exist.
