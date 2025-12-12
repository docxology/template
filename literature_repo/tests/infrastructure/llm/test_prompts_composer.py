"""Tests for prompt composer."""
import json
import tempfile
from pathlib import Path

import pytest

from infrastructure.llm.prompts.loader import PromptFragmentLoader
from infrastructure.llm.prompts.composer import PromptComposer
from infrastructure.core.exceptions import LLMTemplateError


class TestPromptComposer:
    """Test prompt composition functionality."""
    
    @pytest.fixture
    def setup_prompts(self, tmp_path):
        """Set up test prompt files."""
        # Create fragments
        fragments_dir = tmp_path / "fragments"
        fragments_dir.mkdir()
        
        # System prompts
        system_prompts = {
            "test_prompt": {
                "version": "1.0",
                "content": "You are a test assistant."
            }
        }
        with open(fragments_dir / "system_prompts.json", 'w') as f:
            json.dump(system_prompts, f)
        
        # Format requirements
        format_req = {
            "base_template": "FORMAT REQUIREMENTS:\n\n1. Use markdown\n2. Headers:\n${headers_list}\n\n${section_requirements_block}",
            "section_requirements_template": "3. Requirements:\n${requirements_list}"
        }
        with open(fragments_dir / "format_requirements.json", 'w') as f:
            json.dump(format_req, f)
        
        # Content requirements
        content_req = {
            "base_template": "CONTENT REQUIREMENTS:\n\n${no_hallucination_block}\n${cite_sources_block}",
            "no_hallucination": "1. NO HALLUCINATION: Only use provided content",
            "cite_sources": "2. CITE SOURCES: Reference specific sections"
        }
        with open(fragments_dir / "content_requirements.json", 'w') as f:
            json.dump(content_req, f)
        
        # Section structures
        section_structures = {
            "test_template": {
                "headers": ["## Section1", "## Section2"],
                "descriptions": {
                    "## Section1": "First section (50-100 words)",
                    "## Section2": "Second section (50-100 words)"
                },
                "word_targets": {
                    "Section1": [50, 100],
                    "Section2": [50, 100]
                }
            }
        }
        with open(fragments_dir / "section_structures.json", 'w') as f:
            json.dump(section_structures, f)
        
        # Token budget
        token_budget = {
            "base_template": "TOKEN BUDGET:\n\n${total_tokens_block}\n${section_budgets_block}",
            "total_tokens_template": "1. Total: ${total_tokens} tokens",
            "section_budgets_template": "2. Per section:\n${budgets_list}"
        }
        with open(fragments_dir / "token_budget_awareness.json", 'w') as f:
            json.dump(token_budget, f)
        
        # Validation hints
        validation_hints = {
            "base_template": "VALIDATION:\n\n${word_count_block}\n${required_elements_block}",
            "word_count_template": "1. Word count: ${min_words}-${max_words}",
            "required_elements_template": "2. Required:\n${elements_list}"
        }
        with open(fragments_dir / "validation_hints.json", 'w') as f:
            json.dump(validation_hints, f)
        
        # Create templates
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        template_def = {
            "test_template": {
                "version": "1.0",
                "base_template": "=== CONTENT ===\n\n${text}\n\n=== END ===\n\nTASK: ${task}\n\n${format_requirements}\n\n${section_structure}\n\n${token_budget_awareness}\n\n${content_requirements}\n\n${validation_hints}",
                "fragments": {
                    "format_requirements": "format_requirements.json",
                    "section_structure": "section_structures.json#test_template",
                    "token_budget_awareness": "token_budget_awareness.json",
                    "content_requirements": "content_requirements.json",
                    "validation_hints": "validation_hints.json"
                },
                "variables": {
                    "task": "Test task",
                    "word_count_range": [100, 200],
                    "required_elements": ["Section1", "Section2"]
                },
                "section_config": {
                    "structure_key": "test_template",
                    "token_allocation": "equal",
                    "sections": 2
                }
            }
        }
        with open(templates_dir / "test_templates.json", 'w') as f:
            json.dump(template_def, f)
        
        # Create compositions
        compositions_dir = tmp_path / "compositions"
        compositions_dir.mkdir()
        
        retry_prompts = {
            "off_topic_reinforcement": {
                "version": "1.0",
                "content": "IMPORTANT: Review the actual content.\n\n"
            }
        }
        with open(compositions_dir / "retry_prompts.json", 'w') as f:
            json.dump(retry_prompts, f)
        
        return tmp_path
    
    def test_compose_template_basic(self, setup_prompts):
        """Test basic template composition."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer.compose_template(
            "test_templates.json#test_template",
            text="Test content here"
        )
        
        assert "=== CONTENT ===" in result
        assert "Test content here" in result
        assert "FORMAT REQUIREMENTS" in result
        assert "SECTION STRUCTURE" in result
        assert "## Section1" in result
        assert "## Section2" in result
    
    def test_compose_template_with_max_tokens(self, setup_prompts):
        """Test template composition with token budget."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer.compose_template(
            "test_templates.json#test_template",
            text="Test content",
            max_tokens=1000
        )
        
        assert "TOKEN BUDGET" in result
        assert "1000" in result
    
    def test_compose_template_missing_required_var(self, setup_prompts):
        """Test template composition with missing required variable."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        # text is required but not provided
        with pytest.raises(Exception):  # Should raise error during template substitution
            composer.compose_template(
                "test_templates.json#test_template"
            )
    
    def test_add_retry_prompt_off_topic(self, setup_prompts):
        """Test adding retry prompt for off-topic."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        base_prompt = "Original prompt here"
        result = composer.add_retry_prompt(base_prompt, retry_type="off_topic")
        
        assert "IMPORTANT: Review the actual content" in result
        assert base_prompt in result
        assert result.startswith("IMPORTANT")
    
    def test_add_retry_prompt_format_enforcement(self, setup_prompts):
        """Test adding format enforcement retry prompt."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        base_prompt = "Original prompt"
        result = composer.add_retry_prompt(base_prompt, retry_type="format_enforcement")
        
        # Format enforcement is template-specific, should return unchanged
        assert result == base_prompt
    
    def test_build_format_requirements(self, setup_prompts):
        """Test building format requirements fragment."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer._build_format_requirements(
            ["## Header1", "## Header2"]
        )
        
        assert "FORMAT REQUIREMENTS" in result
        assert "## Header1" in result
        assert "## Header2" in result
    
    def test_build_content_requirements(self, setup_prompts):
        """Test building content requirements fragment."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer._build_content_requirements()
        
        assert "CONTENT REQUIREMENTS" in result
        assert "NO HALLUCINATION" in result
        assert "CITE SOURCES" in result
    
    def test_build_section_structure(self, setup_prompts):
        """Test building section structure fragment."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer._build_section_structure("test_template")
        
        assert "SECTION STRUCTURE" in result
        assert "## Section1" in result
        assert "## Section2" in result
        assert "First section" in result
    
    def test_build_section_structure_not_found(self, setup_prompts):
        """Test building section structure with invalid key."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        with pytest.raises(LLMTemplateError) as exc_info:
            composer._build_section_structure("nonexistent")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_build_token_budget_awareness(self, setup_prompts):
        """Test building token budget awareness fragment."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer._build_token_budget_awareness(
            total_tokens=1000,
            section_budgets={"Section1": 500, "Section2": 500}
        )
        
        assert "TOKEN BUDGET" in result
        assert "1000" in result
        assert "Section1" in result
    
    def test_build_validation_hints(self, setup_prompts):
        """Test building validation hints fragment."""
        loader = PromptFragmentLoader(base_path=setup_prompts)
        composer = PromptComposer(loader=loader)
        
        result = composer._build_validation_hints(
            word_count_range=(100, 200),
            required_elements=["Element1", "Element2"]
        )
        
        assert "VALIDATION" in result
        assert "100-200" in result
        assert "Element1" in result












