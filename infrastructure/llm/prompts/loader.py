"""Prompt fragment loader for JSON/YAML prompt files.

Loads prompt fragments, templates, and compositions from JSON files
with caching and validation support.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMTemplateError

logger = get_logger(__name__)


class PromptFragmentLoader:
    """Loads prompt fragments from JSON/YAML files with caching.
    
    Supports fragment references like "file.json#key" to load specific
    sections from JSON files.
    
    Example:
        >>> loader = PromptFragmentLoader()
        >>> system_prompt = loader.load_fragment("system_prompts.json#manuscript_review")
        >>> template = loader.load_template("manuscript_reviews.json#manuscript_executive_summary")
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize fragment loader.
        
        Args:
            base_path: Base path for prompt files. If None, uses default
                      infrastructure/llm/prompts/ directory.
        """
        if base_path is None:
            # Get path relative to this file
            this_file = Path(__file__)
            base_path = this_file.parent
        
        self.base_path = Path(base_path)
        self._fragment_cache: Dict[str, Any] = {}
        self._template_cache: Dict[str, Any] = {}
    
    def _resolve_path(self, filename: str, subdirectory: str = "fragments") -> Path:
        """Resolve path to a prompt file.
        
        Args:
            filename: Filename (e.g., "system_prompts.json")
            subdirectory: Subdirectory within prompts/ (fragments, templates, compositions)
            
        Returns:
            Resolved Path object
        """
        return self.base_path / subdirectory / filename
    
    def _load_json_file(self, filepath: Path) -> Dict[str, Any]:
        """Load and parse JSON file with caching.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Parsed JSON content as dict
            
        Raises:
            LLMTemplateError: If file cannot be loaded or parsed
        """
        filepath_str = str(filepath)
        
        # Check cache
        if filepath_str in self._fragment_cache:
            return self._fragment_cache[filepath_str]
        
        if not filepath.exists():
            raise LLMTemplateError(
                f"Prompt file not found: {filepath}",
                context={"filepath": str(filepath)}
            )
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cache the loaded data
            self._fragment_cache[filepath_str] = data
            return data
            
        except json.JSONDecodeError as e:
            raise LLMTemplateError(
                f"Invalid JSON in prompt file: {filepath}",
                context={"error": str(e), "filepath": str(filepath)}
            )
        except Exception as e:
            raise LLMTemplateError(
                f"Failed to load prompt file: {filepath}",
                context={"error": str(e), "filepath": str(filepath)}
            )
    
    def _resolve_reference(self, reference: str, subdirectory: str = "fragments") -> Any:
        """Resolve a fragment reference like "file.json#key".
        
        Args:
            reference: Reference string (e.g., "system_prompts.json#manuscript_review")
            subdirectory: Subdirectory to search in
            
        Returns:
            Resolved fragment value
            
        Raises:
            LLMTemplateError: If reference cannot be resolved
        """
        if "#" in reference:
            filename, key = reference.split("#", 1)
            filepath = self._resolve_path(filename, subdirectory)
            data = self._load_json_file(filepath)
            
            # Navigate nested keys (e.g., "key1.key2")
            keys = key.split(".")
            value = data
            for k in keys:
                if not isinstance(value, dict) or k not in value:
                    raise LLMTemplateError(
                        f"Key '{key}' not found in {filename}",
                        context={"filename": filename, "key": key, "available_keys": list(data.keys()) if isinstance(data, dict) else []}
                    )
                value = value[k]
            
            return value
        else:
            # No key specified, return entire file
            filepath = self._resolve_path(reference, subdirectory)
            return self._load_json_file(filepath)
    
    def load_fragment(self, reference: str) -> Any:
        """Load a prompt fragment.
        
        Args:
            reference: Fragment reference (e.g., "system_prompts.json#manuscript_review")
            
        Returns:
            Fragment content (string, dict, or other JSON value)
            
        Example:
            >>> loader = PromptFragmentLoader()
            >>> prompt = loader.load_fragment("system_prompts.json#manuscript_review")
        """
        return self._resolve_reference(reference, subdirectory="fragments")
    
    def load_template(self, reference: str) -> Dict[str, Any]:
        """Load a template definition.
        
        Args:
            reference: Template reference (e.g., "manuscript_reviews.json#manuscript_executive_summary")
            
        Returns:
            Template definition dict
            
        Example:
            >>> loader = PromptFragmentLoader()
            >>> template = loader.load_template("manuscript_reviews.json#manuscript_executive_summary")
        """
        return self._resolve_reference(reference, subdirectory="templates")
    
    def load_composition(self, reference: str) -> Any:
        """Load a composition rule.
        
        Args:
            reference: Composition reference (e.g., "retry_prompts.json#off_topic_reinforcement")
            
        Returns:
            Composition content
            
        Example:
            >>> loader = PromptFragmentLoader()
            >>> retry_prompt = loader.load_composition("retry_prompts.json#off_topic_reinforcement")
        """
        return self._resolve_reference(reference, subdirectory="compositions")
    
    def get_system_prompt(self, prompt_name: str = "manuscript_review") -> str:
        """Get a system prompt by name.
        
        Args:
            prompt_name: Name of system prompt (default: "manuscript_review")
            
        Returns:
            System prompt content string
        """
        fragment = self.load_fragment(f"system_prompts.json#{prompt_name}")
        
        # Handle both direct string and dict with "content" key
        if isinstance(fragment, dict):
            return fragment.get("content", str(fragment))
        return str(fragment)
    
    def clear_cache(self) -> None:
        """Clear the fragment cache."""
        self._fragment_cache.clear()
        self._template_cache.clear()


# Global loader instance for convenience
_default_loader: Optional[PromptFragmentLoader] = None


def get_default_loader() -> PromptFragmentLoader:
    """Get the default global fragment loader instance.
    
    Returns:
        PromptFragmentLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptFragmentLoader()
    return _default_loader












