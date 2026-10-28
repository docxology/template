"""Real compiled Code and bounded immutable DATA parser security controls."""

from __future__ import annotations

import builtins
import marshal
import sys
import time

import pytest

from infrastructure.reporting.native_office_cache_structure import (
    _Structure,
    _same_data,
    verify_office_cache_code_structure,
)


def _data(raw: bytes):
    parser = _Structure(raw, time.monotonic() + 10)
    value = parser.object()
    assert parser.position == len(raw)
    return value


def test_actual_compiled_source_and_typed_constants_match_only_exact_code():
    code = compile("value = (1, True, 'one')\ndef nested(x):\n    return x + 1\n", "admitted.py", "exec")
    verify_office_cache_code_structure(marshal.dumps(code), code, deadline=time.monotonic() + 10)
    for source, filename in [
        ("value = (True, 1, 'one')\ndef nested(x):\n    return x + 1\n", "admitted.py"),
        ("value = (1, True, 'one')\ndef nested(x):\n    return x + 2\n", "admitted.py"),
        ("value = (1, True, 'one')\ndef nested(x):\n    return x + 1\n", "foreign.py"),
    ]:
        other = compile(source, filename, "exec")
        with pytest.raises(ValueError, match="Code fields differ"):
            verify_office_cache_code_structure(marshal.dumps(other), code, deadline=time.monotonic() + 10)


def test_compiled_code_truncation_and_trailing_bytes_are_refused():
    code = compile("value = 1\n", "admitted.py", "exec")
    raw = marshal.dumps(code)
    for body in [raw[:1], raw[:5], raw[: len(raw) // 2], raw[:-1], raw + b"0"]:
        with pytest.raises(ValueError):
            verify_office_cache_code_structure(body, code, deadline=time.monotonic() + 10)


def test_immutable_mapping_keeps_type_and_pair_order():
    forward = _data(bytes.fromhex("fdda0161e901000000da0162e90200000030"))
    reverse = _data(bytes.fromhex("fdda0162e902000000da0161e90100000030"))
    assert forward.kind == reverse.kind == b"frozendict"
    assert _same_data(forward, forward, deadline=time.monotonic() + 10)
    assert not _same_data(forward, reverse, deadline=time.monotonic() + 10)
    assert not _same_data(_data(b"}0"), _data(b")\x00"), deadline=time.monotonic() + 10)


def test_completed_mapping_reference_is_data_and_pending_reference_is_refused():
    parser = _Structure(bytes.fromhex("fd307200000000"), time.monotonic() + 10)
    first = parser.object()
    assert parser.object() is first
    assert parser.position == len(parser.raw)
    with pytest.raises(ValueError, match="cyclic or unresolved"):
        _data(bytes.fromhex("fd720000000030"))


@pytest.mark.parametrize(
    "raw",
    [
        b"}",  # missing terminator
        bytes.fromhex("fdda016130"),  # NULL is not a value
        bytes.fromhex("fdda0161e901000000"),  # pair without terminator
        bytes.fromhex("fd720100000030"),  # out-of-range reference
        bytes.fromhex("fdb0"),  # flagged NULL is not a terminator
        b"{0",  # mutable dict is never admitted
    ],
)
def test_invalid_immutable_mapping_bodies_fail_closed(raw):
    with pytest.raises(ValueError):
        _data(raw)


def test_current_trusted_primitive_wire_preserves_runtime_profile():
    for value in [(), (None, True, 1, 2.0, b"wire", "wire"), frozenset({1, 2})]:
        _data(marshal.dumps(value))
    if sys.version_info >= (3, 15):
        value = getattr(builtins, "frozendict")({"first": 1, "second": 2})
        raw = marshal.dumps(value)
        assert raw[0] & 0x7F == ord("}")
        assert _data(raw).kind == b"frozendict"
