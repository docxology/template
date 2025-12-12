#!/usr/bin/env python3
"""Tests for infrastructure/config_loader.py"""

import os
import sys
from pathlib import Path
import pytest

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

from infrastructure.core.config_loader import (
    load_config,
    format_author_details,
    format_author_name,
    get_config_as_dict,
    get_config_as_env_vars,
    find_config_file,
    get_translation_languages,
    YAML_AVAILABLE,
)


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        'paper': {
            'title': 'Test Paper Title',
            'version': '1.0'
        },
        'authors': [
            {
                'name': 'Dr. Jane Smith',
                'orcid': '0000-0000-0000-1234',
                'email': 'jane@example.com',
                'corresponding': True
            },
            {
                'name': 'Dr. John Doe',
                'orcid': '0000-0000-0000-5678',
                'email': 'john@example.com'
            }
        ],
        'publication': {
            'doi': '10.5281/zenodo.12345678'
        }
    }


class TestLoadConfig:
    """Test load_config function."""
    
    def test_load_valid_config(self, tmp_path, sample_config):
        """Test loading a valid config file."""
        import yaml
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        result = load_config(config_file)
        
        assert result is not None
        assert result['paper']['title'] == 'Test Paper Title'
        assert len(result['authors']) == 2
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading nonexistent file returns None."""
        result = load_config(tmp_path / "nonexistent.yaml")
        
        assert result is None
    
    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML returns None."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")
        
        result = load_config(config_file)
        
        assert result is None
    
    def test_load_empty_file(self, tmp_path):
        """Test loading empty file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        result = load_config(config_file)
        
        # Empty YAML file should return None
        assert result is None


class TestFormatAuthorDetails:
    """Test format_author_details function."""
    
    def test_format_with_corresponding_author(self):
        """Test formatting with corresponding author."""
        authors = [
            {'name': 'John', 'orcid': '0000', 'email': 'john@example.com'},
            {'name': 'Jane', 'orcid': '1111', 'email': 'jane@example.com', 'corresponding': True}
        ]
        
        result = format_author_details(authors, doi='10.1234/test')
        
        assert 'ORCID: 1111' in result
        assert 'Email: jane@example.com' in result
        assert 'DOI: 10.1234/test' in result
        assert '\\\\ ' in result  # LaTeX line breaks (two backslashes + space)
    
    def test_format_without_corresponding_uses_first(self):
        """Test formatting uses first author if no corresponding author."""
        authors = [
            {'name': 'John', 'orcid': '0000', 'email': 'john@example.com'},
            {'name': 'Jane', 'orcid': '1111', 'email': 'jane@example.com'}
        ]
        
        result = format_author_details(authors)
        
        assert 'ORCID: 0000' in result
        assert 'Email: john@example.com' in result
    
    def test_format_without_doi(self):
        """Test formatting without DOI."""
        authors = [{'name': 'John', 'orcid': '0000', 'email': 'john@example.com'}]
        
        result = format_author_details(authors)
        
        assert 'DOI' not in result
        assert 'ORCID: 0000' in result
    
    def test_format_empty_authors(self):
        """Test formatting with empty authors list."""
        result = format_author_details([])
        
        assert result == ""
    
    def test_format_partial_info(self):
        """Test formatting with partial author information."""
        authors = [{'name': 'John'}]  # No orcid or email
        
        result = format_author_details(authors)
        
        assert result == ""


class TestFormatAuthorName:
    """Test format_author_name function."""
    
    def test_format_single_author(self):
        """Test formatting single author name."""
        authors = [{'name': 'Dr. Jane Smith'}]
        
        result = format_author_name(authors)
        
        assert result == 'Dr. Jane Smith'
    
    def test_format_multiple_authors(self):
        """Test formatting multiple authors returns first."""
        authors = [
            {'name': 'Dr. Jane Smith'},
            {'name': 'Dr. John Doe'}
        ]
        
        result = format_author_name(authors)
        
        assert result == 'Dr. Jane Smith'
    
    def test_format_empty_authors(self):
        """Test formatting empty authors list."""
        result = format_author_name([])
        
        assert result == 'Project Author'
    
    def test_format_author_without_name(self):
        """Test formatting author without name field."""
        authors = [{'email': 'test@example.com'}]  # No name
        
        result = format_author_name(authors)
        
        assert result == 'Project Author'


class TestGetConfigAsDict:
    """Test get_config_as_dict function."""
    
    def test_get_full_config(self, tmp_path, sample_config):
        """Test getting full configuration as dictionary."""
        import yaml
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        result = get_config_as_dict(tmp_path)
        
        assert result['PROJECT_TITLE'] == 'Test Paper Title'
        assert result['AUTHOR_NAME'] == 'Dr. Jane Smith'
        assert result['AUTHOR_ORCID'] == '0000-0000-0000-1234'
        assert result['AUTHOR_EMAIL'] == 'jane@example.com'
        assert result['DOI'] == '10.5281/zenodo.12345678'
        assert 'AUTHOR_DETAILS' in result
    
    def test_get_config_no_file(self, tmp_path):
        """Test getting config when no file exists."""
        result = get_config_as_dict(tmp_path)
        
        assert result == {}
    
    def test_get_config_minimal(self, tmp_path):
        """Test getting config with minimal information."""
        import yaml
        config = {'paper': {'title': 'Test'}}
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_config_as_dict(tmp_path)
        
        assert result == {'PROJECT_TITLE': 'Test'}


class TestGetConfigAsEnvVars:
    """Test get_config_as_env_vars function."""
    
    def test_respects_existing_env_vars(self, tmp_path, sample_config, monkeypatch):
        """Test that existing environment variables are respected."""
        import yaml
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        monkeypatch.setenv('PROJECT_TITLE', 'Existing Title')
        
        result = get_config_as_env_vars(tmp_path, respect_existing=True)
        
        assert 'PROJECT_TITLE' not in result  # Existing env var should be respected
        assert 'AUTHOR_NAME' in result  # But other vars should be present
    
    def test_ignores_existing_env_vars(self, tmp_path, sample_config, monkeypatch):
        """Test not respecting existing environment variables."""
        import yaml
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        monkeypatch.setenv('PROJECT_TITLE', 'Existing Title')
        
        result = get_config_as_env_vars(tmp_path, respect_existing=False)
        
        assert result['PROJECT_TITLE'] == 'Test Paper Title'  # Config value, not env var


class TestFindConfigFile:
    """Test find_config_file function."""
    
    def test_finds_project_manuscript_config(self, tmp_path):
        """Test finding config in project/manuscript/."""
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("test: content")
        
        result = find_config_file(tmp_path)
        
        assert result == config_file
    
    def test_returns_none_when_not_found(self, tmp_path):
        """Test returns None when config file not found."""
        result = find_config_file(tmp_path)
        
        assert result is None


class TestIntegration:
    """Integration tests for config loading workflow."""
    
    def test_complete_workflow(self, tmp_path):
        """Test complete config loading workflow."""
        import yaml
        
        # Create config file
        config = {
            'paper': {'title': 'Integration Test'},
            'authors': [{'name': 'Test Author', 'orcid': '0000', 'email': 'test@example.com'}]
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Test finding config
        found_file = find_config_file(tmp_path)
        assert found_file is not None
        
        # Test loading config
        loaded_config = load_config(found_file)
        assert loaded_config is not None
        
        # Test converting to dict
        config_dict = get_config_as_dict(tmp_path)
        assert config_dict['PROJECT_TITLE'] == 'Integration Test'
        assert config_dict['AUTHOR_NAME'] == 'Test Author'


class TestGetTranslationLanguages:
    """Test get_translation_languages function."""
    
    def test_returns_empty_when_no_config(self, tmp_path):
        """Test returns empty list when config file doesn't exist."""
        result = get_translation_languages(tmp_path)
        assert result == []
    
    def test_returns_empty_when_translations_disabled(self, tmp_path):
        """Test returns empty list when translations are disabled."""
        import yaml
        config = {
            'llm': {
                'translations': {
                    'enabled': False,
                    'languages': ['zh', 'hi', 'ru']
                }
            }
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_translation_languages(tmp_path)
        assert result == []
    
    def test_returns_empty_when_no_llm_section(self, tmp_path):
        """Test returns empty list when no llm section in config."""
        import yaml
        config = {
            'paper': {'title': 'Test'}
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_translation_languages(tmp_path)
        assert result == []
    
    def test_returns_languages_when_enabled(self, tmp_path):
        """Test returns language list when translations are enabled."""
        import yaml
        config = {
            'llm': {
                'translations': {
                    'enabled': True,
                    'languages': ['zh', 'hi', 'ru']
                }
            }
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_translation_languages(tmp_path)
        assert result == ['zh', 'hi', 'ru']
    
    def test_returns_single_language(self, tmp_path):
        """Test returns single language when only one configured."""
        import yaml
        config = {
            'llm': {
                'translations': {
                    'enabled': True,
                    'languages': ['zh']
                }
            }
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_translation_languages(tmp_path)
        assert result == ['zh']
    
    def test_returns_empty_for_invalid_languages_type(self, tmp_path):
        """Test returns empty list when languages is not a list."""
        import yaml
        config = {
            'llm': {
                'translations': {
                    'enabled': True,
                    'languages': 'zh'  # String instead of list
                }
            }
        }
        config_file = tmp_path / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = get_translation_languages(tmp_path)
        assert result == []
    
