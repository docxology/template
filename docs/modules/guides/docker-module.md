# Docker Module

> **Containerized development and Ollama integration**

**Location:** `infrastructure/docker/`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Cloud Deploy](../../CLOUD_DEPLOY.md)

---

## Overview

`infrastructure/docker/` is a **configuration directory**, not a Python package. It provides a `Dockerfile` and `docker-compose.yml` for running the full pipeline in an isolated container, with an optional Ollama sidecar for local LLM workflows.

---

## Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage image: installs `uv`, Python 3.12, LaTeX, Pandoc, and all Python workspace dependencies. |
| `docker-compose.yml` | Two service definitions: `research-template` (dev container) and `ollama` (LLM sidecar), controlled via `--profile`. |
| `SKILL.md` | AI skill descriptor for this directory (MCP-aligned). |
| `AGENTS.md` | Machine-readable directory guide for AI agents. |

---

## Quick Start

```bash
# Dev environment (no Ollama)
docker compose --profile dev up -d

# Dev environment + Ollama sidecar
docker compose --profile dev --profile ollama up -d

# Enter the container
docker exec -it research-template-dev bash

# Run full pipeline inside container
./run.sh --pipeline --project code_project

# Stop all services
docker compose down
```

---

## Services

### `research-template` (profile: `dev`)

| Setting | Value |
|---------|-------|
| Build context | Repo root (`../../`) |
| Working dir | `/home/research/template` |
| Port | `8000` (for web interfaces) |
| Volumes | Repo root + `output_data` named volume |
| Env vars | `OLLAMA_HOST`, `LOG_LEVEL=1`, `UV_FROZEN=true`, `MPLBACKEND=Agg` |

### `ollama` (profile: `ollama`)

| Setting | Value |
|---------|-------|
| Image | `ollama/ollama:latest` |
| Port | `11434` |
| Volume | `ollama_data` named volume |
| Health check | `GET /api/tags` every 30 s |

---

## Integration with LLM Module

When running inside Docker with the `ollama` profile, the LLM module connects automatically via `OLLAMA_HOST=http://ollama:11434`. No code changes needed.

```bash
# Pull a model (run once after `docker compose up`)
docker exec research-ollama ollama pull gemma3:4b

# Then run LLM-tagged pipeline stages
./run.sh --pipeline --project code_project
```

---

## Related Documentation

- **[Cloud Deploy](../../CLOUD_DEPLOY.md)** — Remote deployment guide
- **[LLM Module](llm-module.md)** — Local Ollama client API
- **[Infrastructure AGENTS.md](../../../infrastructure/docker/AGENTS.md)** — Machine-readable spec
