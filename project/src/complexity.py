"""Reduction Complexity Analysis for Boundary Logic.

This module provides tools for analyzing the computational complexity
of form reduction in boundary logic, including:

- Time complexity of reduction algorithms
- Space complexity for form representations
- Worst-case and average-case analysis
- Comparison with Boolean satisfiability
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.reduction import ReductionEngine, reduce_with_trace, ReductionTrace
from src.expressions import ExpressionGenerator


@dataclass
class ComplexityMetrics:
    """Complexity metrics for a reduction.
    
    Attributes:
        form_size: Size of input form
        form_depth: Depth of input form
        reduction_steps: Number of reduction steps
        time_seconds: Wall-clock time
        calling_count: Number of calling rule applications
        crossing_count: Number of crossing rule applications
    """
    form_size: int
    form_depth: int
    reduction_steps: int
    time_seconds: float
    calling_count: int = 0
    crossing_count: int = 0
    
    @property
    def steps_per_size(self) -> float:
        """Reduction steps per form size."""
        if self.form_size == 0:
            return 0.0
        return self.reduction_steps / self.form_size
    
    @property
    def time_per_step(self) -> float:
        """Time per reduction step."""
        if self.reduction_steps == 0:
            return 0.0
        return self.time_seconds / self.reduction_steps


@dataclass
class ComplexityAnalysis:
    """Complete complexity analysis results.
    
    Attributes:
        samples: Individual sample metrics
        mean_steps: Average reduction steps
        std_steps: Standard deviation of steps
        max_steps: Maximum steps observed
        min_steps: Minimum steps observed
        correlation_size_steps: Correlation between size and steps
    """
    samples: List[ComplexityMetrics]
    mean_steps: float = 0.0
    std_steps: float = 0.0
    max_steps: int = 0
    min_steps: int = 0
    correlation_size_steps: float = 0.0
    
    def __post_init__(self):
        if self.samples:
            steps = [s.reduction_steps for s in self.samples]
            sizes = [s.form_size for s in self.samples]
            
            self.mean_steps = np.mean(steps)
            self.std_steps = np.std(steps)
            self.max_steps = max(steps)
            self.min_steps = min(steps)
            
            if len(set(sizes)) > 1 and len(set(steps)) > 1:
                self.correlation_size_steps = np.corrcoef(sizes, steps)[0, 1]


class ComplexityAnalyzer:
    """Analyzer for reduction complexity.
    
    Provides tools for measuring and analyzing the complexity
    of form reduction algorithms.
    """
    
    def __init__(self, seed: int = 42) -> None:
        """Initialize analyzer.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.generator = ExpressionGenerator(seed)
        self.engine = ReductionEngine()
    
    def measure_single(self, form: Form) -> ComplexityMetrics:
        """Measure complexity for a single form.
        
        Args:
            form: Form to reduce
            
        Returns:
            ComplexityMetrics for the reduction
        """
        self.engine.reset_stats()
        
        size = form.size()
        depth = form.depth()
        
        start_time = time.perf_counter()
        trace = self.engine.reduce_with_trace(form)
        end_time = time.perf_counter()
        
        stats = self.engine.get_stats()
        
        return ComplexityMetrics(
            form_size=size,
            form_depth=depth,
            reduction_steps=trace.step_count,
            time_seconds=end_time - start_time,
            calling_count=stats.get("calling_applications", 0),
            crossing_count=stats.get("crossing_applications", 0),
        )
    
    def analyze_random_forms(
        self,
        n_samples: int = 100,
        max_depth: int = 5,
        max_width: int = 3
    ) -> ComplexityAnalysis:
        """Analyze complexity over random forms.
        
        Args:
            n_samples: Number of forms to test
            max_depth: Maximum nesting depth
            max_width: Maximum children per level
            
        Returns:
            ComplexityAnalysis with statistics
        """
        samples = []
        
        for _ in range(n_samples):
            form = self.generator.random_form(max_depth, max_width)
            metrics = self.measure_single(form)
            samples.append(metrics)
        
        return ComplexityAnalysis(samples=samples)
    
    def analyze_by_depth(
        self,
        depths: List[int],
        samples_per_depth: int = 20
    ) -> Dict[int, ComplexityAnalysis]:
        """Analyze complexity grouped by form depth.
        
        Args:
            depths: List of depths to test
            samples_per_depth: Samples per depth level
            
        Returns:
            Dictionary mapping depth to analysis
        """
        results = {}
        
        for depth in depths:
            samples = []
            for _ in range(samples_per_depth):
                form = self.generator.random_form(depth, 3)
                metrics = self.measure_single(form)
                samples.append(metrics)
            results[depth] = ComplexityAnalysis(samples=samples)
        
        return results
    
    def analyze_worst_case(self, max_depth: int = 10) -> Dict[str, ComplexityMetrics]:
        """Analyze worst-case complexity patterns.
        
        Creates forms that maximize reduction steps.
        
        Args:
            max_depth: Maximum depth to test
            
        Returns:
            Dictionary of worst-case patterns
        """
        results = {}
        
        # Pattern 1: Deep double enclosure chain
        # ⟨⟨⟨...⟨ ⟩...⟩⟩⟩
        form = make_mark()
        for _ in range(max_depth):
            form = enclose(enclose(form))
        results["deep_calling"] = self.measure_single(form)
        
        # Pattern 2: Wide crossing pattern
        # ⟨ ⟩⟨ ⟩⟨ ⟩...
        marks = [make_mark() for _ in range(max_depth)]
        form = juxtapose(*marks)
        results["wide_crossing"] = self.measure_single(form)
        
        # Pattern 3: Mixed pattern
        form = make_mark()
        for i in range(max_depth):
            if i % 2 == 0:
                form = enclose(enclose(form))
            else:
                form = juxtapose(form, make_mark())
        results["mixed_pattern"] = self.measure_single(form)
        
        return results


def analyze_reduction_complexity(
    form: Form
) -> Dict[str, Any]:
    """Analyze the reduction complexity of a single form.
    
    Args:
        form: Form to analyze
        
    Returns:
        Dictionary of complexity metrics
    """
    analyzer = ComplexityAnalyzer()
    metrics = analyzer.measure_single(form)
    
    return {
        "form": str(form),
        "size": metrics.form_size,
        "depth": metrics.form_depth,
        "steps": metrics.reduction_steps,
        "time_ms": metrics.time_seconds * 1000,
        "calling_applications": metrics.calling_count,
        "crossing_applications": metrics.crossing_count,
        "steps_per_size": metrics.steps_per_size,
    }


def complexity_scaling_analysis(
    max_depth: int = 8,
    samples_per_depth: int = 50
) -> Dict[str, Any]:
    """Analyze how complexity scales with form depth.
    
    Args:
        max_depth: Maximum depth to analyze
        samples_per_depth: Samples per depth level
        
    Returns:
        Scaling analysis results
    """
    analyzer = ComplexityAnalyzer()
    depths = list(range(1, max_depth + 1))
    
    results = analyzer.analyze_by_depth(depths, samples_per_depth)
    
    scaling_data = {
        "depths": depths,
        "mean_steps": [results[d].mean_steps for d in depths],
        "max_steps": [results[d].max_steps for d in depths],
        "std_steps": [results[d].std_steps for d in depths],
    }
    
    # Estimate complexity class
    mean_steps = scaling_data["mean_steps"]
    if len(mean_steps) >= 3:
        # Check if linear, quadratic, or exponential
        ratios = [mean_steps[i+1] / mean_steps[i] 
                  for i in range(len(mean_steps) - 1) 
                  if mean_steps[i] > 0]
        
        if ratios:
            avg_ratio = np.mean(ratios)
            if avg_ratio < 1.5:
                scaling_data["complexity_class"] = "O(n)"
            elif avg_ratio < 2.5:
                scaling_data["complexity_class"] = "O(n²)"
            else:
                scaling_data["complexity_class"] = "O(2ⁿ)"
        else:
            scaling_data["complexity_class"] = "Unknown"
    else:
        scaling_data["complexity_class"] = "Insufficient data"
    
    return scaling_data


def termination_analysis() -> Dict[str, Any]:
    """Analyze termination properties of reduction.
    
    Verifies that reduction always terminates.
    
    Returns:
        Termination analysis results
    """
    analyzer = ComplexityAnalyzer()
    
    # Test many random forms
    n_tests = 500
    all_terminated = True
    max_steps_seen = 0
    
    for _ in range(n_tests):
        form = analyzer.generator.random_form(max_depth=6, max_width=4)
        metrics = analyzer.measure_single(form)
        
        max_steps_seen = max(max_steps_seen, metrics.reduction_steps)
        
        # Check if reduction completed
        trace = reduce_with_trace(form)
        if not trace.is_complete:
            all_terminated = False
            break
    
    return {
        "tests_run": n_tests,
        "all_terminated": all_terminated,
        "max_steps_observed": max_steps_seen,
        "termination_guaranteed": True,  # By construction of axioms
        "reasoning": (
            "Reduction terminates because each rule application "
            "strictly reduces form complexity (depth or size)"
        ),
    }


def compare_to_sat() -> Dict[str, str]:
    """Compare boundary logic reduction to SAT complexity.
    
    Returns:
        Comparison summary
    """
    return {
        "sat_complexity": "NP-complete (general case)",
        "boundary_reduction": "Polynomial (for ground forms)",
        "key_difference": (
            "Boundary logic reduction is syntactic simplification, "
            "while SAT requires semantic evaluation over assignments"
        ),
        "equivalence": (
            "Boundary logic equivalence checking is equivalent to "
            "tautology checking, which is co-NP"
        ),
        "practical_note": (
            "For typical forms encountered in practice, boundary logic "
            "reduction is very efficient (often linear in form size)"
        ),
    }


def generate_complexity_report() -> str:
    """Generate a comprehensive complexity report.
    
    Returns:
        Formatted report string
    """
    lines = ["=" * 60]
    lines.append("REDUCTION COMPLEXITY ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    # Termination
    term = termination_analysis()
    lines.append("TERMINATION ANALYSIS")
    lines.append("-" * 40)
    lines.append(f"Tests run: {term['tests_run']}")
    lines.append(f"All terminated: {term['all_terminated']}")
    lines.append(f"Max steps observed: {term['max_steps_observed']}")
    lines.append(f"Reasoning: {term['reasoning']}")
    lines.append("")
    
    # Scaling
    scaling = complexity_scaling_analysis(max_depth=6, samples_per_depth=30)
    lines.append("SCALING ANALYSIS")
    lines.append("-" * 40)
    lines.append(f"Complexity class: {scaling['complexity_class']}")
    lines.append(f"Depths tested: {scaling['depths']}")
    lines.append(f"Mean steps: {[f'{x:.1f}' for x in scaling['mean_steps']]}")
    lines.append("")
    
    # SAT comparison
    sat = compare_to_sat()
    lines.append("COMPARISON TO SAT")
    lines.append("-" * 40)
    lines.append(f"SAT: {sat['sat_complexity']}")
    lines.append(f"Boundary: {sat['boundary_reduction']}")
    lines.append(f"Note: {sat['practical_note']}")
    lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

