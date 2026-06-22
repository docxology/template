"""Tests for the test-suite registry and pytest selector (no mocks)."""

from __future__ import annotations

import pytest

from tests._suite_registry import SUITE_REGISTRY, SuiteSpec, get_suite_spec, list_suites
from tests._test_selector import TestSelector, select_tests


class TestSuiteRegistry:
    def test_three_known_suites(self) -> None:
        assert set(list_suites()) == {"infra_tests", "integration", "regression"}

    def test_infra_floor_is_60(self) -> None:
        spec = get_suite_spec("infra_tests")
        assert isinstance(spec, SuiteSpec)
        assert spec.coverage_floor == 60
        assert spec.coverage_package == "infrastructure"

    def test_paths_point_at_real_dirs(self) -> None:
        for spec in SUITE_REGISTRY.values():
            assert spec.path.startswith("tests/")

    def test_unknown_suite_raises(self) -> None:
        with pytest.raises(KeyError):
            get_suite_spec("does_not_exist")


class TestSelectorBuild:
    def test_suite_resolves_to_path(self) -> None:
        assert TestSelector(suite="integration").build() == ["tests/integration"]

    def test_exclude_markers_become_not_expr(self) -> None:
        argv = TestSelector(suite="integration", exclude_markers=["requires_ollama", "slow"]).build()
        assert argv[0] == "tests/integration"
        assert argv[1] == "-m"
        assert argv[2] == "not requires_ollama and not slow"

    def test_markers_and_exclusions_combine(self) -> None:
        argv = select_tests(markers=["integration"], exclude_markers=["slow"], paths=["tests/x"])
        assert argv == ["tests/x", "-m", "integration and not slow"]

    def test_extra_args_appended(self) -> None:
        argv = select_tests(suite="infra_tests", extra_args=["-q", "--no-header"])
        assert argv[-2:] == ["-q", "--no-header"]

    def test_unknown_suite_raises(self) -> None:
        with pytest.raises(KeyError):
            TestSelector(suite="nope").build()

    def test_no_markers_no_dash_m(self) -> None:
        assert "-m" not in TestSelector(paths=["tests/a"]).build()
