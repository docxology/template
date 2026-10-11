"""Compare retained cache Code as bounded DATA, never construct cached Code.

The caller authenticates origin, cache header/digest and admitted Source. This
parser compares all CPython 3.12–3.14 serialized Code fields and typed constants
against trusted compilation, normalizing only refs/interning and set ordering.
"""

from __future__ import annotations

import hashlib
import importlib.util
import marshal
import struct
import sys
import types
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES
from infrastructure.project.public_reference_git import remaining

_PENDING = object()
_MAX_DEPTH = 2 * 128 + 4  # Serialized co_consts adds a tuple around each Code.


@dataclass(frozen=True, slots=True)
class _Node:
    kind: bytes
    payload: bytes | tuple[_Node, ...]
    ordering_digest: bytes


def _node(kind: bytes, payload: bytes | tuple[_Node, ...]) -> _Node:
    packed = payload if isinstance(payload, bytes) else b"".join(child.ordering_digest for child in payload)
    digest = hashlib.sha256(kind + len(packed).to_bytes(8, "little") + packed).digest()
    return _Node(kind, payload, digest)


def _same_data(left: _Node, right: _Node, *, deadline: float) -> bool:
    pending = [(left, right)]
    seen: set[tuple[int, int]] = set()
    while pending:
        remaining(deadline)
        first, second = pending.pop()
        pair = (id(first), id(second))
        if pair in seen:
            continue
        seen.add(pair)
        if len(seen) > MAX_CACHE_BYTES // 8:
            raise ValueError("Office cache exact DATA comparison exceeds its retained work bound")
        if first.kind != second.kind:
            return False
        if isinstance(first.payload, bytes):
            if not isinstance(second.payload, bytes) or first.payload != second.payload:
                return False
        else:
            if isinstance(second.payload, bytes) or len(first.payload) != len(second.payload):
                return False
            pending.extend(zip(first.payload, second.payload, strict=True))
    remaining(deadline)
    return True


def _small_integer(value: int) -> _Node:
    sign, magnitude = int(value < 0), abs(value)
    digits = bytearray()
    while magnitude:
        digits.extend((magnitude & 0x7FFF).to_bytes(2, "little"))
        magnitude >>= 15
    return _node(b"integer", bytes([sign]) + bytes(digits))


class _Structure:
    """Finite immutable DATA graph only; no Python Code constructors."""

    def __init__(self, raw: bytes, deadline: float) -> None:
        if type(raw) is not bytes or not raw or len(raw) > MAX_CACHE_BYTES:
            raise ValueError("Office cache structure exceeds its admitted byte bound")
        self.raw = raw
        self.position = 0
        self.deadline = deadline
        self.references: list[_Node | object] = []
        self.nodes = 0

    def take(self, count: int) -> bytes:
        remaining(self.deadline)
        end = self.position + count
        if count < 0 or end > len(self.raw):
            raise ValueError("Office cache structure has a truncated or negative field")
        value = self.raw[self.position : end]
        self.position = end
        return value

    def integer(self) -> int:
        return int.from_bytes(self.take(4), "little", signed=True)

    def count(self) -> int:
        value = self.integer()
        if value < 0 or value > len(self.raw) - self.position:
            raise ValueError("Office cache structure count exceeds its actual retained body")
        return value

    def long(self) -> _Node:
        length = self.integer()
        digits = self.take(2 * abs(length))
        for index in range(0, len(digits), 2):
            remaining(self.deadline)
            if digits[index + 1] & 0x80:
                raise ValueError("Office cache integer has an invalid base32768 digit")
        if digits.endswith(b"\0\0"):
            raise ValueError("Office cache integer has an unnormalized leading zero digit")
        return _node(b"integer", bytes([int(length < 0 and bool(digits))]) + digits)

    def floating(self) -> bytes:
        text = self.take(self.take(1)[0])
        try:
            return struct.pack("<d", float(text.decode("ascii")))
        except (UnicodeError, ValueError, OverflowError) as error:
            raise ValueError("Office cache has an invalid primitive float") from error

    def object(self, depth: int = 0) -> _Node:
        remaining(self.deadline)
        self.nodes += 1
        if depth > _MAX_DEPTH or self.nodes > MAX_CACHE_BYTES // 8:
            raise ValueError("Office cache structure exceeds its existing finite work/depth profile")
        marker = self.take(1)[0]
        tag, flagged = marker & 0x7F, bool(marker & 0x80)
        if flagged and tag in b"NFT.":
            raise ValueError("Office cache singleton has an unsupported reference flag")
        if tag == ord("r"):
            index = self.integer()
            if flagged or index < 0 or index >= len(self.references):
                raise ValueError("Office cache structure has an invalid reference")
            value = self.references[index]
            if not isinstance(value, _Node):
                raise ValueError("Office cache structure has a cyclic or unresolved reference")
            return value
        reference = len(self.references) if flagged else None
        if reference is not None:
            if reference >= MAX_CACHE_BYTES // 32:
                raise ValueError("Office cache reference storage exceeds the retained byte ceiling")
            self.references.append(_PENDING)
        value = self.value(tag, depth)
        if reference is not None:
            self.references[reference] = value
        return value

    def value(self, tag: int, depth: int) -> _Node:
        if tag in b"NFT.":
            return _node(bytes([tag]), b"")
        if tag == ord("i"):
            return _small_integer(self.integer())
        if tag == ord("I"):
            return _small_integer(int.from_bytes(self.take(8), "little", signed=True))
        if tag == ord("l"):
            return self.long()
        if tag in b"fg":
            return _node(b"float", self.take(8) if tag == ord("g") else self.floating())
        if tag in b"xy":
            return _node(b"complex", self.take(16) if tag == ord("y") else self.floating() + self.floating())
        if tag == ord("s"):
            return _node(b"bytes", self.take(self.count()))
        if tag in b"utazAZ":
            raw = self.take(self.take(1)[0] if tag in b"zZ" else self.count())
            try:
                text = raw.decode("ascii" if tag in b"azAZ" else "utf-8", "surrogatepass")
            except UnicodeError as error:
                raise ValueError("Office cache has an invalid primitive string") from error
            return _node(b"string", text.encode("utf-8", "surrogatepass"))
        if tag in b"()>":
            count = self.take(1)[0] if tag == ord(")") else self.count()
            children = [self.object(depth + 1) for _ in range(count)]
            if tag == ord(">"):
                children.sort(key=lambda child: child.ordering_digest)
            return _node(b"frozenset" if tag == ord(">") else b"tuple", tuple(children))
        if tag == ord(":"):
            return _node(b"slice", tuple(self.object(depth + 1) for _ in range(3)))
        if tag == ord("c"):
            # Complete CPython3.12–3.14 Code wire fields, in original wire order.
            fields = [_node(b"parameter-fields", self.take(20))]
            fields.extend(self.object(depth + 1) for _ in range(8))
            fields.append(_node(b"first-line-field", self.take(4)))
            fields.extend(self.object(depth + 1) for _ in range(2))
            return _node(b"code", tuple(fields))
        raise ValueError("Office cache has an unsupported executable-constant wire tag")

    def code(self) -> _Node:
        if (self.raw[0] & 0x7F) != ord("c"):
            raise ValueError("Office cache body is not a serialized Code record")
        result = self.object()
        if self.position != len(self.raw):
            raise ValueError("Office cache body has unconsumed trailing bytes")
        remaining(self.deadline)
        return result


def verify_office_cache_code_structure(body: bytes, compiled: types.CodeType, *, deadline: float) -> None:
    """Compare retained DATA with trusted Source Code, without deserializing it.

    This cannot authenticate original execution or grant a Source capability.
    The Office caller supplies its already admitted fresh compilation and keeps
    separate actual Code, original process, cache prefix/header/digest guards.
    """
    remaining(deadline)
    if (
        sys.implementation.name != "cpython"
        or sys.version_info[:2] not in ((3, 12), (3, 13), (3, 14))
        or type(compiled) is not types.CodeType
    ):
        raise ValueError("Office cache structure requires the independently admitted CPython3.12–3.14 Code profile")
    trusted = marshal.dumps(compiled)
    if not _same_data(_Structure(body, deadline).code(), _Structure(trusted, deadline).code(), deadline=deadline):
        raise ValueError("Office original cache Code fields differ from admitted actual Source compilation")
    remaining(deadline)


def verify_office_execution_cache(
    raw: bytes,
    compiled: types.CodeType,
    *,
    original_path: str,
    prefix: Path,
    execution_sha256: str,
    deadline: float,
) -> None:
    """Preserve authenticated caller's original cache/Source pairing predicates.

    These arguments are DATA, not an original capability. The caller separately
    binds them to the genuine original audit/closure and actual executed Code.
    """
    remaining(deadline)
    if (
        not Path(original_path).is_relative_to(prefix)
        or len(raw) < 16
        or raw[:4] != importlib.util.MAGIC_NUMBER
        or hashlib.sha256(raw).hexdigest() != execution_sha256
    ):
        raise ValueError("Office original actual execution-time cache differs")
    verify_office_cache_code_structure(raw[16:], compiled, deadline=deadline)
    remaining(deadline)
