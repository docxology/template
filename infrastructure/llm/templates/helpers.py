"""Helper functions for prompt template generation."""
from __future__ import annotations

from typing import Dict, List, Optional


def format_requirements(
    required_headers: List[str],
    markdown_format: bool = True,
    section_requirements: Optional[Dict[str, str]] = None
) -> str:
    """Generate format requirements section for prompts.
    
    Args:
        required_headers: List of required markdown section headers (e.g., ["## Overview", "## Results"])
        markdown_format: Whether to use markdown formatting
        section_requirements: Optional dict mapping section names to specific requirements
        
    Returns:
        Formatted requirements string
    """
    lines = ["FORMAT REQUIREMENTS:"]
    
    if markdown_format:
        lines.append("1. Use markdown formatting with proper headers")
        lines.append("2. Include these exact section headers (in order):")
        for header in required_headers:
            lines.append(f"   {header}")
    
    if section_requirements:
        lines.append("3. Section-specific requirements:")
        for section, req in section_requirements.items():
            lines.append(f"   - {section}: {req}")
    
    return "\n".join(lines)


def token_budget_awareness(
    total_tokens: Optional[int] = None,
    section_budgets: Optional[Dict[str, int]] = None,
    word_targets: Optional[Dict[str, tuple]] = None
) -> str:
    """Generate token budget awareness hints for prompts.
    
    Args:
        total_tokens: Total token budget available
        section_budgets: Optional dict mapping section names to approximate token budgets
        word_targets: Optional dict mapping section names to (min, max) word counts
        
    Returns:
        Formatted token budget awareness string
    """
    lines = ["TOKEN BUDGET AWARENESS:"]
    
    if total_tokens:
        lines.append(f"1. Total response budget: approximately {total_tokens} tokens")
        lines.append("   (Plan your response to stay within this limit)")
    
    if section_budgets:
        lines.append("2. Approximate token budgets per section:")
        for section, budget in section_budgets.items():
            lines.append(f"   - {section}: ~{budget} tokens")
    
    if word_targets:
        lines.append("3. Word count targets per section:")
        for section, (min_words, max_words) in word_targets.items():
            lines.append(f"   - {section}: {min_words}-{max_words} words")
    
    return "\n".join(lines)


def content_requirements(
    no_hallucination: bool = True,
    cite_sources: bool = True,
    evidence_based: bool = True,
    no_meta_commentary: bool = True
) -> str:
    """Generate content quality requirements section.
    
    Args:
        no_hallucination: Require no invented details
        cite_sources: Require citation of sources
        evidence_based: Require evidence-based claims
        no_meta_commentary: Prohibit meta-commentary about being AI
        
    Returns:
        Formatted content requirements string
    """
    lines = ["CONTENT QUALITY REQUIREMENTS:"]
    
    if no_hallucination:
        lines.append("1. NO HALLUCINATION: Only discuss information explicitly present in the provided content")
        lines.append("   - Do NOT add external knowledge, assumptions, or invented details")
        lines.append("   - Do NOT reference sources not mentioned in the provided content")
    
    if cite_sources:
        lines.append("2. CITE SOURCES: Reference specific sections, passages, or elements from the content")
        lines.append("   - Quote or paraphrase actual text when making observations")
        lines.append("   - Use specific section titles or page references when available")
    
    if evidence_based:
        lines.append("3. EVIDENCE-BASED: Base all claims on evidence from the provided content")
        lines.append("   - Support observations with specific examples")
        lines.append("   - Explain reasoning with reference to actual content")
    
    if no_meta_commentary:
        lines.append("4. NO META-COMMENTARY: Do not mention being an AI, assistant, or that this is generated content")
        lines.append("   - Write as if you are a human expert reviewer")
        lines.append("   - Use professional, academic tone throughout")
    
    return "\n".join(lines)


def section_structure(
    sections: List[str],
    section_descriptions: Optional[Dict[str, str]] = None,
    required_order: bool = True
) -> str:
    """Generate section structure requirements.
    
    Args:
        sections: List of required section names/headers
        section_descriptions: Optional dict mapping section names to descriptions
        required_order: Whether sections must appear in the specified order
        
    Returns:
        Formatted section structure string
    """
    lines = ["SECTION STRUCTURE:"]
    
    if required_order:
        lines.append("1. Sections must appear in this exact order:")
    else:
        lines.append("1. Include these sections:")
    
    for i, section in enumerate(sections, 1):
        if section_descriptions and section in section_descriptions:
            lines.append(f"   {i}. {section}: {section_descriptions[section]}")
        else:
            lines.append(f"   {i}. {section}")
    
    return "\n".join(lines)


def validation_hints(
    word_count_range: Optional[tuple] = None,
    required_elements: Optional[List[str]] = None,
    format_checks: Optional[List[str]] = None
) -> str:
    """Generate validation hints that inform the model what will be checked.
    
    Args:
        word_count_range: Optional (min, max) word count tuple
        required_elements: Optional list of required elements (e.g., ["scores", "headers"])
        format_checks: Optional list of format checks that will be performed
        
    Returns:
        Formatted validation hints string
    """
    lines = ["VALIDATION HINTS (what will be checked):"]
    
    if word_count_range:
        min_words, max_words = word_count_range
        lines.append(f"1. Word count: Must be between {min_words} and {max_words} words")
    
    if required_elements:
        lines.append("2. Required elements:")
        for element in required_elements:
            lines.append(f"   - {element}")
    
    if format_checks:
        lines.append("3. Format compliance checks:")
        for check in format_checks:
            lines.append(f"   - {check}")
    
    return "\n".join(lines)

