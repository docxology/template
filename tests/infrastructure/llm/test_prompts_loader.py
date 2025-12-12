"""Tests for prompt fragment loader."""
import json
import tempfile
from pathlib import Path

import pytest

from infrastructure.llm.prompts.loader import PromptFragmentLoader
from infrastructure.core.exceptions import LLMTemplateError


class TestPromptFragmentLoader:
    """Test prompt fragment loading functionality."""
    
    def test_load_fragment_simple(self, tmp_path):
        """Test loading a simple fragment from JSON."""
        # Create test JSON file
        test_data = {
            "test_key": "test_value",
            "nested": {
                "key": "nested_value"
            }
        }
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.load_fragment("test.json")
        
        assert result == test_data
    
    def test_load_fragment_with_key(self, tmp_path):
        """Test loading a fragment with key reference."""
        test_data = {
            "key1": "value1",
            "key2": "value2"
        }
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.load_fragment("test.json#key1")
        
        assert result == "value1"
    
    def test_load_fragment_nested_key(self, tmp_path):
        """Test loading a fragment with nested key reference."""
        test_data = {
            "level1": {
                "level2": {
                    "value": "nested_value"
                }
            }
        }
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.load_fragment("test.json#level1.level2.value")
        
        assert result == "nested_value"
    
    def test_load_fragment_not_found(self, tmp_path):
        """Test loading a non-existent fragment."""
        loader = PromptFragmentLoader(base_path=tmp_path)
        
        with pytest.raises(LLMTemplateError) as exc_info:
            loader.load_fragment("nonexistent.json")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_fragment_invalid_key(self, tmp_path):
        """Test loading a fragment with invalid key."""
        test_data = {"key1": "value1"}
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        
        with pytest.raises(LLMTemplateError) as exc_info:
            loader.load_fragment("test.json#invalid_key")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_template(self, tmp_path):
        """Test loading a template definition."""
        template_data = {
            "template1": {
                "version": "1.0",
                "base_template": "Test template ${var}"
            }
        }
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        test_file = templates_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(template_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.load_template("test.json#template1")
        
        assert result["version"] == "1.0"
        assert "base_template" in result
    
    def test_get_system_prompt(self, tmp_path):
        """Test getting a system prompt by name."""
        system_prompts = {
            "test_prompt": {
                "version": "1.0",
                "content": "You are a test assistant."
            }
        }
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "system_prompts.json"
        with open(test_file, 'w') as f:
            json.dump(system_prompts, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.get_system_prompt("test_prompt")
        
        assert result == "You are a test assistant."
    
    def test_get_system_prompt_dict_content(self, tmp_path):
        """Test getting system prompt when content is in dict."""
        system_prompts = {
            "test_prompt": {
                "version": "1.0",
                "content": "You are a test assistant."
            }
        }
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "system_prompts.json"
        with open(test_file, 'w') as f:
            json.dump(system_prompts, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.get_system_prompt("test_prompt")
        
        assert isinstance(result, str)
        assert "test assistant" in result
    
    def test_cache_loading(self, tmp_path):
        """Test that fragments are cached after first load."""
        test_data = {"key": "value"}
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        
        # First load
        result1 = loader.load_fragment("test.json")
        
        # Modify file
        test_data["key"] = "modified"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Second load should use cache
        result2 = loader.load_fragment("test.json")
        
        # Should still have original value due to caching
        assert result1 == result2
        assert result2["key"] == "value"
    
    def test_clear_cache(self, tmp_path):
        """Test clearing the fragment cache."""
        test_data = {"key": "value"}
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        test_file = fragments_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        
        # Load and cache
        loader.load_fragment("test.json")
        
        # Modify file
        test_data["key"] = "modified"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Clear cache
        loader.clear_cache()
        
        # Load again should get new value
        result = loader.load_fragment("test.json")
        assert result["key"] == "modified"
    
    def test_load_composition(self, tmp_path):
        """Test loading a composition rule."""
        composition_data = {
            "retry_prompt": {
                "version": "1.0",
                "content": "Retry instructions"
            }
        }
        compositions_dir = tmp_path / "compositions"
        compositions_dir.mkdir()
        test_file = compositions_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(composition_data, f)
        
        loader = PromptFragmentLoader(base_path=tmp_path)
        result = loader.load_composition("test.json#retry_prompt")
        
        assert result["content"] == "Retry instructions"












