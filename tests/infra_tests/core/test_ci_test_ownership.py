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
PROTOCOL_SOURCES = {
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


def test_native_owner_alias_keeps_every_actual_direct_test_consumer() -> None:
    source = "infrastructure/reporting/native_tool_producer.py"
    module = source.removesuffix(".py").replace("/", ".")
    consumers: set[str] = set()
    for path in sorted((ROOT / "tests/infra_tests").rglob("test_*.py")):
        syntax = ast.parse(path.read_bytes())
        if any(
            (isinstance(node, ast.ImportFrom) and node.module == module)
            or (isinstance(node, ast.Import) and any(alias.name == module for alias in node.names))
            for node in ast.walk(syntax)
        ):
            consumers.add(path.relative_to(ROOT).as_posix())
    assert consumers == set(SOURCE_TEST_OWNERS[source])


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
