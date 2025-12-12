"""Streaming support for summarization with periodic progress updates.

This module provides streaming wrappers that emit progress events
during LLM generation, allowing real-time feedback on summarization progress.
"""
from __future__ import annotations

import time
from typing import Callable, Optional, TYPE_CHECKING

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.summarization.models import SummarizationProgressEvent

if TYPE_CHECKING:
    from infrastructure.llm.core.client import LLMClient
    from infrastructure.llm.core.config import GenerationOptions

logger = get_logger(__name__)


def stream_with_progress(
    llm_client: "LLMClient",
    prompt: str,
    progress_callback: Optional[Callable[[SummarizationProgressEvent], None]],
    citation_key: str,
    stage: str = "draft_generation",
    update_interval: float = 5.0,
    timeout: float = 300.0,
    options: Optional["GenerationOptions"] = None
) -> str:
    """Stream LLM response with periodic progress updates.
    
    Streams the LLM response and emits progress events at regular intervals
    (default: every 5 seconds) showing accumulated characters, words, chunks,
    and elapsed time.
    
    Args:
        llm_client: LLM client instance with streaming support.
        prompt: Prompt to send to LLM.
        progress_callback: Optional callback function for progress events.
        citation_key: Citation key for the paper being processed.
        stage: Stage name ("draft_generation" or "refinement").
        update_interval: Interval in seconds between progress updates (default: 5.0).
        timeout: Maximum time to wait for response (default: 300.0).
        options: Optional generation options (temperature, max_tokens, etc.).
        
    Returns:
        Complete accumulated response text.
        
    Example:
        >>> from infrastructure.llm.core.client import LLMClient
        >>> client = LLMClient()
        >>> 
        >>> def on_progress(event):
        ...     print(f"Progress: {event.metadata['chars_received']} chars")
        >>> 
        >>> response = stream_with_progress(
        ...     client, prompt, on_progress, "paper123", "draft_generation"
        ... )
    """
    accumulated = []
    chars_received = 0
    words_received = 0
    chunks_received = 0
    start_time = time.time()
    last_update = start_time
    last_chunk_time = start_time
    last_heartbeat = start_time
    first_chunk_received = False
    heartbeat_interval = 2.5  # More frequent heartbeats (2.5s) for better feedback
    timeout_warning_threshold = timeout * 0.8  # Warn at 80% of timeout
    
    # Estimate processing time based on prompt size
    # Rough estimates: small models ~100 chars/s, medium ~200 chars/s, large ~500 chars/s
    # For prompt processing (before first token), estimate based on prompt size
    prompt_size = len(prompt)
    estimated_prompt_processing = min(prompt_size / 1000, 30.0)  # Max 30s for prompt processing
    estimated_total_time = estimated_prompt_processing + (prompt_size * 0.1) / 200  # Rough estimate for generation
    
    # Log immediate feedback that streaming is starting
    logger.info(
        f"[{citation_key}] Starting streaming for {stage}... "
        f"(timeout: {timeout:.0f}s, prompt: {prompt_size:,} chars, "
        f"estimated processing: {estimated_prompt_processing:.1f}s)"
    )
    
    # Emit initial progress event with time estimate
    if progress_callback:
        progress_callback(SummarizationProgressEvent(
            citation_key=citation_key,
            stage=stage,
            status="started",
            message=f"Processing prompt ({prompt_size:,} chars, estimated: {estimated_prompt_processing:.1f}s)...",
            metadata={
                "streaming": True,
                "elapsed_time": 0.0,
                "prompt_size": prompt_size,
                "estimated_processing_time": estimated_prompt_processing,
                "estimated_total_time": estimated_total_time
            }
        ))
    
    try:
        # Stream from LLM with generation options
        stream_kwargs = {}
        if options:
            stream_kwargs['options'] = options
        
        for chunk in llm_client.stream_query(prompt, **stream_kwargs):
            now = time.time()
            elapsed = now - start_time
            
            # Check for timeout
            if elapsed > timeout:
                raise TimeoutError(
                    f"Streaming timeout after {timeout:.1f}s. "
                    f"Received {chunks_received} chunks, {chars_received:,} chars"
                )
            
            # Warn if approaching timeout
            if elapsed >= timeout_warning_threshold and elapsed < timeout:
                remaining = timeout - elapsed
                logger.warning(
                    f"[{citation_key}] Approaching timeout: {remaining:.1f}s remaining. "
                    f"Received {chunks_received} chunks, {chars_received:,} chars so far"
                )
            
            # Handle empty chunks (waiting for response)
            if not chunk or not chunk.strip():
                # Check for heartbeat if no chunks received for a while
                if not first_chunk_received:
                    # Waiting for first chunk - more frequent heartbeats (every 2.5s)
                    if elapsed >= heartbeat_interval and now - last_heartbeat >= heartbeat_interval:
                        remaining_estimate = max(0, estimated_prompt_processing - elapsed)
                        logger.info(
                            f"[{citation_key}] Processing prompt... "
                            f"({elapsed:.1f}s elapsed, prompt: {len(prompt):,} chars, "
                            f"estimated remaining: {remaining_estimate:.1f}s)"
                        )
                        # Emit progress event
                        if progress_callback:
                            progress_callback(SummarizationProgressEvent(
                                citation_key=citation_key,
                                stage=stage,
                                status="in_progress",
                                message=f"Processing prompt... ({elapsed:.1f}s elapsed, estimated remaining: {remaining_estimate:.1f}s)",
                                metadata={
                                    "streaming": True,
                                    "elapsed_time": elapsed,
                                    "prompt_size": len(prompt),
                                    "estimated_remaining": remaining_estimate,
                                    "waiting_for_first_chunk": True
                                }
                            ))
                        last_heartbeat = now
                else:
                    # Already received chunks, less frequent heartbeats
                    if now - last_chunk_time >= heartbeat_interval * 2 and now - last_heartbeat >= heartbeat_interval * 2:
                        logger.info(
                            f"[{citation_key}] Waiting for more LLM response... "
                            f"({elapsed:.1f}s elapsed, {chunks_received} chunks, {chars_received:,} chars received so far)"
                        )
                        last_heartbeat = now
                continue
                
            # Chunk received - update tracking
            if not first_chunk_received:
                first_chunk_received = True
                time_to_first_chunk = elapsed
                logger.info(
                    f"[{citation_key}] First chunk received after {time_to_first_chunk:.2f}s "
                    f"(chunk size: {len(chunk)} chars)"
                )
                # Emit immediate progress event when first chunk arrives
                if progress_callback:
                    progress_callback(SummarizationProgressEvent(
                        citation_key=citation_key,
                        stage=stage,
                        status="in_progress",
                        message=f"LLM started generating (first chunk: {len(chunk)} chars)",
                        metadata={
                            "chars_received": len(chunk),
                            "words_received": len(chunk.split()),
                            "chunks_received": 1,
                            "elapsed_time": elapsed,
                            "streaming": True,
                            "first_chunk": True
                        }
                    ))
            
            last_chunk_time = now
            accumulated.append(chunk)
            chars_received += len(chunk)
            # Count words in this chunk
            chunk_words = len(chunk.split())
            words_received += chunk_words
            chunks_received += 1
            
            # Calculate chunk rate for monitoring
            if elapsed > 0:
                chars_per_sec = chars_received / elapsed
                chunks_per_sec = chunks_received / elapsed
            else:
                chars_per_sec = 0.0
                chunks_per_sec = 0.0
            
            # Emit progress every update_interval seconds
            if now - last_update >= update_interval:
                if progress_callback:
                    progress_callback(SummarizationProgressEvent(
                        citation_key=citation_key,
                        stage=stage,
                        status="in_progress",
                        message=f"Streaming: {chars_received:,} chars, {words_received:,} words ({elapsed:.1f}s elapsed, {chars_per_sec:.1f} chars/s)",
                        metadata={
                            "chars_received": chars_received,
                            "words_received": words_received,
                            "chunks_received": chunks_received,
                            "elapsed_time": elapsed,
                            "chars_per_sec": chars_per_sec,
                            "chunks_per_sec": chunks_per_sec,
                            "streaming": True
                        }
                    ))
                
                logger.info(
                    f"[{citation_key}] Streaming progress: {chars_received:,} chars, "
                    f"{words_received:,} words, {chunks_received} chunks "
                    f"({elapsed:.1f}s, {chars_per_sec:.1f} chars/s, {chunks_per_sec:.2f} chunks/s)"
                )
                last_update = now
                last_heartbeat = now  # Reset heartbeat timer on progress update
        
        # Emit final progress event
        final_elapsed = time.time() - start_time
        
        # Join all chunks into final text
        full_response = "".join(accumulated)
        
        # Validate response is non-empty
        if not full_response or not full_response.strip():
            error_msg = f"Empty response received from LLM after {final_elapsed:.2f}s ({chunks_received} chunks)"
            logger.error(f"[{citation_key}] {error_msg}")
            if progress_callback:
                progress_callback(SummarizationProgressEvent(
                    citation_key=citation_key,
                    stage=stage,
                    status="failed",
                    message=error_msg,
                    metadata={
                        "chars_received": chars_received,
                        "words_received": words_received,
                        "chunks_received": chunks_received,
                        "elapsed_time": final_elapsed,
                        "error": "empty_response"
                    }
                ))
            raise ValueError(error_msg)
        
        # Calculate final rates
        if final_elapsed > 0:
            final_chars_per_sec = len(full_response) / final_elapsed
            final_words_per_sec = len(full_response.split()) / final_elapsed
        else:
            final_chars_per_sec = 0.0
            final_words_per_sec = 0.0
        
        if progress_callback:
            progress_callback(SummarizationProgressEvent(
                citation_key=citation_key,
                stage=stage,
                status="completed",
                message=f"Streaming completed: {len(full_response):,} chars, {len(full_response.split()):,} words ({final_elapsed:.1f}s)",
                metadata={
                    "chars_received": len(full_response),
                    "words_received": len(full_response.split()),
                    "chunks_received": chunks_received,
                    "elapsed_time": final_elapsed,
                    "chars_per_sec": final_chars_per_sec,
                    "words_per_sec": final_words_per_sec,
                    "streaming": True,
                    "final": True
                }
            ))
        
        logger.info(
            f"[{citation_key}] Streaming completed: {len(full_response):,} chars, "
            f"{len(full_response.split()):,} words, {chunks_received} chunks "
            f"({final_elapsed:.2f}s, {final_chars_per_sec:.1f} chars/s, {final_words_per_sec:.1f} words/s)"
        )
        
        return full_response
        
    except Exception as e:
        elapsed = time.time() - start_time
        import traceback
        
        # Enhanced error logging with context
        error_context = {
            "elapsed_time": elapsed,
            "chunks_received": chunks_received,
            "chars_received": chars_received,
            "words_received": words_received,
            "first_chunk_received": first_chunk_received,
            "prompt_size": len(prompt)
        }
        
        logger.error(
            f"[{citation_key}] Streaming failed after {elapsed:.2f}s: {e}\n"
            f"Context: {error_context}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        if progress_callback:
            progress_callback(SummarizationProgressEvent(
                citation_key=citation_key,
                stage=stage,
                status="failed",
                message=f"Streaming failed: {e}",
                metadata={
                    "chars_received": chars_received,
                    "words_received": words_received,
                    "chunks_received": chunks_received,
                    "elapsed_time": elapsed,
                    "first_chunk_received": first_chunk_received,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ))
        
        raise


