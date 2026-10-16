"""Complementary full-module contract jobs, separate from legacy smoke clocks."""

from __future__ import annotations

# Full modules retain their own pytest timeout markers. This is below the
# existing public_acceptance_root default whole-operation limit of 7200s.
CONTRACT_SECONDS = 6600
CONTRACT_MODULES = frozenset(
    {
        "tests/infra_tests/project/test_installed_acceptance.py",
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_public_reference.py",
        "tests/infra_tests/project/test_public_reference_session.py",
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
        "tests/infra_tests/reporting/test_native_whole_portability.py",
        "tests/infra_tests/reporting/test_native_project_provider_batch.py",
        "tests/infra_tests/project/test_root_case_lanes.py",
        "tests/infra_tests/project/test_root_no_model_acquisition.py",
        "tests/infra_tests/project/test_root_optional_external.py",
        "tests/infra_tests/project/test_root_policy_authoring.py",
        "tests/infra_tests/project/test_root_portable.py",
        "tests/infra_tests/project/test_root_runtime_v2.py",
    }
)


def contract_files(files: tuple[str, ...], legacy: tuple[str, ...]) -> tuple[str, ...]:
    """Existing legacy smoke remains exact; selected extra deep modules isolate."""
    return tuple(name for name in files if name in CONTRACT_MODULES and name not in legacy)


def combined_groups(plan: dict) -> list[list[str]]:
    return [*plan["infra_shards"], *[[name] for name in plan.get("contract_modules", [])]]


__all__ = ["CONTRACT_SECONDS", "CONTRACT_MODULES", "contract_files", "combined_groups"]
