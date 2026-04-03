"""Prompt composer for assembling prompts from fragments and templates.

Implementation of fragment building is in _fragment_builders.py.
This module provides the PromptComposer public API.
"""

from __future__ import annotations

import re
from typing import Any

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.prompts._fragment_builders import (
    build_content_requirements,
    build_format_requirements,
    build_fragment,
    build_section_structure,
    build_token_budget_awareness,
    build_validation_hints,
)
from infrastructure.llm.prompts.loader import PromptFragmentLoader

logger = get_logger(__name__)


class PromptComposer:
    """Composes prompts from fragments and templates.

    Takes prompt fragments loaded by PromptFragmentLoader and assembles
    them into complete prompts with variable substitution and fragment
    composition.

    Example:
        >>> loader = PromptFragmentLoader()
        >>> composer = PromptComposer(loader=loader)
        >>> prompt = composer.compose_template(
        ...     "test_templates.json#test_template",
        ...     text="Content here",
        ...     max_tokens=1000
        ... )
    """

    def __init__(self, loader: PromptFragmentLoader | None = None):
        """Initialize prompt composer.

        Args:
            loader: PromptFragmentLoader instance. If None, creates default loader.
        """
        self.loader = loader or PromptFragmentLoader()

    def compose_template(
        self, template_ref: str, max_tokens: int | None = None, **variables: Any
    ) -> str:
        """Compose a prompt from a template definition.

        Args:
            template_ref: Template reference (e.g., "templates.json#template_name")
            max_tokens: Maximum tokens for token budget awareness
            **variables: Variables to substitute in template

        Returns:
            Composed prompt string

        Raises:
            LLMTemplateError: If template cannot be composed
        """
        try:
            template = self.loader.load_template(template_ref)

            # Get base template
            base_template = template.get("base_template", "")
            if not base_template:
                raise LLMTemplateError(
                    f"Template {template_ref} missing base_template",
                    context={"template": template},
                )

            # Load and substitute fragments
            fragments = template.get("fragments", {})
            fragment_values: dict[str, str] = {}

            for fragment_key, fragment_ref in fragments.items():
                fragment_values[fragment_key] = build_fragment(
                    self.loader, fragment_ref, template, max_tokens
                )

            # Merge template variables
            template_vars = template.get("variables", {})
            template_vars.update(variables)
            template_vars.update(fragment_values)

            # Check for missing required variables (variables referenced in base_template)
            variable_pattern = r"\$\{(\w+)\}"
            referenced_vars = set(re.findall(variable_pattern, base_template))
            missing_vars = referenced_vars - set(template_vars.keys())

            if missing_vars:
                raise LLMTemplateError(
                    f"Missing required variables: {', '.join(sorted(missing_vars))}",
                    context={
                        "template_ref": template_ref,
                        "missing_variables": sorted(missing_vars),
                        "provided_variables": sorted(template_vars.keys()),
                    },
                )

            # Substitute variables in base template
            result = base_template
            for key, value in template_vars.items():
                placeholder = f"${{{key}}}"
                result = result.replace(placeholder, str(value))

            # Handle section structure substitution
            if "section_structure" in fragment_values:
                result = result.replace(
                    "${section_structure}", fragment_values["section_structure"]
                )

            return result

        except Exception as e:
            if isinstance(e, LLMTemplateError):
                raise
            raise LLMTemplateError(
                f"Failed to compose template {template_ref}",
                context={"error": str(e), "template_ref": template_ref},
            ) from e

    def add_retry_prompt(self, base_prompt: str, retry_type: str = "off_topic") -> str:
        """Add a retry prompt to reinforce requirements.

        Args:
            base_prompt: Original prompt
            retry_type: Type of retry (e.g., "off_topic", "format_enforcement")

        Returns:
            Prompt with retry reinforcement added
        """
        try:
            retry_prompt = self.loader.load_composition(
                f"retry_prompts.json#{retry_type}_reinforcement"
            )

            if isinstance(retry_prompt, dict):
                content = retry_prompt.get("content", str(retry_prompt))
            else:
                content = str(retry_prompt)

            # Prepend retry prompt to base
            if content.strip():
                return f"{content}\n\n{base_prompt}"
            return base_prompt

        except LLMTemplateError:
            # If retry prompt not found, return base unchanged
            logger.debug(f"Retry prompt {retry_type} not found, returning base prompt")
            return base_prompt

    def _build_format_requirements(self, headers_list: list[str]) -> str:
        """Backward-compatible wrapper for format requirements assembly."""
        return build_format_requirements(self.loader, headers_list)

    def _build_content_requirements(self) -> str:
        """Backward-compatible wrapper for content requirements assembly."""
        return build_content_requirements(self.loader)

    def _build_section_structure(self, structure_key: str) -> str:
        """Backward-compatible wrapper for section structure assembly."""
        return build_section_structure(self.loader, structure_key)

    def _build_token_budget_awareness(
        self, total_tokens: int, section_budgets: dict[str, int]
    ) -> str:
        """Backward-compatible wrapper for token budget assembly."""
        return build_token_budget_awareness(
            self.loader,
            total_tokens=total_tokens,
            section_budgets=section_budgets,
        )

    def _build_validation_hints(
        self, word_count_range: tuple[int, int], required_elements: list[str]
    ) -> str:
        """Backward-compatible wrapper for validation hints assembly."""
        return build_validation_hints(
            self.loader,
            word_count_range=word_count_range,
            required_elements=required_elements,
        )
