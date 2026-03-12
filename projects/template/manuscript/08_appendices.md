# Appendices

## Appendix A: Pipeline Stage Reference

| Stage | Script | Input | Output | Failure Mode |
|-------|--------|-------|--------|--------------|
| 00 | `00_setup_environment.py` | System environment | Validated env, directories | Hard fail |
| 01 | `01_run_tests.py` | `tests/`, `projects/*/tests/` | Coverage JSON, test reports | Configurable |
| 02 | `02_run_analysis.py` | `projects/*/scripts/*.py` | Figures, data files | Hard fail |
| 03 | `03_render_pdf.py` | `manuscript/*.md`, `config.yaml` | PDF in `output/` | Hard fail |
| 04 | `04_validate_output.py` | `output/` contents | Validation report | Warning |
| 05 | `05_copy_outputs.py` | `output/` artifacts | Organized copies | Soft fail |
| 06 | `06_llm_review.py` | Rendered manuscript | Executive summary, reviews | Skippable |
| 07 | `07_generate_executive_report.py` | All stage outputs | JSON + Markdown report | Soft fail |

## Appendix B: Configuration Reference (`config.yaml`)

```yaml
paper:
  title: "Paper Title"
  subtitle: "Optional Subtitle"
  version: "1.0"
  date: "2026-03-08"

authors:
  - name: "Author Name"
    orcid: "0000-0000-0000-0000"
    email: "author@example.com"
    affiliation: "Institution"
    corresponding: true

publication:
  doi: "10.5281/zenodo.XXXXXX"
  journal: "Target Journal"
  volume: "1"
  pages: "1-10"
  year: "2026"

keywords:
  - "keyword1"
  - "keyword2"

metadata:
  license: "Apache License 2.0"
  language: "en"

llm:
  reviews:
    enabled: true
    types: [executive_summary, quality_review]
  translations:
    enabled: false

testing:
  max_test_failures: 0
  max_infra_test_failures: 3
  max_project_test_failures: 0
```

## Appendix C: Repository Directory Structure

```
docxology/template/
├── infrastructure/           # Layer 1: Shared services (137 .py files)
│   ├── core/                 # 28 files — logging, config, exceptions
│   ├── documentation/        # 6 files — figure management, glossary
│   ├── llm/                  # 30 files — Ollama integration, literature
│   ├── project/              # 2 files — project discovery
│   ├── publishing/           # 9 files — citation generation, Zenodo
│   ├── rendering/            # 12 files — Pandoc + XeLaTeX + reports
│   ├── reporting/            # 14 files — coverage parsing, reports
│   ├── scientific/           # 6 files — stability, benchmarking
│   ├── steganography/        # 8 files — watermarking, hashing
│   └── validation/           # 22 files — PDF + Markdown validation
├── scripts/                  # Pipeline orchestration
│   ├── 00_setup_environment.py
│   ├── 01_run_tests.py
│   ├── 02_run_analysis.py
│   ├── 03_render_pdf.py
│   ├── 04_validate_output.py
│   ├── 05_copy_outputs.py
│   ├── 06_llm_review.py
│   ├── 07_generate_executive_report.py
│   └── execute_pipeline.py
├── projects/                 # Layer 2: Research workspaces
│   ├── code_project/         # Gradient descent exemplar
│   ├── cognitive_case_diagrams/  # Category theory + linguistics
│   └── template/             # This self-referential project
├── tests/                    # Infrastructure test suite (148 files, 3,053 tests)
├── docs/                     # Repository documentation (90+ files, 12 subdirectories)
├── run.sh                    # Interactive TUI orchestrator
├── secure_run.sh             # Steganographic pipeline wrapper
├── AGENTS.md                 # System-level AI agent documentation
├── CLAUDE.md                 # Global AI coding assistant instructions
├── README.md                 # Human-readable project overview
└── pyproject.toml            # Root project configuration (uv)
```

## Appendix D: Exemplar Project Summary

| Project | Domain | src/ Modules | Test Count | Coverage | Figures | Pages |
|---------|--------|:-----------:|:----------:|:--------:|:-------:|:-----:|
| `code_project` | Numerical optimization | `optimizer.py` (248 lines) | 58 | 96.6% | 6 | ~20 |
| `cognitive_case_diagrams` | Category theory / linguistics | 12 modules, 17 DisCoPy renderers | 257 | ~96% | 25+ | ~77 |
| `template` | Meta-architecture | `introspection.py` | 36 | 90%+ | 3 | ~5 |

## Appendix E: Documentation Inventory

The repository maintains documentation at three levels:

| Level | Files | Purpose |
|-------|:-----:|---------|
| Repository root | `AGENTS.md`, `CLAUDE.md`, `README.md`, `RUN_GUIDE.md` | Global navigation and AI agent context |
| `docs/` directory | 90+ files across 12 subdirectories | User guides, API reference, troubleshooting |
| Per-directory | `AGENTS.md` + `README.md` at every directory | Documentation Duality standard |

The `docs/` subdirectories cover: `core/` (essential docs), `guides/` (skill levels 1–12), `architecture/` (system design), `usage/` (content authoring), `operational/` (build, config, logging, troubleshooting), `reference/` (API, FAQ, glossary), `modules/` (10 infrastructure modules), `development/` (contributing, testing), `best-practices/` (version control, migration), `prompts/` (9 AI prompt templates), `security/` (steganography, hashing), and `audit/` (review reports).

## Appendix F: Comparative Tool Matrix

| Capability | Docxology | Snakemake | Nextflow | CWL | Quarto | Jupyter Book | R Markdown |
|------------|:---------:|:---------:|:--------:|:---:|:------:|:------------:|:----------:|
| Pipeline orchestration | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Manuscript rendering | ✓ | — | — | — | ✓ | ✓ | ✓ |
| Code execution | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Testing enforcement | ✓ | — | — | — | — | — | — |
| Coverage thresholds | ✓ | — | — | — | — | — | — |
| Cryptographic provenance | ✓ | — | — | — | — | — | — |
| Steganographic watermarking | ✓ | — | — | — | — | — | — |
| Multi-project management | ✓ | — | — | — | — | — | — |
| AI-agent documentation | ✓ | — | — | — | — | — | — |
| Interactive TUI | ✓ | — | — | — | — | — | — |
| Container support | — | ✓ | ✓ | ✓ | — | — | — |
| Distributed execution | — | ✓ | ✓ | ✓ | — | — | — |
| DAG parallelism | — | ✓ | ✓ | ✓ | — | — | — |
| Multi-language (R/Julia) | — | ✓ | — | ✓ | ✓ | ✓ | ✓ |
