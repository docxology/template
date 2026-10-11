"""Real source files retain complete policy identity under unchanged byte caps."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA, RootCasePolicy
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_policy_encoding import (
    MAX_PART_BYTES,
    decode_policy,
    encode_policy,
    policy_part_path,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_POLICY = "infrastructure/config/owned-policy.json"


def _value() -> dict:
    family = "tests/test_owned.py::test_value"
    return {
        "schema_version": POLICY_SCHEMA,
        "runtimes": ["3.12", "3.13", "3.14"],
        "platforms": ["darwin", "linux"],
        "families": [
            {
                "id": family,
                "lane": "core",
                "obligations": [],
                "members": [
                    {"nodeid": family if item is None else family + "[" + item + "]", "parameter_id": item}
                    for item in (None, "", "λ:explicit")
                ],
                "source_sha256": hashlib.sha256(b"def test_value(): pass\n").hexdigest(),
                "metadata_sha256": hashlib.sha256(b"explicit pure serialization control").hexdigest(),
            }
        ],
        "obligations": [],
    }


def _write(root: Path, manifest: dict, pieces: tuple[bytes, ...]) -> None:
    (root / _POLICY).parent.mkdir(parents=True, exist_ok=True)
    (root / _POLICY).write_text(json.dumps(manifest))
    for ordinal, piece in enumerate(pieces):
        (root / policy_part_path(_POLICY, ordinal)).write_bytes(piece)


def _decode(root: Path) -> dict:
    reader = SnapshotReader(root)
    return decode_policy(reader, reader.read(_POLICY))


def _replace_piece(manifest: dict, pieces: tuple[bytes, ...], content: bytes) -> tuple[bytes, ...]:
    manifest["parts"][0].update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    return (content, *pieces[1:])


def test_literal_and_encoded_source_load_use_the_same_full_policy_admission(tmp_path: Path) -> None:
    value = _value()
    manifest, pieces = encode_policy(value)
    _write(tmp_path, manifest, pieces)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.template.root_acceptance]\nschema_version=2\n"
        f'policy="{_POLICY}"\nprerequisites="infrastructure/config/owned-prerequisites.json"\n'
    )
    (tmp_path / "infrastructure/config/owned-prerequisites.json").write_text(
        '{"schema_version":"template-root-case-prerequisites-v2","obligations":[]}'
    )
    encoded, binding, _, obligations = load_policy(SnapshotReader(tmp_path))
    assert encoded == RootCasePolicy.parse(value) and not obligations
    assert binding["sha256"] == hashlib.sha256((tmp_path / _POLICY).read_bytes()).hexdigest()
    assert _decode(tmp_path) == value
    (tmp_path / _POLICY).write_text(json.dumps(value))
    literal, _, _, _ = load_policy(SnapshotReader(tmp_path))
    assert literal == encoded


def test_multiple_bounded_files_preserve_every_unique_member(tmp_path: Path) -> None:
    value = _value()
    family = value["families"][0]
    parameters = [hashlib.sha256(str(index).encode()).hexdigest() for index in range(14000)]
    family["members"] = [{"nodeid": family["id"] + "[" + item + "]", "parameter_id": item} for item in parameters]
    manifest, pieces = encode_policy(value)
    assert len(pieces) > 1 and all(len(piece) <= MAX_PART_BYTES for piece in pieces)
    _write(tmp_path, manifest, pieces)
    assert _decode(tmp_path) == value
    manifest["parts"].reverse()
    (tmp_path / _POLICY).write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unordered"):
        _decode(tmp_path)


@pytest.mark.parametrize("fault", ["missing", "changed", "oversized", "linked", "ordinal", "digest", "path"])
def test_part_admission_refuses_missing_changed_or_unbounded_files(tmp_path: Path, fault: str) -> None:
    manifest, pieces = encode_policy(_value())
    _write(tmp_path, manifest, pieces)
    part = tmp_path / policy_part_path(_POLICY, 0)
    if fault == "missing":
        part.unlink()
    elif fault == "changed":
        part.write_bytes(pieces[0].replace(b'"ordinal":0', b'"ordinal":1'))
    elif fault == "oversized":
        with part.open("wb") as stream:
            stream.truncate(MAX_PART_BYTES + 1)
        manifest["parts"][0]["bytes"] = MAX_PART_BYTES + 1
    elif fault == "linked":
        alternate = tmp_path / "retained-original.json"
        part.rename(alternate)
        part.symlink_to(alternate)
    elif fault == "ordinal":
        manifest["parts"][0]["ordinal"] = True
    elif fault == "digest":
        manifest["parts"][0]["sha256"] = "0" * 64
    else:
        manifest["parts"][0]["path"] = "../private.json"
    (tmp_path / _POLICY).write_text(json.dumps(manifest))
    with pytest.raises((ValueError, OSError)):
        _decode(tmp_path)


@pytest.mark.parametrize(
    "fault", ["bomb", "truncated", "trailing", "noncanonical", "duplicate", "policy-digest", "size"]
)
def test_rehashed_parts_cannot_hide_expansion_or_ambiguous_policy(tmp_path: Path, fault: str) -> None:
    manifest, pieces = encode_policy(_value())
    payload = json.loads(pieces[0])
    packed = base64.b64decode(payload["data"])
    original = zlib.decompress(packed)
    if fault == "bomb":
        packed = zlib.compress(b"x" * 100000)
        manifest["decoded_bytes"] = 10
    elif fault == "truncated":
        packed = packed[:-1]
    elif fault == "trailing":
        packed += b"unobserved"
    elif fault == "noncanonical":
        packed = zlib.compress(original, level=0)
    elif fault == "duplicate":
        original = original.replace(b'"schema_version":', b'"schema_version":"duplicate","schema_version":')
        packed = zlib.compress(original, level=9)
        manifest.update(decoded_bytes=len(original), decoded_sha256=hashlib.sha256(original).hexdigest())
    elif fault == "policy-digest":
        manifest["policy_sha256"] = "0" * 64
    else:
        manifest["decoded_bytes"] = 64 * 1024 * 1024 + 1
    payload["data"] = base64.b64encode(packed).decode()
    pieces = _replace_piece(
        manifest, pieces, json.dumps(payload, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    )
    _write(tmp_path, manifest, pieces)
    with pytest.raises(ValueError):
        _decode(tmp_path)


def test_manifest_duplicate_fields_are_rejected_before_policy_dispatch(tmp_path: Path) -> None:
    manifest, pieces = encode_policy(_value())
    _write(tmp_path, manifest, pieces)
    path = tmp_path / _POLICY
    path.write_bytes(path.read_bytes().replace(b'"encoding":', b'"encoding":"hidden","encoding":'))
    with pytest.raises(ValueError, match="repeats JSON field"):
        _decode(tmp_path)


@pytest.mark.parametrize(
    "reference",
    [
        "../owned.json",
        "infrastructure/config/./owned.json",
        "infrastructure/owned.json",
        "infrastructure/config/owned\\file.json",
    ],
)
def test_part_paths_are_derived_from_exact_source_configuration(reference: str) -> None:
    with pytest.raises(ValueError, match="exact public"):
        policy_part_path(reference, 0)
