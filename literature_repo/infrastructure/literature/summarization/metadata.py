"""Summary metadata management for literature summaries.

This module provides functionality to manage summary metadata in a centralized
JSON file, keeping summaries clean and standalone while maintaining detailed
statistics and quality information.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Any

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import FileOperationError

logger = get_logger(__name__)


@dataclass
class SummaryMetadata:
    """Metadata for a single paper summary.
    
    Attributes:
        citation_key: Unique identifier for the paper.
        input_words: Number of words in extracted PDF text.
        input_chars: Number of characters in extracted PDF text.
        output_words: Number of words in generated summary.
        compression_ratio: Output/input word ratio.
        generation_time: Time taken for summarization in seconds.
        words_per_second: Generation speed.
        quality_score: Quality validation score (0.0 to 1.0).
        validation_errors: List of quality validation issues.
        attempts: Number of generation attempts.
        generated: Timestamp when summary was generated.
        pdf_path: Path to PDF file (relative to literature/).
        pdf_size_bytes: Size of PDF file in bytes.
        truncated: Whether PDF text was truncated.
    """
    citation_key: str
    input_words: int
    input_chars: int
    output_words: int
    compression_ratio: float
    generation_time: float
    words_per_second: float
    quality_score: float
    validation_errors: list[str]
    attempts: int
    generated: str
    pdf_path: Optional[str] = None
    pdf_size_bytes: Optional[int] = None
    truncated: bool = False
    reference_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class SummaryMetadataManager:
    """Manages summary metadata in a centralized JSON file.
    
    Provides methods to read, write, and update summary metadata.
    """
    
    def __init__(self, metadata_path: Optional[Path] = None):
        """Initialize metadata manager.
        
        Args:
            metadata_path: Path to metadata JSON file. Defaults to 
                         data/summaries_metadata.json.
        """
        if metadata_path is None:
            # Default to data/summaries_metadata.json
            metadata_path = Path("data/summaries_metadata.json")
        
        self.metadata_path = Path(metadata_path)
        self._metadata: Dict[str, SummaryMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata from JSON file."""
        if not self.metadata_path.exists():
            logger.debug(f"Metadata file does not exist yet: {self.metadata_path}")
            return
        
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to SummaryMetadata objects
            for key, meta_dict in data.items():
                try:
                    self._metadata[key] = SummaryMetadata(**meta_dict)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {key}: {e}")
            
            logger.debug(f"Loaded metadata for {len(self._metadata)} summaries")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            # Start with empty metadata
            self._metadata = {}
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self._metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        try:
            # Ensure directory exists
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict for JSON serialization
            data = {
                key: meta.to_dict() 
                for key, meta in self._metadata.items()
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved metadata for {len(self._metadata)} summaries to {self.metadata_path}")
        except Exception as e:
            raise FileOperationError(
                f"Failed to save metadata: {e}",
                context={"path": str(self.metadata_path)}
            )
    
    def add_metadata(self, metadata: SummaryMetadata) -> None:
        """Add or update metadata for a summary.
        
        Args:
            metadata: Summary metadata to add/update.
        """
        self._metadata[metadata.citation_key] = metadata
        self._save_metadata()
    
    def get_metadata(self, citation_key: str) -> Optional[SummaryMetadata]:
        """Get metadata for a citation key.
        
        Args:
            citation_key: Citation key to look up.
            
        Returns:
            SummaryMetadata if found, None otherwise.
        """
        return self._metadata.get(citation_key)
    
    def get_all_metadata(self) -> Dict[str, SummaryMetadata]:
        """Get all metadata.
        
        Returns:
            Dictionary mapping citation keys to metadata.
        """
        return self._metadata.copy()
    
    def remove_metadata(self, citation_key: str) -> None:
        """Remove metadata for a citation key.
        
        Args:
            citation_key: Citation key to remove.
        """
        if citation_key in self._metadata:
            del self._metadata[citation_key]
            self._save_metadata()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics across all summaries.
        
        Returns:
            Dictionary with aggregate statistics.
        """
        if not self._metadata:
            return {
                "total_summaries": 0,
                "avg_quality_score": 0.0,
                "avg_compression_ratio": 0.0,
                "avg_generation_time": 0.0,
                "total_input_words": 0,
                "total_output_words": 0
            }
        
        total = len(self._metadata)
        quality_scores = [m.quality_score for m in self._metadata.values() if m.quality_score > 0]
        compression_ratios = [m.compression_ratio for m in self._metadata.values() if m.compression_ratio > 0]
        generation_times = [m.generation_time for m in self._metadata.values() if m.generation_time > 0]
        
        return {
            "total_summaries": total,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
            "avg_compression_ratio": sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0.0,
            "avg_generation_time": sum(generation_times) / len(generation_times) if generation_times else 0.0,
            "total_input_words": sum(m.input_words for m in self._metadata.values()),
            "total_output_words": sum(m.output_words for m in self._metadata.values())
        }


