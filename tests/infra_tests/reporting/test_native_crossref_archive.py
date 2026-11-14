"""Synthetic archive DATA controls; these never qualify a real native provider."""

import copy
import hashlib
import lzma
import tarfile
import time
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.reporting.native_crossref_archive import (
    SCHEMA,
    _observation,
    _physical,
    _validate_record,
    observe_crossref_provider_archive,
    replay_crossref_provider_archive,
)
from infrastructure.reporting.native_document_provider_archives import (
    MAX_EXECUTABLE_BYTES,
    _BoundedTarBytes,
    _MAX_METADATA_READ_BYTES,
    provider_archive_member,
)
from infrastructure.reporting.native_document_provider_contracts import PIN_SOURCE, select_document_tool
from infrastructure.reporting.native_stage_crossref_archive_replay import replay_stage_crossref_provider_archive
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_BODY = b"synthetic Crossref member DATA; not a native executable\n"


def _archive(rows=None, *, mtime=0):
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, body, mode in rows if rows is not None else [("pandoc-crossref", _BODY, 0o755)]:
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(body), mode, mtime
            archive.addfile(member, BytesIO(body))
    return lzma.compress(stream.getvalue())


def _pin(archive, *, kind="nix-source-build", body=_BODY):
    # Deliberately only DATA-predicate inputs, not an admitted Source manifest.
    if kind == "official-archives":
        return {
            "kind": kind,
            "member": "pandoc-crossref",
            "format": "tar.xz",
            "archive_sha256": hashlib.sha256(archive).hexdigest(),
            "archive_bytes": len(archive),
        }
    return {
        "kind": kind,
        "member": "pandoc-crossref",
        "binary_sha256": hashlib.sha256(body).hexdigest(),
        "binary_bytes": len(body),
    }


def _extract(archive, pin):
    return provider_archive_member(archive, pin, deadline=time.monotonic() + 5)


def test_source_built_transport_retains_the_complete_exact_member():
    archive = _archive()
    member, body = _extract(archive, _pin(archive))
    assert body == _BODY
    assert member == {
        "name": "pandoc-crossref",
        "canonical_name": "pandoc-crossref",
        "mode": 0o755,
        "bytes": len(_BODY),
        "sha256": hashlib.sha256(_BODY).hexdigest(),
        "archive_members": 1,
        "uncompressed_payload_bytes": len(_BODY),
        "complete_uncompressed_archive_bytes": len(lzma.decompress(archive)),
    }


def test_source_body_pin_not_an_archive_producer_digest_is_authoritative():
    archive, repacked = _archive(), _archive(mtime=1)
    assert archive != repacked
    assert _extract(archive, _pin(archive)) == _extract(repacked, _pin(archive))


@pytest.mark.parametrize("field", ["binary_sha256", "binary_bytes"])
def test_source_built_member_must_match_both_source_body_pins(field):
    archive = _archive()
    pin = _pin(archive)
    pin[field] = "0" * 64 if field == "binary_sha256" else len(_BODY) + 1
    with pytest.raises(ValueError, match="Source-pinned single executable body"):
        _extract(archive, pin)


def test_changed_member_cannot_be_authorized_by_the_transport_that_contains_it():
    original = _archive()
    changed = _archive([("pandoc-crossref", _BODY + b"changed", 0o755)])
    with pytest.raises(ValueError, match="Source-pinned single executable body"):
        _extract(changed, _pin(original))


def test_source_built_transport_cannot_add_incidental_receipts_or_other_members():
    archive = _archive([("pandoc-crossref", _BODY, 0o755), ("build-receipt.json", b"{}", 0o644)])
    with pytest.raises(ValueError, match="single executable body"):
        _extract(archive, _pin(archive))


@pytest.mark.parametrize(
    "rows",
    [
        [("not-crossref", _BODY, 0o755)],
        [("pandoc-crossref", _BODY, 0o644)],
        [("../pandoc-crossref", _BODY, 0o755)],
        [("pandoc-crossref", _BODY, 0o755), ("pandoc-crossref", _BODY, 0o755)],
    ],
)
def test_missing_nonexecutable_unsafe_or_duplicate_members_are_refused(rows):
    archive = _archive(rows)
    with pytest.raises(ValueError):
        _extract(archive, _pin(archive))


def test_official_provider_keeps_complete_pinned_archive_correspondence():
    archive = _archive()
    pin = _pin(archive, kind="official-archives")
    assert _extract(archive, pin)[1] == _BODY
    # Even the identical member cannot replace an exact official compressed body.
    with pytest.raises(ValueError, match="official document provider archive bytes"):
        _extract(_archive(mtime=1), pin)
    with pytest.raises(ValueError, match="official document provider archive bytes"):
        _extract(archive, {**pin, "archive_bytes": len(archive) + 1})


@pytest.mark.parametrize("kind", ["worker-receipt", "official-linux-static", "unversioned-source-build"])
def test_unapproved_provider_kinds_have_no_archive_admission(kind):
    archive = _archive()
    with pytest.raises(ValueError, match="admitted Source-selected provider kind"):
        _extract(archive, _pin(archive, kind=kind))


@pytest.mark.parametrize("change", ["truncated", "concatenated", "trailing"])
def test_complete_source_transport_cannot_omit_or_append_xz_bytes(change):
    archive = _archive()
    changed = {
        "truncated": archive[:-1],
        "concatenated": archive + archive,
        "trailing": archive + b"trailing DATA",
    }[change]
    with pytest.raises(ValueError):
        _extract(changed, _pin(archive))


def test_archive_parser_preserves_finite_metadata_and_original_clock_bounds():
    with _BoundedTarBytes(b"metadata", time.monotonic() + 5) as stream:
        with pytest.raises(ValueError, match="metadata bytes"):
            stream.read(_MAX_METADATA_READ_BYTES + 1)
    with pytest.raises(TimeoutError):
        provider_archive_member(_archive(), _pin(b""), deadline=time.monotonic() - 1)


def test_physical_observations_retain_the_complete_body_and_refuse_symlinks(tmp_path):
    actual = (tmp_path / "archive.tar.xz").resolve()
    actual.write_bytes(_archive())
    body, observation = _physical(actual, max_bytes=1024 * 1024, deadline=time.monotonic() + 5)
    assert body == actual.read_bytes()
    assert observation["sha256"] == hashlib.sha256(body).hexdigest()
    assert _observation(observation, max_bytes=1024 * 1024) == observation
    with pytest.raises(ValueError, match="identity/byte observation"):
        _observation({**observation, "bytes": len(body) + 1}, max_bytes=1024 * 1024)
    link = tmp_path / "archive-link.tar.xz"
    link.symlink_to(actual)
    with pytest.raises(ValueError, match="actual physical path"):
        _physical(link, max_bytes=1024 * 1024, deadline=time.monotonic() + 5)


def test_receipt_or_version_data_cannot_create_original_provider_custody(tmp_path):
    reader = SnapshotReader(tmp_path)
    receipt = {"kind": "nix-source-build", "version": "v0.3.25a", "build": {"compiler": "ghc-9.8.4"}}
    with pytest.raises(ValueError, match="actual live Source/SDK owner"):
        observe_crossref_provider_archive(
            receipt,
            tmp_path / "retained",
            tmp_path / "archive.tar.xz",
            tmp_path / "pandoc-crossref",
            reader,
            deadline=time.monotonic() + 5,
        )


def test_record_pointers_cannot_create_external_replay_or_renderer_authority(tmp_path):
    reader = SnapshotReader(tmp_path)
    binding = {"path": "untrusted.json", "sha256": "0" * 64}
    with pytest.raises(ValueError):
        replay_crossref_provider_archive(
            None,
            binding,
            binding,
            reader,
            tool_reader=reader,
            scope="paper",
            run_id="untrusted",
            deadline=time.monotonic() + 5,
        )
    with pytest.raises(ValueError, match="concrete genuine renderer"):
        replay_stage_crossref_provider_archive(object(), binding, binding, reader)


def _source_record():
    content = (Path(__file__).resolve().parents[3] / PIN_SOURCE).read_bytes()
    host = {"system": "Linux", "machine": "x86_64"}
    pin = select_document_tool(content, host, "crossref")
    record = {
        "schema_version": SCHEMA,
        "run_id": "data-predicate-only",
        "host": host,
        "pin": copy.deepcopy(pin),
        "pin_source_path": PIN_SOURCE,
        "bindings": {"pin_source": {}, "archive": {}},
        "member": {},
        "archive_observation": {},
        "executable_observation": {},
        "source_binding": ["original-Source-commit", "original-Source-identity"],
    }
    return content, pin, record


@pytest.mark.parametrize(
    "field",
    [
        "flake_url",
        "revision",
        "nar_hash",
        "flake_lock_sha256",
        "upstream_freeze_sha256",
        "upstream_compiler",
        "recipe_path",
        "recipe_sha256",
        "freeze_path",
        "freeze_sha256",
        "compiler_patches",
        "resolved_freeze_sha256",
        "compiler",
        "ghc_options",
        "compiler_derivation",
        "compiler_output",
        "plan_derivation",
        "plan_output",
        "derivation",
        "output",
    ],
)
def test_retained_provider_pin_cannot_replace_any_source_compiler_or_dependency_pin(field):
    _, pin, record = _source_record()
    expected = {
        "run_id": record["run_id"],
        "host": record["host"],
        "pin": pin,
        "source_binding": record["source_binding"],
    }
    _validate_record(record, **expected)
    value = record["pin"]["build"][field]
    record["pin"]["build"][field] = value + ["-tampered"] if type(value) is list else value + "-tampered"
    with pytest.raises(ValueError, match="Source/platform/pin"):
        _validate_record(record, **expected)


@pytest.mark.parametrize("patch_index", [0, 1])
@pytest.mark.parametrize("field", ["path", "sha256"])
def test_retained_compiler_patch_row_cannot_replace_the_selected_source(patch_index: int, field: str) -> None:
    _, pin, record = _source_record()
    expected = {
        "run_id": record["run_id"],
        "host": record["host"],
        "pin": pin,
        "source_binding": record["source_binding"],
    }
    row = record["pin"]["build"]["compiler_patches"][patch_index]
    row[field] += "-tampered"
    with pytest.raises(ValueError, match="Source/platform/pin"):
        _validate_record(record, **expected)


@pytest.mark.parametrize(
    "host",
    [
        {"system": "Linux", "machine": "aarch64"},
        {"system": "Darwin", "machine": "amd64"},
        {"system": "Windows", "machine": "x86_64"},
    ],
)
def test_archive_source_selection_cannot_admit_an_unsupported_host(host):
    content, _, _ = _source_record()
    with pytest.raises(ValueError):
        select_document_tool(content, host, "crossref")


def test_declared_tar_extent_cannot_weaken_the_native_executable_payload_bound():
    member = tarfile.TarInfo("pandoc-crossref")
    member.mode, member.size = 0o755, MAX_EXECUTABLE_BYTES + 1
    archive = lzma.compress(member.tobuf() + b"\0" * 1024)
    with pytest.raises(ValueError, match="finite uncompressed payload bound"):
        _extract(archive, _pin(archive))


@pytest.mark.parametrize("deadline", [True, float("inf"), float("nan"), None])
def test_archive_decoder_cannot_replace_the_original_finite_clock(deadline):
    archive = _archive()
    with pytest.raises(ValueError, match="original finite monotonic deadline"):
        provider_archive_member(archive, _pin(archive), deadline=deadline)
