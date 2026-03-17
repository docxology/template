# 🧠 PAI.md — Personal AI Infrastructure Context

## 🆔 Identity

- **System**: Research Project Template
- **Role**: Standardized Research Execution Environment
- **Type**: Core Infrastructure / Skill
- **Version**: Pipeline v2.1 (full pipeline shown as [1/9]..[9/9] with clean shown as [0/9]; core pipeline available without LLM)
- **Signposting**: This repository is a PAI “template” node; it is intended to be self-describing via `AGENTS.md` and `docs/`.

---

## 📍 Purpose

This repository is the **canonical template** for all research projects in the Personal AI
Infrastructure (PAI). It provides a reproducible, zero-mock, agent-friendly environment for:

1. **Standardized Structure** — `infrastructure/` for generic tools, `projects/{name}/src/` for domain logic.
2. **Thin Orchestration** — Scripts coordinate; all business logic lives in src/ modules.
3. **Multi-Project Support** — Multiple independent research projects in a single repo.
4. **Zero-Mock Testing** — Absolute prohibition on mocks; tests use real execution only.
5. **Agent-Friendly Documentation** — Full `AGENTS.md` / `README.md` / `PAI.md` coverage at every level.
6. **Headless Cloud Deployment** — `./run.sh --pipeline` bootstraps uv automatically on any server.

---

## 🏗️ Architecture

```
template/
├── infrastructure/        # Generic reusable tools (Layer 1)
│   ├── core/              # Logging, config, pipeline, checkpoint, security
│   ├── validation/        # PDF, markdown, integrity, audit
│   ├── rendering/         # PDF, HTML, slides (xelatex + pandoc)
│   ├── llm/               # Ollama integration + prompt templates
│   ├── publishing/        # Zenodo, arXiv, GitHub release
│   ├── reporting/         # Pipeline + executive reports
│   ├── scientific/        # Numerical stability, benchmarking
│   └── documentation/     # Figure manager, glossary gen
├── scripts/               # Entry-point orchestrators (thin wrappers)
│   ├── run.sh             # Main interactive + pipeline entry point
│   ├── bash_utils.sh      # Shared bash utilities + ensure_uv() bootstrap
│   ├── 00_setup_environment.py → 06_llm_review.py  # Pipeline stages
│   ├── execute_pipeline.py     # Single-project orchestrator
│   └── execute_multi_project.py # Multi-project orchestrator
├── projects/              # Active research projects (Layer 2)
│   ├── code_project/      # Optimization research exemplar (example)
│   ├── biology_textbook/  # Example project (content-heavy)
│   └── project/           # Example project scaffold
├── projects_archive/      # Archived projects (not executed)
├── tests/                 # Infrastructure tests
├── CLOUD_DEPLOY.md        # ☁️ Headless cloud server guide
├── infrastructure/docker/Dockerfile             # Container specification
└── infrastructure/docker/docker-compose.yml     # Multi-service orchestration
```

---

## 🛠️ Usage for Agents

### Discover

```python
from infrastructure.project.discovery import discover_projects
projects = discover_projects(repo_root)
```

### Execute

```bash
# Full pipeline (auto-installs uv on headless servers)
./run.sh --pipeline

# Core pipeline (no LLM stages)
uv run scripts/execute_pipeline.py --project code_project --core-only

# Specific project
./run.sh --project code_project --pipeline

# All projects
./run.sh --all-projects --pipeline
```

### Verify

```bash
# Always run tests before changes
uv run scripts/01_run_tests.py

# Validate markdown
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/
```

### Document

- Update `AGENTS.md` when architectural patterns change.
- Update `PAI.md` when the system identity or purpose changes.
- Update `CLOUD_DEPLOY.md` when deployment requirements change.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MPLBACKEND` | `Agg` | Headless matplotlib (required on servers) |
| `UV_FROZEN` | `true` | Reproducible locked dependency installs |
| `LOG_LEVEL` | `1` | 0=DEBUG 1=INFO 2=WARN 3=ERROR |
| `PIPELINE_MODE` | `0` | Set to `1` by `run.sh` for non-interactive flags |
| `OLLAMA_HOST` | `http://localhost:11434` | LLM server URL |
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars per LLM prompt |

---

## 🔗 Architecture Linkage

| Layer | Location | Purpose |
|-------|----------|---------|
| Infrastructure | `infrastructure/` | Generic, reusable tools — 60%+ test coverage |
| Projects | `projects/{name}/src/` | Domain-specific science — 90%+ test coverage |
| Outputs | `output/{name}/` | Final deliverables (git-ignored) |
| Entry Points | `scripts/`, `run.sh` | Thin orchestrators only |

---

## ⚠️ Constraints

- **No Legacy** — Legacy methods are actively removed.
- **Real Tests** — No mocks allowed. Verified by `scripts/verify_no_mocks.py`.
- **Thin Orchestrators** — Scripts must not contain business logic.
- **Coverage** — Infrastructure ≥ 60%, Projects ≥ 90%.
- **PIPELINE_MODE** — Set automatically by `run.sh` for all non-interactive flags;
  triggers `ensure_uv()` + `uv sync` bootstrap on first run.

---

## 📚 Key References

- [`AGENTS.md`](AGENTS.md) — Full system documentation
- [`CLOUD_DEPLOY.md`](CLOUD_DEPLOY.md) — Headless cloud deployment guide ☁️
- [`RUN_GUIDE.md`](RUN_GUIDE.md) — Pipeline orchestration reference
- [`docs/documentation-index.md`](documentation-index.md) — Full docs hub
- [`../infrastructure/docker/Dockerfile`](../infrastructure/docker/Dockerfile) — Container specification
- [`../infrastructure/docker/docker-compose.yml`](../infrastructure/docker/docker-compose.yml) — Multi-service orchestration
