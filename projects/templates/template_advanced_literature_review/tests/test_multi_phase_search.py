"""Tests for multi-phase literature search functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from scripts.multi_phase_search import (
    LLMFilterEngine,
    MultiPhaseSearchRunner,
    PhaseMetadata,
    PhasedPaper,
)
from literature.models import Paper


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "project_config": {
            "search_phases": {
                "phase_1_foundation": {
                    "name": "Foundation Phase",
                    "description": "Basic search",
                    "queries": ["test query"],
                    "max_results_per_query": 100,
                    "engines": {"arxiv": True, "openalex": False},
                    "deterministic_filters": {
                        "min_year": 2020,
                        "min_citation_count": 5
                    }
                }
            },
            "llm_filters": {
                "test_filter": {
                    "name": "Test Filter",
                    "description": "Test description",
                    "prompt": "Classify this: {abstract}",
                    "apply_to_phases": ["phase_1_foundation"],
                    "keep_values": ["yes"]
                }
            },
            "llm_extraction": {
                "model": "gemma3:4b",
                "base_url": "http://localhost:11434",
                "temperature": 0.1,
                "timeout_seconds": 120,
                "max_retries": 3
            }
        }
    }


@pytest.fixture
def sample_papers():
    """Sample papers for testing."""
    return [
        Paper(
            title="Test Paper 1",
            abstract="This is a test abstract about exoplanets.",
            year=2022,
            citation_count=10,
            venue="Nature"
        ),
        Paper(
            title="Test Paper 2", 
            abstract="Another test abstract about atmospheres.",
            year=2019,
            citation_count=2,
            venue="arXiv"
        ),
        Paper(
            title="Test Paper 3",
            abstract="A third test paper.",
            year=2023,
            citation_count=15,
            venue="Science"
        )
    ]


def test_phase_metadata_initialization():
    """Test PhaseMetadata dataclass initialization."""
    metadata = PhaseMetadata(
        phase_id="test_phase",
        name="Test Phase",
        description="A test phase",
        start_time=1000.0
    )
    
    assert metadata.phase_id == "test_phase"
    assert metadata.name == "Test Phase"
    assert metadata.queries_executed == []
    assert metadata.deterministic_filters_applied == {}
    assert metadata.depends_on == []


def test_phased_paper_initialization():
    """Test PhasedPaper dataclass initialization."""
    paper = Paper(title="Test", abstract="Test abstract")
    
    phased_paper = PhasedPaper(
        paper=paper,
        discovered_in_phase="phase_1",
        phases_found_in=[],
        deterministic_filters_passed={},
        llm_filters_passed={},
        cross_phase_citations={}
    )
    
    assert phased_paper.paper.title == "Test"
    assert phased_paper.discovered_in_phase == "phase_1"
    assert phased_paper.phases_found_in == ["phase_1"]


def test_deterministic_filters(sample_config, sample_papers):
    """Test deterministic filtering logic."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump(sample_config, f)
        config_path = Path(f.name)
        
        runner = MultiPhaseSearchRunner(config_path)
        
        # Test year filter
        filters = {"min_year": 2020}
        filtered = runner.apply_deterministic_filters(sample_papers, filters)
        
        # Should keep papers from 2020 onwards (2022, 2023)
        assert len(filtered) == 2
        assert all(p.year >= 2020 for p in filtered if p.year)
        
        # Test citation count filter
        filters = {"min_citation_count": 10}
        filtered = runner.apply_deterministic_filters(sample_papers, filters)
        
        # Should keep papers with >= 10 citations
        assert len(filtered) == 2
        assert all(p.citation_count >= 10 for p in filtered if p.citation_count)


def test_llm_filter_engine_initialization(sample_config):
    """Test LLM filter engine initialization."""
    llm_config = sample_config["project_config"]["llm_extraction"]
    
    engine = LLMFilterEngine(llm_config)
    
    assert engine.model == "gemma3:4b"
    assert engine.base_url == "http://localhost:11434"
    assert engine.temperature == 0.1
    assert engine.timeout == 120
    assert engine.max_retries == 3


@patch('scripts.multi_phase_search.requests')
def test_llm_filter_application(mock_requests, sample_papers):
    """Test LLM filter application with mocked API."""
    # Mock successful LLM response
    mock_response = Mock()
    mock_response.json.return_value = {"response": "yes"}
    mock_response.raise_for_status = Mock()
    mock_requests.post.return_value = mock_response
    
    llm_config = {
        "model": "gemma3:4b",
        "base_url": "http://localhost:11434",
        "temperature": 0.1,
        "timeout_seconds": 120,
        "max_retries": 3
    }
    
    engine = LLMFilterEngine(llm_config)
    
    filter_config = {
        "prompt": "Is this relevant? {abstract}",
        "keep_values": ["yes"]
    }
    
    # Test filter application
    paper = sample_papers[0]
    result = engine.apply_filter(paper, filter_config)
    
    assert result == "yes"
    assert mock_requests.post.called


def test_multi_phase_runner_initialization(sample_config):
    """Test MultiPhaseSearchRunner initialization."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump(sample_config, f)
        config_path = Path(f.name)
        
        runner = MultiPhaseSearchRunner(config_path)
        
        assert runner.config == sample_config
        assert "phase_1_foundation" in runner.search_phases
        assert "test_filter" in runner.llm_filters
        assert runner.llm_engine is not None


def test_phase_overlap_calculation():
    """Test phase overlap calculation logic."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump({"project_config": {}}, f)
        config_path = Path(f.name)
        
        runner = MultiPhaseSearchRunner(config_path)
        
        # Simulate papers found in multiple phases
        paper1 = Paper(title="Paper 1", abstract="Test")
        paper2 = Paper(title="Paper 2", abstract="Test")
        paper3 = Paper(title="Paper 3", abstract="Test")
        
        runner.all_phased_papers = {
            "id1": PhasedPaper(
                paper=paper1,
                discovered_in_phase="phase_1",
                phases_found_in=["phase_1", "phase_2"],
                deterministic_filters_passed={},
                llm_filters_passed={},
                cross_phase_citations={}
            ),
            "id2": PhasedPaper(
                paper=paper2,
                discovered_in_phase="phase_1", 
                phases_found_in=["phase_1"],
                deterministic_filters_passed={},
                llm_filters_passed={},
                cross_phase_citations={}
            ),
            "id3": PhasedPaper(
                paper=paper3,
                discovered_in_phase="phase_2",
                phases_found_in=["phase_2"],
                deterministic_filters_passed={},
                llm_filters_passed={},
                cross_phase_citations={}
            )
        }
        
        overlap = runner._calculate_phase_overlap()
        
        # Should calculate Jaccard similarity between phases
        assert "phase_1" in overlap
        assert "phase_2" in overlap["phase_1"]
        
        # Phase 1 has papers [id1, id2], Phase 2 has [id1, id3]
        # Intersection: 1 (id1), Union: 3 (id1, id2, id3)
        # Jaccard: 1/3 = 0.333...
        jaccard = overlap["phase_1"]["phase_2"]["jaccard_similarity"]
        assert abs(jaccard - 1/3) < 0.001


def test_config_validation(sample_config):
    """Test configuration validation and error handling."""
    # Test missing search_phases
    bad_config = {"project_config": {}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump(bad_config, f)
        config_path = Path(f.name)
        
        runner = MultiPhaseSearchRunner(config_path)
        
        # Should handle missing configuration gracefully
        assert runner.search_phases == {}
        assert runner.llm_filters == {}


@pytest.mark.integration
def test_full_pipeline_mock():
    """Integration test with mocked search results."""
    config = {
        "project_config": {
            "search_phases": {
                "phase_1": {
                    "name": "Test Phase",
                    "queries": ["test"],
                    "engines": {"arxiv": True},
                    "max_results_per_query": 10
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump(config, f)
        config_path = Path(f.name)
        
        runner = MultiPhaseSearchRunner(config_path)
        
        # Mock the search execution to avoid network calls
        with patch.object(runner, 'execute_phase') as mock_execute:
            mock_execute.return_value = []
            
            # Should not raise exceptions
            runner.run(specific_phase="phase_1")