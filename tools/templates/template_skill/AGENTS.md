# AGENTS.md — template_skill

> Agent-oriented documentation for the `skill` exemplar tool.
> Human developers: see [README.md](README.md).

## Identity

- **Type:** `skill`
- **Manifest:** `tools.yaml`
- **Version:** `1.0`

## Invocation

### Invoke

```
stdin:  prompt string (UTF-8 text), OR pass prompt as $1
stdout: LLM response text
exit:   0 = invocation succeeded
        1 = invocation failed (LLM error, missing API key, timeout)
        2 = usage error (empty prompt)
```

```bash
# Positional argument
bash scripts/invoke.sh "Summarise the following: ..."

# Stdin
echo "Summarise the following: ..." | bash scripts/invoke.sh
```

### Prompt Template

`scripts/prompt.md` is a Markdown prompt template.
Agents may read this file to understand the skill's instruction framing before invoking.

Template variables use `{{VARIABLE_NAME}}` syntax and are substituted by `invoke.sh` at runtime.

## Agent Decision Guidance

- Use this skill when the task matches the capability described in `tools.yaml → description`.
- Read `scripts/prompt.md` first to understand input expectations and output format.
- Pass well-formed, complete prompts — the skill does not retry on partial input.
- Output is plain text; parse as needed by the calling agent.

## Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| `bash` ≥ 3.2 | Script runtime | Yes |
| `curl` | LLM API calls | Yes |
| `jq` | JSON payload construction | Yes |
| `OPENAI_API_KEY` (env) | Authentication | Yes (or equivalent) |
