"""Core summarization engine.

This module provides the main SummarizationEngine that orchestrates
the complete multi-stage summarization workflow.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError, FileOperationError
from infrastructure.literature.sources import SearchResult
from infrastructure.validation.pdf_validator import extract_text_from_pdf, PDFValidationError

from infrastructure.literature.summarization.models import SummarizationResult, SummarizationProgressEvent
from infrastructure.literature.summarization.context_extractor import ContextExtractor
from infrastructure.literature.summarization.prompt_builder import SummarizationPromptBuilder
from infrastructure.literature.summarization.multi_stage_summarizer import MultiStageSummarizer
from infrastructure.literature.summarization.validator import SummaryQualityValidator
from infrastructure.literature.summarization.pdf_processor import PDFProcessor, PrioritizedPDFText
from infrastructure.literature.summarization.extractor import TextExtractor
from infrastructure.literature.summarization.utils import detect_model_size

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient

logger = get_logger(__name__)


class SummarizationEngine:
    """Main interface for paper summarization with multi-stage generation.

    Orchestrates the complete summarization workflow including:
    - PDF text extraction with prioritization
    - Context extraction and structuring
    - Multi-stage summary generation (draft + refine)
    - Quality validation
    - Result management

    Attributes:
        llm_client: LLM client for summary generation.
        context_extractor: Context extraction instance.
        prompt_builder: Prompt builder instance.
        multi_stage_summarizer: Multi-stage summarizer instance.
        validator: Quality validator instance.
        pdf_processor: PDF processor instance.
        max_pdf_chars: Maximum characters to send to LLM.
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        quality_validator: Optional[SummaryQualityValidator] = None,
        context_extractor: Optional[ContextExtractor] = None,
        prompt_builder: Optional[SummarizationPromptBuilder] = None,
        max_pdf_chars: Optional[int] = None
    ):
        """Initialize summarization engine.

        Args:
            llm_client: Configured LLM client for summary generation.
            quality_validator: Quality validator instance (created if None).
            context_extractor: Context extractor instance (created if None).
            prompt_builder: Prompt builder instance (created if None).
            max_pdf_chars: Maximum PDF characters to send to LLM.
                          Defaults to 200000 (200K) or LLM_MAX_INPUT_LENGTH env var.
        """
        import os
        
        self.llm_client = llm_client
        self.validator = quality_validator or SummaryQualityValidator()
        self.context_extractor = context_extractor or ContextExtractor()
        self.prompt_builder = prompt_builder or SummarizationPromptBuilder(llm_client=llm_client)
        self.pdf_processor = PDFProcessor()
        self.text_extractor = TextExtractor()
        self._last_ref_info: Optional[Dict[str, Any]] = None  # Store ref_info for metadata
        
        # Get max_pdf_chars from parameter, environment variable, or model-aware default
        if max_pdf_chars is not None:
            self.max_pdf_chars = max_pdf_chars
        else:
            env_limit = os.getenv('LLM_MAX_INPUT_LENGTH')
            if env_limit:
                try:
                    self.max_pdf_chars = int(env_limit)
                except ValueError:
                    self.max_pdf_chars = self._get_model_aware_limit()
            else:
                self.max_pdf_chars = self._get_model_aware_limit()
        
        # Create multi-stage summarizer (with two-stage support)
        self.multi_stage_summarizer = MultiStageSummarizer(
            llm_client=llm_client,
            validator=self.validator,
            prompt_builder=self.prompt_builder,
            max_refinement_attempts=2,
            two_stage_enabled=None,  # Auto-detect from env
            chunk_size=None,  # Auto-detect from env
            chunk_overlap=None,  # Auto-detect from env
            two_stage_threshold=None  # Auto-detect from env
        )

    def summarize_paper(
        self,
        result: SearchResult,
        pdf_path: Path,
        max_retries: int = 2,
        progress_callback: Optional[Callable[[SummarizationProgressEvent], None]] = None
    ) -> SummarizationResult:
        """Generate summary for a single paper with quality validation.
        
        This method orchestrates the complete summarization workflow:
        1. PDF text extraction (from pre-extracted files or on-the-fly)
        2. Context extraction (abstract, intro, conclusion, key terms)
        3. Multi-stage summary generation (draft + optional refinement)
        4. Post-processing deduplication
        5. Quality validation
        
        The summary is always included in the result (even if validation fails)
        to ensure it can be saved for review. Validation metadata is available
        in the result for transparency.

        Args:
            result: Search result with paper metadata (title, authors, year, etc.).
            pdf_path: Path to PDF file for summarization.
            max_retries: Maximum retry attempts for LLM connection failures
                        (refinement attempts are handled internally by MultiStageSummarizer).
            progress_callback: Optional callback function for real-time progress events.
                            Receives SummarizationProgressEvent instances at each stage.

        Returns:
            SummarizationResult containing:
            - summary_text: Generated summary (always present, even if validation failed)
            - success: Whether validation passed (score >= 0.5)
            - quality_score: Validation score (0.0 to 1.0)
            - validation_errors: List of validation issues (if any)
            - Metadata: input/output sizes, generation time, attempts
            
        Note:
            Summaries are always saved with validation metadata, allowing review
            of rejected summaries. Use save_summary() to persist to disk.
        """
        citation_key = pdf_path.stem
        start_time = time.time()
        
        # Helper function to emit progress events
        def emit_progress(stage: str, status: str, message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
            if progress_callback:
                event = SummarizationProgressEvent(
                    citation_key=citation_key,
                    stage=stage,
                    status=status,
                    message=message,
                    metadata=metadata or {}
                )
                progress_callback(event)
        
        # Load extracted text from file (preferred) or extract on-the-fly (fallback)
        emit_progress("pdf_extraction", "started", f"Loading text for {pdf_path.name}")
        extraction_start = time.time()
        
        # Try to load from extracted_text directory first
        pdf_text = self.text_extractor.load_extracted_text(citation_key)
        
        if pdf_text:
            # Successfully loaded from file
            extraction_time = time.time() - extraction_start
            input_chars = len(pdf_text)
            input_words = len(pdf_text.split())
            
            logger.info(
                f"[{citation_key}] Loaded extracted text from file: "
                f"{input_chars:,} chars, {input_words:,} words ({extraction_time:.2f}s)"
            )
            
            emit_progress(
                "pdf_extraction",
                "completed",
                f"Loaded {input_chars:,} chars, {input_words:,} words from extracted text file",
                {"chars": input_chars, "words": input_words, "time": extraction_time, "source": "file"}
            )
        else:
            # Fallback: extract on-the-fly (with warning)
            logger.warning(
                f"[{citation_key}] No extracted text file found at "
                f"data/extracted_text/{citation_key}.txt. "
                f"Extracting on-the-fly (recommended: run extraction step first)."
            )
            
            emit_progress("pdf_extraction", "started", f"Extracting text from {pdf_path.name} (on-the-fly)")
            
            try:
                file_size = pdf_path.stat().st_size
                logger.debug(f"Starting on-the-fly PDF text extraction for {pdf_path.name} ({file_size:,} bytes)")
                
                prioritized_result = self.pdf_processor.extract_prioritized_text(
                    pdf_path, self.max_pdf_chars
                )
                pdf_text = prioritized_result.text
                extraction_time = time.time() - extraction_start
                
                if not pdf_text or len(pdf_text.strip()) < 100:
                    error_msg = "Insufficient text extracted from PDF (less than 100 characters). PDF extraction may have failed or yielded insufficient text."
                    emit_progress("pdf_extraction", "failed", error_msg)
                    logger.warning(
                        f"PDF extraction yielded insufficient text: "
                        f"{len(pdf_text) if pdf_text else 0} chars, "
                        f"{len(pdf_text.split()) if pdf_text else 0} words from {pdf_path.name}"
                    )
                    return SummarizationResult(
                        citation_key=citation_key,
                        success=False,
                        input_chars=len(pdf_text) if pdf_text else 0,
                        input_words=len(pdf_text.split()) if pdf_text else 0,
                        generation_time=time.time() - start_time,
                        attempts=1,
                        error=error_msg
                    )
                
                input_chars = len(pdf_text)
                input_words = len(pdf_text.split())
                
                if prioritized_result.truncation_occurred:
                    logger.info(
                        f"PDF prioritized: {prioritized_result.original_length:,} -> "
                        f"{prioritized_result.final_length:,} chars. "
                        f"Sections included: {', '.join(prioritized_result.sections_included)}"
                    )
                
                emit_progress(
                    "pdf_extraction",
                    "completed",
                    f"Extracted {input_chars:,} chars, {input_words:,} words (on-the-fly)",
                    {"chars": input_chars, "words": input_words, "time": extraction_time, "source": "on-the-fly"}
                )
            except PDFValidationError as e:
                extraction_time = time.time() - extraction_start
                emit_progress("pdf_extraction", "failed", f"PDF extraction failed: {e}")
                logger.error(f"PDF text extraction failed for {pdf_path.name}: {e}")
                return SummarizationResult(
                    citation_key=citation_key,
                    success=False,
                    input_chars=0,
                    input_words=0,
                    generation_time=time.time() - start_time,
                    attempts=1,
                    error=f"PDF extraction failed: {e}"
                )
        
        # Ensure we have valid text at this point
        if not pdf_text or len(pdf_text.strip()) < 100:
            error_msg = "No valid text available for summarization"
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                input_chars=len(pdf_text) if pdf_text else 0,
                input_words=len(pdf_text.split()) if pdf_text else 0,
                generation_time=time.time() - start_time,
                attempts=1,
                error=error_msg
            )
        
        input_chars = len(pdf_text)
        input_words = len(pdf_text.split())

        # Extract structured context
        emit_progress("context_extraction", "started", "Extracting structured context")
        context_start_time = time.time()
        try:
            context = self.context_extractor.create_summarization_context(
                pdf_text=pdf_text,
                title=result.title,
                max_chars=self.max_pdf_chars
            )
            context_time = time.time() - context_start_time
            
            # Save context summary to file for debugging
            # Note: Extracted text is already saved in data/extracted_text/ by extraction step
            try:
                debug_dir = Path("data/summaries") / "_debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                
                # Save context summary
                context_summary = f"""# Context Summary for {citation_key}

## Paper Identity
- Title: {context.title}
- Full Text Length: {len(context.full_text):,} chars
- Full Text Words: {len(context.full_text.split()):,} words

## Extracted Sections
- Abstract: {len(context.abstract)} chars
- Introduction: {len(context.introduction)} chars
- Conclusion: {len(context.conclusion)} chars
- Methods: {len(context.methods) if context.methods else 0} chars
- Results: {len(context.results) if context.results else 0} chars
- Discussion: {len(context.discussion) if context.discussion else 0} chars

## Key Terms
{', '.join(context.key_terms) if context.key_terms else 'None'}

## Equations Found
{len(context.equations)} equations extracted

## Full Text Preview (first 500 chars)
{context.full_text[:500]}...
"""
                context_summary_path = debug_dir / f"{citation_key}_context_summary.md"
                context_summary_path.write_text(context_summary, encoding='utf-8')
                logger.debug(f"[{citation_key}] Saved context summary: {context_summary_path}")
            except Exception as save_error:
                logger.debug(f"[{citation_key}] Failed to save debug files: {save_error}")
            
            logger.info(
                f"[{citation_key}] Context extracted in {context_time:.2f}s: "
                f"abstract={len(context.abstract)} chars, intro={len(context.introduction)} chars, "
                f"conclusion={len(context.conclusion)} chars, key_terms={len(context.key_terms)}, "
                f"full_text={len(context.full_text):,} chars (COMPLETE)"
            )
            emit_progress(
                "context_extraction",
                "completed",
                f"Context extracted: abstract={len(context.abstract)} chars, intro={len(context.introduction)} chars, conclusion={len(context.conclusion)} chars, key_terms={len(context.key_terms)}, full_text={len(context.full_text):,} chars",
                {
                    "abstract_chars": len(context.abstract),
                    "intro_chars": len(context.introduction),
                    "conclusion_chars": len(context.conclusion),
                    "key_terms_count": len(context.key_terms),
                    "full_text_chars": len(context.full_text),
                    "time": context_time
                }
            )
        except Exception as e:
            context_time = time.time() - context_start_time
            import traceback
            error_type = type(e).__name__
            error_context = {
                "stage": "context_extraction",
                "elapsed_time": f"{context_time:.2f}s",
                "input_chars": f"{input_chars:,}",
                "input_words": f"{input_words:,}",
                "error_type": error_type
            }
            emit_progress("context_extraction", "failed", f"Context extraction failed: {e}")
            logger.error(
                f"[{citation_key}] Context extraction failed after {context_time:.2f}s: {e}\n"
                f"Context: {error_context}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                input_chars=input_chars,
                input_words=input_words,
                generation_time=time.time() - start_time,
                attempts=1,
                error=f"Context extraction failed: {e}"
            )
        
        # Prepare metadata (include citation_key for proper logging)
        metadata = {
            'title': result.title,
            'authors': result.authors or [],
            'year': str(result.year) if result.year else '',
            'source': result.source or 'unknown',
            'citation_key': citation_key
        }
        
        logger.info(f"[{citation_key}] Starting multi-stage summarization...")
        generation_start_time = time.time()
        
        # Generate summary with multi-stage approach (with retry logic for LLM failures)
        attempts = 0
        summary = None
        validation_result = None
        total_attempts = 0
        base_backoff = 2.0  # Base backoff time in seconds
        
        for attempt in range(max_retries + 1):
            attempts = attempt + 1
            
            # Check LLM connection before each attempt
            if attempt > 0:
                # Exponential backoff: 2^attempt seconds (2s, 4s, 8s, etc.)
                backoff_time = base_backoff ** attempt
                logger.info(
                    f"[{citation_key}] Retry attempt {attempts}/{max_retries + 1} "
                    f"(waiting {backoff_time:.1f}s with exponential backoff)..."
                )
                time.sleep(backoff_time)
                
                # Verify LLM connection before retry
                logger.debug(f"[{citation_key}] Verifying LLM connection before retry...")
                if not self.llm_client.check_connection():
                    logger.warning(f"[{citation_key}] LLM connection check failed before retry {attempts}")
                    if attempt < max_retries:
                        continue  # Will retry again
                    else:
                        logger.error(f"[{citation_key}] LLM connection unavailable after {attempts} attempts")
                        return SummarizationResult(
                            citation_key=citation_key,
                            success=False,
                            input_chars=input_chars,
                            input_words=input_words,
                            generation_time=time.time() - start_time,
                            attempts=attempts,
                            error=f"LLM connection unavailable after {attempts} attempts"
                        )
                logger.debug(f"[{citation_key}] LLM connection verified before retry")
            
            try:
                summary, validation_result, total_attempts = self.multi_stage_summarizer.summarize_with_refinement(
                    context=context,
                    pdf_text=pdf_text,
                    metadata=metadata,
                    citation_key=citation_key,
                    progress_callback=progress_callback
                )
                
                # Validate summary is non-empty before proceeding
                if not summary or not summary.strip():
                    raise ValueError(f"Empty summary received for {citation_key}")
                
                generation_time = time.time() - generation_start_time
                summary_words = len(summary.split())
                logger.info(
                    f"[{citation_key}] Summary generation completed in {generation_time:.2f}s "
                    f"({total_attempts} total attempts, {summary_words} words, "
                    f"quality score: {validation_result.score:.2f})"
                )
                # Success - break out of retry loop
                break
            except LLMConnectionError as e:
                logger.warning(
                    f"[{citation_key}] LLM connection error on attempt {attempts}: {e}\n"
                    f"Context: prompt_size={len(prompt) if 'prompt' in locals() else 'unknown'}, "
                    f"elapsed={time.time() - generation_start_time:.2f}s"
                )
                if attempt < max_retries:
                    logger.info(f"[{citation_key}] Will retry with exponential backoff (attempt {attempts + 1}/{max_retries + 1})...")
                    continue
                else:
                    logger.error(f"[{citation_key}] LLM connection failed after {attempts} attempts")
                    return SummarizationResult(
                        citation_key=citation_key,
                        success=False,
                        input_chars=input_chars,
                        input_words=input_words,
                        generation_time=time.time() - start_time,
                        attempts=attempts,
                        error=f"LLM connection error after {attempts} attempts: {e}"
                    )
            except ValueError as e:
                # Empty response or validation error
                logger.error(
                    f"[{citation_key}] Summary validation error on attempt {attempts}: {e}\n"
                    f"Context: elapsed={time.time() - generation_start_time:.2f}s"
                )
                if attempt < max_retries:
                    logger.info(f"[{citation_key}] Will retry with exponential backoff (attempt {attempts + 1}/{max_retries + 1})...")
                    continue
                else:
                    return SummarizationResult(
                        citation_key=citation_key,
                        success=False,
                        input_chars=input_chars,
                        input_words=input_words,
                        generation_time=time.time() - start_time,
                        attempts=attempts,
                        error=f"Summary validation failed after {attempts} attempts: {e}"
                    )
            except Exception as e:
                import traceback
                logger.error(
                    f"[{citation_key}] Summary generation failed on attempt {attempts}: {e}\n"
                    f"Context: elapsed={time.time() - generation_start_time:.2f}s\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                if attempt < max_retries:
                    logger.info(f"[{citation_key}] Will retry with exponential backoff (attempt {attempts + 1}/{max_retries + 1})...")
                    continue
                else:
                    return SummarizationResult(
                        citation_key=citation_key,
                        success=False,
                        input_chars=input_chars,
                        input_words=input_words,
                        generation_time=time.time() - start_time,
                        attempts=attempts,
                        error=f"Summary generation failed after {attempts} attempts: {e}"
                    )
        
        # If we exhausted retries without success, return failure
        if summary is None or validation_result is None:
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                input_chars=input_chars,
                input_words=input_words,
                generation_time=time.time() - start_time,
                attempts=attempts,
                error="Summary generation failed after all retry attempts"
            )
        
        generation_time = time.time() - start_time
        output_words = len(summary.split())
        
        # Check if summary should be accepted
        if validation_result.has_hard_failure():
            logger.warning(
                f"[{citation_key}] Summary rejected due to hard failure: {validation_result.errors[:3]}"
            )
            # Always include summary_text even when validation fails (for saving)
            return SummarizationResult(
                citation_key=citation_key,
                success=False,
                summary_text=summary,  # Always include summary for saving
                input_chars=input_chars,
                input_words=input_words,
                output_words=output_words,
                generation_time=generation_time,
                attempts=total_attempts,
                quality_score=validation_result.score,
                validation_errors=validation_result.errors,
                error=f"Hard failure: {', '.join(validation_result.errors[:3])}"
            )
        
        # Accept if validation passed or score is acceptable
        success = validation_result.is_valid or validation_result.score >= 0.5
        
        if success:
            logger.info(
                f"[{citation_key}] Summary accepted: {output_words} words, "
                f"quality score: {validation_result.score:.2f}, "
                f"compression ratio: {output_words/max(1, input_words):.2%}"
            )
        else:
            logger.warning(
                f"[{citation_key}] Summary rejected: quality score {validation_result.score:.2f} "
                f"below threshold (0.5) - will still be saved"
            )
        
        # Always include summary_text even when validation fails (for saving)
        return SummarizationResult(
            citation_key=citation_key,
            success=success,
            summary_text=summary,  # Always include summary for saving
            input_chars=input_chars,
            input_words=input_words,
            output_words=output_words,
            generation_time=generation_time,
            attempts=total_attempts,
            quality_score=validation_result.score,
            validation_errors=validation_result.errors if not success else []
        )
    
    def _get_model_aware_limit(self) -> int:
        """Get model-aware max_pdf_chars limit based on model size.
        
        Automatically adjusts limits based on detected model size:
        - Small models (<7B): 50K chars max
        - Medium models (7-13B): 100K chars max
        - Large models (>13B): 200K chars max
        
        Returns:
            Maximum PDF characters to send to LLM.
        """
        # Use shared utility function for model detection
        model_size = detect_model_size(self.llm_client, None)
        
        if model_size < 7:
            # Small models: 50K chars
            logger.info(f"Detected small model ({model_size}B), using 50K char limit")
            return 50000
        elif model_size <= 13:
            # Medium models: 100K chars
            logger.info(f"Detected medium model ({model_size}B), using 100K char limit")
            return 100000
        else:
            # Large models: 200K chars
            logger.info(f"Detected large model ({model_size}B), using 200K char limit")
            return 200000
    
    @property
    @property
    def quality_validator(self) -> SummaryQualityValidator:
        """Get quality validator instance.
        
        Property alias for `self.validator` (backward compatibility).
        
        Returns:
            SummaryQualityValidator instance used for quality validation.
        """
        return self.validator
    
    def _analyze_references(self, pdf_text: str) -> Dict[str, Any]:
        """Analyze references in PDF text.
        
        Args:
            pdf_text: Extracted PDF text.
            
        Returns:
            Dictionary with reference analysis:
            {
                'count': Optional[int] - Number of references found,
                'section_found': bool - Whether references section exists,
                'section_start': Optional[int] - Character position of references section
            }
        """
        ref_info = {
            'count': None,
            'section_found': False,
            'section_start': None
        }
        
        # Look for references section header
        ref_section_patterns = [
            r'^\s*(?:References?|Bibliography|Works\s+Cited)\s*$',
            r'^#+\s*(?:References?|Bibliography)',
            r'\\begin\{thebibliography\}',
            r'\\bibliography'
        ]
        
        for pattern in ref_section_patterns:
            match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
            if match:
                ref_info['section_found'] = True
                ref_info['section_start'] = match.start()
                break
        
        # Count references using multiple patterns
        citation_patterns = [
            (r'\[(\d+)\]', lambda m: int(m.group(1))),  # [1], [2], etc.
            (r'\\cite\{[^}]+\}', lambda m: 1),  # \cite{key} - count occurrences
            (r'\\bibitem', lambda m: 1),  # \bibitem entries
        ]
        
        max_ref_num = 0
        citation_count = 0
        
        for pattern, extractor in citation_patterns:
            matches = list(re.finditer(pattern, pdf_text))
            if matches:
                if pattern == r'\[(\d+)\]':
                    # Extract numbers and find max
                    numbers = [int(m.group(1)) for m in matches if m.group(1).isdigit()]
                    if numbers:
                        max_ref_num = max(max_ref_num, max(numbers))
                else:
                    # Count occurrences
                    citation_count += len(matches)
        
        # Use max reference number if found, otherwise use citation count
        if max_ref_num > 0:
            ref_info['count'] = max_ref_num
        elif citation_count > 0:
            ref_info['count'] = citation_count
        
        return ref_info
    
    def _generate_summary(
        self,
        result: SearchResult,
        pdf_text: str,
        ref_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate summary using LLM with paper-specific prompt.
        
        This is a compatibility method that provides the same interface as PaperSummarizer.
        For tests and simple use cases, it generates a single-stage summary.
        For production, use summarize_paper() which uses multi-stage refinement.
        
        Args:
            result: Search result with paper metadata.
            pdf_text: Extracted PDF text.
            ref_info: Optional reference analysis info.
            
        Returns:
            Generated summary text.
        """
        # Store ref_info for later use
        if ref_info:
            self._last_ref_info = ref_info
        
        # Use prompt builder to create the summary prompt (compatibility with old interface)
        from infrastructure.llm.templates.research import PaperSummarization
        from infrastructure.literature.analysis.domain_detector import DomainDetector
        
        # Detect domain for context-aware prompts
        domain_detector = DomainDetector()
        domain_result = domain_detector.detect_domain(
            text=pdf_text,
            title=result.title,
            abstract=result.abstract
        )
        
        # Get domain-specific instructions
        domain_instructions = domain_detector.get_domain_specific_instructions(domain_result.domain)
        
        # Create paper summarization prompt with domain context and reference info
        template = PaperSummarization()
        prompt = template.render(
            title=result.title,
            authors=', '.join(result.authors) if result.authors else 'Unknown',
            year=str(result.year) if result.year else 'Unknown',
            source=f"{result.source} ({result.venue or 'N/A'})",
            text=pdf_text,
            domain=domain_result.domain.value if domain_result.confidence > 0.5 else None,
            domain_instructions=domain_instructions if domain_result.confidence > 0.5 else None,
            reference_count=ref_info.get('count') if ref_info else None,
            references_section_found=ref_info.get('section_found', False) if ref_info else False
        )

        # Generate summary with improved parameters
        from infrastructure.llm.core.config import GenerationOptions
        options = GenerationOptions(
            temperature=0.45,
            max_tokens=4000
        )

        summary = self.llm_client.query(prompt, options=options, reset_context=True)
        cleaned = self._clean_summary_content(summary)
        # Apply deduplication BEFORE validation so validation sees clean content
        deduplicated = self._deduplicate_summary(cleaned)
        
        return deduplicated
    
    def _clean_summary_content(self, summary: str) -> str:
        """Remove unwanted sections and content from summary.
        
        Filters out sections that shouldn't appear in final summaries:
        - References, Citation, BibTeX sections
        - Abstract section (already extracted separately)
        - Summary section (redundant)
        - Keywords, Tags sections
        - AI-generated disclaimers and notes
        
        Args:
            summary: Raw summary text from LLM.
            
        Returns:
            Cleaned summary text with unwanted sections removed.
        """
        lines = summary.split('\n')
        cleaned_lines = []
        skip_section = False

        unwanted_sections = [
            '### References',
            '### Citation',
            '### BibTex',
            '### Abstract',
            '### Summary',  # Also remove Summary section
            '### Keywords',
            '### Tags',
            'Note:',
            'Note: The above',
            'This summary was generated',
            'generated by an AI model'
        ]

        for line in lines:
            line_lower = line.lower().strip()
            # Check if this line starts an unwanted section
            # Match both "### Section" and "## Section" formats
            is_unwanted_header = False
            for unwanted in unwanted_sections:
                unwanted_lower = unwanted.lower().strip('#').strip()
                # Check if line is a header matching unwanted section
                if (line_lower.startswith('###') or line_lower.startswith('##')) and unwanted_lower in line_lower:
                    is_unwanted_header = True
                    break
            
            if is_unwanted_header:
                skip_section = True
                continue

            # Stop skipping when we hit a valid section header (not unwanted)
            if (line.startswith('### ') or line.startswith('## ')) and skip_section:
                # Check if this new section is also unwanted
                line_lower_check = line.lower().strip()
                is_also_unwanted = any(
                    unwanted.lower().strip('#').strip() in line_lower_check 
                    for unwanted in unwanted_sections
                )
                if not is_also_unwanted:
                    skip_section = False

            if not skip_section:
                cleaned_lines.append(line)

        cleaned = '\n'.join(cleaned_lines).strip()

        # Remove trailing disclaimers
        disclaimer_patterns = [
            r'Note:.*$',
            r'This summary.*$',
            r'generated by.*$'
        ]

        for pattern in disclaimer_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        return cleaned.strip()
    
    def _deduplicate_summary(self, summary: str) -> str:
        """Remove duplicate sections and paragraphs from summary.
        
        Args:
            summary: Summary text that may contain duplicates.
            
        Returns:
            Deduplicated summary text.
        """
        if not summary:
            return summary
        
        # First, remove duplicate sections at the header level
        # Group content by section to compare and remove duplicates
        lines = summary.split('\n')
        sections = []
        current_section_title = None
        current_section_content = []
        
        for line in lines:
            # Check if this is a section header
            if line.strip().startswith('###'):
                # Save previous section if any
                if current_section_title is not None:
                    sections.append((current_section_title, current_section_content))
                
                # Start new section
                current_section_title = line.strip()
                current_section_content = [line]
            else:
                if current_section_title is not None:
                    current_section_content.append(line)
                else:
                    # Content before any section - add as preamble
                    if not sections or sections[0][0] is None:
                        if not sections:
                            sections.append((None, []))
                        sections[0][1].append(line)
        
        # Add last section
        if current_section_title is not None:
            sections.append((current_section_title, current_section_content))
        
        # Deduplicate sections by title and content similarity
        # Keep first occurrence of each section, skip exact duplicates
        seen_sections = {}  # Maps normalized_title -> (section_title, section_content)
        deduplicated_sections = []
        
        for section_title, section_content in sections:
            if section_title is None:
                # Preamble - always include
                deduplicated_sections.append((None, section_content))
                continue
            
            # Normalize section title for comparison
            normalized_title = section_title.lower().strip('#').strip()
            # Get content text without the header for comparison
            content_lines = [line for line in section_content if not line.strip().startswith('###')]
            section_text = '\n'.join(content_lines).strip()
            
            # Check if we've seen this section title before
            if normalized_title in seen_sections:
                # Compare content - if identical, skip (duplicate)
                prev_title, prev_content = seen_sections[normalized_title]
                prev_content_lines = [line for line in prev_content if not line.strip().startswith('###')]
                previous_text = '\n'.join(prev_content_lines).strip()
                
                # If content is identical, it's a duplicate - skip
                if section_text == previous_text:
                    continue  # Exact duplicate, skip
                # If content is different, keep both (different content under same header)
                # This is rare but possible - same section title with different content
                deduplicated_sections.append((section_title, section_content))
            else:
                # First time seeing this section - keep it
                seen_sections[normalized_title] = (section_title, section_content)
                deduplicated_sections.append((section_title, section_content))
        
        # Reconstruct summary
        result_lines = []
        for section_title, section_content in deduplicated_sections:
            result_lines.extend(section_content)
        
        result = '\n'.join(result_lines)
        
        # Then use the deduplication from validation_repetition module for paragraph-level
        from infrastructure.llm.validation.repetition import deduplicate_sections
        
        # Use balanced mode for better paragraph deduplication
        return deduplicate_sections(
            result,
            max_repetitions=1,  # More aggressive for summaries
            mode="balanced",
            similarity_threshold=0.8,
            min_content_preservation=0.6
        )
    
    def save_summary(
        self,
        result: SearchResult,
        summary_result: SummarizationResult,
        output_dir: Path,
        pdf_path: Optional[Path] = None
    ) -> Path:
        """Save summary to markdown file with validation metadata.
        
        Saves the summary to `{citation_key}_summary.md` in the output directory.
        The saved file includes:
        - Paper metadata (title, authors, year, source, DOI)
        - Validation status and quality score
        - Validation errors (if any)
        - Generated summary text
        
        Summaries are saved even if validation failed, with clear indication
        of validation status for review purposes.

        Args:
            result: Search result with paper metadata (title, authors, year, etc.).
            summary_result: SummarizationResult to save (must have summary_text).
            output_dir: Directory for summary files (created if doesn't exist).
            pdf_path: Optional path to PDF file (for metadata tracking).

        Returns:
            Path to saved summary markdown file.

        Raises:
            FileOperationError: If summary_text is None or file writing fails.
            
        Note:
            This method always saves summaries, regardless of validation status.
            Validation metadata is included in the saved file for transparency.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        citation_key = summary_result.citation_key
        output_path = output_dir / f"{citation_key}_summary.md"

        # Check if summary text exists
        if not summary_result.summary_text:
            logger.warning(f"[{citation_key}] No summary text to save, skipping save operation")
            raise FileOperationError(
                f"No summary text to save for {citation_key}",
                context={"path": str(output_path)}
            )

        # Build validation metadata section
        validation_section = ""
        if summary_result.quality_score is not None or summary_result.validation_errors:
            validation_status = "✓ Accepted" if summary_result.success else "⚠ Rejected"
            quality_score_str = f"{summary_result.quality_score:.2f}" if summary_result.quality_score is not None else 'N/A'
            validation_section = f"""
**Validation Status:** {validation_status}
**Quality Score:** {quality_score_str}
"""
            if summary_result.validation_errors:
                validation_section += f"**Validation Errors:** {len(summary_result.validation_errors)} error(s)\n"
                for error in summary_result.validation_errors[:5]:  # Show first 5 errors
                    validation_section += f"  - {error}\n"
            validation_section += "\n"

        # Build markdown content with validation metadata
        content = f"""# {result.title}

**Authors:** {', '.join(result.authors) if result.authors else 'Unknown'}

**Year:** {result.year or 'Unknown'}

**Source:** {result.source}

**Venue:** {result.venue or 'N/A'}

**DOI:** {result.doi or 'N/A'}

**PDF:** [{citation_key}.pdf](../pdfs/{citation_key}.pdf)

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
{validation_section}---

{summary_result.summary_text}
"""

        try:
            output_path.write_text(content, encoding='utf-8')
            file_size = output_path.stat().st_size
            logger.info(f"Saved summary: {output_path.name} ({file_size:,} bytes) -> {output_path}")
            
            # Save metadata to JSON if available
            try:
                from infrastructure.literature.summarization.metadata import (
                    SummaryMetadataManager,
                    SummaryMetadata
                )
                
                metadata_path = output_dir.parent / "summaries_metadata.json"
                manager = SummaryMetadataManager(metadata_path=metadata_path)
                
                pdf_size_bytes = None
                pdf_relative_path = None
                if pdf_path and pdf_path.exists():
                    pdf_size_bytes = pdf_path.stat().st_size
                    try:
                        pdf_relative_path = str(pdf_path.relative_to(output_dir.parent.parent))
                    except ValueError:
                        pdf_relative_path = str(pdf_path)
                
                metadata = SummaryMetadata(
                    citation_key=citation_key,
                    title=result.title,
                    authors=result.authors or [],
                    year=result.year,
                    pdf_size_bytes=pdf_size_bytes,
                    pdf_path=pdf_relative_path,
                    summary_path=str(output_path.relative_to(output_dir.parent)) if output_path.exists() else None,
                    input_chars=summary_result.input_chars,
                    input_words=summary_result.input_words,
                    output_words=summary_result.output_words,
                    generation_time=summary_result.generation_time,
                    quality_score=summary_result.quality_score,
                    reference_count=self._last_ref_info.get('count') if self._last_ref_info else None
                )
                
                manager.save_metadata(metadata)
            except Exception as e:
                logger.debug(f"Failed to save summary metadata: {e}")
            
            return output_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to save summary: {e}",
                context={"path": str(output_path)}
            )
