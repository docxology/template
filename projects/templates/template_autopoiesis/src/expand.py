"""Expand a Grammar into deterministic Specs.

Each Spec is a complete, reproducible description of a generated child project.
The seed + grammar hash together uniquely determine every selection made.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .common import DERIVED_SEED_BITS, HASH_PREFIX_HEX_LENGTH
from .grammar import Grammar

SCHEMA_VERSION = "autopoiesis/spec/1"
_UNIT_SEP = "\x1f"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _digest_index(seed: int, slot_name: str, ordinal: int, options: tuple[str, ...]) -> int:
    """Return a deterministic index into *options* based on the given inputs."""
    key = f"{seed}{_UNIT_SEP}{slot_name}{_UNIT_SEP}{ordinal}{_UNIT_SEP}{','.join(options)}"
    digest = hashlib.sha256(key.encode()).digest()
    value = int.from_bytes(digest[:8], "big")
    return value % len(options)


# ---------------------------------------------------------------------------
# Spec dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Spec:
    """A fully-resolved specification for one generated child project."""

    schema_version: str
    seed: int
    grammar_hash: str
    selections: tuple[tuple[str, str], ...]  # (slot_name, chosen_value)
    deps: tuple[str, ...]
    primitive_domain: str

    def to_dict(self) -> dict:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "schema_version": self.schema_version,
            "seed": self.seed,
            "grammar_hash": self.grammar_hash,
            "selections": {k: v for k, v in self.selections},
            "deps": list(self.deps),
            "primitive_domain": self.primitive_domain,
        }

    def to_json(self) -> str:
        """Serialize this object to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @property
    def spec_hash(self) -> str:
        """Process spec hash."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:HASH_PREFIX_HEX_LENGTH]


# ---------------------------------------------------------------------------
# Core expand function
# ---------------------------------------------------------------------------


def expand(grammar: Grammar, seed: Optional[int] = None) -> Spec:
    """Deterministically expand *grammar* into a Spec.

    If *seed* is provided it overrides grammar.seed for this expansion.
    """
    effective_seed = grammar.seed if seed is None else seed
    selections: list[tuple[str, str]] = []
    primitive_domain = ""

    for ordinal, slot in enumerate(grammar.slots):
        idx = _digest_index(effective_seed, slot.name, ordinal, slot.options)
        chosen = slot.options[idx]
        selections.append((slot.name, chosen))
        if slot.name == "primitive_domain":
            primitive_domain = chosen

    # If no primitive_domain slot exists, fall back to first known domain
    if not primitive_domain:
        from .grammar import KNOWN_DOMAINS

        primitive_domain = KNOWN_DOMAINS[0]

    return Spec(
        schema_version=SCHEMA_VERSION,
        seed=effective_seed,
        grammar_hash=grammar.grammar_hash,
        selections=tuple(selections),
        deps=grammar.deps,
        primitive_domain=primitive_domain,
    )


# ---------------------------------------------------------------------------
# Write spec to disk
# ---------------------------------------------------------------------------


def write_spec(spec: Spec, out_path: str | Path) -> Path:
    """Write *spec* as JSON to *out_path* and return the resolved Path."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(spec.to_json())
    return out


# ---------------------------------------------------------------------------
# Seed derivation
# ---------------------------------------------------------------------------


def derive_seed(base_seed: int, index: int) -> int:
    """Derive a deterministic child seed from *base_seed* and *index*."""
    key = f"{base_seed}{_UNIT_SEP}{index}"
    digest = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << DERIVED_SEED_BITS) - 1)


# ---------------------------------------------------------------------------
# Enumerate / sample
# ---------------------------------------------------------------------------


def enumerate_all(grammar: Grammar) -> list[dict]:
    """Return one dict per cell in the full grammar product space."""
    slot_options = [(s.name, s.options) for s in grammar.slots]
    results = []
    for combo in itertools.product(*[opts for _, opts in slot_options]):
        entry: dict[str, str] = {}
        for (name, _), value in zip(slot_options, combo):
            entry[name] = value
        results.append(entry)
    return results


def sample(grammar: Grammar, count: int, base_seed: Optional[int] = None) -> list[Spec]:
    """Return *count* Specs sampled with derived seeds."""
    root_seed = grammar.seed if base_seed is None else base_seed
    return [expand(grammar, seed=derive_seed(root_seed, i)) for i in range(count)]
