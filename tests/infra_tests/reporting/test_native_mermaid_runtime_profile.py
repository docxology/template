"""Finite Source DATA contracts; genuine Node process admission remains separate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

import infrastructure.rendering._mermaid_v11 as _mermaid_v11
import infrastructure.rendering._mermaid_v122 as _mermaid_v122
from infrastructure.rendering._mermaid_native_profile import (
    adapter_bytes,
    adapter_sha256,
    rendering_profile,
    request_bytes,
    validate_rendering_profile,
)
from infrastructure.reporting.native_mermaid_batch_source_reference import _adapter as ordered_adapter_bytes
from infrastructure.reporting.native_mermaid_runtime_selection import _validate_source_inputs
from infrastructure.reporting.native_mermaid_source_reference import _runtime_version, _source11_live_node_reports

REPO = Path(__file__).absolute().parents[3]


def _binding(content: bytes) -> dict:
    return {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content), "utf8": content.decode("utf-8")}


def _inputs() -> dict:
    return {name: _binding((REPO / name).read_bytes()) for name in ("package.json", "package-lock.json")}


def _replace(inputs: dict, name: str, payload: dict) -> None:
    inputs[name] = _binding((json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))


def test_actual_root_profile_binds_locked_node24_and_current_mermaid_source() -> None:
    package, lock = _validate_source_inputs(_inputs())
    assert package["engines"] == lock["packages"][""]["engines"] == {"node": "24.x"}
    assert package["packageManager"] == "npm@11.20.0"
    version = package["devDependencies"]["@mermaid-js/mermaid-cli"]
    assert _runtime_version({"version": version}) == "12.2.0"
    assert lock["packages"]["node_modules/mermaid"]["version"] == "12.3.0"
    katex = [row for path, row in lock["packages"].items() if path.endswith("node_modules/katex")]
    assert katex and all(row["version"] == "0.18.10" for row in katex)


@pytest.mark.parametrize("engine", ["20.x", "22.x", "26.x"])
def test_matching_foreign_root_and_lock_engine_cannot_enter_current_profile(engine: str) -> None:
    inputs = _inputs()
    package = json.loads(inputs["package.json"]["utf8"])
    lock = json.loads(inputs["package-lock.json"]["utf8"])
    package["engines"] = lock["packages"][""]["engines"] = {"node": engine}
    _replace(inputs, "package.json", package)
    _replace(inputs, "package-lock.json", lock)
    with pytest.raises(ValueError, match="Root Node24 engine declarations differ"):
        _validate_source_inputs(inputs)


@pytest.mark.parametrize("change", ["missing", "foreign"])
def test_missing_or_disagreeing_locked_root_engine_refuses(change: str) -> None:
    inputs = _inputs()
    lock = json.loads(inputs["package-lock.json"]["utf8"])
    if change == "missing":
        del lock["packages"][""]["engines"]
    else:
        lock["packages"][""]["engines"] = {"node": "22.x"}
    _replace(inputs, "package-lock.json", lock)
    with pytest.raises(ValueError, match="Root Node24 engine declarations differ"):
        _validate_source_inputs(inputs)


def test_actual_single_and_ordered_sdk_adapters_match_current_source_bytes() -> None:
    single = (REPO / "infrastructure/rendering/_mermaid_v122_adapter.mjs").read_bytes()
    ordered = (REPO / "infrastructure/rendering/_mermaid_v122_batch_adapter.mjs").read_bytes()
    assert adapter_bytes("12.2.0") == _mermaid_v122.adapter_bytes() == single
    assert adapter_sha256("12.2.0") == hashlib.sha256(single).hexdigest()
    assert ordered_adapter_bytes() == ordered
    historical_single = (REPO / "infrastructure/rendering/_mermaid_v11_adapter.mjs").read_bytes()
    historical_ordered = (REPO / "infrastructure/rendering/_mermaid_v11_batch_adapter.mjs").read_bytes()
    assert adapter_bytes("11.16.0") == historical_single
    assert hashlib.sha256(historical_ordered).hexdigest() == (
        "c97dfc3e8fdad22cbacb94d20a0a808fa6b27ea064837046c699359c9ca1ca9c"
    )
    assert adapter_bytes("12.0.0") == (REPO / "infrastructure/rendering/_mermaid_v12_adapter.mjs").read_bytes()


def test_actual_private_adapter_loader_rejects_changed_packaged_asset(tmp_path: Path) -> None:
    # Copy the real helper unchanged so its normal __file__-relative asset lookup
    # can consume private files. No Source module, dependency or function is replaced.
    original_helper = REPO / "infrastructure/rendering/_mermaid_v11.py"
    helper = tmp_path / original_helper.name
    helper.write_bytes(original_helper.read_bytes())
    original_asset = _mermaid_v11.adapter_bytes()
    asset = tmp_path / "_mermaid_v11_adapter.mjs"
    asset.write_bytes(original_asset)
    spec = importlib.util.spec_from_file_location("node24_private_adapter_contract", helper)
    assert spec is not None and spec.loader is not None
    private_helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(private_helper)
    assert private_helper.adapter_bytes() == original_asset
    asset.write_bytes(original_asset + b"\n// changed private asset\n")
    with pytest.raises(ValueError, match="adapter bytes differ from the declared source profile"):
        private_helper.adapter_bytes()


@pytest.mark.parametrize(
    ("field", "value"),
    [("font_embed", True), ("viewport_width", True), ("viewport_height", 1400), ("source_used_face_embedding", False)],
)
def test_current122_cannot_borrow_legacy_or_malformed_render_profiles(field: str, value: object) -> None:
    profile = rendering_profile("12.2.0")
    assert profile["font_embed"] is False
    assert profile["viewport_width"] == 1400 and profile["viewport_height"] == 900
    assert profile["device_scale_factor"] == 1 and profile["source_used_face_embedding"] is True
    profile[field] = value
    with pytest.raises(ValueError, match="embedding or viewport semantics"):
        validate_rendering_profile("12.2.0", profile)


def test_current122_literal_request_keeps_its_distinct_fixed_native_namespace() -> None:
    # Literal DATA paths do not nominate or execute a native provider.
    request = json.loads(
        request_bytes(
            "12.2.0", Path("/runtime/package"), Path("/data/original.mmd"), Path("/data/original.png"), "png", None
        )
    )
    assert (
        request["schema_version"]
        == "template-mermaid-v122-source-pinned-default-theme-viewport-licensed-font-request-v1"
    )
    assert request["render_profile"] == rendering_profile("12.2.0")
    assert request["render_profile"]["font_embed"] is False
    assert rendering_profile("12.0.0")["font_embed"] is True
    assert rendering_profile("11.16.0")["font_embed"] is False


@pytest.mark.parametrize("version", ["11.16.0", "12.2.0"])
def test_licensed_live_report_data_namespace_is_bound_to_exact_version(version: str) -> None:
    # Structural parser DATA only: these records create no process, runtime,
    # custodian, Original or acceptance authority.
    schema = (
        "template-native-source122-node-live-loaded-report-v1"
        if version == "12.2.0"
        else "template-native-source11-node-live-loaded-report-v1"
    )
    reports = []
    for phase in ("before-import", "after-run"):
        reports.append(
            {
                "schema_version": schema,
                "api": "process.report.getReport",
                "phase": phase,
                "pid": 42,
                "owner_pid": 41,
                "node_version": "v24.22.0",
                "platform": "linux",
                "architecture": "x64",
                "shared_objects": [],
                "loaded_library_bodies": [],
                "remaining_admission": ["source-required loaded library bodies and shared-cache/kernel closure"],
            }
        )
    process = {"pid": 42, "owner_pid": 41, "stdout": "\n".join(json.dumps(row) for row in reports)}
    _source11_live_node_reports(process, version=version)
    for row in reports:
        row["schema_version"] = (
            "template-native-source11-node-live-loaded-report-v1"
            if version == "12.2.0"
            else "template-native-source122-node-live-loaded-report-v1"
        )
    process["stdout"] = "\n".join(json.dumps(row) for row in reports)
    with pytest.raises(ValueError, match="self/API/PID observation differs"):
        _source11_live_node_reports(process, version=version)


def test_historical12_cannot_borrow_current_licensed_live_report_gate() -> None:
    with pytest.raises(ValueError, match="exact licensed-font profile"):
        _source11_live_node_reports({}, version="12.0.0")


@pytest.mark.parametrize("version", ["11.16.0", "12.0.0", "12.2.0"])
def test_historical_office_cli_keeps_current_api_profile_explicitly_unsupported(version: str) -> None:
    from infrastructure.reporting.native_office_mermaid_source import _reject_current_cli_api_profile

    if version == "12.2.0":
        with pytest.raises(ValueError, match="full Source-owned Mermaid API"):
            _reject_current_cli_api_profile(version)
    else:
        assert _reject_current_cli_api_profile(version) is None
