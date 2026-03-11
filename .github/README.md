<div align="center">

# 🔬 Research Project Template

**Production-grade scaffold for reproducible academic research**

[![CI](https://github.com/docxology/template/actions/workflows/ci.yml/badge.svg)](https://github.com/docxology/template/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-purple?logo=astral)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/linter-ruff-orange?logo=ruff)](https://docs.astral.sh/ruff/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](../LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-informational)](../pyproject.toml)

[**⚡ Quick Start**](#-quick-start) · [**📐 Architecture**](#-architecture) · [**🔄 CI/CD Pipeline**](#-cicd-pipeline) · [**📋 Templates**](#-issue--pr-templates) · [**🔧 Configuration**](#-configuration)

</div>

---

## ⚡ Quick Start

```bash
# 1. Clone / use template
gh repo create my-research --template docxology/template --private
cd my-research

# 2. Install dependencies (uv required)
uv sync

# 3. Run the full 10-stage pipeline
./run.sh --pipeline

# 4. Outputs land in output/{project-name}/
```

> **Don't have `uv`?** Install it: `curl -Ls https://astral.sh/uv/install.sh | sh`

---

## 📐 Architecture

```
template/
├── infrastructure/          ← Generic reusable library (Layer 1)
│   ├── core/                   logging, pipeline, checkpointing
│   ├── rendering/              PDF + LaTeX generation
│   ├── validation/             markdown + PDF QA
│   ├── scientific/             benchmarking, numerical stability
│   ├── reporting/              executive reports, dashboards
│   └── steganography/          cryptographic watermarking
│
├── projects/{name}/         ← Your research project (Layer 2)
│   ├── src/                    domain-specific algorithms
│   ├── tests/                  project test suite (≥90% coverage)
│   ├── scripts/                thin orchestrators → import from src/
│   ├── manuscript/             markdown → PDF pipeline
│   │   └── config.yaml         paper metadata, LLM/translation opts
│   └── output/                 generated artefacts (disposable)
│
├── scripts/                 ← Generic pipeline entry points (00–07)
├── output/{name}/           ← Final deliverables (PDF, web, data)
├── run.sh                   ← Main interactive + pipeline entry point
└── secure_run.sh            ← Pipeline + steganographic PDF hardening
```

**Key pattern:** business logic lives in `projects/{name}/src/` — scripts are **thin orchestrators** that import and call it. Violating this breaks the architecture.

---

## 🔄 CI/CD Pipeline

### Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| [`ci.yml`](workflows/ci.yml) | push · PR · weekly · manual | Full 7-job quality gate |
| [`stale.yml`](workflows/stale.yml) | Daily 01:00 UTC | Close inactive issues/PRs |
| [`release.yml`](workflows/release.yml) | `v*.*.*` tag · manual | GitHub Release with changelog |

### CI Job Flow

```
lint ──────────────────────────────────────────────────────┐
 └─► verify-no-mocks                                        │
      ├─► test-infra  [ubuntu+mac × 3.10/3.11/3.12]  ≥60% │
      ├─► test-project [ubuntu+mac × 3.10/3.11/3.12]  ≥90% │
      ├─► validate    [manuscript markdown + imports]        │
      └─► security    [pip-audit + bandit MEDIUM+]           │
test-infra + test-project                                   │
 └─► performance     [import time ≤ 5 s]                   ◄┘
```

### Quality Gates

| Gate | Tool | Threshold |
|---|---|---|
| Code style | Ruff | zero violations |
| Formatting | Ruff | zero diffs |
| Type safety | mypy | no errors |
| No mocks | `verify_no_mocks.py` | zero mock usage |
| Infra coverage | pytest-cov | **≥ 60%** |
| Project coverage | pytest-cov | **≥ 90%** |
| Security | Bandit MEDIUM+ | zero findings |
| Performance | import timer | **≤ 5 s** |

### Simulate CI Locally

```bash
# Lint
uvx ruff check infrastructure/ projects/*/src/ && uvx ruff format --check infrastructure/ projects/*/src/

# Tests with coverage isolation
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-datafile=.coverage.infra --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/*/tests/ --cov=projects --cov-datafile=.coverage.project --cov-fail-under=90 -m "not requires_ollama"

# Security
uv run pip-audit && uv run bandit -r -ll infrastructure/ scripts/ projects/ --exclude projects_archive,projects_in_progress
```

---

## 📦 Dependency Management

[`dependabot.yml`](dependabot.yml) — weekly automated PRs for both ecosystems:

| Ecosystem | Group | Max open PRs |
|---|---|---|
| GitHub Actions | all minor/patch batched | 5 |
| Python (pip/uv) | `dev-tools` (pytest, mypy, ruff…) | 5 |
| Python (pip/uv) | `scientific-core` (numpy, scipy…) | 5 |

Labels added automatically: `dependencies` · `automated` · ecosystem tag.

---

## 📋 Issue & PR Templates

### Issues → [New Issue](https://github.com/docxology/template/issues/new/choose)

| Template | Labels | Best for |
|---|---|---|
| [🐛 Bug Report](ISSUE_TEMPLATE/bug_report.md) | `bug` · `needs-triage` | Reproducible errors with log output and pipeline stage |
| [✨ Feature Request](ISSUE_TEMPLATE/feature_request.md) | `enhancement` · `needs-triage` | New capabilities with priority and alternatives |
| [📝 Documentation](ISSUE_TEMPLATE/documentation.md) | `documentation` · `needs-triage` | Incorrect, missing, or outdated docs with file paths |

> 💬 **Questions?** Use [GitHub Discussions](https://github.com/docxology/template/discussions) — blank issues are disabled.

### Pull Requests → [PR Template](PULL_REQUEST_TEMPLATE.md)

The PR template enforces:
- ✅ Linked issue(s)
- ✅ Type-of-change classification
- ✅ Pipeline stage(s) affected
- ✅ Test evidence (local run confirmation)
- ✅ **No-mocks policy confirmation** (zero `MagicMock`/`mocker.patch`)
- ✅ Thin Orchestrator pattern compliance

---

## 🔧 Configuration

### Branch Protection (Recommended)

Set in **Settings → Branches → main**:

```
Required status checks:
  Lint & Type Check
  Infra Tests (ubuntu-latest, 3.10/3.11/3.12)
  Project Tests (ubuntu-latest, 3.10/3.11/3.12)
  Validate Manuscripts
  Security Scan
  Performance Check

Require PR review before merging: 1 approver
```

### Secrets Needed

| Secret | Required for |
|---|---|
| `CODECOV_TOKEN` | Coverage upload to Codecov (optional but recommended) |

---

## 🔍 Troubleshooting

```bash
# Workflow status
gh workflow list
gh run list --workflow=CI --limit=5

# View failure logs
gh run view <run-id> --log-failed

# Re-run failed jobs only
gh run rerun <run-id> --failed

# Fix linting locally
uvx ruff check infrastructure/ projects/*/src/ --fix
uvx ruff format infrastructure/ projects/*/src/
```

---

## 📂 Navigation

| Directory | Purpose |
|---|---|
| [`workflows/`](workflows/) | CI/CD workflow YAML files |
| [`ISSUE_TEMPLATE/`](ISSUE_TEMPLATE/) | Structured issue templates |
| [`PULL_REQUEST_TEMPLATE.md`](PULL_REQUEST_TEMPLATE.md) | PR checklist |
| [`dependabot.yml`](dependabot.yml) | Automated dependency updates |
| [`AGENTS.md`](AGENTS.md) | Deep technical CI/CD documentation |
| [`workflows/AGENTS.md`](workflows/AGENTS.md) | Per-workflow technical docs |

---

<div align="center">

**[📖 Root AGENTS.md](../AGENTS.md)** · **[🚀 How To Use](../docs/core/how-to-use.md)** · **[🏗️ Architecture](../docs/core/architecture.md)** · **[🐛 Issues](https://github.com/docxology/template/issues)** · **[💬 Discussions](https://github.com/docxology/template/discussions)**

</div>