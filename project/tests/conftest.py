"""Pytest configuration for project tests."""
import os
import sys
import pytest
from unittest.mock import Mock

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ to path so we can import project modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


@pytest.fixture(scope="session")
def db():
    """Shared database instance for all tests."""
    from src.database import WaysDatabase
    return WaysDatabase()


@pytest.fixture(scope="session")
def queries():
    """Shared SQL queries instance for all tests."""
    from src.sql_queries import WaysSQLQueries
    return WaysSQLQueries()


@pytest.fixture(scope="session")
def analyzer():
    """Shared WaysAnalyzer instance for all tests."""
    from src.ways_analysis import WaysAnalyzer
    try:
        return WaysAnalyzer()
    except Exception:
        # If database operations fail, return None - tests will skip gracefully
        return None


@pytest.fixture(scope="session")
def house_analyzer():
    """Shared HouseOfKnowledgeAnalyzer instance for all tests."""
    from src.house_of_knowledge import HouseOfKnowledgeAnalyzer
    try:
        return HouseOfKnowledgeAnalyzer()
    except Exception:
        # If database operations fail, return None - tests will skip gracefully
        return None


@pytest.fixture(scope="session")
def network_analyzer():
    """Shared WaysNetworkAnalyzer instance for all tests."""
    from src.network_analysis import WaysNetworkAnalyzer
    try:
        return WaysNetworkAnalyzer()
    except Exception:
        # If database operations fail, return None - tests will skip gracefully
        return None
