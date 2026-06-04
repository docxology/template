# Maintainers

Primary contact for the public **docxology/template** repository and its Layer-1 infrastructure.

## Primary maintainer

| Name | Role | ORCID | Email |
| --- | --- | --- | --- |
| Daniel Ari Friedman | Repository owner; subsystem verification | [0000-0001-6232-9096](https://orcid.org/0000-0001-6232-9096) | daniel@activeinference.institute |

For contribution workflow, see [`CONTRIBUTING.md`](CONTRIBUTING.md). For per-subsystem freshness and last manual verification dates, see [`STATUS.md`](STATUS.md).

## Subsystem ownership

| Subsystem | Path / entry | Owner | Notes |
| --- | --- | --- | --- |
| Pipeline orchestration | `infrastructure/orchestration/`, `./run.sh`, `./secure_run.sh` | Daniel | Default DAG, secure subcommand, multi-project modes |
| Test runner & CI gates | `scripts/01_run_tests.py`, `tests/infra_tests/`, `.github/workflows/ci.yml` | Daniel | Coverage floors, no-mocks policy, public scope |
| PDF / multi-format rendering | `infrastructure/rendering/` | Daniel | Combined PDF, slides, HTML, DOCX, EPUB |
| Output validation | `infrastructure/validation/` | Daniel | Markdown, PDF, prerender, evidence registry |
| Publishing & Zenodo | `infrastructure/publishing/`, `scripts/publish_project_release.py` | Daniel | Split concept/version DOI layout — [`docs/guides/zenodo-doi-strategy.md`](docs/guides/zenodo-doi-strategy.md) |
| Steganography | `infrastructure/steganography/`, `./secure_run.sh` | Daniel | Post-render PDF hardening |
| LLM stages (optional) | `infrastructure/llm/`, Stages 7–8 | Daniel | Local Ollama draft assistance |
| Project discovery & confidentiality | `infrastructure/project/`, `scripts/check_tracked_projects.py` | Daniel | Public exemplars only in git; private lifecycle repo |
| Template drift & exemplar contracts | `infrastructure/project/drift/`, `scripts/check_template_drift.py` | Daniel | `PUBLIC_PROJECT_NAMES` alignment |
| Regression / claim-binding tests | `tests/regression/` | Daniel | Scaffold — see [`docs/maintenance/regression-testing.md`](docs/maintenance/regression-testing.md) |
| Generated facts & doc index | `docs/_generated/`, `scripts/generate_active_projects_doc.py`, `scripts/lint_docs.py` | Daniel | Do not hand-edit scripted outputs except maintained snapshots noted in [`docs/_generated/README.md`](docs/_generated/README.md) |
| Public exemplar projects | `projects/templates/template_*` | Daniel | Nine tracked exemplars — roster in [`projects/AGENTS.md`](projects/AGENTS.md) |

## Escalation

1. **Freshness / health** — check [`STATUS.md`](STATUS.md) verification ledger before assuming a subsystem is production-ready.
2. **Architecture & commands** — [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`.github/AGENTS.md`](.github/AGENTS.md).
3. **Private or rotating projects** — never commit under `projects/` except the nine public exemplars; see confidentiality invariant in [`AGENTS.md`](AGENTS.md) and [`docs/maintenance/private-projects-repo.md`](docs/maintenance/private-projects-repo.md).

## Public vs private scope

This repository is **public**. Only `projects/templates/template_active_inference/`, `projects/templates/template_autoresearch_project/`, `projects/templates/template_autoscientists/`, `projects/templates/template_code_project/`, `projects/templates/template_newspaper/`, `projects/templates/template_prose_project/`, `projects/templates/template_sia/`, `projects/templates/template_template/`, and `projects/templates/template_textbook/` are git-tracked project trees. Confidential work lives in a separate private lifecycle repository (symlinked locally). Do not commit secrets, machine-local paths, or non-exemplar project content.
