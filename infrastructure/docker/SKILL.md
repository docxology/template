---
name: infrastructure-docker
description: Container build and compose assets for the research template. Use when reproducing CI or cloud environments with Docker, following docs/CLOUD_DEPLOY.md, or wiring Ollama sidecars via docker-compose.
---

# Skill Descriptor — infrastructure/docker

## Module Overview

Containerization assets for running the template in a consistent environment.

## Capabilities

- **Docker container build**: `Dockerfile` provides a reproducible build environment
- **Multi-service orchestration**: `docker-compose.yml` manages dev environment and optional Ollama

## Use Cases

1. **Local development**: Run pipeline in container for consistent environment
2. **Cloud deployment**: Deploy using Docker for reproducibility
3. **Ollama integration**: Optional LLM support via docker-compose

## Integration Points

- Referenced by [`docs/CLOUD_DEPLOY.md`](../../docs/CLOUD_DEPLOY.md) for headless and container deployment
- Invoked directly via `docker build` / `docker compose` (not wired into the default Python pipeline stages)

## See Also

- [`docs/CLOUD_DEPLOY.md`](../../docs/CLOUD_DEPLOY.md)
- [`infrastructure/docker/Dockerfile`](Dockerfile)
- [`infrastructure/docker/docker-compose.yml`](docker-compose.yml)