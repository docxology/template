"""Canonical lossless census representation preserves original observations."""

from copy import deepcopy

import pytest

from infrastructure.project.public_root_census_encoding import decode, encode, _encode_dag, _decode_dag, _inflate


def test_original_metadata_and_literal_empty_parameter_identity_roundtrip():
    case = {"family": "tests/test_owned.py::test_value", "parameter_id": "", "fixtures": {"scope": ["session"]}}
    original = {"original_pytest_exit_code": 0, "exit_code": 0, "cases": [case, case], "executed_reports": 0}
    encoded = encode(original)
    assert decode(encoded) == original
    assert _encode_dag(original)["nodes"].count(["scalar", "session"]) == 1


@pytest.mark.parametrize("corruption", ["forward", "unused", "digest", "duplicate-key"])
def test_census_encoding_refuses_ambiguous_or_altered_observations(corruption):
    encoded = deepcopy(_encode_dag({"original_pytest_exit_code": 0, "cases": ["actual"]}))
    if corruption == "forward":
        encoded["nodes"][0] = ["array", [0]]
    elif corruption == "unused":
        encoded["nodes"].append(["scalar", "unobserved"])
    elif corruption == "digest":
        encoded["value_sha256"] = "0" * 64
    else:
        root = encoded["nodes"][encoded["root"]]
        root[1].append(root[1][0])
    with pytest.raises(ValueError):
        _decode_dag(encoded)


@pytest.mark.parametrize("corruption", ["trailing", "truncated", "digest", "size", "bomb", "noncanonical"])
def test_compressed_original_census_refuses_corrupt_or_unbounded_bytes(corruption):
    import base64
    import zlib

    encoded = encode({"actual": ["original", "original"]})
    packed = base64.b64decode(encoded["data"])
    if corruption == "trailing":
        packed += b"unexpected"
    elif corruption == "truncated":
        packed = packed[:-1]
    elif corruption == "digest":
        encoded["decoded_sha256"] = "0" * 64
    elif corruption == "size":
        encoded["decoded_size"] = 64 * 1024 * 1024 + 1
    elif corruption == "bomb":
        packed = zlib.compress(b"x" * 100000)
        encoded["decoded_size"] = 10
    else:
        packed = zlib.compress(zlib.decompress(packed), level=0)
    encoded["data"] = base64.b64encode(packed).decode()
    with pytest.raises(ValueError):
        decode(encoded)


def test_decompression_exact_byte_ceiling_and_one_byte_over_refusal():
    import zlib

    # This pure allocation boundary is identical to the production64MiB bound.
    payload = b"x" * 1024
    assert _inflate(zlib.compress(payload), len(payload), limit=1024) == payload
    with pytest.raises(ValueError):
        _inflate(zlib.compress(payload + b"x"), 1025, limit=1024)
    with pytest.raises(ValueError):
        _inflate(zlib.compress(payload + b"x"), 1024, limit=1024)


def test_actual_64MiB_decompression_ceiling_preserves_guard():
    import zlib

    from infrastructure.project.public_root_census_encoding import MAX_BYTES

    packed = zlib.compress(b"x" * MAX_BYTES)
    assert len(_inflate(packed, MAX_BYTES)) == MAX_BYTES
    with pytest.raises(ValueError):
        _inflate(zlib.compress(b"x" * (MAX_BYTES + 1)), MAX_BYTES)
