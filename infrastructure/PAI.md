# 🧠 PAI.md - Infrastructure Context

## 📍 Purpose

This directory contains the **Layer 1** generic tools that power the research template. Code here is **project-agnostic** and strictly separated from domain-specific logic.

## 🤖 Agent skills (`SKILL.md`)

Every infrastructure subpackage ships a **`SKILL.md`** at its root with YAML frontmatter (`name`, `description`) plus usage notes—search **`infrastructure/**/SKILL.md`**, start from [`infrastructure/SKILL.md`](SKILL.md), read [`.cursor/skill_manifest.json`](../.cursor/skill_manifest.json), or in Cursor reference `@infrastructure/SKILL.md` / `@infrastructure/<module>/SKILL.md` / `@.cursor/skill_manifest.json`. Programmatic enumeration: `from infrastructure.skills import discover_skills`. Pair with the matching **`AGENTS.md`** for API tables.

## 🛠️ Components (summary)

- **config**: `.env.template`, `secure_config.yaml` (repo defaults).
- **core**: Logging, config loading, pipeline, checkpoint, security, file I/O.
- **docker**: `Dockerfile`, `docker-compose.yml` (see `docs/CLOUD_DEPLOY.md`).
- **documentation**: Figures, images, markdown integration, glossary generation.
- **validation**: PDF/Markdown validation, integrity, audits, CLI.
- **rendering**: PDF, HTML, slides.
- **llm**: Ollama client, templates, review flows.
- **publishing**: Citations, Zenodo/arXiv-style packaging helpers.
- **project**: `discover_projects`, structure validation.
- **reporting**: Pipeline and executive reports.
- **scientific**: Benchmarking, stability, templates.
- **skills**: `discover_skills`, `.cursor/skill_manifest.json`, `python -m infrastructure.skills` (write/check/list-json).
- **steganography**: Post-render PDF hardening (overlays, hashes, optional encryption).
- **core/telemetry**: Unified per-stage resource + diagnostic tracking (`TelemetryCollector`; JSON/text reports in `output/reports/`).

## 🤖 Agent Guidelines

- **Import Rules**: Can import from standard libs. **Cannot** import from `projects/` (prevents circular dependency).
- **Testing**: Must be tested in `tests/infra_tests/`.
- **Modifications**: Changes here affect ALL projects. Exercise caution.
