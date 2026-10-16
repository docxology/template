"""Finite Source DATA contracts; genuine Node process admission remains separate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

import infrastructure.rendering._mermaid_v11 as _mermaid_v11
from infrastructure.rendering._mermaid_native_profile import adapter_bytes, adapter_sha256
from infrastructure.reporting.native_mermaid_batch_source_reference import _adapter as ordered_adapter_bytes
from infrastructure.reporting.native_mermaid_runtime_selection import _validate_source_inputs
from infrastructure.reporting.native_mermaid_source_reference import _runtime_version

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
    assert _runtime_version({"version": version}) == "11.16.0"


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
    single = (REPO / "infrastructure/rendering/_mermaid_v11_adapter.mjs").read_bytes()
    ordered = (REPO / "infrastructure/rendering/_mermaid_v11_batch_adapter.mjs").read_bytes()
    assert adapter_bytes("11.16.0") == single
    assert adapter_sha256("11.16.0") == hashlib.sha256(single).hexdigest()
    assert ordered_adapter_bytes() == ordered


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
