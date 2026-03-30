# Manuscript Appendix Templates (Infrastructure)

## Scope

`infrastructure/project/manuscript/` holds **template/stub appendix files** shipped with the infrastructure layer.

It does not contain executable manuscript-processing logic. Glossary generation lives under
`infrastructure/documentation/`.

## Files

| File | Purpose |
| --- | --- |
| `98_symbols_glossary.md` | Marker-delimited placeholder for an API symbols table |
| `README.md` | Quick reference and usage |
| `AGENTS.md` | This file |

## `98_symbols_glossary.md`

Contains markers that a generator can update in place:

- `<!-- BEGIN: AUTO-API-GLOSSARY -->`
- `<!-- END: AUTO-API-GLOSSARY -->`

The current generator (`infrastructure/documentation/glossary_gen.py`) produces a table with columns:

- `Module | Name | Kind | Summary`

## Updating a project’s glossary

Use the CLI wrapper to scan a project’s `src/` and inject the generated table into the target file:

```bash
uv run python infrastructure/documentation/generate_glossary_cli.py \
  "projects/<project_name>/src" \
  "projects/<project_name>/manuscript/98_symbols_glossary.md"
```

## See also

- `infrastructure/documentation/glossary_gen.py`
- `infrastructure/documentation/generate_glossary_cli.py`
