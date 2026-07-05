# tools/

Executable entry points for the `template` research infrastructure — scripts, skill manifests, agent manifests, validators, and renderers.

## Structure

```
tools/
├── README.md          # This file
├── AGENTS.md          # Agent-oriented documentation
└── templates/         # Public exemplar tool definitions
    ├── template_code_executor/   # Generic code execution tool
    ├── template_validator/       # Validation tool
    └── template_skill/           # Agent skill manifest
```

## Concepts

| Concept | Description |
|---|---|
| **code_executor** | Runs arbitrary code in a sandboxed context; exposes `run.sh` and `validate.sh` entrypoints |
| **validator** | Checks inputs / outputs against a schema or rule-set; exposes `validate.sh` and a `schema.json` |
| **skill** | An agent capability definition — prompt template + `invoke.sh` entrypoint |
| **agent** | Full agent manifest with memory, tools, and goals |
| **renderer** | Converts source artefacts (Markdown, LaTeX, YAML) into rendered outputs |

## Usage

Each subdirectory under `templates/` is a self-contained exemplar:

1. Copy the relevant template directory to your working location.
2. Edit `tools.yaml` — update `description`, `version`, `tags`, and `entrypoints`.
3. Implement the scripts under `scripts/`.
4. Run `scripts/validate.sh` to confirm the manifest is well-formed.

## Conventions

- All entrypoint scripts must be executable (`chmod +x`).
- `tools.yaml` is the canonical manifest; keep it in sync with actual scripts.
- Tags should include at least one of: `curated`, `exemplar`, `production`, `experimental`.
- License field must be a valid SPDX identifier.
