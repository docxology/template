"""Fragment builder functions for prompt composition.

Each builder loads a fragment via the PromptFragmentLoader and assembles
it into a formatted string suitable for inclusion in a composed prompt.
"""

from __future__ import annotations

from typing import Any

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.prompts.loader import PromptFragmentLoader


def build_fragment(
    loader: PromptFragmentLoader,
    fragment_ref: str,
    template: dict[str, Any],
    max_tokens: int | None,
) -> str:
    """Dispatch fragment_ref to the appropriate builder.

    Fragment dispatch registry (checked in order -- first match wins):
        "section_structures.json#<key>" -> build_section_structure(key)
        "format_requirements"           -> build_format_requirements(headers)
        "content_requirements"          -> build_content_requirements()
        "token_budget_awareness"        -> build_token_budget_awareness(total, budgets)
        "validation_hints"              -> build_validation_hints(range, elements)
        <anything else>                 -> loader.load_fragment(fragment_ref)

    To add a new fragment type: append an entry to this docstring and add
    an elif branch below.  The keyword should be unique to avoid false matches.
    """
    if "section_structures.json#" in fragment_ref:
        structure_key = fragment_ref.split("#", 1)[1]
        return build_section_structure(loader, structure_key)

    if "format_requirements" in fragment_ref:
        headers = template.get("section_config", {}).get("headers", [])
        return build_format_requirements(loader, headers)

    if "content_requirements" in fragment_ref:
        return build_content_requirements(loader)

    if "token_budget_awareness" in fragment_ref:
        section_config = template.get("section_config", {})
        sections = section_config.get("sections", 2)
        total = max_tokens or 1000
        section_budgets = {f"Section{i + 1}": total // sections for i in range(sections)}
        return build_token_budget_awareness(
            loader, total_tokens=total, section_budgets=section_budgets
        )

    if "validation_hints" in fragment_ref:
        word_count = template.get("variables", {}).get("word_count_range", [100, 200])
        required = template.get("variables", {}).get("required_elements", [])
        return build_validation_hints(
            loader, word_count_range=tuple(word_count), required_elements=required
        )

    # Default: load fragment directly from disk
    fragment_data = loader.load_fragment(fragment_ref)
    if isinstance(fragment_data, dict):
        return str(fragment_data.get("content", fragment_data))
    return str(fragment_data)


def build_format_requirements(
    loader: PromptFragmentLoader, headers_list: list[str]
) -> str:
    """Build format requirements fragment.

    Args:
        loader: Fragment loader instance
        headers_list: List of required headers

    Returns:
        Formatted requirements string
    """
    format_data = loader.load_fragment("format_requirements.json")

    base_template = format_data.get("base_template", "")
    if not base_template:
        raise LLMTemplateError(
            "format_requirements.json missing 'base_template' key",
            context={"fragment": "format_requirements.json"},
        )

    headers_text = "\n".join(f"  - {h}" for h in headers_list)
    result = base_template.replace("${headers_list}", headers_text)

    # Handle section requirements if present
    if "section_requirements_template" in format_data:
        section_template = format_data["section_requirements_template"]
        result = result.replace("${section_requirements_block}", section_template)
    else:
        result = result.replace("${section_requirements_block}", "")

    return result


def build_content_requirements(loader: PromptFragmentLoader) -> str:
    """Build content requirements fragment.

    Returns:
        Formatted content requirements string
    """
    content_data = loader.load_fragment("content_requirements.json")

    base_template = content_data.get("base_template", "")
    if not base_template:
        raise LLMTemplateError(
            "content_requirements.json missing 'base_template' key",
            context={"fragment": "content_requirements.json"},
        )

    no_hallucination = content_data.get("no_hallucination", "")
    cite_sources = content_data.get("cite_sources", "")

    result = base_template.replace("${no_hallucination_block}", no_hallucination)
    result = result.replace("${cite_sources_block}", cite_sources)

    return result


def build_section_structure(loader: PromptFragmentLoader, structure_key: str) -> str:
    """Build section structure fragment.

    Args:
        loader: Fragment loader instance
        structure_key: Key in section_structures.json

    Returns:
        Formatted section structure string

    Raises:
        LLMTemplateError: If structure key not found
    """
    try:
        structures = loader.load_fragment("section_structures.json")

        if structure_key not in structures:
            raise LLMTemplateError(
                f"Section structure '{structure_key}' not found",
                context={
                    "available_keys": (
                        list(structures.keys()) if isinstance(structures, dict) else []
                    )
                },
            )

        structure = structures[structure_key]
        headers = structure.get("headers", [])
        descriptions = structure.get("descriptions", {})

        lines = ["SECTION STRUCTURE:"]
        for header in headers:
            desc = descriptions.get(header, "")
            lines.append(f"{header}: {desc}")

        return "\n".join(lines)

    except LLMTemplateError:
        raise
    except Exception as e:
        raise LLMTemplateError(
            f"Failed to build section structure for '{structure_key}'",
            context={"error": str(e)},
        ) from e


def build_token_budget_awareness(
    loader: PromptFragmentLoader,
    total_tokens: int,
    section_budgets: dict[str, int],
) -> str:
    """Build token budget awareness fragment.

    Args:
        loader: Fragment loader instance
        total_tokens: Total token budget
        section_budgets: Dictionary of section name -> token budget

    Returns:
        Formatted token budget string
    """
    budget_data = loader.load_fragment("token_budget_awareness.json")

    base_template = budget_data.get("base_template", "")
    if not base_template:
        raise LLMTemplateError(
            "token_budget_awareness.json missing 'base_template' key",
            context={"fragment": "token_budget_awareness.json"},
        )

    total_template = budget_data.get(
        "total_tokens_template", "1. Total: ${total_tokens} tokens"
    )
    section_template = budget_data.get(
        "section_budgets_template", "2. Per section:\n${budgets_list}"
    )

    total_block = total_template.replace("${total_tokens}", str(total_tokens))

    budgets_list = "\n".join(
        f"  - {name}: {budget} tokens" for name, budget in section_budgets.items()
    )
    section_block = section_template.replace("${budgets_list}", budgets_list)

    result = base_template.replace("${total_tokens_block}", total_block)
    result = result.replace("${section_budgets_block}", section_block)

    return result


def build_validation_hints(
    loader: PromptFragmentLoader,
    word_count_range: tuple[int, int],
    required_elements: list[str],
) -> str:
    """Build validation hints fragment.

    Args:
        loader: Fragment loader instance
        word_count_range: Tuple of (min_words, max_words)
        required_elements: List of required element names

    Returns:
        Formatted validation hints string
    """
    validation_data = loader.load_fragment("validation_hints.json")

    base_template = validation_data.get("base_template", "")
    if not base_template:
        raise LLMTemplateError(
            "validation_hints.json missing 'base_template' key",
            context={"fragment": "validation_hints.json"},
        )

    word_template = validation_data.get(
        "word_count_template", "1. Word count: ${min_words}-${max_words}"
    )
    elements_template = validation_data.get(
        "required_elements_template", "2. Required:\n${elements_list}"
    )

    min_words, max_words = word_count_range
    word_block = word_template.replace("${min_words}", str(min_words)).replace(
        "${max_words}", str(max_words)
    )

    elements_list = "\n".join(f"  - {elem}" for elem in required_elements)
    elements_block = elements_template.replace("${elements_list}", elements_list)

    result = base_template.replace("${word_count_block}", word_block)
    result = result.replace("${required_elements_block}", elements_block)

    return result
