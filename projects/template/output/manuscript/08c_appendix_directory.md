\newpage

## Appendix: Repository Directory Structure {#appendix-directory}

```text
template/
├── infrastructure/           # Layer 1: Shared services (~150 .py files)
│   ├── core/                 # 28 files — logging, config, exceptions
│   ├── documentation/        # 6 files — figure management, glossary
│   ├── llm/                  # 30 files — Ollama integration, literature
│   ├── project/              # 2 files — project discovery
│   ├── publishing/           # 9 files — citation generation, Zenodo
│   ├── rendering/            # 12 files — Pandoc + XeLaTeX + reports
│   ├── reporting/            # 14 files — coverage parsing, reports
│   ├── scientific/           # 6 files — stability, benchmarking
│   ├── steganography/        # 8 files — watermarking, hashing
│   ├── validation/           # 22 files — PDF + Markdown validation
│   ├── config/               # Configuration
│   └── docker/               # Containerization
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
│   ├── act_inf_metaanalysis/ # Meta-analysis pipeline
│   └── biology_textbook/     # Domain content exemplar (when populated)
├── projects_in_progress/     # Work-in-progress (template, etc.)
├── tests/                    # Infrastructure test suite (160+ files, ~3,050 tests)
├── docs/                     # Repository documentation (90+ files, 12 subdirectories)
├── run.sh                    # Interactive TUI orchestrator
├── secure_run.sh             # Steganographic pipeline wrapper
├── AGENTS.md                 # System-level AI agent documentation
├── CLAUDE.md                 # Global AI coding assistant instructions
├── README.md                 # Human-readable project overview
└── pyproject.toml            # Root project configuration (uv)
```
