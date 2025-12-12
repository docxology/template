"""Prompt building for paper summarization.

This module builds improved multi-stage prompts with examples and
validation checklists to guide the LLM toward better summaries.
"""
from __future__ import annotations

from typing import List, Optional

from infrastructure.literature.summarization.models import SummarizationContext
from infrastructure.literature.summarization.utils import detect_model_size


class SummarizationPromptBuilder:
    """Builds optimized prompts for paper summarization.
    
    Creates model-size-aware prompts that are ~50% shorter than original
    versions while maintaining clarity. Automatically detects model size
    and adjusts prompt complexity accordingly.
    
    Features:
    - Model-size awareness (shorter prompts for small models <7B)
    - Consolidated instructions (removed redundant sections)
    - Explicit anti-repetition guidance
    - Structured output format requirements
    - Fallback simple prompts for refinement failures
    """
    
    def __init__(self, llm_client=None):
        """Initialize prompt builder.
        
        Args:
            llm_client: Optional LLM client for model size detection.
        """
        self.llm_client = llm_client
        self._model_size_cache: Optional[float] = None
    
    def _detect_model_size(self, metadata: dict) -> float:
        """Detect model size in billions of parameters (with caching).
        
        Args:
            metadata: Paper metadata (may contain model info).
            
        Returns:
            Model size in billions (e.g., 4.0 for gemma3:4b), or 7.0 as default.
        """
        if self._model_size_cache is not None:
            return self._model_size_cache
        
        # Use shared utility function
        self._model_size_cache = detect_model_size(self.llm_client, metadata)
        return self._model_size_cache
    
    def _is_small_model(self, metadata: dict) -> bool:
        """Check if using a small model (<7B parameters)."""
        return self._detect_model_size(metadata) < 7.0
    
    def build_draft_prompt(self, context: SummarizationContext, metadata: dict) -> str:
        """Build prompt for initial draft generation.
        
        Args:
            context: Structured context from paper.
            metadata: Paper metadata (title, authors, year, source).
            
        Returns:
            Complete prompt string for draft generation.
        """
        title = metadata.get('title', context.title)
        authors = metadata.get('authors', [])
        year = metadata.get('year', '')
        source = metadata.get('source', '')
        is_small = self._is_small_model(metadata)
        
        # Build prompt sections (optimized, ~50% shorter)
        sections = []
        
        # Section 1: Paper Identity (concise)
        sections.append(f"Title: {title}")
        if authors:
            sections.append(f"Authors: {', '.join(authors[:3])}")
        if year:
            sections.append(f"Year: {year}")
        sections.append("")
        
        # Section 2: Key Context (only for small models, skip for large)
        if is_small and context.abstract:
            sections.append("Abstract: " + context.abstract[:500] + ("..." if len(context.abstract) > 500 else ""))
            sections.append("")
        
        if context.key_terms:
            sections.append(f"Key Terms: {', '.join(context.key_terms[:10])}")
            sections.append("")
        
        # Section 3: Full Paper Text (single mention, concise instructions)
        sections.append("=== FULL PAPER TEXT ===")
        if not is_small:
            sections.append("Use this as your PRIMARY source for all information.")
        sections.append("")
        sections.append(context.full_text)
        sections.append("")
        
        # Section 4: Instructions (consolidated, model-aware)
        sections.append(self._build_instructions_section(context, is_small))
        
        return "\n".join(sections)
    
    def build_refinement_prompt(
        self,
        draft: str,
        issues: List[str],
        context: SummarizationContext,
        metadata: Optional[dict] = None
    ) -> str:
        """Build prompt for refining a draft summary (optimized, ~50% shorter).
        
        Args:
            draft: Current draft summary.
            issues: List of specific issues found during validation.
            context: Structured context from paper.
            metadata: Optional metadata for model size detection.
            
        Returns:
            Refinement prompt string.
        """
        is_small = self._is_small_model(metadata or {})
        sections = []
        
        # Issues (concise)
        sections.append("Issues to fix:")
        for i, issue in enumerate(issues[:5], 1):  # Limit to top 5 issues
            sections.append(f"{i}. {issue}")
        sections.append("")
        
        # Current draft (truncated for small models)
        if is_small and len(draft) > 2000:
            sections.append("Current draft (first 2000 chars):")
            sections.append(draft[:2000] + "...")
        else:
            sections.append("Current draft:")
            sections.append(draft)
        sections.append("")
        
        # Key terms (if needed)
        if context.key_terms:
            sections.append(f"Key terms: {', '.join(context.key_terms[:8])}")
            sections.append("")
        
        # Full text (single mention)
        sections.append("=== FULL PAPER TEXT ===")
        sections.append(context.full_text)
        sections.append("")
        
        # Refinement instructions (consolidated)
        sections.append("=== REVISE TO ===")
        sections.append(f"1. Fix all issues above")
        sections.append(f"2. Title: \"{context.title}\"")
        sections.append("3. Include 10-15 quotes from paper text")
        
        # Add specific guidance based on issues
        has_missing_quotes = any("quote" in issue.lower() or "quotes" in issue.lower() for issue in issues)
        has_missing_methodology = any("methodology" in issue.lower() or "method" in issue.lower() for issue in issues)
        
        if has_missing_quotes:
            sections.append("   - Search the full paper text to find relevant quotes")
            sections.append("   - Extract quotes that support your claims")
        
        if has_missing_methodology:
            sections.append("   - Include detailed methodology: experimental setup, algorithms, procedures")
            sections.append("   - Describe the approach and implementation details")
        
        sections.append("4. ELIMINATE ALL REPETITION - each sentence must be unique")
        sections.append("5. Extract methodology, results with numbers, key quotes")
        sections.append("6. 1000-1500 words, structured with ### headers")
        sections.append("")
        sections.append("Generate COMPLETE revised summary.")
        
        return "\n".join(sections)
    
    def build_simple_refinement_prompt(
        self,
        draft: str,
        issues: List[str],
        context: SummarizationContext
    ) -> str:
        """Build simplified refinement prompt for fallback strategy.
        
        Args:
            draft: Current draft summary.
            issues: List of specific issues.
            context: Structured context.
            
        Returns:
            Simplified refinement prompt.
        """
        sections = []
        sections.append(f"Fix these issues in your summary:")
        for issue in issues[:3]:  # Top 3 issues only
            sections.append(f"- {issue}")
        sections.append("")
        sections.append("Current summary:")
        sections.append(draft[:1500] if len(draft) > 1500 else draft)
        sections.append("")
        sections.append("Paper text:")
        sections.append(context.full_text[:30000] if len(context.full_text) > 30000 else context.full_text)
        sections.append("")
        sections.append("Rewrite the summary fixing the issues. Use exact title: " + context.title)
        sections.append("NO REPETITION. Each sentence must be unique.")
        
        return "\n".join(sections)
    
    def _build_instructions_section(self, context: SummarizationContext, is_small: bool = False) -> str:
        """Build instructions section (consolidated, ~50% shorter)."""
        sections = []
        
        sections.append("=== INSTRUCTIONS ===")
        
        # Title matching (critical, always include)
        sections.append(f"1. Start with exact title: \"{context.title}\"")
        sections.append("")
        
        # Key terms (concise)
        if context.key_terms:
            sections.append(f"2. Discuss key terms: {', '.join(context.key_terms[:8])}")
            sections.append("")
        
        # Evidence (consolidated)
        sections.append("3. Include 10-15 quotes from paper text with format: 'The authors state: \"quote\"'")
        sections.append("   - All claims must be supported by evidence from the paper")
        sections.append("   - Search the full text to find relevant quotes")
        sections.append("")
        
        # Anti-repetition (CRITICAL - emphasized)
        sections.append("4. NO REPETITION: Each sentence and paragraph must be UNIQUE.")
        sections.append("   - Do NOT repeat the same sentence, even with slight variations")
        sections.append("   - Do NOT repeat paragraphs or sections")
        sections.append("   - Each claim should appear only once")
        sections.append("")
        
        # Content focus (consolidated)
        if not is_small:
            sections.append("5. Extract from full text: methodology, results with numbers, key quotes")
            sections.append("")
        
        # Structure (simplified)
        sections.append("6. Structure: ### Overview, ### Methodology, ### Results, ### Discussion (1000-1500 words)")
        sections.append("")
        
        return "\n".join(sections)
    
    def _build_validation_checklist(self, context: SummarizationContext) -> str:
        """Build validation checklist for summary quality.
        
        Args:
            context: Structured context from paper.
            
        Returns:
            Validation checklist string.
        """
        sections = []
        
        sections.append("=== VALIDATION CHECKLIST ===")
        sections.append("")
        sections.append("Before submitting, verify:")
        sections.append("")
        sections.append("1. Quote Requirements:")
        sections.append("   - Contains 10-15 quotes from the paper text")
        sections.append("   - Each quote is properly formatted: 'The authors state: \"quote\"'")
        sections.append("   - Quotes support the claims made in the summary")
        sections.append("")
        sections.append("2. Length Requirements:")
        sections.append("   - Summary is 1000-1500 words")
        sections.append("   - All sections are adequately covered")
        sections.append("")
        sections.append("3. Content Requirements:")
        sections.append("   - Title matches exactly: \"" + context.title + "\"")
        sections.append("   - All key terms are discussed")
        sections.append("   - Methodology is clearly described")
        sections.append("   - Results include numerical data")
        sections.append("   - Discussion provides meaningful insights")
        sections.append("")
        sections.append("4. Quality Requirements:")
        sections.append("   - NO repetition of sentences or paragraphs")
        sections.append("   - Each claim is supported by evidence")
        sections.append("   - Structure follows: ### Overview, ### Methodology, ### Results, ### Discussion")
        sections.append("")
        
        return "\n".join(sections)
    
    def build_examples_section(self) -> str:
        """Build section with examples of good and bad summaries."""
        sections = []
        
        sections.append("=== EXAMPLES ===")
        sections.append("")
        
        sections.append("GOOD SUMMARY EXAMPLE:")
        sections.append("---")
        sections.append("# Active Inference: A Process Theory")
        sections.append("")
        sections.append("### Overview")
        sections.append("This paper presents active inference as a process theory. The authors state:")
        sections.append("\"Active inference provides a unified framework for understanding behavior.\"")
        sections.append("")
        sections.append("### Key Contributions")
        sections.append("The paper introduces three key concepts: (1) variational free energy, (2) expected free energy,")
        sections.append("and (3) active inference. The abstract notes: [paraphrase of key finding].")
        sections.append("")
        sections.append("### Methodology")
        sections.append("The approach uses Bayesian inference principles...")
        sections.append("---")
        sections.append("")
        
        sections.append("BAD SUMMARY EXAMPLE (AVOID):")
        sections.append("---")
        sections.append("# Overview/Summary")
        sections.append("")
        sections.append("This paper presents methods. The paper presents methods.")
        sections.append("The paper presents methods. The paper presents methods.")
        sections.append("[REPETITION - BAD]")
        sections.append("")
        sections.append("The paper discusses neural networks. [WRONG - paper is about active inference, not neural networks]")
        sections.append("[HALLUCINATION - BAD]")
        sections.append("---")
        sections.append("")
        
        return "\n".join(sections)
