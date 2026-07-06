"""Grammar definition, parsing, and loading for template_autopoiesis.

The grammar is the combinatoric specification that determines what projects can
be generated.  Each *slot* names a dimension of variation and its allowed
options; the cross product of all slot options (minus reserved slots) is the
*effective product size*.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Domain / dependency constants
# ---------------------------------------------------------------------------

KNOWN_DOMAINS: tuple[str, ...] = (
    "optimization",
    "dynamics",
    "statistics",
    "signal",
    "graph",
)

VENDORABLE_DEPS: tuple[str, ...] = (
    "logging",
    "glossary_gen",
    "figure_manager",
    "manuscript_injection",
    "steganography",
)

DEP_MODES: tuple[str, ...] = ("template", "vendor")

RESERVED_SLOTS: tuple[str, ...] = (
    "figure_profile",
    "qr_profile",
    "integrity_profile",
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GrammarError(ValueError):
    """Raised when a grammar definition is malformed."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GrammarSlot:
    """A single dimension in the grammar with its allowed options."""

    name: str
    options: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise GrammarError("GrammarSlot.name must not be empty")
        if not self.options:
            raise GrammarError(f"GrammarSlot '{self.name}' must have ≥1 option")
        dupes = {o for o in self.options if self.options.count(o) > 1}
        if dupes:
            raise GrammarError(f"GrammarSlot '{self.name}' has duplicate options: {dupes}")


@dataclass(frozen=True)
class Grammar:
    """Full grammar specification loaded from config.yaml."""

    seed: int
    slots: tuple[GrammarSlot, ...]
    deps: tuple[str, ...]
    source_path: Optional[str] = field(default=None, compare=False, hash=False)

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def product_size(self) -> int:
        """Raw cross-product of all slots."""
        n = 1
        for s in self.slots:
            n *= len(s.options)
        return n

    @property
    def reserved_slots(self) -> tuple[GrammarSlot, ...]:
        return tuple(s for s in self.slots if s.name in RESERVED_SLOTS)

    @property
    def effective_slots(self) -> tuple[GrammarSlot, ...]:
        return tuple(s for s in self.slots if s.name not in RESERVED_SLOTS)

    @property
    def effective_product_size(self) -> int:
        n = 1
        for s in self.effective_slots:
            n *= len(s.options)
        return n

    @property
    def grammar_hash(self) -> str:
        canonical = self.canonical()
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def slot(self, name: str) -> GrammarSlot:
        for s in self.slots:
            if s.name == name:
                return s
        raise KeyError(f"No slot named '{name}'")

    def canonical(self) -> str:
        """JSON-stable canonical representation used for hashing."""
        obj = {
            "seed": self.seed,
            "slots": [{"name": s.name, "options": list(s.options)} for s in self.slots],
            "deps": list(self.deps),
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_grammar(block: dict, source_path: Optional[str] = None) -> Grammar:
    """Validate and construct a Grammar from a raw YAML dict."""
    if not isinstance(block, dict):
        raise GrammarError("Grammar block must be a mapping")

    seed = block.get("seed", 42)
    if not isinstance(seed, int):
        raise GrammarError(f"Grammar seed must be int, got {type(seed).__name__}")

    raw_slots = block.get("slots", [])
    if not raw_slots:
        raise GrammarError("Grammar must define at least one slot")

    slots: list[GrammarSlot] = []
    for entry in raw_slots:
        if not isinstance(entry, dict):
            raise GrammarError(f"Each slot must be a mapping, got {type(entry)}")
        name = entry.get("name", "")
        options = tuple(entry.get("options", []))
        slots.append(GrammarSlot(name=name, options=options))

    raw_deps = block.get("deps", [])
    for d in raw_deps:
        if d not in VENDORABLE_DEPS:
            raise GrammarError(f"Unknown dep '{d}'. Known: {VENDORABLE_DEPS}")

    return Grammar(
        seed=seed,
        slots=tuple(slots),
        deps=tuple(raw_deps),
        source_path=source_path,
    )


def force_domain(grammar: Grammar, domain: str) -> Grammar:
    """Return a copy of *grammar* with the primitive_domain slot forced to *domain*."""
    if domain not in KNOWN_DOMAINS:
        raise GrammarError(f"Unknown domain '{domain}'. Known: {KNOWN_DOMAINS}")

    new_slots: list[GrammarSlot] = []
    found = False
    for s in grammar.slots:
        if s.name == "primitive_domain":
            new_slots.append(GrammarSlot(name=s.name, options=(domain,)))
            found = True
        else:
            new_slots.append(s)

    if not found:
        new_slots.append(GrammarSlot(name="primitive_domain", options=(domain,)))

    return Grammar(
        seed=grammar.seed,
        slots=tuple(new_slots),
        deps=grammar.deps,
        source_path=grammar.source_path,
    )


def load_grammar(project_root: str | Path) -> Grammar:
    """Load grammar from *project_root*/manuscript/config.yaml."""
    config_path = Path(project_root) / "manuscript" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open() as fh:
        cfg = yaml.safe_load(fh)

    block = cfg.get("autopoiesis", {})
    return parse_grammar(block, source_path=str(config_path))
