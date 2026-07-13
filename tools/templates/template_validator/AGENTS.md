# AGENTS.md — template_validator

> Agent-oriented documentation for the `validator` exemplar tool.
> Human developers: see [README.md](README.md).

## Identity

- **Type:** `validator`
- **Manifest:** `tools.yaml`
- **Version:** `1.0`

## Invocation

### Validate

```
stdin:  JSON document to validate (or pass file path as $1)
stdout: human-readable validation report
exit:   0 = input is valid
        1 = validation failed (details on stdout)
        2 = usage error (bad arguments, missing schema)
```

```bash
# From file
bash scripts/validate.sh path/to/input.json

# From stdin
echo '{"name": "example", "version": "1.0"}' | bash scripts/validate.sh
```

### Schema

`scripts/schema.json` is a standard JSON Schema (Draft-07).
Agents may read this file directly to understand the expected data shape.

## Agent Decision Guidance

- Use this tool to **gate pipeline stages** — run before consuming any external input.
- A non-zero exit means the input MUST NOT be processed further; surface the stdout report.
- The schema is the authoritative contract; check it before assuming field names or types.
- To extend validation beyond JSON Schema, add shell logic to `scripts/validate.sh` after the schema check.

## Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| `bash` ≥ 3.2 | Script runtime | Yes |
| `python3` | JSON Schema validation (`jsonschema` module) | Yes |
| `jq` | Optional pretty-printing | Optional |
