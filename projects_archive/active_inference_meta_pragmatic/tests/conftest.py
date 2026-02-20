"""Pytest configuration for active_inference_meta_pragmatic project tests.

This file:
- Forces headless matplotlib (MPLBACKEND=Agg)
- Inserts project/src/ ahead of tests/ to avoid shadowing
- Keeps imports consistent for project test suite
- Provides shared fixtures for all test modules
"""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent

# Add project src/ to path so we can import src modules
PROJECT_SRC = PROJECT_ROOT / "src"
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = PROJECT_ROOT / "tests"
if TESTS_DIR in sys.path:
    sys.path.remove(str(TESTS_DIR))


from src.core.generative_models import GenerativeModel, create_simple_generative_model
from src.framework.meta_cognition import MetaCognitiveSystem
from src.framework.quadrant_framework import QuadrantFramework


@pytest.fixture
def simple_generative_model():
    """A minimal generative model for testing.

    Creates a 3-state, 3-observation, 2-action model with valid
    stochastic matrices.
    """
    n_states = 3
    n_obs = 3
    n_actions = 2

    # A: observation likelihood (columns sum to 1)
    A = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.1, 0.8],
    ])

    # B: transition matrix (columns sum to 1 per action)
    B = np.zeros((n_states, n_states, n_actions))
    B[:, :, 0] = np.array([
        [0.9, 0.05, 0.05],
        [0.05, 0.9, 0.05],
        [0.05, 0.05, 0.9],
    ])
    B[:, :, 1] = np.array([
        [0.1, 0.45, 0.45],
        [0.45, 0.1, 0.45],
        [0.45, 0.45, 0.1],
    ])

    # C: preferences (log priors over observations)
    C = np.array([2.0, 0.0, -2.0])

    # D: prior beliefs (valid probability distribution)
    D = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    return GenerativeModel(A, B, C, D)


@pytest.fixture
def quadrant_framework():
    """Initialized QuadrantFramework instance."""
    return QuadrantFramework()


@pytest.fixture
def meta_cognitive_system():
    """Initialized MetaCognitiveSystem instance."""
    return MetaCognitiveSystem(confidence_threshold=0.7, adaptation_rate=0.1)


@pytest.fixture
def sample_posterior_beliefs():
    """Sample posterior belief distributions for testing.

    Returns a dict with various belief configurations useful for
    testing inference, anomaly detection, and meta-cognition.
    """
    return {
        "confident": np.array([0.9, 0.05, 0.05]),
        "uncertain": np.array([0.4, 0.3, 0.3]),
        "uniform": np.array([1.0 / 3, 1.0 / 3, 1.0 / 3]),
        "bimodal": np.array([0.45, 0.45, 0.1]),
        "degenerate": np.array([1.0, 0.0, 0.0]),
    }


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory for test artifacts."""
    out = tmp_path / "output"
    out.mkdir()
    return out
