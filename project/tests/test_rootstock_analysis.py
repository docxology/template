"""Comprehensive tests for rootstock_analysis module."""
import pytest
from rootstock_analysis import (
    RootstockProfile,
    evaluate_rootstock_suitability,
    select_optimal_rootstock,
    analyze_vigor_effects,
    calculate_dwarfing_effect
)


class TestRootstockProfile:
    """Test rootstock profile."""
    
    def test_profile_creation(self):
        """Test creating rootstock profile."""
        profile = RootstockProfile(
            name="M9",
            vigor=0.3,
            disease_resistance={"fire_blight": 0.7},
            climate_adaptation=["temperate"]
        )
        assert profile.name == "M9"
        assert profile.vigor == 0.3
    
    def test_disease_resistance(self):
        """Test disease resistance calculation."""
        profile = RootstockProfile(
            name="Test",
            vigor=0.5,
            disease_resistance={"disease1": 0.8, "disease2": 0.6},
            climate_adaptation=["temperate"]
        )
        overall = profile.overall_disease_resistance()
        assert overall == pytest.approx(0.7)


class TestRootstockEvaluation:
    """Test rootstock evaluation."""
    
    def test_evaluate_suitability(self):
        """Test evaluating rootstock suitability."""
        rootstock = RootstockProfile(
            name="M9",
            vigor=0.3,
            disease_resistance={"fire_blight": 0.7},
            climate_adaptation=["temperate"]
        )
        scion_requirements = {"vigor": 0.4, "disease_resistance": 0.6}
        score, factors = evaluate_rootstock_suitability(
            rootstock, scion_requirements, "temperate", "well_drained"
        )
        assert 0.0 <= score <= 1.0
        assert "vigor_match" in factors
    
    def test_evaluate_suitability_insufficient_resistance(self):
        """Test evaluation with insufficient disease resistance (penalty branch)."""
        rootstock = RootstockProfile(
            name="LowResistance",
            vigor=0.5,
            disease_resistance={"fire_blight": 0.3},  # Low resistance
            climate_adaptation=["temperate"]
        )
        scion_requirements = {"vigor": 0.5, "disease_resistance": 0.7}  # Requires 0.7
        score, factors = evaluate_rootstock_suitability(
            rootstock, scion_requirements, "temperate", "well_drained"
        )
        assert 0.0 <= score <= 1.0
        assert "disease_resistance" in factors
        # Should have penalty (0.3 * 0.7 = 0.21)
        assert factors["disease_resistance"] < 0.3
    
    def test_evaluate_suitability_climate_mismatch(self):
        """Test evaluation with climate mismatch."""
        rootstock = RootstockProfile(
            name="Tropical",
            vigor=0.5,
            disease_resistance={"fire_blight": 0.7},
            climate_adaptation=["tropical"]  # Not temperate
        )
        scion_requirements = {"vigor": 0.5}
        score, factors = evaluate_rootstock_suitability(
            rootstock, scion_requirements, "temperate", "well_drained"
        )
        assert factors["climate_adaptation"] == 0.5  # Mismatch penalty
    
    def test_evaluate_suitability_soil_mismatch(self):
        """Test evaluation with soil mismatch."""
        rootstock = RootstockProfile(
            name="Test",
            vigor=0.5,
            disease_resistance={"fire_blight": 0.7},
            climate_adaptation=["temperate"],
            soil_preference="clay"
        )
        scion_requirements = {"vigor": 0.5}
        score, factors = evaluate_rootstock_suitability(
            rootstock, scion_requirements, "temperate", "well_drained"  # Mismatch
        )
        assert factors["soil_preference"] == 0.7  # Mismatch penalty


class TestVigorAnalysis:
    """Test vigor analysis."""
    
    def test_vigor_effects(self):
        """Test vigor effect analysis."""
        effects = analyze_vigor_effects(0.5, 0.6)
        assert "vigor_ratio" in effects
        assert "risk_level" in effects
    
    def test_vigor_effects_scion_overgrowth(self):
        """Test vigor effects with scion overgrowth (ratio > 1.5)."""
        effects = analyze_vigor_effects(0.3, 0.6)  # ratio = 2.0
        assert effects["vigor_ratio"] > 1.5
        assert effects["effect"] == "scion_overgrowth"
        assert effects["risk_level"] == "high"
    
    def test_vigor_effects_rootstock_overgrowth(self):
        """Test vigor effects with rootstock overgrowth (ratio < 0.67)."""
        effects = analyze_vigor_effects(0.6, 0.3)  # ratio = 0.5
        assert effects["vigor_ratio"] < 0.67
        assert effects["effect"] == "rootstock_overgrowth"
        assert effects["risk_level"] == "high"
    
    def test_vigor_effects_balanced(self):
        """Test vigor effects with balanced vigor."""
        effects = analyze_vigor_effects(0.5, 0.6)  # ratio = 1.2
        assert 0.67 <= effects["vigor_ratio"] <= 1.5
        assert effects["effect"] == "balanced"
        assert effects["risk_level"] == "low"


class TestOptimalSelection:
    """Test optimal rootstock selection."""
    
    def test_select_optimal_rootstock(self):
        """Test selecting optimal rootstock from candidates."""
        candidates = [
            RootstockProfile(
                name="M9",
                vigor=0.3,
                disease_resistance={"fire_blight": 0.7},
                climate_adaptation=["temperate"]
            ),
            RootstockProfile(
                name="M26",
                vigor=0.5,
                disease_resistance={"fire_blight": 0.8},
                climate_adaptation=["temperate"]
            ),
            RootstockProfile(
                name="MM106",
                vigor=0.7,
                disease_resistance={"fire_blight": 0.6},
                climate_adaptation=["temperate"]
            )
        ]
        scion_requirements = {"vigor": 0.4, "disease_resistance": 0.7}
        best, score, factors = select_optimal_rootstock(
            candidates, scion_requirements, "temperate", "well_drained"
        )
        assert best is not None
        assert 0.0 <= score <= 1.0
        assert isinstance(factors, dict)
        assert best.name in ["M9", "M26", "MM106"]


class TestDwarfing:
    """Test dwarfing effect calculation."""
    
    def test_calculate_dwarfing_effect(self):
        """Test calculating dwarfing effect."""
        dwarfing = calculate_dwarfing_effect(0.3, standard_vigor=1.0)
        assert 0.0 <= dwarfing <= 1.0
        assert dwarfing == pytest.approx(0.3)  # 0.3 / 1.0
    
    def test_calculate_dwarfing_effect_standard(self):
        """Test dwarfing effect with standard rootstock."""
        dwarfing = calculate_dwarfing_effect(1.0, standard_vigor=1.0)
        assert dwarfing == pytest.approx(1.0)  # No dwarfing
    
    def test_calculate_dwarfing_effect_high_vigor(self):
        """Test dwarfing effect with high vigor rootstock."""
        dwarfing = calculate_dwarfing_effect(1.2, standard_vigor=1.0)
        # Should be clipped to 1.0
        assert dwarfing == pytest.approx(1.0)
    
    def test_calculate_dwarfing_effect_low_vigor(self):
        """Test dwarfing effect with low vigor rootstock."""
        dwarfing = calculate_dwarfing_effect(0.2, standard_vigor=1.0)
        assert dwarfing == pytest.approx(0.2)


if __name__ == "__main__":
    pytest.main([__file__])


if __name__ == "__main__":
    pytest.main([__file__])

