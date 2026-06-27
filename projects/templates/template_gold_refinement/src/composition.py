"""Mega-madlib token composition for the gold-refinement exemplar.

Deterministic token selection via seeded SHA-256 digest over category
inventories. Each token choice is reproducible, traceable, and config-owned.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass

try:
    from .config import GoldRefinementConfig, SlotSpec
except ImportError:
    from config import GoldRefinementConfig, SlotSpec  # type: ignore[no-redef]


@dataclass(frozen=True)
class TokenChoice:
    """A single selected token with full provenance."""

    variable_name: str
    slot_name: str
    category: str
    value: str
    section: str
    ordinal: int
    source_key: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TokenPlan:
    """The full token plan from all slots."""

    seed: int
    choices: tuple[TokenChoice, ...]

    @property
    def category_counts(self) -> dict[str, int]:
        return dict(Counter(choice.category for choice in self.choices))

    @property
    def section_counts(self) -> dict[str, int]:
        return dict(Counter(choice.section for choice in self.choices))

    @property
    def provenance(self) -> dict[str, dict[str, object]]:
        return {
            choice.variable_name: {
                "category": choice.category,
                "value": choice.value,
                "section": choice.section,
                "source": choice.source_key,
            }
            for choice in self.choices
        }

    def values_for_category(self, category: str) -> tuple[str, ...]:
        return tuple(c.value for c in self.choices if c.category == category)

    def values_for_section(self, section: str) -> tuple[str, ...]:
        return tuple(c.value for c in self.choices if c.section == section)

    def first_value(self, category: str, default: str) -> str:
        vals = self.values_for_category(category)
        return vals[0] if vals else default


def generate_token_plan(config: GoldRefinementConfig) -> TokenPlan:
    """Generate the full token plan from a config's slots and lexicon."""
    choices: list[TokenChoice] = []
    for slot in config.slots:
        for ordinal in range(1, slot.count + 1):
            variable_name = _variable_name(slot, ordinal)
            value, index = _choose_value(config, slot, ordinal)
            choices.append(
                TokenChoice(
                    variable_name=variable_name,
                    slot_name=slot.name,
                    category=slot.category,
                    value=value,
                    section=slot.section,
                    ordinal=ordinal,
                    source_key=f"manuscript/config.yaml#gold_refinement.lexicon.{slot.category}[{index}]",
                )
            )
    return TokenPlan(seed=config.seed, choices=tuple(choices))


def _variable_name(slot: SlotSpec, ordinal: int) -> str:
    base = slot.name.upper()
    return base if slot.count == 1 else f"{base}_{ordinal}"


def _choose_value(config: GoldRefinementConfig, slot: SlotSpec, ordinal: int) -> tuple[str, int]:
    """Deterministic selection: SHA-256(seed|slot|category|ordinal|inventory)."""
    values = config.lexicon[slot.category]
    if not values:
        raise ValueError(f"lexicon category '{slot.category}' is empty")
    digest_input = "|".join(
        (
            str(config.seed),
            slot.name,
            slot.category,
            str(ordinal),
            "\x1f".join(values),
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
    index = int(digest[:12], 16) % len(values)
    return values[index], index


def compose_section_body(
    section: str,
    plan: TokenPlan,
    config: GoldRefinementConfig,
) -> str:
    """Compose a draft section body from narrative moves and selected tokens.

    This is a deterministic prose generator — the "smelting" stage that
    combines raw ore (lexicon) with narrative structure (moves) into
    a composed section body.
    """
    moves = config.narrative_moves.get(section, ())
    section_tokens = plan.values_for_section(section)
    lines: list[str] = []
    for i, move in enumerate(moves):
        token_val = section_tokens[i] if i < len(section_tokens) else ""
        if token_val:
            lines.append(f"- {move.capitalize()}: {token_val}")
        else:
            lines.append(f"- {move.capitalize()}")
    return "\n".join(lines)


def compose_all_sections(
    plan: TokenPlan,
    config: GoldRefinementConfig,
) -> dict[str, str]:
    """Compose bodies for all enabled sections."""
    result: dict[str, str] = {}
    for section in config.enabled_sections:
        result[section] = compose_section_body(section, plan, config)
    return result


__all__ = [
    "TokenChoice",
    "TokenPlan",
    "compose_all_sections",
    "compose_section_body",
    "generate_token_plan",
]
