# template_code_executor

A **code_executor** exemplar tool — runs arbitrary code in a sandboxed context and returns structured output.

## Files

```
template_code_executor/
├── tools.yaml           # Tool manifest
├── README.md            # This file
├── AGENTS.md            # Agent-oriented documentation
├── .gitignore
└── scripts/
    ├── run.sh           # Primary execution entrypoint
    └── validate.sh      # Manifest & environment validation
```

## Quick Start

```bash
# Validate environment
bash scripts/validate.sh

# Run with a JSON payload on stdin
echo '{"code": "print(42)", "language": "python"}' | bash scripts/run.sh
```

## Manifest (`tools.yaml`)

| Field | Value |
|---|---|
| type | `code_executor` |
| version | `1.0` |
| license | `CC0-1.0` |
| entrypoints | `scripts/run.sh`, `scripts/validate.sh` |

## Customising

1. Replace the stub logic in `scripts/run.sh` with your actual execution engine.
2. Update `tools.yaml` — bump `version`, adjust `tags`, and add any additional entrypoints.
3. Keep `scripts/validate.sh` green before committing.
