\newpage

## Appendix: Repository Directory Structure {#appendix-directory}

```text
template/
├── infrastructure/           # Layer 1: Shared services (~276 .py files)
│   ├── core/                 # Logging, config, exceptions, pipeline
│   ├── documentation/        # Figure management, glossary
│   ├── llm/                  # Ollama integration, literature search
│   ├── project/              # Project discovery, workspace management
│   ├── publishing/           # Citation generation, Zenodo
│   ├── rendering/            # Pandoc + XeLaTeX + reports
│   ├── reporting/            # Coverage parsing, executive reports
│   ├── scientific/           # Stability, benchmarking
│   ├── skills/               # Skill manifest discovery
│   ├── steganography/        # Watermarking, hashing
│   ├── validation/           # PDF + Markdown validation
│   ├── config/               # Configuration templates
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
│   ├── cognitive_case_diagrams/ # Compositional case modeling
│   └── template/             # Self-referential meta-analysis
├── projects_in_progress/     # Work-in-progress (not pipeline-discovered)
├── tests/                    # Infrastructure test suite (347+ files, ~6,036 tests)
├── docs/                     # Repository documentation (163+ files, 15 subdirectories)
├── run.sh                    # Interactive TUI orchestrator
├── secure_run.sh             # Steganographic pipeline wrapper
├── AGENTS.md                 # System-level AI agent documentation
├── CLAUDE.md                 # Global AI coding assistant instructions
├── README.md                 # Human-readable project overview
└── pyproject.toml            # Root project configuration (uv)
```
