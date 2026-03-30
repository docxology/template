# Manuscript Appendix Templates (Project Infrastructure)

This directory contains **template/stub manuscript appendix files** shipped with the infrastructure layer.

It is not a runtime “manuscript utilities” module. The actual glossary generation logic lives in:

- `infrastructure/documentation/glossary_gen.py` (AST scan + table + marker injection)
- `infrastructure/documentation/generate_glossary_cli.py` (CLI wrapper)

## `98_symbols_glossary.md`

`98_symbols_glossary.md` is a **marker-delimited placeholder** intended to be updated in place.

Markers:

- `<!-- BEGIN: AUTO-API-GLOSSARY -->`
- `<!-- END: AUTO-API-GLOSSARY -->`

Generated table format (from `generate_markdown_table()`):

- `Module | Name | Kind | Summary`

## Updating a project’s glossary

Use the CLI and point it at a project’s `src/` and target markdown file:

```bash
uv run python infrastructure/documentation/generate_glossary_cli.py \
  "projects/<project_name>/src" \
  "projects/<project_name>/manuscript/98_symbols_glossary.md"
```

## See also

- `infrastructure/documentation/README.md`
- `infrastructure/documentation/AGENTS.md`