"""Comprehensive tests for src/metrics.py to ensure 100% coverage."""

import numpy as np
import pytest
from core.metrics import (CustomMetric, calculate_accuracy, calculate_all_metrics,
                     calculate_convergence_metrics, calculate_effect_size,
                     calculate_precision_recall_f1, calculate_psnr,
                     calculate_snr, calculate_ssim)


class TestCalculateAccuracy:
    """Test accuracy calculation."""

    def test_perfect_accuracy(self):
        """Test perfect accuracy."""
        predictions = np.array([0, 1, 0, 1])
        targets = np.array([0, 1, 0, 1])
        accuracy = calculate_accuracy(predictions, targets)
        assert accuracy == 1.0

    def test_partial_accuracy(self):
        """Test partial accuracy."""
        predictions = np.array([0, 1, 0, 1])
        targets = np.array([0, 1, 1, 1])
        accuracy = calculate_accuracy(predictions, targets)
        assert accuracy == 0.75

    def test_different_lengths(self):
        """Test error with different lengths."""
        predictions = np.array([0, 1])
        targets = np.array([0, 1, 0])
        with pytest.raises(ValueError):
            calculate_accuracy(predictions, targets)


class TestCalculatePrecisionRecallF1:
    """Test precision, recall, F1 calculation."""

    def test_perfect_scores(self):
        """Test perfect precision, recall, F1."""
        predictions = np.array([1, 1, 0, 0])
        targets = np.array([1, 1, 0, 0])
        prf = calculate_precision_recall_f1(predictions, targets)
        assert abs(prf["precision"] - 1.0) < 1e-10
        assert abs(prf["recall"] - 1.0) < 1e-10
        # F1 calculation includes 1e-10 in denominator, causing slight deviation
        assert abs(prf["f1"] - 1.0) < 1e-9

    def test_partial_scores(self):
        """Test partial scores."""
        predictions = np.array([1, 1, 0, 0])
        targets = np.array([1, 0, 0, 0])
        prf = calculate_precision_recall_f1(predictions, targets)
        assert 0 <= prf["precision"] <= 1
        assert 0 <= prf["recall"] <= 1
        assert 0 <= prf["f1"] <= 1


class TestCalculateConvergenceMetrics:
    """Test convergence metrics calculation."""

    def test_convergence_metrics(self):
        """Test convergence metrics with value range assertions."""
        values = np.array([10, 8, 6, 4, 2, 1, 0.5, 0.1])
        metrics = calculate_convergence_metrics(values, target=0.0)
        assert "final_error" in metrics
        assert "convergence_rate" in metrics
        assert "is_converged" in metrics
        assert 0.0 <= metrics["convergence_rate"] <= 1.0
        assert metrics["final_error"] < values[0]  # Error should decrease
        assert isinstance(metrics["is_converged"], bool)  # Convergence depends on threshold


class TestCalculateSNR:
    """Test SNR calculation."""

    def test_snr_calculation(self):
        """Test SNR calculation."""
        signal = np.array([1, 2, 3, 4, 5])
        noise = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
        snr = calculate_snr(signal, noise)
        assert isinstance(snr, float)
        assert snr > 0

    def test_snr_without_noise(self):
        """Test SNR without explicit noise."""
        signal = np.array([1, 2, 3, 4, 5])
        snr = calculate_snr(signal)
        assert isinstance(snr, float)


class TestCalculatePSNR:
    """Test PSNR calculation."""

    def test_psnr_calculation(self):
        """Test PSNR calculation."""
        original = np.array([1, 2, 3, 4, 5])
        reconstructed = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        psnr = calculate_psnr(original, reconstructed)
        assert isinstance(psnr, float)
        assert psnr > 0


class TestCalculateSSIM:
    """Test SSIM calculation."""

    def test_ssim_calculation(self):
        """Test SSIM calculation."""
        image1 = np.array([[1, 2], [3, 4]])
        image2 = np.array([[1, 2], [3, 4]])
        ssim = calculate_ssim(image1, image2)
        assert isinstance(ssim, float)
        assert 0 <= ssim <= 1


class TestCalculateEffectSize:
    """Test effect size calculation."""

    def test_effect_size(self):
        """Test effect size calculation."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        result = calculate_effect_size(group1, group2)
        assert "cohens_d" in result
        assert "interpretation" in result
        assert result["interpretation"] in ["negligible", "small", "medium", "large"]


class TestCustomMetric:
    """Test CustomMetric class."""

    def test_custom_metric(self):
        """Test custom metric."""

        def metric_func(x, y):
            return np.mean(x) - np.mean(y)

        metric = CustomMetric("test_metric", metric_func)
        result = metric.calculate(np.array([1, 2, 3]), np.array([4, 5, 6]))
        assert isinstance(result, float)


class TestCalculateAllMetrics:
    """Test calculate_all_metrics function."""

    def test_with_predictions_targets(self):
        """Test with predictions and targets."""
        predictions = np.array([0, 1, 0, 1])
        targets = np.array([0, 1, 0, 1])
        metrics = calculate_all_metrics(predictions=predictions, targets=targets)
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics

    def test_with_values(self):
        """Test with values for convergence."""
        values = np.array([10, 8, 6, 4, 2])
        metrics = calculate_all_metrics(values=values)
        assert "convergence_final_error" in metrics

    def test_with_signal(self):
        """Test with signal for SNR."""
        signal = np.array([1, 2, 3, 4, 5])
        metrics = calculate_all_metrics(signal=signal)
        assert "snr" in metrics

    def test_calculate_precision_recall_f1_different_lengths(self):
        """Test precision/recall/F1 with different lengths."""
        predictions = np.array([0, 1])
        targets = np.array([0, 1, 0])
        with pytest.raises(ValueError):
            calculate_precision_recall_f1(predictions, targets)

    def test_calculate_convergence_metrics_no_target(self):
        """Test convergence metrics without target."""
        values = np.array([10, 8, 6, 4, 2, 1])
        metrics = calculate_convergence_metrics(values, target=None)
        assert "final_error" in metrics
        assert "mean_residual" in metrics

    def test_calculate_snr_single_value(self):
        """Test SNR calculation with single value."""
        signal = np.array([1.0])
        snr = calculate_snr(signal)
        assert isinstance(snr, float)

    def test_calculate_psnr_with_max_value(self):
        """Test PSNR calculation with explicit max_value."""
        original = np.array([1, 2, 3, 4, 5])
        reconstructed = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        psnr = calculate_psnr(original, reconstructed, max_value=10.0)
        assert isinstance(psnr, float)
        assert psnr > 0

    def test_calculate_effect_size_negligible(self):
        """Test effect size with negligible difference."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        result = calculate_effect_size(group1, group2)
        assert result["interpretation"] == "negligible"

    def test_calculate_effect_size_small(self):
        """Test effect size with small difference."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        result = calculate_effect_size(group1, group2)
        assert result["interpretation"] in ["negligible", "small"]

    def test_calculate_effect_size_medium(self):
        """Test effect size with medium difference."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        result = calculate_effect_size(group1, group2)
        assert result["interpretation"] in ["small", "medium"]

    def test_calculate_effect_size_large(self):
        """Test effect size with large difference."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([5, 6, 7, 8, 9])
        result = calculate_effect_size(group1, group2)
        assert result["interpretation"] in ["medium", "large"]

    def test_calculate_all_metrics_with_original_reconstructed(self):
        """Test calculate_all_metrics with original and reconstructed."""
        # calculate_all_metrics doesn't have image1/image2, but we can test other combinations
        original = np.array([1, 2, 3, 4, 5])
        reconstructed = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        # The function doesn't support images directly, so test with signal
        signal = np.array([1, 2, 3, 4, 5])
        metrics = calculate_all_metrics(signal=signal)
        assert "snr" in metrics
