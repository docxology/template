"""Prompt composition engine.

Composes prompts from fragments, templates, and variables with support
for inheritance, overrides, and conditional fragments.
"""
from __future__ import annotations

import re
from string import Template
from typing import Dict, Any, Optional, List
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.llm.prompts.loader import PromptFragmentLoader, get_default_loader

logger = get_logger(__name__)


class PromptComposer:
    """Composes prompts from fragments and templates.
    
    Handles variable substitution, fragment loading, and prompt assembly
    with support for conditional fragments and retry-specific modifications.
    
    Example:
        >>> composer = PromptComposer()
        >>> prompt = composer.compose_template(
        ...     "manuscript_reviews.json#manuscript_executive_summary",
        ...     text=manuscript_text,
        ...     max_tokens=4096
        ... )
    """
    
    def __init__(self, loader: Optional[PromptFragmentLoader] = None):
        """Initialize prompt composer.
        
        Args:
            loader: PromptFragmentLoader instance. If None, uses default loader.
        """
        self.loader = loader or get_default_loader()
    
    def _render_fragment_template(
        self,
        template_str: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render a fragment template string with variables.
        
        Args:
            template_str: Template string with ${variable} placeholders
            variables: Variables for substitution
            
        Returns:
            Rendered string
            
        Raises:
            LLMTemplateError: If required variables are missing
        """
        try:
            template = Template(template_str)
            # Use substitute() instead of safe_substitute() to raise KeyError for missing variables
            result = template.substitute(**variables)
            return result
        except KeyError as e:
            # Missing required variable
            missing_var = str(e).strip("'")
            raise LLMTemplateError(
                f"Missing required template variable: {missing_var}",
                context={
                    "missing_variable": missing_var,
                    "available_variables": list(variables.keys()),
                    "template": template_str[:100]
                }
            )
        except Exception as e:
            raise LLMTemplateError(
                f"Failed to render fragment template: {e}",
                context={"error": str(e), "template": template_str[:100]}
            )
    
    def _build_format_requirements(
        self,
        required_headers: List[str],
        section_requirements: Optional[Dict[str, str]] = None
    ) -> str:
        """Build format requirements fragment.
        
        Args:
            required_headers: List of required section headers
            section_requirements: Optional section-specific requirements
            
        Returns:
            Formatted requirements string
        """
        fragment = self.loader.load_fragment("format_requirements.json")
        base_template = fragment.get("base_template", "")
        
        # Build headers list
        headers_list = "\n".join(f"   {header}" for header in required_headers)
        
        # Build section requirements if provided
        section_requirements_block = ""
        if section_requirements:
            requirements_template = fragment.get("section_requirements_template", "")
            requirements_list = "\n".join(
                f"   - {section}: {req}" for section, req in section_requirements.items()
            )
            section_requirements_block = self._render_fragment_template(
                requirements_template,
                {"requirements_list": requirements_list}
            )
        
        return self._render_fragment_template(
            base_template,
            {
                "headers_list": headers_list,
                "section_requirements_block": section_requirements_block
            }
        )
    
    def _build_content_requirements(
        self,
        no_hallucination: bool = True,
        cite_sources: bool = True,
        evidence_based: bool = True,
        no_meta_commentary: bool = True
    ) -> str:
        """Build content requirements fragment.
        
        Args:
            no_hallucination: Include no-hallucination requirement
            cite_sources: Include citation requirement
            evidence_based: Include evidence-based requirement
            no_meta_commentary: Include no-meta-commentary requirement
            
        Returns:
            Formatted content requirements string
        """
        fragment = self.loader.load_fragment("content_requirements.json")
        base_template = fragment.get("base_template", "")
        
        blocks = []
        if no_hallucination:
            blocks.append(fragment.get("no_hallucination", ""))
        if cite_sources:
            blocks.append(fragment.get("cite_sources", ""))
        if evidence_based:
            blocks.append(fragment.get("evidence_based", ""))
        if no_meta_commentary:
            blocks.append(fragment.get("no_meta_commentary", ""))
        
        return self._render_fragment_template(
            base_template,
            {
                "no_hallucination_block": blocks[0] if len(blocks) > 0 else "",
                "cite_sources_block": blocks[1] if len(blocks) > 1 else "",
                "evidence_based_block": blocks[2] if len(blocks) > 2 else "",
                "no_meta_commentary_block": blocks[3] if len(blocks) > 3 else "",
            }
        )
    
    def _build_section_structure(
        self,
        structure_key: str,
        required_order: bool = True
    ) -> str:
        """Build section structure fragment.
        
        Args:
            structure_key: Key in section_structures.json (e.g., "executive_summary")
            required_order: Whether sections must appear in order
            
        Returns:
            Formatted section structure string
        """
        structures = self.loader.load_fragment("section_structures.json")
        structure = structures.get(structure_key)
        
        if not structure:
            raise LLMTemplateError(
                f"Section structure '{structure_key}' not found",
                context={"available_keys": list(structures.keys())}
            )
        
        headers = structure.get("headers", [])
        descriptions = structure.get("descriptions", {})
        
        lines = ["SECTION STRUCTURE:"]
        if required_order:
            lines.append("1. Sections must appear in this exact order:")
        else:
            lines.append("1. Include all of these sections:")
        
        for i, header in enumerate(headers, 1):
            desc = descriptions.get(header, "")
            if desc:
                lines.append(f"   {i}. {header}: {desc}")
            else:
                lines.append(f"   {i}. {header}")
        
        return "\n".join(lines)
    
    def _build_token_budget_awareness(
        self,
        total_tokens: Optional[int] = None,
        section_budgets: Optional[Dict[str, int]] = None,
        word_targets: Optional[Dict[str, tuple]] = None
    ) -> str:
        """Build token budget awareness fragment.
        
        Args:
            total_tokens: Total token budget
            section_budgets: Token budgets per section
            word_targets: Word count targets per section
            
        Returns:
            Formatted token budget awareness string
        """
        fragment = self.loader.load_fragment("token_budget_awareness.json")
        base_template = fragment.get("base_template", "")
        
        total_tokens_block = ""
        if total_tokens:
            total_template = fragment.get("total_tokens_template", "")
            total_tokens_block = self._render_fragment_template(
                total_template,
                {"total_tokens": total_tokens}
            )
        
        section_budgets_block = ""
        if section_budgets:
            budgets_template = fragment.get("section_budgets_template", "")
            budgets_list = "\n".join(
                f"   - {section}: ~{budget} tokens" for section, budget in section_budgets.items()
            )
            section_budgets_block = self._render_fragment_template(
                budgets_template,
                {"budgets_list": budgets_list}
            )
        
        word_targets_block = ""
        if word_targets:
            targets_template = fragment.get("word_targets_template", "")
            targets_list = "\n".join(
                f"   - {section}: {min_words}-{max_words} words"
                for section, (min_words, max_words) in word_targets.items()
            )
            word_targets_block = self._render_fragment_template(
                targets_template,
                {"targets_list": targets_list}
            )
        
        return self._render_fragment_template(
            base_template,
            {
                "total_tokens_block": total_tokens_block,
                "section_budgets_block": section_budgets_block,
                "word_targets_block": word_targets_block
            }
        )
    
    def _build_validation_hints(
        self,
        word_count_range: Optional[tuple] = None,
        required_elements: Optional[List[str]] = None,
        format_checks: Optional[List[str]] = None
    ) -> str:
        """Build validation hints fragment.
        
        Args:
            word_count_range: (min, max) word count tuple
            required_elements: List of required elements
            format_checks: List of format checks
            
        Returns:
            Formatted validation hints string
        """
        fragment = self.loader.load_fragment("validation_hints.json")
        base_template = fragment.get("base_template", "")
        
        word_count_block = ""
        if word_count_range:
            min_words, max_words = word_count_range
            word_template = fragment.get("word_count_template", "")
            word_count_block = self._render_fragment_template(
                word_template,
                {"min_words": min_words, "max_words": max_words}
            )
        
        required_elements_block = ""
        if required_elements:
            elements_template = fragment.get("required_elements_template", "")
            elements_list = "\n".join(f"   - {element}" for element in required_elements)
            required_elements_block = self._render_fragment_template(
                elements_template,
                {"elements_list": elements_list}
            )
        
        format_checks_block = ""
        if format_checks:
            checks_template = fragment.get("format_checks_template", "")
            checks_list = "\n".join(f"   - {check}" for check in format_checks)
            format_checks_block = self._render_fragment_template(
                checks_template,
                {"checks_list": checks_list}
            )
        
        return self._render_fragment_template(
            base_template,
            {
                "word_count_block": word_count_block,
                "required_elements_block": required_elements_block,
                "format_checks_block": format_checks_block
            }
        )
    
    def compose_template(
        self,
        template_ref: str,
        **kwargs: Any
    ) -> str:
        """Compose a prompt from a template definition.
        
        Args:
            template_ref: Template reference (e.g., "manuscript_reviews.json#manuscript_executive_summary")
            **kwargs: Template variables (text, max_tokens, target_language, etc.)
            
        Returns:
            Composed prompt string
            
        Example:
            >>> composer = PromptComposer()
            >>> prompt = composer.compose_template(
            ...     "manuscript_reviews.json#manuscript_executive_summary",
            ...     text=manuscript_text,
            ...     max_tokens=4096
            ... )
        """
        # Load template definition
        template_def = self.loader.load_template(template_ref)
        
        # Get base template
        base_template_str = template_def.get("base_template", "")
        if not base_template_str:
            raise LLMTemplateError(
                f"Template '{template_ref}' missing base_template",
                context={"template": template_ref}
            )
        
        # Get section config
        section_config = template_def.get("section_config", {})
        structure_key = section_config.get("structure_key", "")
        
        # Get variables from template definition
        template_vars = template_def.get("variables", {})
        
        # Merge template variables with provided kwargs (kwargs take precedence)
        all_vars = {**template_vars, **kwargs}
        
        # Build fragments
        fragments = template_def.get("fragments", {})
        
        # Build format requirements
        if "format_requirements" in fragments:
            structures = self.loader.load_fragment("section_structures.json")
            structure = structures.get(structure_key, {})
            required_headers = structure.get("headers", [])
            section_requirements = structure.get("section_requirements", {})
            format_req = self._build_format_requirements(required_headers, section_requirements)
        else:
            format_req = ""
        
        # Build section structure
        if "section_structure" in fragments:
            section_struct = self._build_section_structure(structure_key)
        else:
            section_struct = ""
        
        # Build token budget awareness
        if "token_budget_awareness" in fragments:
            max_tokens = all_vars.get("max_tokens")
            section_budgets = None
            word_targets = None
            
            if max_tokens and structure_key:
                structures = self.loader.load_fragment("section_structures.json")
                structure = structures.get(structure_key, {})
                headers = structure.get("headers", [])
                word_targets_dict = structure.get("word_targets", {})
                
                # Calculate section budgets
                token_allocation = section_config.get("token_allocation", "equal")
                num_sections = section_config.get("sections", len(headers))
                
                if token_allocation == "equal":
                    tokens_per_section = max_tokens // num_sections
                    section_budgets = {
                        header.replace("## ", ""): tokens_per_section
                        for header in headers
                    }
                elif token_allocation == "weighted":
                    weights = section_config.get("weights", {})
                    base_tokens = max_tokens // num_sections
                    section_budgets = {
                        header.replace("## ", ""): int(base_tokens * weights.get(header.replace("## ", ""), 1.0))
                        for header in headers
                    }
                
                # Convert word targets to tuples
                if word_targets_dict:
                    word_targets = {
                        k: tuple(v) if isinstance(v, list) else v
                        for k, v in word_targets_dict.items()
                    }
            
            token_budget = self._build_token_budget_awareness(
                total_tokens=max_tokens,
                section_budgets=section_budgets,
                word_targets=word_targets
            )
        else:
            token_budget = ""
        
        # Build content requirements
        if "content_requirements" in fragments:
            content_req = self._build_content_requirements()
        else:
            content_req = ""
        
        # Build validation hints
        if "validation_hints" in fragments:
            word_count_range = all_vars.get("word_count_range")
            required_elements = all_vars.get("required_elements")
            format_checks = all_vars.get("format_checks")
            validation = self._build_validation_hints(
                word_count_range=word_count_range,
                required_elements=required_elements,
                format_checks=format_checks
            )
        else:
            validation = ""
        
        # Substitute all variables in base template
        final_vars = {
            **all_vars,
            "format_requirements": format_req,
            "section_structure": section_struct,
            "token_budget_awareness": token_budget,
            "content_requirements": content_req,
            "validation_hints": validation,
        }
        
        # Handle target_language substitution in section structure
        if "target_language" in all_vars:
            target_lang = all_vars["target_language"]
            # Replace {target_language} placeholder in section structure
            section_struct = section_struct.replace("{target_language}", target_lang)
            final_vars["section_structure"] = section_struct
        
        return self._render_fragment_template(base_template_str, final_vars)
    
    def add_retry_prompt(
        self,
        base_prompt: str,
        retry_type: str = "off_topic"
    ) -> str:
        """Add retry-specific prompt modifications.
        
        Args:
            base_prompt: Original prompt
            retry_type: Type of retry ("off_topic", "format_enforcement")
            
        Returns:
            Modified prompt with retry instructions prepended
        """
        try:
            if retry_type == "off_topic":
                retry_prompt = self.loader.load_composition("retry_prompts.json#off_topic_reinforcement")
                if isinstance(retry_prompt, dict):
                    retry_content = retry_prompt.get("content", "")
                else:
                    retry_content = str(retry_prompt)
                return retry_content + base_prompt
            elif retry_type == "format_enforcement":
                # Format enforcement is template-specific, handled in review script
                return base_prompt
            else:
                return base_prompt
        except Exception as e:
            logger.warning(f"Failed to load retry prompt: {e}")
            return base_prompt

