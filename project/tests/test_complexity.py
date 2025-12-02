"""Tests for complexity analysis module.

Tests cover:
- Complexity metrics
- Scaling analysis
- Termination guarantees
"""
import pytest
from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.complexity import (
    ComplexityMetrics, ComplexityAnalysis, ComplexityAnalyzer,
    analyze_reduction_complexity, complexity_scaling_analysis,
    termination_analysis, compare_to_sat, generate_complexity_report
)


class TestComplexityMetrics:
    """Tests for ComplexityMetrics class."""
    
    def test_metrics_creation(self):
        """Test metrics creation."""
        metrics = ComplexityMetrics(
            form_size=5,
            form_depth=3,
            reduction_steps=2,
            time_seconds=0.001
        )
        assert metrics.form_size == 5
        assert metrics.form_depth == 3
    
    def test_steps_per_size(self):
        """Test steps per size calculation."""
        metrics = ComplexityMetrics(
            form_size=10,
            form_depth=3,
            reduction_steps=5,
            time_seconds=0.001
        )
        assert metrics.steps_per_size == 0.5
    
    def test_time_per_step(self):
        """Test time per step calculation."""
        metrics = ComplexityMetrics(
            form_size=10,
            form_depth=3,
            reduction_steps=5,
            time_seconds=0.010
        )
        assert metrics.time_per_step == 0.002
    
    def test_zero_handling(self):
        """Test zero values handled correctly."""
        metrics = ComplexityMetrics(
            form_size=0,
            form_depth=0,
            reduction_steps=0,
            time_seconds=0.0
        )
        assert metrics.steps_per_size == 0.0
        assert metrics.time_per_step == 0.0


class TestComplexityAnalysis:
    """Tests for ComplexityAnalysis class."""
    
    def test_analysis_creation(self):
        """Test analysis creation."""
        samples = [
            ComplexityMetrics(5, 2, 1, 0.001),
            ComplexityMetrics(10, 3, 2, 0.002),
        ]
        analysis = ComplexityAnalysis(samples=samples)
        assert len(analysis.samples) == 2
    
    def test_mean_steps(self):
        """Test mean steps calculation."""
        samples = [
            ComplexityMetrics(5, 2, 2, 0.001),
            ComplexityMetrics(10, 3, 4, 0.002),
        ]
        analysis = ComplexityAnalysis(samples=samples)
        assert analysis.mean_steps == 3.0
    
    def test_max_min_steps(self):
        """Test max/min steps."""
        samples = [
            ComplexityMetrics(5, 2, 1, 0.001),
            ComplexityMetrics(10, 3, 5, 0.002),
        ]
        analysis = ComplexityAnalysis(samples=samples)
        assert analysis.max_steps == 5
        assert analysis.min_steps == 1


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer class."""
    
    def test_analyzer_creation(self):
        """Test analyzer creation."""
        analyzer = ComplexityAnalyzer(seed=42)
        assert analyzer.seed == 42
    
    def test_measure_single(self):
        """Test measuring single form."""
        analyzer = ComplexityAnalyzer(seed=42)
        form = enclose(enclose(make_mark()))
        metrics = analyzer.measure_single(form)
        assert metrics.form_size >= 1
        assert metrics.reduction_steps >= 0
    
    def test_analyze_random_forms(self):
        """Test analyzing random forms."""
        analyzer = ComplexityAnalyzer(seed=42)
        analysis = analyzer.analyze_random_forms(n_samples=10, max_depth=3)
        assert len(analysis.samples) == 10
    
    def test_analyze_by_depth(self):
        """Test analysis grouped by depth."""
        analyzer = ComplexityAnalyzer(seed=42)
        results = analyzer.analyze_by_depth(depths=[1, 2, 3], samples_per_depth=5)
        assert len(results) == 3
        assert 1 in results
        assert 2 in results
        assert 3 in results
    
    def test_analyze_worst_case(self):
        """Test worst case analysis."""
        analyzer = ComplexityAnalyzer(seed=42)
        results = analyzer.analyze_worst_case(max_depth=5)
        assert "deep_calling" in results
        assert "wide_crossing" in results
        assert "mixed_pattern" in results


class TestAnalyzeFunctions:
    """Tests for analysis functions."""
    
    def test_analyze_reduction_complexity(self):
        """Test analyze_reduction_complexity function."""
        form = enclose(make_mark())
        result = analyze_reduction_complexity(form)
        assert "form" in result
        assert "size" in result
        assert "steps" in result
    
    def test_complexity_scaling_analysis(self):
        """Test scaling analysis."""
        result = complexity_scaling_analysis(max_depth=3, samples_per_depth=5)
        assert "depths" in result
        assert "mean_steps" in result
        assert "complexity_class" in result
    
    def test_termination_analysis(self):
        """Test termination analysis."""
        result = termination_analysis()
        assert "all_terminated" in result
        assert result["all_terminated"] == True
        assert result["termination_guaranteed"] == True
    
    def test_compare_to_sat(self):
        """Test SAT comparison."""
        result = compare_to_sat()
        assert "sat_complexity" in result
        assert "boundary_reduction" in result


class TestComplexityReport:
    """Tests for complexity report generation."""
    
    def test_generate_report(self):
        """Test report generation."""
        report = generate_complexity_report()
        assert "COMPLEXITY ANALYSIS" in report
        assert "TERMINATION" in report
        assert "SCALING" in report


class TestEdgeCases:
    """Tests for edge cases in complexity analysis."""
    
    def test_void_complexity(self):
        """Test complexity of void form."""
        result = analyze_reduction_complexity(make_void())
        assert result["size"] == 0
    
    def test_already_canonical(self):
        """Test complexity of already canonical form."""
        result = analyze_reduction_complexity(make_mark())
        assert result["steps"] == 0

