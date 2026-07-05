# template_validator

A **validator** exemplar tool — checks inputs and outputs against a JSON schema and reports errors in a structured format.

## Files

```
template_validator/
├── tools.yaml           # Tool manifest
├── README.md            # This file
├── AGENTS.md            # Agent-oriented documentation
├── .gitignore
└── scripts/
    ├── validate.sh      # Primary validation entrypoint
    └── schema.json      # JSON schema used for validation
```

## Quick Start

```bash
# Validate a file against the bundled schema
bash scripts/validate.sh path/to/input.json

# Validate stdin
echo '{"name": "example"}' | bash scripts/validate.sh
```

## Manifest (`tools.yaml`)

| Field | Value |
|---|---|
| type | `validator` |
| version | `1.0` |
| license | `CC0-1.0` |
| entrypoints | `scripts/validate.sh`, `scripts/schema.json` |

## Customising

1. Edit `scripts/schema.json` to define your domain schema.
2. Extend `scripts/validate.sh` with additional rule-based checks beyond JSON Schema.
3. Update `tools.yaml` — bump `version` and adjust `tags`.
