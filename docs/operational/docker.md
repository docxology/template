# Docker Operations Guide

Container definitions live under [`infrastructure/docker/`](../../infrastructure/docker/): [`Dockerfile`](../../infrastructure/docker/Dockerfile) and [`docker-compose.yml`](../../infrastructure/docker/docker-compose.yml). Use them for an isolated environment to run `./run.sh`, tests, or optional local Ollama.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

## Compose file location

Compose is **not** at the repository root. Either change directory first or pass `-f`:

```bash
cd infrastructure/docker

docker compose --profile dev build
docker compose --profile dev up -d
```

From the repo root without changing directory:

```bash
docker compose -f infrastructure/docker/docker-compose.yml --profile dev up -d
```

## Services and profiles

| Service             | Profile   | Purpose |
| ------------------- | --------- | ------- |
| `research-template` | `dev`     | Repo mounted read-write; default command keeps the container running (`sleep infinity`) so you can `exec` a shell and run the pipeline. |
| `ollama`            | `ollama`  | Optional LLM sidecar on port `11434`. |

Examples:

```bash
# Dev container only
docker compose --profile dev up -d

# Dev container + Ollama
docker compose --profile dev --profile ollama up -d
```

Stop everything:

```bash
docker compose down
```

(or the same command with `-f infrastructure/docker/docker-compose.yml` when running from repo root).

## Inside the container

The compose file sets `working_dir` to `/home/research/template` (repository root mounted from the host). Open a shell:

```bash
docker compose exec research-template bash
```

Then run the pipeline or tests as usual, for example:

```bash
./run.sh --pipeline --project template_code_project
uv run pytest tests/infra_tests/ -q
```

## Ports and networking

- **`8000`** is exposed on the dev service for optional tooling; the default image command does not start an HTTP server on that port unless you add one.
- **`11434`** is published when the `ollama` profile is enabled; `OLLAMA_HOST=http://ollama:11434` is set for pipeline stages that use the LLM stack.

## Volumes (actual compose behaviour)

From [`docker-compose.yml`](../../infrastructure/docker/docker-compose.yml):

- Host repository tree → `/home/research/template` (bind mount).
- Named volume `output_data` → `/home/research/template/output` for persisted outputs.

Hermes caches or extra host paths are **not** defined in compose; configure those on the host outside Docker if needed.

## Rebuilding after dependency changes

After edits to `pyproject.toml` or `uv.lock`:

```bash
cd infrastructure/docker
docker compose --profile dev build --no-cache
docker compose --profile dev up -d
```

## Troubleshooting

### Permissions on mounted directories (Linux)

If the container cannot write to `./output` or the repo checkout:

```bash
sudo chown -R "$(id -u):$(id -g)" output
sudo chmod -R u+rw output
```

### Logs

```bash
docker compose logs -f research-template
```

### Compose cannot find services

Ensure you activated the **`dev`** profile (`--profile dev`). Services are gated by profile.

## Additional notes

- The Dockerfile is a single-stage `python:3.12-slim` build that installs `uv`, a full LaTeX distribution (`texlive-latex-base`, `-recommended`, `-extra`, `texlive-fonts-recommended`, `texlive-fonts-extra`, `texlive-xetex`), and then `pyproject.toml` dependencies — PDF rendering (`scripts/pipeline/stage_03_render.py`) works inside the container without adding any TeX tooling yourself.
- See also [`docs/CLOUD_DEPLOY.md`](../CLOUD_DEPLOY.md) § Docker and [`docs/modules/guides/docker-module.md`](../modules/guides/docker-module.md).
