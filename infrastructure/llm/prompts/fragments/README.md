# Prompt Fragments - Quick Reference

Reusable JSON prompt components loaded by `PromptFragmentLoader` and assembled by
the builder functions in `_fragment_builders.py`.

## Overview

This directory contains JSON data files only — there is no Python package here.
Each file is loaded on demand by `PromptFragmentLoader.load_fragment("file.json#key")`
and cached in memory. The `PromptComposer` dispatches to a dedicated builder function
based on the fragment reference string; builders interpolate the JSON content into
a formatted text block suitable for inclusion in the final prompt.

## Loading Fragments

```python
from infrastructure.llm.prompts import PromptFragmentLoader

loader = PromptFragmentLoader()

# Load a specific key from a JSON file
system_prompt = loader.load_fragment("system_prompts.json#manuscript_review")
# Returns the dict at that key: {"version": "1.0", "content": "..."}

# Load the whole file (no # key)
all_structures = loader.load_fragment("section_structures.json")

# Convenience wrapper that unwraps the "content" field for system prompts
prompt_str = loader.get_system_prompt("manuscript_review")
```

Reference format: `"filename.json"` loads the whole file; `"filename.json#key"` returns
the value at `key`; `"filename.json#key.subkey"` traverses nested dicts.

## Fragment Files

### `system_prompts.json`

Role definitions. Each top-level key is a named role:

```json
{
  "manuscript_review": {
    "version": "1.0",
    "content": "You are an expert academic manuscript reviewer..."
  },
  "research_assistant": {
    "version": "1.0",
    "content": "You are an expert research assistant..."
  }
}
```

Loaded via `loader.load_fragment("system_prompts.json#manuscript_review")` or the
convenience `loader.get_system_prompt("manuscript_review")` which unwraps `content`.

### `format_requirements.json`

Template for markdown header instructions. Consumed by `build_format_requirements()`:

```json
{
  "base_template": "FORMAT REQUIREMENTS:\n\n...\n${headers_list}\n\n${section_requirements_block}",
  "section_requirements_template": "3. Section-specific requirements:\n${requirements_list}"
}
```

The builder substitutes `${headers_list}` with one `- Header` line per header, then
fills `${section_requirements_block}` from `section_requirements_template` if present.

### `content_requirements.json`

Anti-hallucination and evidence-based writing rules. Consumed by
`build_content_requirements()`:

```json
{
  "base_template": "CONTENT QUALITY REQUIREMENTS:\n\n${no_hallucination_block}\n...",
  "no_hallucination": "1. NO HALLUCINATION: ...",
  "cite_sources": "2. CITE SOURCES: ...",
  "evidence_based": "3. EVIDENCE-BASED: ...",
  "no_meta_commentary": "4. NO META-COMMENTARY: ..."
}
```

The builder substitutes each named block into `base_template`.

### `section_structures.json`

Section layout definitions used by `build_section_structure(loader, structure_key)`.
Each key defines the ordered headers and per-section descriptions for one review type:

```json
{
  "executive_summary": {
    "headers": ["## Overview", "## Key Contributions", "..."],
    "descriptions": {"## Overview": "Brief introduction (80-120 words)", "...": "..."},
    "word_targets": {"Overview": [80, 120], "...": [...]}
  },
  "quality_review": { "..." : "..." },
  "methodology_review": { "..." : "..." },
  "improvement_suggestions": { "..." : "..." },
  "translation_abstract": { "..." : "..." }
}
```

Referenced from templates via `"section_structures.json#executive_summary"`, which
triggers `build_section_structure` and produces a formatted `SECTION STRUCTURE:` block.

### `token_budget_awareness.json`

Token and word budget guidance. Consumed by `build_token_budget_awareness()`:

```json
{
  "base_template": "TOKEN BUDGET AWARENESS:\n\n${total_tokens_block}\n${section_budgets_block}...",
  "total_tokens_template": "1. Total response budget: approximately ${total_tokens} tokens",
  "section_budgets_template": "2. Approximate token budgets per section:\n${budgets_list}",
  "word_targets_template": "3. Word count targets per section:\n${targets_list}"
}
```

Caller supplies `total_tokens` and a `{section_name: budget}` dict; the builder
formats them into the template.

### `validation_hints.json`

Checklist of what the pipeline will validate. Consumed by `build_validation_hints()`:

```json
{
  "base_template": "VALIDATION HINTS (what will be checked):\n\n${word_count_block}\n...",
  "word_count_template": "1. Word count: Must be between ${min_words} and ${max_words} words",
  "required_elements_template": "2. Required elements:\n${elements_list}",
  "format_checks_template": "3. Format compliance checks:\n${checks_list}"
}
```

Caller supplies `word_count_range=(min, max)` and `required_elements=[...]`.

## Fragment Builder Dispatch

When `PromptComposer.compose_template()` processes a template's `fragments` map,
it calls `build_fragment(loader, fragment_ref, template, max_tokens)`.
The dispatcher in `_fragment_builders.py` checks the reference string in order:

| Reference pattern | Builder called |
| --- | --- |
| contains `section_structures.json#` | `build_section_structure(loader, key)` |
| contains `format_requirements` | `build_format_requirements(loader, headers)` |
| contains `content_requirements` | `build_content_requirements(loader)` |
| contains `token_budget_awareness` | `build_token_budget_awareness(loader, total, budgets)` |
| contains `validation_hints` | `build_validation_hints(loader, range, elements)` |
| anything else | `loader.load_fragment(ref)` directly |

## Adding New Fragments

1. Create or extend a JSON file in this directory with your fragment data.
2. Reference it from a template's `fragments` map (e.g. `"my_fragment.json#key"`).
3. If the fragment needs custom assembly logic, add a builder in `_fragment_builders.py`
   and register a new `elif` branch in `build_fragment()`.
4. For a raw-text fragment loaded directly, no builder code is needed — the loader
   returns the value and the composer converts it to a string.

## Best Practices

- **Single purpose**: each fragment should serve one role in the assembled prompt.
- **Versioned**: include a `"version"` field for traceability.
- **Template-style fields**: use `${placeholder}` syntax; builders handle substitution.
- **No logic in JSON**: computation lives in `_fragment_builders.py`, data lives here.

## See Also

- [AGENTS.md](AGENTS.md) - fragments documentation
- [../README.md](../README.md) - Prompts module overview
- [../loader.py](../loader.py) - PromptFragmentLoader implementation
- [../composer.py](../composer.py) - PromptComposer and fragment dispatch
