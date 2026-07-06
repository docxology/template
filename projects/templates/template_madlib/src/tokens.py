from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass

from .config import MadlibConfig, SlotSpec


@dataclass(frozen=True)
class TokenChoice:
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
        return tuple(choice.value for choice in self.choices if choice.category == category)

    def first_value(self, category: str, default: str) -> str:
        values = self.values_for_category(category)
        return values[0] if values else default


def generate_token_plan(config: MadlibConfig) -> TokenPlan:
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
                    source_key=f"manuscript/config.yaml#madlib.lexicon.{slot.category}[{index}]",
                )
            )
    return TokenPlan(seed=config.seed, choices=tuple(choices))


def _variable_name(slot: SlotSpec, ordinal: int) -> str:
    base = slot.name.upper()
    return base if slot.count == 1 else f"{base}_{ordinal}"


def _choose_value(config: MadlibConfig, slot: SlotSpec, ordinal: int) -> tuple[str, int]:
    values = config.lexicon[slot.category]
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
