"""Provenance tiers and a hash-chained state history.

Mirrors BPL's audit model ("hash-chained state history with three trust
tiers: Declared, Calibrated, Verified") at the same honest scope BPL itself
claims: a hash chain makes *accidental* corruption, dropped records, or
out-of-order edits to a state history detectable by recomputing the chain —
it is a consistency check, not a cryptographic tamper-proof guarantee against
an actor with write access to the entire stored chain (that would require an
independently-anchored or keyed signature, which this DSL does not
implement). :func:`verify_chain` documents and tests exactly that boundary:
it detects in-chain tampering (any record after the tampered one no longer
matches) but cannot detect a chain rewritten from record zero.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum


class ProvenanceTier(Enum):
    """How a state value was obtained, ordered from least to most trusted."""

    DECLARED = "declared"
    CALIBRATED = "calibrated"
    VERIFIED = "verified"


_GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class StateRecord:
    """One entry in a hash-chained state history."""

    key: str
    value: str
    tier: ProvenanceTier
    prev_hash: str
    record_hash: str


def _record_hash(key: str, value: str, tier: ProvenanceTier, prev_hash: str) -> str:
    payload = json.dumps(
        {"key": key, "value": value, "tier": tier.value, "prev_hash": prev_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_record(
    chain: tuple[StateRecord, ...], key: str, value: str, tier: ProvenanceTier
) -> tuple[StateRecord, ...]:
    """Append a new state record to *chain*, returning the extended chain.

    *chain* is never mutated — the caller holds the previous chain and the
    new one as distinct immutable tuples, matching the project's
    no-in-place-mutation convention.
    """
    prev_hash = chain[-1].record_hash if chain else _GENESIS_HASH
    record_hash = _record_hash(key, value, tier, prev_hash)
    record = StateRecord(key=key, value=value, tier=tier, prev_hash=prev_hash, record_hash=record_hash)
    return (*chain, record)


def verify_chain(chain: tuple[StateRecord, ...]) -> bool:
    """Return whether every record's hash is consistent with its predecessor.

    Recomputes each record's ``record_hash`` from its own fields and the
    *recorded* ``prev_hash``, then checks that ``prev_hash`` chains to the
    actual previous record's hash. A single altered field — value, tier, or
    a swapped record order — breaks the chain at that point.
    """
    expected_prev = _GENESIS_HASH
    for record in chain:
        if record.prev_hash != expected_prev:
            return False
        if _record_hash(record.key, record.value, record.tier, record.prev_hash) != record.record_hash:
            return False
        expected_prev = record.record_hash
    return True


def demo_chain_report() -> dict[str, object]:
    """Declare, calibrate, then verify one value — the manuscript's worked example.

    Returns a JSON-serializable summary (``chain_length``, ``verified``) for
    ``scripts/methods_analysis.py`` to write to ``output/reports/`` and
    ``src/manuscript_variables.py`` to read back as ``{{TRUST_CHAIN_*}}``
    tokens.
    """
    chain: tuple[StateRecord, ...] = ()
    chain = append_record(chain, "calibration_offset", "0.42", ProvenanceTier.DECLARED)
    chain = append_record(chain, "calibration_offset", "0.41", ProvenanceTier.CALIBRATED)
    chain = append_record(chain, "calibration_offset", "0.41", ProvenanceTier.VERIFIED)
    return {"chain_length": len(chain), "verified": verify_chain(chain)}
