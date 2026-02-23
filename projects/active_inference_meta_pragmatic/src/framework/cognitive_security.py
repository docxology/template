"""Cognitive Security Analysis for Active Inference Meta-Pragmatic Framework.

This module implements computational models from Section 07 (Security Implications),
analyzing cognitive security through the lens of the 2x2 quadrant framework.
Each quadrant creates different attack surfaces and defense mechanisms in
Active Inference systems.

Key Concepts:
- Attack Surface Analysis: Vulnerability assessment per quadrant
- Parameter Drift Detection: Monitoring adversarial manipulation of A/B/C/D matrices
- Anomaly Detection: KL divergence-based belief state monitoring
- Framework Integrity Validation: Tamper detection for generative models
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from utils.exceptions import ValidationError
from utils.logging import get_logger

logger = get_logger(__name__)

# Quadrant-specific vulnerability profiles
_QUADRANT_PROFILES = {
    1: {
        "name": "Data-Cognitive",
        "base_vulnerability": 0.3,
        "meta_level_exposure": 0.2,
        "attack_vectors": [
            "Observation injection (corrupted sensory data)",
            "Likelihood manipulation (A-matrix poisoning)",
            "State confusion (ambiguous observations)",
        ],
        "defense_mechanisms": [
            "Observation validation against priors",
            "Redundant sensory channels",
            "Anomaly detection on raw inputs",
        ],
    },
    2: {
        "name": "MetaData-Cognitive",
        "base_vulnerability": 0.4,
        "meta_level_exposure": 0.4,
        "attack_vectors": [
            "Schema poisoning (corrupted meta-data structures)",
            "Category confusion (misclassification of data types)",
            "Transition model corruption (B-matrix tampering)",
        ],
        "defense_mechanisms": [
            "Schema validation checksums",
            "Type-level consistency checking",
            "Transition probability auditing",
        ],
    },
    3: {
        "name": "Data-MetaCognitive",
        "base_vulnerability": 0.55,
        "meta_level_exposure": 0.7,
        "attack_vectors": [
            "Confidence manipulation (inflating/deflating belief certainty)",
            "Attention hijacking (redirecting meta-cognitive monitoring)",
            "Reflective loop poisoning (corrupted self-assessment)",
            "Preference drift (C-matrix gradual manipulation)",
        ],
        "defense_mechanisms": [
            "Confidence bounds enforcement",
            "Attention allocation auditing",
            "Self-assessment cross-validation",
            "Preference stability monitoring",
        ],
    },
    4: {
        "name": "MetaData-MetaCognitive",
        "base_vulnerability": 0.7,
        "meta_level_exposure": 0.9,
        "attack_vectors": [
            "Meta-model corruption (tampering with models of models)",
            "Strategy manipulation (subverting strategy selection)",
            "Epistemic value distortion (corrupting exploration drives)",
            "Framework-level injection (altering the quadrant structure itself)",
            "Prior belief manipulation (D-matrix attacks)",
        ],
        "defense_mechanisms": [
            "Multi-layer integrity verification",
            "Strategy diversity enforcement",
            "Epistemic value bounds checking",
            "Constitutional validation of framework axioms",
            "Prior distribution monitoring",
        ],
    },
}


class CognitiveSecurityAnalyzer:
    """Implements computational models from Section 07 (Security Implications).

    Analyzes cognitive security through the lens of the 2x2 quadrant framework,
    examining how each quadrant creates different attack surfaces and defense
    mechanisms.
    """

    def __init__(self, quadrant_framework: Optional[object] = None) -> None:
        """Initialize with optional quadrant framework reference.

        Args:
            quadrant_framework: Optional QuadrantFramework instance for integration.
        """
        self.quadrant_framework = quadrant_framework
        self._drift_history: List[Dict] = []
        logger.info("Initialized CognitiveSecurityAnalyzer")

    def analyze_attack_surface(self, quadrant: int) -> Dict[str, Union[float, List[str]]]:
        """Analyze attack surface for a specific quadrant (1-4).

        Each quadrant in the 2x2 framework (Data/MetaData x Cognitive/MetaCognitive)
        exposes different vulnerabilities based on its processing level and
        information type.

        Args:
            quadrant: Quadrant number (1-4).

        Returns:
            Dict with:
            - vulnerability_score: float (0-1), composite risk metric
            - attack_vectors: list of identified attack vectors
            - defense_mechanisms: list of available defenses
            - meta_level_exposure: float, higher for Q3/Q4

        Raises:
            ValidationError: If quadrant is not 1-4.
        """
        if quadrant not in (1, 2, 3, 4):
            raise ValidationError(f"Quadrant must be 1-4, got {quadrant}")

        profile = _QUADRANT_PROFILES[quadrant]

        # Compute vulnerability score from base + meta-level exposure
        vulnerability_score = float(
            np.clip(
                profile["base_vulnerability"] * 0.6 + profile["meta_level_exposure"] * 0.4,
                0.0,
                1.0,
            )
        )

        result = {
            "quadrant": quadrant,
            "quadrant_name": profile["name"],
            "vulnerability_score": vulnerability_score,
            "attack_vectors": list(profile["attack_vectors"]),
            "defense_mechanisms": list(profile["defense_mechanisms"]),
            "meta_level_exposure": profile["meta_level_exposure"],
        }

        logger.debug(f"Attack surface Q{quadrant}: vulnerability={vulnerability_score:.3f}")
        return result

    def simulate_parameter_drift(
        self,
        params: Dict[str, NDArray],
        noise_level: float = 0.1,
        steps: int = 100,
    ) -> Dict[str, Union[NDArray, float, bool]]:
        """Simulate gradual parameter drift in generative model matrices.

        Models adversarial manipulation of A/B/C/D matrices over time by
        injecting small perturbations and tracking cumulative drift.

        Args:
            params: Dictionary mapping matrix names ('A', 'B', 'C', 'D')
                to their numpy array values.
            noise_level: Standard deviation of Gaussian noise per step.
            steps: Number of simulation steps.

        Returns:
            Dict with:
            - drift_trajectory: dict of matrix name to (steps,) array of
              Frobenius norm drift from original
            - total_drift: float, sum of final drift across all matrices
            - drift_detected: bool, True if total drift exceeds detection threshold
            - detection_threshold: float, the threshold used
            - steps: int, number of steps simulated

        Raises:
            ValidationError: If params is empty or noise_level is negative.
        """
        if not params:
            raise ValidationError("params dictionary must not be empty")
        if noise_level < 0:
            raise ValidationError(f"noise_level must be non-negative, got {noise_level}")
        if steps < 1:
            raise ValidationError(f"steps must be >= 1, got {steps}")

        rng = np.random.default_rng(seed=42)
        drift_trajectory: Dict[str, NDArray] = {}

        for name, matrix in params.items():
            original = matrix.copy().astype(float)
            current = original.copy()
            norms = np.zeros(steps)

            for t in range(steps):
                perturbation = rng.normal(0, noise_level, size=current.shape)
                current = current + perturbation
                norms[t] = float(np.linalg.norm(current - original))

            drift_trajectory[name] = norms

        # Total drift is sum of final drift values
        total_drift = float(sum(trajectory[-1] for trajectory in drift_trajectory.values()))

        # Detection threshold: scale with dimensionality and noise
        total_params = sum(m.size for m in params.values())
        detection_threshold = float(noise_level * np.sqrt(total_params * steps) * 0.5)

        drift_detected = total_drift > detection_threshold

        result = {
            "drift_trajectory": drift_trajectory,
            "total_drift": total_drift,
            "drift_detected": drift_detected,
            "detection_threshold": detection_threshold,
            "steps": steps,
        }

        self._drift_history.append(
            {
                "total_drift": total_drift,
                "detected": drift_detected,
            }
        )

        logger.debug(
            f"Parameter drift simulation: total_drift={total_drift:.4f}, detected={drift_detected}"
        )
        return result

    def detect_anomaly(
        self,
        beliefs: NDArray,
        baseline: NDArray,
        threshold: float = 0.05,
    ) -> Dict[str, Union[bool, float, str]]:
        """Detect anomalous belief states using KL divergence from baseline.

        Computes KL(beliefs || baseline) and classifies severity.

        Args:
            beliefs: Current belief distribution (must sum to ~1).
            baseline: Reference/expected belief distribution (must sum to ~1).
            threshold: KL divergence threshold for anomaly detection.

        Returns:
            Dict with:
            - is_anomalous: bool
            - kl_divergence: float
            - severity: str ('low', 'medium', 'high', 'critical')
            - threshold: float

        Raises:
            ValidationError: If arrays have different shapes or invalid distributions.
        """
        beliefs = np.asarray(beliefs, dtype=float)
        baseline = np.asarray(baseline, dtype=float)

        if beliefs.shape != baseline.shape:
            raise ValidationError(
                f"beliefs shape {beliefs.shape} != baseline shape {baseline.shape}"
            )
        if beliefs.ndim != 1:
            raise ValidationError("beliefs must be a 1-D array")

        # Clip to avoid log(0)
        eps = 1e-10
        p = np.clip(beliefs, eps, 1.0)
        q = np.clip(baseline, eps, 1.0)

        # Normalize
        p = p / p.sum()
        q = q / q.sum()

        # KL divergence: sum p_i * log(p_i / q_i)
        kl_div = float(np.sum(p * np.log(p / q)))

        is_anomalous = kl_div > threshold

        # Classify severity
        if kl_div <= threshold:
            severity = "low"
        elif kl_div <= threshold * 5:
            severity = "medium"
        elif kl_div <= threshold * 20:
            severity = "high"
        else:
            severity = "critical"

        result = {
            "is_anomalous": is_anomalous,
            "kl_divergence": kl_div,
            "severity": severity,
            "threshold": threshold,
        }

        logger.debug(
            f"Anomaly detection: KL={kl_div:.6f}, anomalous={is_anomalous}, severity={severity}"
        )
        return result

    def validate_framework_integrity(
        self,
        model_params: Dict[str, NDArray],
    ) -> Dict[str, Union[bool, List[str], Dict]]:
        """Validate that a generative model has not been tampered with.

        Checks matrix properties (stochasticity, non-negativity, bounds),
        parameter bounds, and structural consistency across the model.

        Args:
            model_params: Dictionary with keys 'A', 'B', 'C', 'D' mapping
                to their respective numpy arrays.

        Returns:
            Dict with:
            - is_valid: bool, True if all checks pass
            - issues: list of str describing any detected problems
            - checks: dict mapping check name to pass/fail bool
            - integrity_score: float (0-1), fraction of checks passed

        Raises:
            ValidationError: If required matrices are missing.
        """
        required = {"A", "B", "C", "D"}
        missing = required - set(model_params.keys())
        if missing:
            raise ValidationError(f"Missing required matrices: {sorted(missing)}")

        issues: List[str] = []
        checks: Dict[str, bool] = {}

        A = model_params["A"]
        B = model_params["B"]
        C = model_params["C"]
        D = model_params["D"]

        # Check A: non-negative, columns sum to ~1 (stochastic)
        checks["A_non_negative"] = bool(np.all(A >= 0))
        if not checks["A_non_negative"]:
            issues.append("A matrix contains negative values")

        if A.ndim == 2:
            col_sums = A.sum(axis=0)
            checks["A_stochastic"] = bool(np.allclose(col_sums, 1.0, atol=1e-4))
            if not checks["A_stochastic"]:
                issues.append(
                    f"A matrix columns do not sum to 1 (range: {col_sums.min():.4f}-{col_sums.max():.4f})"  # noqa: E501
                )
        else:
            checks["A_stochastic"] = False
            issues.append("A matrix is not 2-dimensional")

        # Check B: non-negative, transition columns sum to ~1
        checks["B_non_negative"] = bool(np.all(B >= 0))
        if not checks["B_non_negative"]:
            issues.append("B matrix contains negative values")

        if B.ndim == 3:
            for action_idx in range(B.shape[2]):
                b_slice = B[:, :, action_idx]
                col_sums_b = b_slice.sum(axis=0)
                is_stochastic = bool(np.allclose(col_sums_b, 1.0, atol=1e-4))
                check_name = f"B_stochastic_action_{action_idx}"
                checks[check_name] = is_stochastic
                if not is_stochastic:
                    issues.append(f"B matrix action {action_idx} columns do not sum to 1")
        elif B.ndim == 2:
            col_sums_b = B.sum(axis=0)
            checks["B_stochastic"] = bool(np.allclose(col_sums_b, 1.0, atol=1e-4))
            if not checks["B_stochastic"]:
                issues.append("B matrix columns do not sum to 1")

        # Check C: finite values (preferences can be any real number)
        checks["C_finite"] = bool(np.all(np.isfinite(C)))
        if not checks["C_finite"]:
            issues.append("C matrix contains non-finite values")

        # Check D: valid probability distribution
        checks["D_non_negative"] = bool(np.all(D >= 0))
        if not checks["D_non_negative"]:
            issues.append("D matrix contains negative values")

        checks["D_normalized"] = bool(np.isclose(D.sum(), 1.0, atol=1e-4))
        if not checks["D_normalized"]:
            issues.append(f"D matrix does not sum to 1 (sum: {D.sum():.6f})")

        # Check dimensional consistency
        if A.ndim == 2 and D.ndim == 1:
            checks["AD_compatible"] = A.shape[1] == D.shape[0]
            if not checks["AD_compatible"]:
                issues.append(f"A columns ({A.shape[1]}) != D length ({D.shape[0]})")

        if A.ndim == 2 and C.ndim == 1:
            checks["AC_compatible"] = A.shape[0] == C.shape[0]
            if not checks["AC_compatible"]:
                issues.append(f"A rows ({A.shape[0]}) != C length ({C.shape[0]})")

        # Compute integrity score
        n_checks = len(checks)
        n_passed = sum(1 for v in checks.values() if v)
        integrity_score = n_passed / n_checks if n_checks > 0 else 0.0

        result = {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "checks": checks,
            "integrity_score": integrity_score,
        }

        logger.debug(
            f"Framework integrity: valid={result['is_valid']}, "
            f"score={integrity_score:.2f}, issues={len(issues)}"
        )
        return result
