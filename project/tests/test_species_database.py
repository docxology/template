"""Comprehensive tests for species_database module."""
import pytest
import numpy as np
from species_database import SpeciesDatabase, create_default_database


class TestSpeciesDatabase:
    """Test species database."""
    
    def test_add_species(self):
        """Test adding species."""
        db = SpeciesDatabase()
        db.add_species("Apple", {"type": "temperate"})
        assert "Apple" in db.species_info
    
    def test_get_compatibility(self):
        """Test getting compatibility."""
        db = create_default_database()
        compat = db.get_compatibility("Malus_domestica", "Pyrus_communis")
        assert compat is not None
        assert 0.0 <= compat <= 1.0
    
    def test_find_compatible_pairs(self):
        """Test finding compatible pairs."""
        db = create_default_database()
        pairs = db.find_compatible_pairs(min_compatibility=0.7)
        assert len(pairs) > 0
        assert all(pair[2] >= 0.7 for pair in pairs)
    
    def test_suitable_techniques(self):
        """Test getting suitable techniques."""
        db = create_default_database()
        techniques = db.get_suitable_techniques("Malus_domestica", "Pyrus_communis")
        assert len(techniques) > 0
    
    def test_get_compatibility_matrix_error(self):
        """Test get_compatibility with matrix index errors."""
        db = SpeciesDatabase()
        matrix = np.array([[1.0, 0.8], [0.8, 1.0]])
        db.set_compatibility_matrix(matrix, ["Species1", "Species2"])
        # Try to get compatibility for species not in list
        compat = db.get_compatibility("Unknown", "Species1")
        assert compat is None
    
    def test_get_compatibility_fallback(self):
        """Test get_compatibility fallback to species_info."""
        db = SpeciesDatabase()
        db.add_species("Apple", {"type": "temperate"})
        db.add_species("Pear", {"type": "temperate"})
        # No matrix set, should use fallback
        compat = db.get_compatibility("Apple", "Pear")
        assert compat == 0.7  # Default fallback value
    
    def test_get_compatibility_not_found(self):
        """Test get_compatibility when species not found."""
        db = SpeciesDatabase()
        compat = db.get_compatibility("Unknown1", "Unknown2")
        assert compat is None
    
    def test_set_compatibility_matrix_no_species_list(self):
        """Test set_compatibility_matrix without species_list."""
        db = SpeciesDatabase()
        matrix = np.array([[1.0, 0.8], [0.8, 1.0]])
        db.set_compatibility_matrix(matrix)
        # Should create default species list
        assert len(db.species_list) == 2
        assert db.species_list[0] == "Species_1"
    
    def test_set_compatibility_matrix_mismatched_size(self):
        """Test set_compatibility_matrix with mismatched species_list size."""
        db = SpeciesDatabase()
        db.species_list = ["Species1"]  # Only 1 species
        matrix = np.array([[1.0, 0.8], [0.8, 1.0]])  # 2x2 matrix
        db.set_compatibility_matrix(matrix)
        # Should create default list for matrix size
        assert len(db.species_list) == 2
    
    def test_find_compatible_pairs_with_rootstock(self):
        """Test find_compatible_pairs with specific rootstock."""
        db = create_default_database()
        pairs = db.find_compatible_pairs(rootstock="Malus_domestica", min_compatibility=0.7)
        assert isinstance(pairs, list)
        # May be empty or have pairs
    
    def test_find_compatible_pairs_invalid_rootstock(self):
        """Test find_compatible_pairs with invalid rootstock."""
        db = create_default_database()
        pairs = db.find_compatible_pairs(rootstock="UnknownSpecies", min_compatibility=0.7)
        assert pairs == []  # Should return empty list on ValueError
    
    def test_find_compatible_pairs_no_matrix(self):
        """Test find_compatible_pairs when no matrix is set."""
        db = SpeciesDatabase()
        pairs = db.find_compatible_pairs()
        assert pairs == []
    
    def test_get_suitable_techniques_intersection(self):
        """Test get_suitable_techniques with technique intersection."""
        db = SpeciesDatabase()
        db.add_species("Rootstock", {"preferred_techniques": ["whip", "cleft"]})
        db.add_species("Scion", {"preferred_techniques": ["cleft", "bark"]})
        techniques = db.get_suitable_techniques("Rootstock", "Scion")
        assert "cleft" in techniques
        # Should be intersection: only "cleft" is in both
    
    def test_get_suitable_techniques_no_intersection(self):
        """Test get_suitable_techniques when no intersection."""
        db = SpeciesDatabase()
        db.add_species("Rootstock", {"preferred_techniques": ["whip"]})
        db.add_species("Scion", {"preferred_techniques": ["bark"]})
        techniques = db.get_suitable_techniques("Rootstock", "Scion")
        # Should return empty list, then fallback to default
        assert len(techniques) > 0  # Falls back to default techniques
    
    def test_get_suitable_techniques_only_rootstock(self):
        """Test get_suitable_techniques with only rootstock info."""
        db = SpeciesDatabase()
        db.add_species("Rootstock", {"preferred_techniques": ["whip", "cleft"]})
        techniques = db.get_suitable_techniques("Rootstock", "Unknown")
        assert len(techniques) > 0
    
    def test_get_suitable_techniques_only_scion(self):
        """Test get_suitable_techniques with only scion info."""
        db = SpeciesDatabase()
        db.add_species("Scion", {"preferred_techniques": ["bark", "bud"]})
        techniques = db.get_suitable_techniques("Unknown", "Scion")
        assert len(techniques) > 0


if __name__ == "__main__":
    pytest.main([__file__])

