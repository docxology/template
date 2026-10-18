"""Shared helper aliases retain focused or protocol tests and complete routing."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from infrastructure.core.testing.ci_infra import infrastructure_files
from infrastructure.core.testing.ci_test_ownership import SOURCE_TEST_OWNERS

ROOT = Path(__file__).resolve().parents[3]

# These owners exercise the integration protocol or a real module CLI rather
# than importing each internal leaf directly. Their full modules remain selected.
# Root/native collectors run through actual installed subprocesses; print
# integration owners also exercise producers through their Source-owned wrappers.
FOCUSED_PROTOCOL_SOURCES = {
    "infrastructure/core/pipeline/fingerprint_files.py",
    "infrastructure/core/pipeline/fingerprints.py",
    "infrastructure/reporting/readiness_receipts.py",
    "infrastructure/reporting/native_print_source_loader.py",
    "infrastructure/reporting/native_source_external_admission.py",
    "infrastructure/reporting/native_tool_producer.py",
    "infrastructure/reporting/native_stage_child.py",
    "infrastructure/project/_hosted_api.py",
    "infrastructure/project/auxiliary_print_code.py",
    "infrastructure/project/auxiliary_print_hosted.py",
    "infrastructure/project/public_acceptance_auxiliary.py",
    "infrastructure/project/public_acceptance_auxiliary_bootstrap.py",
    "infrastructure/project/public_acceptance_auxiliary_parallel.py",
    "infrastructure/project/public_acceptance_auxiliary_supervision.py",
    "infrastructure/project/public_acceptance_auxiliary_validation.py",
    "infrastructure/project/public_hosted_origin.py",
    "infrastructure/reporting/_native_hosted_launch.py",
    "infrastructure/reporting/native_auxiliary_print_custody.py",
    "infrastructure/reporting/native_environment_custody.py",
    "infrastructure/reporting/native_format_acceptance_checks.py",
    "infrastructure/reporting/native_hosted_original_custody.py",
    "infrastructure/reporting/native_hosted_reader.py",
    "infrastructure/reporting/native_installed_invocation.py",
    "infrastructure/reporting/native_print_witness.py",
    "infrastructure/reporting/native_print_witness_validation.py",
    "infrastructure/reporting/native_tool_process.py",
    "infrastructure/reporting/native_tool_replay.py",
    "infrastructure/reporting/required_candidate_collection.py",
}
PROTOCOL_SOURCES = FOCUSED_PROTOCOL_SOURCES | {
    # The genuine shell owner copies and executes this exact repository helper.
    "scripts/shell/setup-system-deps.sh",
    # Real project runner and measurement subprocesses load this private plugin.
    "infrastructure/core/testing/_pytest_runtime_controls.py",
    # The measurement owner imports the runner in its actual stage child Source.
    "infrastructure/reporting/pipeline_test_runner.py",
    # Actual source-owned subprocess/case controls exercise the worker through
    # produce_root_lane, while the same complete module directly reads results.
    "infrastructure/project/public_root_lane_worker.py",
    "infrastructure/core/testing/pytest_receipt.py",
    "infrastructure/core/testing/ci_infra.py",
    "infrastructure/core/testing/test_runner_outputs.py",
    # Cleanup owners exercise execution_boundary reexports and copied Source/Code custody.
    "infrastructure/core/_bounded_kill.py",
    # Complete analysis/measurement owners launch the actual worker through the
    # controller; the isolated import control also binds both protocol identities.
    "infrastructure/core/pipeline/_stage_protocol.py",
    "infrastructure/core/pipeline/stage_launch.py",
    "infrastructure/core/pipeline/stage_worker.py",
    "infrastructure/project/public_acceptance_auxiliary_pipeline_failure.py",
    "infrastructure/project/public_acceptance_auxiliary_pipeline_environment.py",
    "infrastructure/project/public_acceptance_auxiliary_supervision.py",
    "infrastructure/project/public_acceptance_auxiliary_transfer_validation.py",
    "infrastructure/project/installed_domain_acceptance.py",
    "infrastructure/project/public_acceptance_auxiliary_cli.py",
    "infrastructure/reporting/native_current_reader_inputs.py",
    "infrastructure/reporting/native_revalidation_progress.py",
    "infrastructure/reporting/native_installed_launcher.py",
    "infrastructure/reporting/native_installed_invocation.py",
    "infrastructure/reporting/native_installed_custody_capture.py",
}


@pytest.fixture(scope="module")
def actual_direct_consumers() -> dict[str, set[str]]:
    """Parse the real test tree once for all ownership controls."""
    consumers: dict[str, set[str]] = {}
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        syntax = ast.parse(path.read_bytes())
        imports = (
            {node.module for node in ast.walk(syntax) if isinstance(node, ast.ImportFrom)}
            | {alias.name for node in ast.walk(syntax) if isinstance(node, ast.Import) for alias in node.names}
            | {
                node.module + "." + alias.name
                for node in ast.walk(syntax)
                if isinstance(node, ast.ImportFrom) and node.module
                for alias in node.names
            }
        )
        for module in imports:
            if module is not None:
                consumers.setdefault(module, set()).add(path.relative_to(ROOT).as_posix())
    return consumers


def test_native_owner_alias_keeps_every_actual_direct_test_consumer(
    actual_direct_consumers: dict[str, set[str]],
) -> None:
    source = "infrastructure/reporting/native_tool_producer.py"
    module = source.removesuffix(".py").replace("/", ".")
    assert actual_direct_consumers[module] == set(SOURCE_TEST_OWNERS[source])


@pytest.mark.parametrize("source", sorted(SOURCE_TEST_OWNERS))
def test_shared_helper_routes_every_focused_or_protocol_owner_without_broad_package(source: str) -> None:
    module = source.removesuffix(".py").replace("/", ".")
    owners = SOURCE_TEST_OWNERS[source]
    assert (ROOT / source).is_file()
    for owner in owners:
        syntax = ast.parse((ROOT / owner).read_bytes())
        assert any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
            for node in ast.walk(syntax)
        )
        imports = {node.module for node in ast.walk(syntax) if isinstance(node, ast.ImportFrom)} | {
            alias.name for node in ast.walk(syntax) if isinstance(node, ast.Import) for alias in node.names
        }
        if source.endswith(".mjs"):
            assert any(isinstance(node, ast.Constant) and node.value == source for node in ast.walk(syntax)), (
                source,
                owner,
            )
        elif source not in PROTOCOL_SOURCES:
            assert module in imports, (source, owner)
    selected = set(infrastructure_files(ROOT, (source,)))
    assert selected == set(infrastructure_files(ROOT)) | set(owners)


@pytest.mark.parametrize("source", sorted(FOCUSED_PROTOCOL_SOURCES))
def test_focused_protocol_aliases_preserve_every_actual_direct_consumer(
    source: str,
    actual_direct_consumers: dict[str, set[str]],
) -> None:
    module = source.removesuffix(".py").replace("/", ".")
    assert actual_direct_consumers.get(module, set()) <= set(SOURCE_TEST_OWNERS[source])


def test_unowned_reporting_helper_still_selects_complete_package_fallback() -> None:
    source = "infrastructure/reporting/a_genuinely_unowned_new_protocol_helper.py"
    assert source not in SOURCE_TEST_OWNERS
    expected = set(infrastructure_files(ROOT)) | {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "tests/infra_tests/reporting").rglob("test_*.py")
    }
    assert set(infrastructure_files(ROOT, (source,))) == expected
