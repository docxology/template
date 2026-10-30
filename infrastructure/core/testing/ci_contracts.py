"""Complementary full-module contract jobs, separate from baseline smoke clocks."""

from __future__ import annotations

# Full modules retain their own pytest timeout markers. This is below the
# existing public_acceptance_root default whole-operation limit of 7200s.
CONTRACT_SECONDS = 6600
# Preparation follows the actual consumer, including modules selected through
# broad facade changes. Matrix projection and hosted setup use this one roster.
_NATIVE_PREPARATION = {
    "tests/infra_tests/project/test_public_acceptance_auxiliary.py": ("native", False, False),
    "tests/infra_tests/project/test_scientific_reference_replay.py": ("converter", True, False),
    "tests/infra_tests/reporting/test_native_browser_oracles.py": ("converter", False, True),
    "tests/infra_tests/reporting/test_native_browser_scientific_structure.py": ("converter", False, True),
    "tests/infra_tests/reporting/test_native_pdf_citations.py": ("converter", True, False),
    "tests/infra_tests/reporting/test_native_pdf_math.py": ("converter", True, False),
    "tests/infra_tests/reporting/test_native_pdf_source_witness.py": ("converter", True, False),
    "tests/infra_tests/reporting/test_pdf_raw_natbib_source.py": ("converter", True, False),
    "tests/infra_tests/rendering/test_latex_texttt_native.py": ("converter", True, False),
    "tests/infra_tests/rendering/test_latex_utils.py": ("none", True, False),
}
CONTRACT_MODULES = frozenset(
    {
        "tests/infra_tests/documentation/test_counts_coverage_measurement.py",
        "tests/infra_tests/documentation/test_counts_coverage_support.py",
        "tests/infra_tests/documentation/test_counts_provenance.py",
        "tests/infra_tests/documentation/test_counts_refresh.py",
        "tests/infra_tests/project/test_installed_acceptance.py",
        "tests/infra_tests/project/test_public_reference.py",
        "tests/infra_tests/project/test_public_reference_session.py",
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
        "tests/infra_tests/reporting/test_native_whole_portability.py",
        "tests/infra_tests/reporting/test_native_hosted_credentials.py",
        "tests/infra_tests/reporting/test_native_project_provider_batch.py",
        "tests/infra_tests/reporting/test_project_verifier.py",
        "tests/infra_tests/project/test_root_case_lanes.py",
        "tests/infra_tests/project/test_root_no_model_acquisition.py",
        "tests/infra_tests/project/test_root_wheel_typing.py",
        "tests/infra_tests/project/test_root_optional_external.py",
        "tests/infra_tests/project/test_root_policy_authoring.py",
        "tests/infra_tests/project/test_root_portable.py",
        "tests/infra_tests/project/test_root_runtime_v2.py",
        "tests/infra_tests/project/test_root_runtime_controls.py",
        "tests/infra_tests/project/test_root_source_controls.py",
    }
) | frozenset(_NATIVE_PREPARATION)


def contract_preparation(module: str) -> dict[str, str | bool]:
    """Project source-owned native requirements for one serial module job."""
    documents, tex, browser = _NATIVE_PREPARATION.get(module, ("none", False, False))
    return {"documents": documents, "tex": tex, "browser": browser}


def contract_files(files: tuple[str, ...], baseline: tuple[str, ...]) -> tuple[str, ...]:
    """Existing baseline smoke remains exact; selected extra deep modules isolate."""
    return tuple(name for name in files if name in CONTRACT_MODULES and name not in baseline)


def combined_groups(plan: dict) -> list[list[str]]:
    return [*plan["infra_shards"], *[[name] for name in plan.get("contract_modules", [])]]


__all__ = ["CONTRACT_SECONDS", "CONTRACT_MODULES", "contract_files", "contract_preparation", "combined_groups"]
