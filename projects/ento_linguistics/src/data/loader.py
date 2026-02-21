"""Data loading utilities for Ento-Linguistic analysis.

This module provides functionality for loading real entomological text corpora
from local storage or external sources, replacing synthetic generation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

__all__ = [
    "DataLoader",
]


class DataLoader:
    """Load and validate entomological text corpora."""
    
    def __init__(self, data_root: Optional[Union[str, Path]] = None):
        """Initialize data loader.
        
        Args:
            data_root: Root directory for data storage. If None, tries to find
                      project data directory relative to this file.
        """
        if data_root is None:
            # Default to ../../../data relative to src/data/loader.py
            self.data_root = Path(__file__).resolve().parent.parent.parent / "data"
        else:
            self.data_root = Path(data_root)
            
    def load_corpus(self, filename: str = "corpus/abstracts.json") -> List[str]:
        """Load text corpus from JSON file.
        
        Args:
            filename: Path to JSON file relative to data_root
            
        Returns:
            List of text strings
            
        Raises:
            FileNotFoundError: If corpus file doesn't exist
            ValueError: If corpus format is invalid
        """
        file_path = self.data_root / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Corpus file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            # Verify list of strings
            texts = [str(item) for item in data if item]
            logger.info(f"Loaded {len(texts)} texts from {file_path}")
            return texts
        elif isinstance(data, dict) and "abstracts" in data:
            # Handle structured format
            texts = [str(item) for item in data["abstracts"] if item]
            logger.info(f"Loaded {len(texts)} texts from {file_path}")
            return texts
        else:
            raise ValueError(f"Invalid corpus format in {file_path}. Expected list or dict with 'abstracts' key.")

    def save_corpus(self, texts: List[str], filename: str = "corpus/custom_corpus.json") -> Path:
        """Save text corpus to JSON file.
        
        Args:
            texts: List of text strings
            filename: Output filename relative to data_root
            
        Returns:
            Path to saved file
        """
        file_path = self.data_root / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(texts, f, indent=2)
            
        logger.info(f"Saved {len(texts)} texts to {file_path}")
        return file_path
