"""Complementary full-module contract jobs, separate from legacy smoke clocks."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from infrastructure.core.testing.ci_module_durations import load_module_durations

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

# Full modules retain their own pytest timeout markers. This is below the
# existing public_acceptance_root default whole-operation limit of 7200s.
CONTRACT_SECONDS = 6600
# Preparation follows the actual consumer, including modules selected through
# broad facade changes. Matrix projection and hosted setup use this one roster.
_NATIVE_PREPARATION = {
    "tests/infra_tests/rendering/test_paper_frontmatter_native.py": ("converter", True, False),
    "tests/infra_tests/reporting/test_paper_frontmatter_reconstruction_native.py": ("converter", True, False),
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
    }
) | frozenset(_NATIVE_PREPARATION)


_XDIST_THRESHOLD_SECONDS = 300.0
_XDIST_MAX_WORKERS = 4


def contract_preparation(module: str, durations: Mapping[str, float] | None = None) -> dict[str, str | bool | int]:
    """Project source-owned native requirements and a measured worker budget."""
    documents, tex, browser = _NATIVE_PREPARATION.get(module, ("none", False, False))
    measured = load_module_durations(_REPOSITORY_ROOT) if durations is None else durations
    seconds = measured.get(module, 0.0)
    workers = 0
    if seconds > _XDIST_THRESHOLD_SECONDS:
        workers = _XDIST_MAX_WORKERS if seconds > 2 * _XDIST_THRESHOLD_SECONDS else 2
    return {"documents": documents, "tex": tex, "browser": browser, "workers": workers}


def contract_files(files: tuple[str, ...], legacy: tuple[str, ...]) -> tuple[str, ...]:
    """Existing legacy smoke remains exact; selected extra deep modules isolate."""
    return tuple(name for name in files if name in CONTRACT_MODULES and name not in legacy)


def combined_groups(plan: dict) -> list[list[str]]:
    return [*plan["infra_shards"], *[[name] for name in plan.get("contract_modules", [])]]


__all__ = ["CONTRACT_SECONDS", "CONTRACT_MODULES", "contract_files", "contract_preparation", "combined_groups"]
