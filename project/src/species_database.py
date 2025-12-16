"""Species compatibility database for tree grafting.

This module provides a comprehensive database of rootstock-scion compatibility
information, technique suitability, and species characteristics.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


class SpeciesDatabase:
    """Database of species compatibility and characteristics."""
    
    def __init__(self):
        """Initialize species database."""
        self.species_info: Dict[str, Dict[str, any]] = {}
        self.compatibility_matrix: Optional[np.ndarray] = None
        self.species_list: List[str] = []
    
    def add_species(
        self,
        species_name: str,
        characteristics: Dict[str, any]
    ) -> None:
        """Add species to database.
        
        Args:
            species_name: Name of species
            characteristics: Dictionary with species characteristics
        """
        self.species_info[species_name] = characteristics
        
        if species_name not in self.species_list:
            self.species_list.append(species_name)
    
    def get_compatibility(
        self,
        rootstock: str,
        scion: str
    ) -> Optional[float]:
        """Get compatibility score for rootstock-scion pair.
        
        Args:
            rootstock: Rootstock species name
            scion: Scion species name
            
        Returns:
            Compatibility score (0-1) or None if not found
        """
        if self.compatibility_matrix is not None:
            try:
                root_idx = self.species_list.index(rootstock)
                scion_idx = self.species_list.index(scion)
                return float(self.compatibility_matrix[root_idx, scion_idx])
            except (ValueError, IndexError):
                pass
        
        # Fallback: check species info
        if rootstock in self.species_info and scion in self.species_info:
            # Default compatibility if both species exist
            return 0.7
        
        return None
    
    def set_compatibility_matrix(
        self,
        matrix: np.ndarray,
        species_list: Optional[List[str]] = None
    ) -> None:
        """Set compatibility matrix.
        
        Args:
            matrix: Compatibility matrix (n_species x n_species)
            species_list: Optional list of species names (must match matrix order)
        """
        self.compatibility_matrix = matrix
        
        if species_list is not None:
            self.species_list = species_list
        elif len(self.species_list) != matrix.shape[0]:
            # Create default species list
            self.species_list = [f"Species_{i+1}" for i in range(matrix.shape[0])]
    
    def find_compatible_pairs(
        self,
        rootstock: Optional[str] = None,
        min_compatibility: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """Find compatible rootstock-scion pairs.
        
        Args:
            rootstock: Optional rootstock to search for (if None, search all)
            min_compatibility: Minimum compatibility threshold
            
        Returns:
            List of (rootstock, scion, compatibility) tuples
        """
        compatible_pairs = []
        
        if self.compatibility_matrix is None:
            return compatible_pairs
        
        if rootstock is not None:
            try:
                root_idx = self.species_list.index(rootstock)
                for scion_idx, scion in enumerate(self.species_list):
                    compat = self.compatibility_matrix[root_idx, scion_idx]
                    if compat >= min_compatibility and root_idx != scion_idx:
                        compatible_pairs.append((rootstock, scion, float(compat)))
            except ValueError:
                pass
        else:
            # Search all pairs
            for root_idx, root in enumerate(self.species_list):
                for scion_idx, scion in enumerate(self.species_list):
                    if root_idx != scion_idx:
                        compat = self.compatibility_matrix[root_idx, scion_idx]
                        if compat >= min_compatibility:
                            compatible_pairs.append((root, scion, float(compat)))
        
        # Sort by compatibility (descending)
        compatible_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return compatible_pairs
    
    def get_suitable_techniques(
        self,
        rootstock: str,
        scion: str
    ) -> List[str]:
        """Get suitable grafting techniques for species pair.
        
        Args:
            rootstock: Rootstock species
            scion: Scion species
            
        Returns:
            List of suitable technique names
        """
        # Default techniques
        default_techniques = ["whip", "cleft", "bark", "bud"]
        
        # Check species characteristics for technique preferences
        techniques = []
        
        if rootstock in self.species_info:
            root_info = self.species_info[rootstock]
            preferred = root_info.get("preferred_techniques", default_techniques)
            techniques.extend(preferred)
        
        if scion in self.species_info:
            scion_info = self.species_info[scion]
            preferred = scion_info.get("preferred_techniques", default_techniques)
            # Intersect with existing techniques
            if techniques:
                techniques = [t for t in techniques if t in preferred]
            else:
                techniques.extend(preferred)
        
        # Remove duplicates and return
        return list(dict.fromkeys(techniques)) if techniques else default_techniques


def create_default_database() -> SpeciesDatabase:
    """Create default species database with common fruit tree species.
    
    Returns:
        SpeciesDatabase instance
    """
    db = SpeciesDatabase()
    
    # Add common fruit tree species
    common_species = [
        "Malus_domestica",  # Apple
        "Pyrus_communis",   # Pear
        "Prunus_persica",   # Peach
        "Prunus_avium",     # Cherry
        "Prunus_domestica", # Plum
        "Citrus_sinensis",  # Orange
        "Citrus_limon",     # Lemon
        "Vitis_vinifera"    # Grape
    ]
    
    for species in common_species:
        db.add_species(species, {
            "preferred_techniques": ["whip", "cleft", "bud"],
            "type": "temperate"
        })
    
    # Create default compatibility matrix (higher within genera)
    n_species = len(common_species)
    compat_matrix = np.random.beta(3, 1, size=(n_species, n_species))
    
    # Increase compatibility within same genus
    for i, sp1 in enumerate(common_species):
        for j, sp2 in enumerate(common_species):
            if i != j:
                genus1 = sp1.split('_')[0]
                genus2 = sp2.split('_')[0]
                if genus1 == genus2:
                    compat_matrix[i, j] = min(1.0, compat_matrix[i, j] + 0.3)
    
    # Make symmetric and set diagonal to 1.0
    compat_matrix = (compat_matrix + compat_matrix.T) / 2
    np.fill_diagonal(compat_matrix, 1.0)
    
    db.set_compatibility_matrix(compat_matrix, common_species)
    
    return db

