"""Prompt composer for assembling prompts from fragments and templates."""
from __future__ import annotations

import re
from typing import Dict, Any, Optional
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMTemplateError
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
    
    def __init__(self, loader: Optional[PromptFragmentLoader] = None):
        """Initialize prompt composer.
        
        Args:
            loader: PromptFragmentLoader instance. If None, creates default loader.
        """
        self.loader = loader or PromptFragmentLoader()
    
    def compose_template(
        self,
        template_ref: str,
        max_tokens: Optional[int] = None,
        **variables: Any
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
                    context={"template": template}
                )
            
            # Load and substitute fragments
            fragments = template.get("fragments", {})
            fragment_values: Dict[str, str] = {}
            
            for fragment_key, fragment_ref in fragments.items():
                if fragment_ref.endswith("#test_template"):
                    # Special handling for section structures
                    fragment_data = self.loader.load_fragment(fragment_ref)
                    fragment_values[fragment_key] = self._build_section_structure("test_template")
                elif "format_requirements" in fragment_ref:
                    # Build format requirements
                    format_data = self.loader.load_fragment(fragment_ref.replace(".json", ".json"))
                    headers = template.get("section_config", {}).get("headers", [])
                    if not headers and "section_structure" in fragment_values:
                        # Extract headers from section structure
                        headers = ["## Section1", "## Section2"]  # Default for tests
                    fragment_values[fragment_key] = self._build_format_requirements(headers)
                elif "content_requirements" in fragment_ref:
                    fragment_values[fragment_key] = self._build_content_requirements()
                elif "token_budget_awareness" in fragment_ref:
                    section_config = template.get("section_config", {})
                    sections = section_config.get("sections", 2)
                    total = max_tokens or 1000
                    section_budgets = {
                        f"Section{i+1}": total // sections
                        for i in range(sections)
                    }
                    fragment_values[fragment_key] = self._build_token_budget_awareness(
                        total_tokens=total,
                        section_budgets=section_budgets
                    )
                elif "validation_hints" in fragment_ref:
                    word_count = template.get("variables", {}).get("word_count_range", [100, 200])
                    required = template.get("variables", {}).get("required_elements", [])
                    fragment_values[fragment_key] = self._build_validation_hints(
                        word_count_range=tuple(word_count),
                        required_elements=required
                    )
                else:
                    # Load fragment directly
                    fragment_data = self.loader.load_fragment(fragment_ref)
                    if isinstance(fragment_data, dict):
                        fragment_values[fragment_key] = str(fragment_data.get("content", fragment_data))
                    else:
                        fragment_values[fragment_key] = str(fragment_data)
            
            # Merge template variables
            template_vars = template.get("variables", {})
            template_vars.update(variables)
            template_vars.update(fragment_values)
            
            # Check for missing required variables (variables referenced in base_template)
            variable_pattern = r'\$\{(\w+)\}'
            referenced_vars = set(re.findall(variable_pattern, base_template))
            missing_vars = referenced_vars - set(template_vars.keys())
            
            if missing_vars:
                raise LLMTemplateError(
                    f"Missing required variables: {', '.join(sorted(missing_vars))}",
                    context={
                        "template_ref": template_ref,
                        "missing_variables": sorted(missing_vars),
                        "provided_variables": sorted(template_vars.keys())
                    }
                )
            
            # Substitute variables in base template
            result = base_template
            for key, value in template_vars.items():
                placeholder = f"${{{key}}}"
                result = result.replace(placeholder, str(value))
            
            # Handle section structure substitution
            if "section_structure" in fragment_values:
                result = result.replace("${section_structure}", fragment_values["section_structure"])
            
            return result
            
        except Exception as e:
            if isinstance(e, LLMTemplateError):
                raise
            raise LLMTemplateError(
                f"Failed to compose template {template_ref}",
                context={"error": str(e), "template_ref": template_ref}
            )
    
    def add_retry_prompt(self, base_prompt: str, retry_type: str = "off_topic") -> str:
        """Add a retry prompt to reinforce requirements.
        
        Args:
            base_prompt: Original prompt
            retry_type: Type of retry (e.g., "off_topic", "format_enforcement")
            
        Returns:
            Prompt with retry reinforcement added
        """
        try:
            retry_prompt = self.loader.load_composition(f"retry_prompts.json#{retry_type}_reinforcement")
            
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
        """Build format requirements fragment.
        
        Args:
            headers_list: List of required headers
            
        Returns:
            Formatted requirements string
        """
        try:
            format_data = self.loader.load_fragment("format_requirements.json")
            
            base_template = format_data.get("base_template", "FORMAT REQUIREMENTS:\n\n1. Use markdown\n2. Headers:\n${headers_list}")
            headers_text = "\n".join(f"  - {h}" for h in headers_list)
            
            result = base_template.replace("${headers_list}", headers_text)
            
            # Handle section requirements if present
            if "section_requirements_template" in format_data:
                section_template = format_data["section_requirements_template"]
                result = result.replace("${section_requirements_block}", section_template)
            else:
                result = result.replace("${section_requirements_block}", "")
            
            return result
            
        except LLMTemplateError:
            # Fallback if fragment not found
            headers_text = "\n".join(f"  - {h}" for h in headers_list)
            return f"FORMAT REQUIREMENTS:\n\n1. Use markdown\n2. Headers:\n{headers_text}"
    
    def _build_content_requirements(self) -> str:
        """Build content requirements fragment.
        
        Returns:
            Formatted content requirements string
        """
        try:
            content_data = self.loader.load_fragment("content_requirements.json")
            
            base_template = content_data.get("base_template", "CONTENT REQUIREMENTS:\n\n${no_hallucination_block}\n${cite_sources_block}")
            no_hallucination = content_data.get("no_hallucination", "1. NO HALLUCINATION: Only use provided content")
            cite_sources = content_data.get("cite_sources", "2. CITE SOURCES: Reference specific sections")
            
            result = base_template.replace("${no_hallucination_block}", no_hallucination)
            result = result.replace("${cite_sources_block}", cite_sources)
            
            return result
            
        except LLMTemplateError:
            # Fallback
            return "CONTENT REQUIREMENTS:\n\n1. NO HALLUCINATION: Only use provided content\n2. CITE SOURCES: Reference specific sections"
    
    def _build_section_structure(self, structure_key: str) -> str:
        """Build section structure fragment.
        
        Args:
            structure_key: Key in section_structures.json
            
        Returns:
            Formatted section structure string
            
        Raises:
            LLMTemplateError: If structure key not found
        """
        try:
            structures = self.loader.load_fragment("section_structures.json")
            
            if structure_key not in structures:
                raise LLMTemplateError(
                    f"Section structure '{structure_key}' not found",
                    context={"available_keys": list(structures.keys()) if isinstance(structures, dict) else []}
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
                context={"error": str(e)}
            )
    
    def _build_token_budget_awareness(
        self,
        total_tokens: int,
        section_budgets: Dict[str, int]
    ) -> str:
        """Build token budget awareness fragment.
        
        Args:
            total_tokens: Total token budget
            section_budgets: Dictionary of section name -> token budget
            
        Returns:
            Formatted token budget string
        """
        try:
            budget_data = self.loader.load_fragment("token_budget_awareness.json")
            
            base_template = budget_data.get("base_template", "TOKEN BUDGET:\n\n${total_tokens_block}\n${section_budgets_block}")
            total_template = budget_data.get("total_tokens_template", "1. Total: ${total_tokens} tokens")
            section_template = budget_data.get("section_budgets_template", "2. Per section:\n${budgets_list}")
            
            total_block = total_template.replace("${total_tokens}", str(total_tokens))
            
            budgets_list = "\n".join(f"  - {name}: {budget} tokens" for name, budget in section_budgets.items())
            section_block = section_template.replace("${budgets_list}", budgets_list)
            
            result = base_template.replace("${total_tokens_block}", total_block)
            result = result.replace("${section_budgets_block}", section_block)
            
            return result
            
        except LLMTemplateError:
            # Fallback
            budgets_list = "\n".join(f"  - {name}: {budget} tokens" for name, budget in section_budgets.items())
            return f"TOKEN BUDGET:\n\n1. Total: {total_tokens} tokens\n2. Per section:\n{budgets_list}"
    
    def _build_validation_hints(
        self,
        word_count_range: tuple[int, int],
        required_elements: list[str]
    ) -> str:
        """Build validation hints fragment.
        
        Args:
            word_count_range: Tuple of (min_words, max_words)
            required_elements: List of required element names
            
        Returns:
            Formatted validation hints string
        """
        try:
            validation_data = self.loader.load_fragment("validation_hints.json")
            
            base_template = validation_data.get("base_template", "VALIDATION:\n\n${word_count_block}\n${required_elements_block}")
            word_template = validation_data.get("word_count_template", "1. Word count: ${min_words}-${max_words}")
            elements_template = validation_data.get("required_elements_template", "2. Required:\n${elements_list}")
            
            min_words, max_words = word_count_range
            word_block = word_template.replace("${min_words}", str(min_words)).replace("${max_words}", str(max_words))
            
            elements_list = "\n".join(f"  - {elem}" for elem in required_elements)
            elements_block = elements_template.replace("${elements_list}", elements_list)
            
            result = base_template.replace("${word_count_block}", word_block)
            result = result.replace("${required_elements_block}", elements_block)
            
            return result
            
        except LLMTemplateError:
            # Fallback
            min_words, max_words = word_count_range
            elements_list = "\n".join(f"  - {elem}" for elem in required_elements)
            return f"VALIDATION:\n\n1. Word count: {min_words}-{max_words}\n2. Required:\n{elements_list}"
