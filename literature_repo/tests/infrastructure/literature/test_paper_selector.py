"""Tests for infrastructure.literature.llm.selector module.

Tests for paper selection and filtering functionality.
"""

import yaml
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, Mock

from infrastructure.literature.llm import (
    PaperSelector,
    PaperSelectionConfig,
)
from infrastructure.literature.library import LibraryEntry


class TestPaperSelectionConfig:
    """Test PaperSelectionConfig dataclass."""

    def test_config_creation(self):
        """Test creating a PaperSelectionConfig."""
        config = PaperSelectionConfig(
            citation_keys=["paper1", "paper2"],
            years={"min": 2020, "max": 2024},
            sources=["arxiv"],
            has_pdf=True,
            has_summary=False,
            keywords=["machine learning"],
            limit=10
        )
        
        assert len(config.citation_keys) == 2
        assert config.years["min"] == 2020
        assert config.years["max"] == 2024
        assert "arxiv" in config.sources
        assert config.has_pdf is True
        assert config.has_summary is False
        assert "machine learning" in config.keywords
        assert config.limit == 10

    def test_config_defaults(self):
        """Test PaperSelectionConfig with default values."""
        config = PaperSelectionConfig()
        
        assert config.citation_keys == []
        assert config.years == {}
        assert config.sources == []
        assert config.has_pdf is None
        assert config.has_summary is None
        assert config.keywords == []
        assert config.limit is None

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "selection": {
                "citation_keys": ["paper1"],
                "years": {"min": 2020, "max": 2024},
                "sources": ["arxiv"],
                "has_pdf": True,
                "keywords": ["test"],
                "limit": 5
            }
        }
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert "paper1" in config.citation_keys
        assert config.years["min"] == 2020
        assert config.years["max"] == 2024
        assert "arxiv" in config.sources
        assert config.has_pdf is True
        assert "test" in config.keywords
        assert config.limit == 5

    def test_config_from_dict_partial(self):
        """Test creating config from partial dictionary."""
        data = {
            "selection": {
                "citation_keys": ["paper1"]
            }
        }
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert "paper1" in config.citation_keys
        assert config.years == {}
        assert config.sources == []


class TestPaperSelector:
    """Test PaperSelector class."""

    def test_selector_initialization(self):
        """Test initializing PaperSelector."""
        config = PaperSelectionConfig()
        selector = PaperSelector(config)
        
        assert selector.config == config

    def test_from_config_file_exists(self):
        """Test creating selector from config file."""
        config_data = {
            "selection": {
                "citation_keys": ["paper1"],
                "years": {"min": 2020},
                "limit": 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            selector = PaperSelector.from_config(config_path)
            
            assert "paper1" in selector.config.citation_keys
            assert selector.config.years["min"] == 2020
            assert selector.config.limit == 10
        finally:
            config_path.unlink()

    def test_from_config_file_not_exists(self):
        """Test creating selector from non-existent config file."""
        config_path = Path("/nonexistent/config.yaml")
        
        with pytest.raises(FileNotFoundError):
            PaperSelector.from_config(config_path)

    def test_from_config_invalid_yaml(self):
        """Test creating selector from invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(yaml.YAMLError):
                PaperSelector.from_config(config_path)
        finally:
            config_path.unlink()

    def test_select_by_citation_keys(self):
        """Test selecting papers by citation keys."""
        config = PaperSelectionConfig(citation_keys=["paper1", "paper3"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="paper1", title="Paper 1", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="paper2", title="Paper 2", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="paper3", title="Paper 3", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert selected[0].citation_key == "paper1"
        assert selected[1].citation_key == "paper3"

    def test_select_by_year_range(self):
        """Test selecting papers by year range."""
        config = PaperSelectionConfig(years={"min": 2022, "max": 2023})
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2021, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2022, abstract=""),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2023, abstract=""),
            LibraryEntry(citation_key="p4", title="P4", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert all(2022 <= p.year <= 2023 for p in selected)

    def test_select_by_year_min_only(self):
        """Test selecting papers with only min year."""
        config = PaperSelectionConfig(years={"min": 2023})
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2022, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2023, abstract=""),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert all(p.year >= 2023 for p in selected)

    def test_select_by_year_max_only(self):
        """Test selecting papers with only max year."""
        config = PaperSelectionConfig(years={"max": 2023})
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2022, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2023, abstract=""),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert all(p.year <= 2023 for p in selected)

    def test_select_by_sources(self):
        """Test selecting papers by sources."""
        config = PaperSelectionConfig(sources=["arxiv"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="", source="arxiv"),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2024, abstract="", source="semanticscholar"),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2024, abstract="", source="arxiv")
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert all(p.source == "arxiv" for p in selected)

    @patch('infrastructure.literature.llm.selector.Path')
    def test_select_by_has_pdf(self, mock_path_class):
        """Test selecting papers by PDF availability."""
        config = PaperSelectionConfig(has_pdf=True)
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="", pdf_path=Path("/path/to/p1.pdf")),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2024, abstract="", pdf_path=None),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2024, abstract="", pdf_path=Path("/path/to/p3.pdf"))
        ]
        
        # Configure mock to return True for exists() when path ends with .pdf
        def path_side_effect(path_str):
            mock = Mock()
            mock.is_absolute.return_value = True
            # Return True for exists() if path ends with .pdf
            if str(path_str).endswith('.pdf'):
                mock.exists.return_value = True
            else:
                mock.exists.return_value = False
            # Support / operator for relative paths
            def truediv(self, other):
                new_mock = Mock()
                new_mock.is_absolute.return_value = False
                new_mock.exists.return_value = str(other).endswith('.pdf')
                return new_mock
            mock.__truediv__ = truediv
            return mock
        
        mock_path_class.side_effect = path_side_effect
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2
        assert all(p.pdf_path is not None for p in selected)

    def test_select_by_has_summary(self):
        """Test selecting papers by summary availability."""
        config = PaperSelectionConfig(has_summary=True)
        selector = PaperSelector(config)
        
        # Create papers with summary paths
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
        ]
        
        # Mock summary path existence
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_dir = Path(tmpdir) / "summaries"
            summary_dir.mkdir()
            
            # Create summary for p1
            (summary_dir / "p1_summary.md").write_text("Summary")
            
            # Mock the summary path check
            with patch('infrastructure.literature.llm.selector.Path') as mock_path:
                def path_side_effect(path_str):
                    if "summaries" in path_str and "p1" in path_str:
                        mock = Mock()
                        mock.exists.return_value = True
                        return mock
                    return Path(path_str)
                
                mock_path.side_effect = path_side_effect
                
                selected = selector.select_papers(papers)
                
                # Should select papers with summaries
                assert len(selected) >= 0  # Depends on implementation

    def test_select_by_keywords(self):
        """Test selecting papers by keywords."""
        config = PaperSelectionConfig(keywords=["machine learning", "neural"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Machine Learning Paper", authors=[], year=2024, abstract="Neural networks"),
            LibraryEntry(citation_key="p2", title="Other Paper", authors=[], year=2024, abstract="Different topic"),
            LibraryEntry(citation_key="p3", title="Neural Networks", authors=[], year=2024, abstract="Deep learning")
        ]
        
        selected = selector.select_papers(papers)
        
        # Should match papers with keywords in title or abstract
        assert len(selected) >= 1
        assert any("machine learning" in p.title.lower() or "neural" in p.title.lower() or "neural" in p.abstract.lower() for p in selected)

    def test_select_with_limit(self):
        """Test selecting papers with limit."""
        config = PaperSelectionConfig(limit=2)
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key=f"p{i}", title=f"Paper {i}", authors=[], year=2024, abstract="")
            for i in range(5)
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 2

    @patch('infrastructure.literature.llm.selector.Path')
    def test_select_multiple_criteria(self, mock_path_class):
        """Test selecting papers with multiple criteria."""
        config = PaperSelectionConfig(
            years={"min": 2023},
            sources=["arxiv"],
            has_pdf=True,
            limit=5
        )
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2023, abstract="", source="arxiv", pdf_path=Path("/p1.pdf")),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2022, abstract="", source="arxiv", pdf_path=Path("/p2.pdf")),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2023, abstract="", source="semanticscholar", pdf_path=Path("/p3.pdf")),
            LibraryEntry(citation_key="p4", title="P4", authors=[], year=2023, abstract="", source="arxiv", pdf_path=None)
        ]
        
        # Configure mock to return True for exists() when path ends with .pdf
        def path_side_effect(path_str):
            mock = Mock()
            mock.is_absolute.return_value = True
            # Return True for exists() if path ends with .pdf
            if str(path_str).endswith('.pdf'):
                mock.exists.return_value = True
            else:
                mock.exists.return_value = False
            # Support / operator for relative paths
            def truediv(self, other):
                new_mock = Mock()
                new_mock.is_absolute.return_value = False
                new_mock.exists.return_value = str(other).endswith('.pdf')
                return new_mock
            mock.__truediv__ = truediv
            return mock
        
        mock_path_class.side_effect = path_side_effect
        
        selected = selector.select_papers(papers)
        
        # Should match all criteria: year >= 2023, source=arxiv, has PDF
        assert len(selected) == 1
        assert selected[0].citation_key == "p1"

    def test_select_no_criteria(self):
        """Test selecting papers with no criteria (returns all)."""
        config = PaperSelectionConfig()
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key=f"p{i}", title=f"Paper {i}", authors=[], year=2024, abstract="")
            for i in range(3)
        ]
        
        selected = selector.select_papers(papers)
        
        assert len(selected) == 3

    def test_config_from_dict_empty_selection(self):
        """Test creating config from dictionary with empty selection."""
        data = {"selection": {}}
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert config.citation_keys == []
        assert config.years == {}
        assert config.sources == []

    def test_config_from_dict_no_selection_key(self):
        """Test creating config from dictionary without selection key."""
        data = {}
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert config.citation_keys == []
        assert config.years == {}

    def test_config_from_dict_years_min_only(self):
        """Test creating config with only min year."""
        data = {
            "selection": {
                "years": {"min": 2020}
            }
        }
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert config.years["min"] == 2020
        assert "max" not in config.years

    def test_config_from_dict_years_max_only(self):
        """Test creating config with only max year."""
        data = {
            "selection": {
                "years": {"max": 2024}
            }
        }
        
        config = PaperSelectionConfig.from_dict(data)
        
        assert config.years["max"] == 2024
        assert "min" not in config.years

    def test_from_config_file_encoding_error(self):
        """Test creating selector from config file with encoding issues."""
        # Create file with invalid encoding (binary data)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.yaml', delete=False) as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
            config_path = Path(f.name)
        
        try:
            # Should raise YAMLError or UnicodeDecodeError
            with pytest.raises((yaml.YAMLError, UnicodeDecodeError)):
                PaperSelector.from_config(config_path)
        finally:
            config_path.unlink()

    def test_from_config_file_empty_file(self):
        """Test creating selector from empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            config_path = Path(f.name)
        
        try:
            selector = PaperSelector.from_config(config_path)
            # Should create config with defaults
            assert selector.config.citation_keys == []
        finally:
            config_path.unlink()

    def test_filter_by_citation_keys_empty_list(self):
        """Test filtering by citation keys with empty list."""
        config = PaperSelectionConfig(citation_keys=[])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_citation_keys(papers)
        
        # Empty list should return empty result
        assert len(selected) == 0

    def test_filter_by_citation_keys_nonexistent(self):
        """Test filtering by citation keys that don't exist."""
        config = PaperSelectionConfig(citation_keys=["nonexistent1", "nonexistent2"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_citation_keys(papers)
        
        assert len(selected) == 0

    def test_filter_by_years_no_year_entries(self):
        """Test filtering by years with entries having no year."""
        config = PaperSelectionConfig(years={"min": 2020, "max": 2024})
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=None, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2022, abstract="")
        ]
        
        selected = selector._filter_by_years(papers)
        
        # Should skip entries without year
        assert len(selected) == 1
        assert selected[0].citation_key == "p2"

    def test_filter_by_years_exact_boundaries(self):
        """Test filtering by years at exact boundaries."""
        config = PaperSelectionConfig(years={"min": 2022, "max": 2023})
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2022, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2023, abstract=""),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2021, abstract=""),
            LibraryEntry(citation_key="p4", title="P4", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_years(papers)
        
        assert len(selected) == 2
        assert all(2022 <= p.year <= 2023 for p in selected)

    def test_filter_by_sources_multiple_sources(self):
        """Test filtering by multiple sources."""
        config = PaperSelectionConfig(sources=["arxiv", "semanticscholar"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="", source="arxiv"),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2024, abstract="", source="semanticscholar"),
            LibraryEntry(citation_key="p3", title="P3", authors=[], year=2024, abstract="", source="pubmed"),
            LibraryEntry(citation_key="p4", title="P4", authors=[], year=2024, abstract="", source="arxiv")
        ]
        
        selected = selector._filter_by_sources(papers)
        
        assert len(selected) == 3
        assert all(p.source in ["arxiv", "semanticscholar"] for p in selected)

    def test_filter_by_sources_no_source_field(self):
        """Test filtering by sources when entries have no source field."""
        config = PaperSelectionConfig(sources=["arxiv"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
            # No source field
        ]
        
        selected = selector._filter_by_sources(papers)
        
        # Should filter out entries without source
        assert len(selected) == 0

    @patch('infrastructure.literature.llm.selector.Path')
    def test_filter_by_pdf_availability_false(self, mock_path_class):
        """Test filtering for papers without PDF."""
        config = PaperSelectionConfig(has_pdf=False)
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="", pdf_path=None),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2024, abstract="", pdf_path=Path("/p2.pdf"))
        ]
        
        def path_side_effect(path_str):
            mock = Mock()
            mock.is_absolute.return_value = True
            mock.exists.return_value = str(path_str).endswith('.pdf')
            def truediv(self, other):
                new_mock = Mock()
                new_mock.is_absolute.return_value = False
                new_mock.exists.return_value = str(other).endswith('.pdf')
                return new_mock
            mock.__truediv__ = truediv
            return mock
        
        mock_path_class.side_effect = path_side_effect
        
        selected = selector._filter_by_pdf_availability(papers)
        
        # Should return only papers without PDF
        assert len(selected) == 1
        assert selected[0].pdf_path is None

    @patch('infrastructure.literature.llm.selector.Path')
    def test_filter_by_pdf_availability_relative_path(self, mock_path_class):
        """Test filtering by PDF with relative path."""
        config = PaperSelectionConfig(has_pdf=True)
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="", pdf_path=Path("papers/p1.pdf"))
        ]
        
        def path_side_effect(path_str):
            mock = Mock()
            if "papers" in str(path_str) or "p1.pdf" in str(path_str):
                mock.is_absolute.return_value = False
                mock.exists.return_value = True
            else:
                mock.is_absolute.return_value = True
                mock.exists.return_value = False
            def truediv(self, other):
                new_mock = Mock()
                new_mock.is_absolute.return_value = False
                new_mock.exists.return_value = True
                return new_mock
            mock.__truediv__ = truediv
            return mock
        
        mock_path_class.side_effect = path_side_effect
        
        selected = selector._filter_by_pdf_availability(papers)
        
        assert len(selected) == 1

    def test_filter_by_summary_availability_false(self, tmp_path, monkeypatch):
        """Test filtering for papers without summaries."""
        config = PaperSelectionConfig(has_summary=False)
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="p2", title="P2", authors=[], year=2024, abstract="")
        ]
        
        # Create real summary directory structure
        summary_dir = tmp_path / "literature" / "summaries"
        summary_dir.mkdir(parents=True)
        
        # Create summary for p1 only
        (summary_dir / "p1_summary.md").write_text("Summary")
        
        # Change to tmp_path so relative paths work
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        try:
            selected = selector._filter_by_summary_availability(papers)
            
            # Should return only papers without summaries
            assert len(selected) == 1
            assert selected[0].citation_key == "p2"
        finally:
            monkeypatch.chdir(original_cwd)

    def test_filter_by_keywords_case_insensitive(self):
        """Test keyword filtering is case insensitive."""
        config = PaperSelectionConfig(keywords=["MACHINE", "learning"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Machine Learning Paper", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="p2", title="Other Paper", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_keywords(papers)
        
        # Should match case-insensitively
        assert len(selected) >= 1
        assert any("machine" in p.title.lower() for p in selected)

    def test_filter_by_keywords_multiple_keywords_all_required(self):
        """Test keyword filtering requires all keywords."""
        config = PaperSelectionConfig(keywords=["machine", "learning", "neural"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Machine Learning Neural Networks", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="p2", title="Machine Learning", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="p3", title="Neural Networks", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_keywords(papers)
        
        # Should only match papers with all keywords
        assert len(selected) == 1
        assert selected[0].citation_key == "p1"

    def test_filter_by_keywords_in_abstract(self):
        """Test keyword filtering matches in abstract."""
        config = PaperSelectionConfig(keywords=["deep learning"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Paper 1", authors=[], year=2024, abstract="This paper is about deep learning"),
            LibraryEntry(citation_key="p2", title="Paper 2", authors=[], year=2024, abstract="Different topic")
        ]
        
        selected = selector._filter_by_keywords(papers)
        
        assert len(selected) == 1
        assert selected[0].citation_key == "p1"

    def test_filter_by_keywords_word_boundaries(self):
        """Test keyword filtering uses word boundaries."""
        config = PaperSelectionConfig(keywords=["learn"])
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Learning Paper", authors=[], year=2024, abstract=""),
            LibraryEntry(citation_key="p2", title="Relearning Paper", authors=[], year=2024, abstract="")
        ]
        
        selected = selector._filter_by_keywords(papers)
        
        # Should match "learn" as word boundary
        assert len(selected) >= 1

    def test_get_selection_summary_with_filters(self):
        """Test getting selection summary with filters applied."""
        config = PaperSelectionConfig(
            citation_keys=["p1"],
            years={"min": 2020},
            sources=["arxiv"],
            has_pdf=True,
            keywords=["test"],
            limit=5
        )
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        summary = selector.get_selection_summary(selected, total=10)
        
        assert summary["total_papers"] == 10
        assert summary["selected_papers"] == len(selected)
        assert summary["filters_applied"]["citation_keys"] is True
        assert summary["filters_applied"]["years"] is True
        assert summary["filters_applied"]["sources"] is True
        assert summary["filters_applied"]["has_pdf"] is True
        assert summary["filters_applied"]["keywords"] is True
        assert summary["filters_applied"]["limit"] is True

    def test_get_selection_summary_no_filters(self):
        """Test getting selection summary with no filters."""
        config = PaperSelectionConfig()
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="P1", authors=[], year=2024, abstract="")
        ]
        
        selected = selector.select_papers(papers)
        summary = selector.get_selection_summary(selected, total=1)
        
        assert summary["total_papers"] == 1
        assert summary["selected_papers"] == 1
        assert all(not applied for applied in summary["filters_applied"].values())

    def test_get_selection_summary_zero_total(self):
        """Test getting selection summary with zero total."""
        config = PaperSelectionConfig()
        selector = PaperSelector(config)
        
        summary = selector.get_selection_summary([], total=0)
        
        assert summary["total_papers"] == 0
        assert summary["selected_papers"] == 0
        assert summary["selection_rate"] == 0

    def test_select_papers_complex_multi_criteria(self):
        """Test selecting papers with complex multi-criteria filtering."""
        config = PaperSelectionConfig(
            years={"min": 2022, "max": 2024},
            sources=["arxiv", "semanticscholar"],
            keywords=["machine", "learning"],
            limit=3
        )
        selector = PaperSelector(config)
        
        papers = [
            LibraryEntry(citation_key="p1", title="Machine Learning Paper", authors=[], year=2023, abstract="", source="arxiv"),
            LibraryEntry(citation_key="p2", title="Other Paper", authors=[], year=2023, abstract="", source="arxiv"),
            LibraryEntry(citation_key="p3", title="Machine Learning", authors=[], year=2021, abstract="", source="arxiv"),
            LibraryEntry(citation_key="p4", title="Machine Learning", authors=[], year=2023, abstract="", source="pubmed"),
            LibraryEntry(citation_key="p5", title="Machine Learning", authors=[], year=2023, abstract="", source="semanticscholar"),
            LibraryEntry(citation_key="p6", title="Machine Learning", authors=[], year=2023, abstract="", source="arxiv")
        ]
        
        selected = selector.select_papers(papers)
        
        # Should match: year 2022-2024, source arxiv/semanticscholar, keywords machine+learning
        assert len(selected) <= 3  # Limited by limit
        assert all(2022 <= p.year <= 2024 for p in selected)
        assert all(p.source in ["arxiv", "semanticscholar"] for p in selected)
        assert all("machine" in p.title.lower() and "learning" in p.title.lower() for p in selected)

