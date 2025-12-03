"""Metrics calculation for scientific computing.

This module provides performance metrics, convergence metrics,
quality metrics, statistical metrics, and a custom metric framework.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


def calculate_accuracy(
    predictions: np.ndarray,
    targets: np.ndarray
) -> float:
    """Calculate accuracy for classification.
    
    Args:
        predictions: Predicted labels
        targets: True labels
        
    Returns:
        Accuracy (0-1)
    """
    if len(predictions) != len(targets):
        raise ValueError("predictions and targets must have same length")
    
    correct = np.sum(predictions == targets)
    return float(correct / len(predictions))


def calculate_precision_recall_f1(
    predictions: np.ndarray,
    targets: np.ndarray,
    positive_class: int = 1
) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score.
    
    Args:
        predictions: Predicted labels
        targets: True labels
        positive_class: Label for positive class
        
    Returns:
        Dictionary with precision, recall, and f1
    """
    if len(predictions) != len(targets):
        raise ValueError("predictions and targets must have same length")
    
    true_positives = np.sum((predictions == positive_class) & (targets == positive_class))
    false_positives = np.sum((predictions == positive_class) & (targets != positive_class))
    false_negatives = np.sum((predictions != positive_class) & (targets == positive_class))
    
    precision = true_positives / (true_positives + false_positives + 1e-10)
    recall = true_positives / (true_positives + false_negatives + 1e-10)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
    
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    }


def calculate_convergence_metrics(
    values: np.ndarray,
    target: Optional[float] = None
) -> Dict[str, float]:
    """Calculate convergence metrics.
    
    Args:
        values: Sequence of values
        target: Target value (if known)
        
    Returns:
        Dictionary with convergence metrics
    """
    from performance import analyze_convergence
    
    convergence = analyze_convergence(values, target)
    
    # Calculate residuals
    if target is not None:
        residuals = np.abs(values - target)
    else:
        # Use relative change
        residuals = np.abs(np.diff(values))
        residuals = np.concatenate([[residuals[0]], residuals])
    
    return {
        "final_error": convergence.error,
        "convergence_rate": convergence.convergence_rate or 0.0,
        "iterations_to_convergence": convergence.iterations_to_convergence or len(values),
        "is_converged": convergence.is_converged,
        "mean_residual": float(np.mean(residuals)),
        "max_residual": float(np.max(residuals)),
        "final_residual": float(residuals[-1])
    }


def calculate_snr(
    signal: np.ndarray,
    noise: Optional[np.ndarray] = None
) -> float:
    """Calculate Signal-to-Noise Ratio (SNR).
    
    Args:
        signal: Signal values
        noise: Noise values (if None, estimates from signal)
        
    Returns:
        SNR in dB
    """
    signal_power = np.mean(signal ** 2)
    
    if noise is not None:
        noise_power = np.mean(noise ** 2)
    else:
        # Estimate noise as high-frequency component
        if len(signal) > 1:
            noise_estimate = np.std(np.diff(signal))
            noise_power = noise_estimate ** 2
        else:
            noise_power = 1e-10
    
    snr_linear = signal_power / (noise_power + 1e-10)
    snr_db = 10 * np.log10(snr_linear + 1e-10)
    
    return float(snr_db)


def calculate_psnr(
    original: np.ndarray,
    reconstructed: np.ndarray,
    max_value: Optional[float] = None
) -> float:
    """Calculate Peak Signal-to-Noise Ratio (PSNR).
    
    Args:
        original: Original signal
        reconstructed: Reconstructed signal
        max_value: Maximum possible value (if None, uses max of original)
        
    Returns:
        PSNR in dB
    """
    if max_value is None:
        max_value = np.max(original)
    
    mse = np.mean((original - reconstructed) ** 2)
    psnr = 10 * np.log10((max_value ** 2) / (mse + 1e-10))
    
    return float(psnr)


def calculate_ssim(
    image1: np.ndarray,
    image2: np.ndarray,
    window_size: int = 11
) -> float:
    """Calculate Structural Similarity Index (SSIM).
    
    Simplified implementation - for full SSIM use scipy or skimage.
    
    Args:
        image1: First image
        image2: Second image
        window_size: Window size for local SSIM
        
    Returns:
        SSIM value (0-1)
    """
    # Simplified SSIM calculation
    mu1 = np.mean(image1)
    mu2 = np.mean(image2)
    
    sigma1_sq = np.var(image1)
    sigma2_sq = np.var(image2)
    sigma12 = np.mean((image1 - mu1) * (image2 - mu2))
    
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2) + 1e-10
    )
    
    return float(ssim)


def calculate_effect_size(
    group1: np.ndarray,
    group2: np.ndarray
) -> Dict[str, float]:
    """Calculate effect size (Cohen's d).
    
    Args:
        group1: First group
        group2: Second group
        
    Returns:
        Dictionary with effect size and interpretation
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2))
    
    # Cohen's d
    cohens_d = (mean1 - mean2) / (pooled_std + 1e-10)
    
    # Interpretation
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = "negligible"
    elif abs_d < 0.5:
        interpretation = "small"
    elif abs_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"
    
    return {
        "cohens_d": float(cohens_d),
        "interpretation": interpretation,
        "mean1": float(mean1),
        "mean2": float(mean2),
        "pooled_std": float(pooled_std)
    }


def calculate_p_value_approximation(
    statistic: float,
    distribution: str = "normal"
) -> float:
    """Approximate p-value from test statistic.
    
    Simplified approximation - for accurate p-values use scipy.stats.
    
    Args:
        statistic: Test statistic value
        distribution: Distribution type (normal, t, chi2)
        
    Returns:
        Approximate p-value
    """
    # Simplified p-value calculation
    # In practice, use proper statistical distributions
    abs_stat = abs(statistic)
    
    if distribution == "normal":
        # Normal distribution approximation
        if abs_stat > 3:
            p_value = 0.001
        elif abs_stat > 2:
            p_value = 0.05
        else:
            p_value = 0.1
    else:
        # Default approximation
        p_value = 0.05
    
    return float(p_value)


class CustomMetric:
    """Framework for custom metrics."""
    
    def __init__(self, name: str, metric_function: Callable):
        """Initialize custom metric.
        
        Args:
            name: Metric name
            metric_function: Function that calculates the metric
        """
        self.name = name
        self.metric_function = metric_function
    
    def calculate(self, *args, **kwargs) -> float:
        """Calculate the metric.
        
        Args:
            *args: Positional arguments for metric function
            **kwargs: Keyword arguments for metric function
            
        Returns:
            Metric value
        """
        return float(self.metric_function(*args, **kwargs))


def calculate_all_metrics(
    predictions: Optional[np.ndarray] = None,
    targets: Optional[np.ndarray] = None,
    values: Optional[np.ndarray] = None,
    signal: Optional[np.ndarray] = None,
    noise: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate all applicable metrics.
    
    Args:
        predictions: Predicted values (for classification metrics)
        targets: True values (for classification metrics)
        values: Sequence values (for convergence metrics)
        signal: Signal values (for SNR)
        noise: Noise values (for SNR)
        
    Returns:
        Dictionary of all calculated metrics
    """
    metrics = {}
    
    # Classification metrics
    if predictions is not None and targets is not None:
        metrics["accuracy"] = calculate_accuracy(predictions, targets)
        prf = calculate_precision_recall_f1(predictions, targets)
        metrics.update(prf)
    
    # Convergence metrics
    if values is not None:
        conv_metrics = calculate_convergence_metrics(values)
        metrics.update({f"convergence_{k}": v for k, v in conv_metrics.items()})
    
    # Signal quality metrics
    if signal is not None:
        metrics["snr"] = calculate_snr(signal, noise)
    
    return metrics


# ============================================================================
# WAYS-SPECIFIC METRICS FUNCTIONS
# ============================================================================

def compute_way_coverage_metrics(db) -> Dict[str, Any]:
    """Compute coverage metrics for ways across rooms and frameworks.

    Args:
        db: Database connection instance

    Returns:
        Coverage metrics analysis
    """
    from .sql_queries import WaysSQLQueries
    queries = WaysSQLQueries()

    # Get room statistics
    _, room_stats = queries.get_room_statistics_sql()
    _, room_counts = queries.count_ways_by_room_sql()

    total_ways = sum(count for _, count in room_counts)
    occupied_rooms = sum(1 for _, count in room_counts if count > 0)

    # Calculate coverage metrics
    coverage_metrics = {
        'overall_coverage': {
            'total_ways': total_ways,
            'occupied_rooms': occupied_rooms,
            'total_rooms': len(room_stats),
            'room_coverage_ratio': occupied_rooms / len(room_stats) if room_stats else 0,
            'ways_per_room_avg': total_ways / occupied_rooms if occupied_rooms > 0 else 0
        },
        'room_coverage': {}
    }

    # Individual room coverage
    for row in room_stats:
        room_short = row[0]
        way_count = row[2]
        coverage_metrics['room_coverage'][room_short] = {
            'ways': way_count,
            'coverage_ratio': way_count / total_ways if total_ways > 0 else 0,
            'relative_to_avg': way_count / coverage_metrics['overall_coverage']['ways_per_room_avg'] if coverage_metrics['overall_coverage']['ways_per_room_avg'] > 0 else 0
        }

    return coverage_metrics


def compute_framework_completeness(db) -> Dict[str, Any]:
    """Compute completeness metrics for philosophical frameworks.

    Args:
        db: Database connection instance

    Returns:
        Framework completeness analysis
    """
    from .house_of_knowledge import HouseOfKnowledgeAnalyzer
    analyzer = HouseOfKnowledgeAnalyzer()

    framework_stats = analyzer.get_framework_statistics()

    completeness_metrics = {}

    for framework_name, stats in framework_stats.items():
        if framework_name == 'house_overall':
            continue

        completeness_metrics[framework_name] = {
            'total_ways': stats['total_ways'],
            'room_coverage': stats['room_coverage'],
            'balance_score': stats['balance_score'],
            'type_diversity': stats['type_diversity'],
            'completeness_score': (
                stats['room_coverage'] * 0.4 +
                min(stats['balance_score'], 1.0) * 0.3 +
                min(stats['type_diversity'] / 10, 1.0) * 0.3
            ),
            'room_details': stats['room_details']
        }

    # Overall completeness
    framework_completeness_scores = [m['completeness_score'] for m in completeness_metrics.values()]
    completeness_metrics['overall'] = {
        'avg_completeness': sum(framework_completeness_scores) / len(framework_completeness_scores) if framework_completeness_scores else 0,
        'frameworks_analyzed': len(completeness_metrics),
        'most_complete': max(completeness_metrics.keys(), key=lambda k: completeness_metrics[k]['completeness_score']) if completeness_metrics else None,
        'least_complete': min(completeness_metrics.keys(), key=lambda k: completeness_metrics[k]['completeness_score']) if completeness_metrics else None
    }

    return completeness_metrics


def compute_way_interconnectedness(db) -> Dict[str, Any]:
    """Compute interconnectedness metrics for ways network.

    Args:
        db: Database connection instance

    Returns:
        Network interconnectedness analysis
    """
    from .network_analysis import WaysNetworkAnalyzer
    analyzer = WaysNetworkAnalyzer()

    network = analyzer.build_ways_network()
    metrics = analyzer.compute_centrality_metrics()
    communities = analyzer.detect_communities()

    interconnectedness = {
        'network_structure': {
            'nodes': metrics.node_count,
            'edges': metrics.edge_count,
            'density': metrics.density,
            'avg_degree': metrics.average_degree,
            'connected_components': metrics.connected_components,
            'largest_component_ratio': metrics.largest_component_size / metrics.node_count if metrics.node_count > 0 else 0
        },
        'centrality_measures': {
            'degree_centralization': 0.0,  # Would need full calculation
            'betweenness_centralization': 0.0,
            'closeness_centralization': 0.0
        },
        'community_structure': {
            'communities': len(communities.communities),
            'modularity': communities.modularity,
            'largest_community': max(communities.community_sizes) if communities.community_sizes else 0,
            'community_balance': len([c for c in communities.community_sizes if c > 1]) / len(communities.community_sizes) if communities.community_sizes else 0
        },
        'interconnectedness_score': (
            metrics.density * 0.3 +
            (1.0 / metrics.connected_components if metrics.connected_components > 0 else 1.0) * 0.3 +
            communities.modularity * 0.4
        )
    }

    return interconnectedness


def compute_room_balance_metrics(db) -> Dict[str, Any]:
    """Compute balance metrics across rooms in the House of Knowledge.

    Args:
        db: Database connection instance

    Returns:
        Room balance analysis
    """
    from .sql_queries import WaysSQLQueries
    queries = WaysSQLQueries()

    # Get room statistics
    _, room_stats = queries.get_room_statistics_sql()

    balance_metrics = {
        'room_distribution': {},
        'balance_analysis': {}
    }

    # Extract way counts per room
    way_counts = []
    room_names = []

    for row in room_stats:
        room_short = row[0]
        way_count = row[2]
        way_counts.append(way_count)
        room_names.append(room_short)

        balance_metrics['room_distribution'][room_short] = {
            'ways': way_count,
            'relative_weight': 0.0  # Will calculate below
        }

        # Calculate balance metrics
        if way_counts:
            total_ways = sum(way_counts)
            mean_ways = sum(way_counts) / len(way_counts)

        # Calculate relative weights
        for i, room in enumerate(room_names):
            weight = way_counts[i] / total_ways if total_ways > 0 else 0
            balance_metrics['room_distribution'][room]['relative_weight'] = weight

        # Overall balance analysis
        if len(way_counts) > 1:
            variance = sum((x - mean_ways) ** 2 for x in way_counts) / (len(way_counts) - 1)
            std_dev = variance ** 0.5
            cv = std_dev / mean_ways if mean_ways > 0 else 0  # Coefficient of variation

            balance_metrics['balance_analysis'] = {
                'mean_ways_per_room': mean_ways,
                'variance': variance,
                'std_deviation': std_dev,
                'coefficient_of_variation': cv,
                'balance_score': 1.0 / (1.0 + cv),  # Higher score = more balanced
                'assessment': 'well_balanced' if cv < 0.3 else 'moderately_balanced' if cv < 0.6 else 'unbalanced'
            }
        else:
            balance_metrics['balance_analysis'] = {
                'mean_ways_per_room': mean_ways,
                'variance': 0,
                'std_deviation': 0,
                'coefficient_of_variation': 0,
                'balance_score': 1.0,
                'assessment': 'single_room'
            }

        # Identify outliers
        balance_metrics['outliers'] = {
            'high_outliers': [room for room, data in balance_metrics['room_distribution'].items()
                            if data['ways'] > mean_ways + 2 * balance_metrics['balance_analysis']['std_deviation']],
            'low_outliers': [room for room, data in balance_metrics['room_distribution'].items()
                           if data['ways'] < mean_ways - 2 * balance_metrics['balance_analysis']['std_deviation']]
        }

    return balance_metrics

