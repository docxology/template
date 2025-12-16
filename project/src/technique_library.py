"""Encyclopedia of grafting techniques.

This module provides comprehensive information about grafting techniques including
whip & tongue, cleft, bark, bud, approach, bridge, and inarching methods.
"""
from __future__ import annotations

from typing import Dict, List, Optional


class TechniqueLibrary:
    """Library of grafting techniques with descriptions and protocols."""
    
    def __init__(self):
        """Initialize technique library."""
        self.techniques: Dict[str, Dict[str, any]] = {}
        self._initialize_default_techniques()
    
    def _initialize_default_techniques(self) -> None:
        """Initialize default grafting techniques."""
        # Whip and Tongue Grafting
        self.techniques["whip_and_tongue"] = {
            "name": "Whip and Tongue Grafting",
            "description": "A precise method where matching cuts with interlocking tongues create strong unions.",
            "best_for": ["Similar diameter rootstock and scion", "Deciduous trees"],
            "difficulty": "moderate",
            "success_rate": 0.85,
            "optimal_season": "late_winter_early_spring",
            "steps": [
                "Make matching 30-45° angle cuts on rootstock and scion",
                "Create interlocking tongues on both pieces",
                "Align cambium layers precisely",
                "Secure with grafting tape or wax",
                "Protect from desiccation"
            ],
            "diameter_range": (5, 25)  # mm
        }
        
        # Cleft Grafting
        self.techniques["cleft"] = {
            "name": "Cleft Grafting",
            "description": "A simple method where a wedge-shaped scion is inserted into a split rootstock.",
            "best_for": ["Larger diameter rootstock", "Established trees"],
            "difficulty": "easy",
            "success_rate": 0.75,
            "optimal_season": "late_winter",
            "steps": [
                "Make a vertical split in the rootstock",
                "Prepare wedge-shaped scion with 2-3 buds",
                "Insert scion into cleft, aligning cambium",
                "Seal with grafting wax",
                "Protect from weather"
            ],
            "diameter_range": (10, 50)  # mm
        }
        
        # Bark Grafting
        self.techniques["bark"] = {
            "name": "Bark Grafting",
            "description": "Scion is inserted under the bark of the rootstock, useful for larger trees.",
            "best_for": ["Large diameter rootstock", "Mature trees"],
            "difficulty": "moderate",
            "success_rate": 0.70,
            "optimal_season": "early_spring",
            "steps": [
                "Make vertical cut through bark on rootstock",
                "Loosen bark flaps",
                "Prepare scion with beveled cut",
                "Insert scion under bark, cambium aligned",
                "Secure and seal"
            ],
            "diameter_range": (20, 100)  # mm
        }
        
        # Bud Grafting (T-budding)
        self.techniques["bud"] = {
            "name": "Bud Grafting (T-budding)",
            "description": "A single bud is inserted under the bark, very efficient for propagation.",
            "best_for": ["Young rootstock", "Mass propagation"],
            "difficulty": "moderate",
            "success_rate": 0.80,
            "optimal_season": "summer",
            "steps": [
                "Make T-shaped cut in rootstock bark",
                "Remove bud from scion with shield",
                "Insert bud under bark flaps",
                "Wrap securely with budding tape",
                "Remove tape after bud takes"
            ],
            "diameter_range": (5, 15)  # mm
        }
        
        # Approach Grafting
        self.techniques["approach"] = {
            "name": "Approach Grafting",
            "description": "Two growing plants are joined while both remain on their own roots.",
            "best_for": ["Difficult-to-graft species", "Container plants"],
            "difficulty": "moderate",
            "success_rate": 0.75,
            "optimal_season": "spring_summer",
            "steps": [
                "Make matching cuts on both plants",
                "Align cambium layers",
                "Secure together",
                "Allow union to form",
                "Sever scion from its roots after union"
            ],
            "diameter_range": (5, 20)  # mm
        }
        
        # Bridge Grafting
        self.techniques["bridge"] = {
            "name": "Bridge Grafting",
            "description": "Used to repair damaged bark by bridging the wound with scions.",
            "best_for": ["Bark damage repair", "Tree rescue"],
            "difficulty": "advanced",
            "success_rate": 0.65,
            "optimal_season": "early_spring",
            "steps": [
                "Prepare damaged area by cleaning",
                "Make cuts above and below damage",
                "Insert scion pieces to bridge gap",
                "Align cambium with healthy tissue",
                "Seal and protect"
            ],
            "diameter_range": (10, 50)  # mm
        }
        
        # Inarching
        self.techniques["inarch"] = {
            "name": "Inarching",
            "description": "Rootstock seedlings are grafted to established trees to add roots.",
            "best_for": ["Root system improvement", "Weak root systems"],
            "difficulty": "advanced",
            "success_rate": 0.70,
            "optimal_season": "spring",
            "steps": [
                "Prepare rootstock seedlings",
                "Make matching cuts on tree and rootstock",
                "Join and secure",
                "Allow union to form",
                "Rootstock provides additional root system"
            ],
            "diameter_range": (5, 15)  # mm
        }
    
    def get_technique(self, technique_name: str) -> Optional[Dict[str, any]]:
        """Get technique information.
        
        Args:
            technique_name: Name of technique
            
        Returns:
            Technique information dictionary or None
        """
        return self.techniques.get(technique_name)
    
    def list_techniques(self) -> List[str]:
        """List all available techniques.
        
        Returns:
            List of technique names
        """
        return list(self.techniques.keys())
    
    def recommend_technique(
        self,
        rootstock_diameter: float,
        scion_diameter: float,
        species_type: str = "temperate"
    ) -> List[Tuple[str, float]]:
        """Recommend techniques based on conditions.
        
        Args:
            rootstock_diameter: Rootstock diameter (mm)
            scion_diameter: Scion diameter (mm)
            species_type: Species type (temperate, tropical, subtropical)
            
        Returns:
            List of (technique_name, suitability_score) tuples, sorted by suitability
        """
        recommendations = []
        
        for tech_name, tech_info in self.techniques.items():
            score = 0.0
            
            # Check diameter compatibility
            diameter_range = tech_info.get("diameter_range", (5, 25))
            if diameter_range[0] <= rootstock_diameter <= diameter_range[1]:
                score += 0.4
            
            # Check diameter match
            ratio = scion_diameter / (rootstock_diameter + 1e-10)
            if 0.8 <= ratio <= 1.2:
                score += 0.3
            elif 0.6 <= ratio <= 1.5:
                score += 0.15
            
            # Base success rate
            score += tech_info.get("success_rate", 0.7) * 0.3
            
            recommendations.append((tech_name, score))
        
        # Sort by suitability (descending)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
    def get_technique_protocol(self, technique_name: str) -> Optional[List[str]]:
        """Get step-by-step protocol for technique.
        
        Args:
            technique_name: Name of technique
            
        Returns:
            List of protocol steps or None
        """
        technique = self.get_technique(technique_name)
        if technique:
            return technique.get("steps", [])
        return None

