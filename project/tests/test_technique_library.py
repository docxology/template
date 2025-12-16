"""Comprehensive tests for technique_library module."""
import pytest
from technique_library import TechniqueLibrary


class TestTechniqueLibrary:
    """Test technique library."""
    
    def test_get_technique(self):
        """Test getting technique information."""
        library = TechniqueLibrary()
        technique = library.get_technique("whip_and_tongue")
        assert technique is not None
        assert "name" in technique
        assert "steps" in technique
    
    def test_list_techniques(self):
        """Test listing all techniques."""
        library = TechniqueLibrary()
        techniques = library.list_techniques()
        assert len(techniques) > 0
        assert "whip_and_tongue" in techniques
    
    def test_recommend_technique(self):
        """Test technique recommendation."""
        library = TechniqueLibrary()
        recommendations = library.recommend_technique(15.0, 15.0)
        assert len(recommendations) > 0
        assert all(isinstance(r, tuple) and len(r) == 2 for r in recommendations)
    
    def test_get_protocol(self):
        """Test getting technique protocol."""
        library = TechniqueLibrary()
        protocol = library.get_technique_protocol("whip_and_tongue")
        assert protocol is not None
        assert len(protocol) > 0


if __name__ == "__main__":
    pytest.main([__file__])

