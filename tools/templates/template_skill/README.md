# template_skill

A **skill** exemplar tool — defines a reusable agent capability with a structured prompt template and an invocation script.

## Files

```
template_skill/
├── tools.yaml           # Tool manifest
├── README.md            # This file
├── AGENTS.md            # Agent-oriented documentation
├── .gitignore
└── scripts/
    ├── invoke.sh        # Primary invocation entrypoint
    └── prompt.md        # Prompt template for this skill
```

## Quick Start

```bash
# Invoke the skill with a prompt on stdin
echo "Summarise the following text: ..." | bash scripts/invoke.sh

# Or pass the prompt as a positional argument
bash scripts/invoke.sh "Summarise the following text: ..."
```

## Manifest (`tools.yaml`)

| Field | Value |
|---|---|
| type | `skill` |
| version | `1.0` |
| license | `CC0-1.0` |
| entrypoints | `scripts/invoke.sh`, `scripts/prompt.md` |

## Customising

1. Edit `scripts/prompt.md` — replace the placeholder sections with your actual prompt logic.
2. Update `scripts/invoke.sh` to wire the prompt to your LLM backend of choice.
3. Update `tools.yaml` — bump `version` and adjust `tags`.
