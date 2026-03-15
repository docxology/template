"""Mock validator module.

Validates that no mock objects or frameworks are used in tests,
enforcing the 'No Mocks Policy' for cognitive integrity.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def validate_no_mocks(tests_dir: Path, repo_root: Path) -> list[str]:
    """Scans tests_dir for mock usage and returns a list of violation messages.

    Args:
        tests_dir: The directory containing test files
        repo_root: Repository root path to make output relative

    Returns:
        List of formatted violation strings. Empty list means no violations.
    """
    mock_frameworks = [
        "from unittest.mock",
        "import unittest.mock",
        "unittest.mock import",
        "MagicMock(",
        "@patch",
        "with patch(",
        "patch.object(",
        "Mock(",
        "mocker.patch",
        "pytest.mock",
    ]

    skip_patterns = [
        "#",  # Comments
        "def patch_",
        "def patched_",
        "patch_llm_client",
        "patched_init",
        "monkeypatch.setattr",  # pytest monkeypatch is acceptable
        "No Mocks Policy",
        "mock usage",
        "mocking framework",
        "mock_repo",
        "mock_",
        "pytest.mark",
    ]

    violations: list[str] = []

    if not tests_dir.exists():
        return violations

    for py_file in tests_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line_str = line.strip()

                    if not any(fw in line_str for fw in mock_frameworks):
                        continue

                    if "def " in line_str or any(sp in line_str for sp in skip_patterns):
                        continue

                    relative_path = py_file.relative_to(repo_root)
                    violations.append(f"{relative_path}:{line_num}: {line_str}")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {py_file}: {e}")

    return violations
