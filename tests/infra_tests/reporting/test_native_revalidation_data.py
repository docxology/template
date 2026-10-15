"""Real-file revalidation DATA controls; no Source/SDK/native authority invented."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_current_nomination_batch import verify_current_nomination_batch
from infrastructure.reporting.native_office_pdfium_provider import _file, _installed
from infrastructure.reporting.native_pdfium_provider_data import observe_provider_files
from infrastructure.reporting.native_pdfium_revalidation import verify_reader_runtime_batch
from infrastructure.reporting.native_pdfium_runtime_data import validate_runtime_owner
from infrastructure.reporting.native_pdfium_source_wheel import inspect_pdfium_locked_wheel
from tests.infra_tests.reporting.test_native_pdfium_batch_data import NAME, _archive, _lock, _members


def _held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    site = tmp_path / "site"
    members = _members()
    for label, body in members.items():
        target = site / label
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    monkeypatch.syspath_prepend(str(site))
    wheel = tmp_path / NAME
    wheel.write_bytes(_archive(members))
    raw, identity = _file(wheel, time.monotonic() + 10)
    lock = _lock(raw)
    _, declared = inspect_pdfium_locked_wheel(NAME, raw, lock, deadline=time.monotonic() + 10)
    observation = {"path": str(wheel), **declared, "identity": identity}
    installed = _installed(site, members, time.monotonic() + 10)
    return site, wheel, members, observation, installed, lock


def test_revalidation_data_repeats_exact_locked_wheel_and_actual_distribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    held = _held(tmp_path, monkeypatch)
    assert observe_provider_files(*held, deadline=time.monotonic() + 10) == (held[3], held[4])
    assert observe_provider_files(*held, deadline=time.monotonic() + 10) == (held[3], held[4])


@pytest.mark.parametrize("change", ["wheel-aba", "site-aba", "extra", "alias", "record", "wheel-body", "metadata"])
def test_revalidation_data_refuses_real_bytes_restored_aba_and_negative_membership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    held = _held(tmp_path, monkeypatch)
    site, wheel = held[:2]
    target = wheel if change.startswith("wheel") else site / "pypdfium2/__init__.py"
    if change.endswith("aba"):
        original = target.read_bytes()
        target.write_bytes(original + b"\nactual owned transient edit\n")
        target.write_bytes(original)
        assert target.read_bytes() == original
    elif change == "extra":
        (site / "pypdfium2/unlisted.txt").write_text("undeclared actual file")
    elif change == "alias":
        target.unlink()
        target.symlink_to(site / "pypdfium2_raw/__init__.py")
    elif change == "record":
        target = site / "pypdfium2-0.0.0.dist-info/RECORD"
        target.write_text(target.read_text() + "unlisted.txt,,\n")
    elif change == "metadata":
        target = site / "pypdfium2-0.0.0.dist-info/METADATA"
        target.write_text(target.read_text().replace("0.0.0", "9.9.9"))
    else:
        wheel.write_bytes(wheel.read_bytes() + b"actual changed ZIP body")
    with pytest.raises((ValueError, OSError)):
        observe_provider_files(*held, deadline=time.monotonic() + 10)


def test_revalidation_data_cannot_renew_the_existing_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    held = _held(tmp_path, monkeypatch)
    with pytest.raises(TimeoutError):
        observe_provider_files(*held, deadline=time.monotonic() - 1)


def test_revalidation_entrypoints_refuse_data_before_observing_source_or_runtime(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="genuine Source/runtime"):
        verify_reader_runtime_batch(None, (None,), deadline=time.monotonic() + 10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="genuine typed runtime"):
        validate_runtime_owner(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="actual reader's clock"):
        verify_current_nomination_batch(None, None, frozenset(), deadline=time.monotonic() + 10)  # type: ignore[arg-type]
    assert not tuple(tmp_path.iterdir())


def test_installed_sdk_version_predicate_uses_actual_runtime_identity() -> None:
    from infrastructure import __version__
    from infrastructure.reporting.native_format_joint_source import _require_installed_sdk

    # This exercises only the metadata predicate; it creates no Source or native
    # execution capability and does not assert genuine installation acceptance.
    raw = {
        "binding_kind": "installed-distribution",
        "distribution": {
            "name": "research-project-template",
            "version": __version__,
        },
    }
    _require_installed_sdk(json.dumps(raw).encode())
    for changed in (
        {**raw, "binding_kind": "source-checkout"},
        {**raw, "distribution": {"name": "foreign", "version": __version__}},
        {**raw, "distribution": {"name": "research-project-template", "version": "0.invalid-mismatch"}},
        {**raw, "distribution": {"name": "research-project-template"}},
    ):
        with pytest.raises(ValueError):
            _require_installed_sdk(json.dumps(changed).encode())
