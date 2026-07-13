from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass

from .config import MadlibConfig, SlotSpec


@dataclass(frozen=True)
class TokenChoice:
    """Data container for TokenChoice."""

    variable_name: str
    slot_name: str
    category: str
    value: str
    section: str
    ordinal: int
    source_key: str

    def as_dict(self) -> dict[str, object]:
        """Process as dict."""
        return asdict(self)


@dataclass(frozen=True)
class TokenPlan:
    """Data container for TokenPlan."""

    seed: int
    choices: tuple[TokenChoice, ...]

    @property
    def category_counts(self) -> dict[str, int]:
        """Tally how many resolved token choices came from each lexicon category.

        Used by the analysis/figure layer to show category distribution
        (e.g. how many "villain", "setting", or "tone" tokens were injected)
        without re-walking `choices` at each call site.
        """
        return dict(Counter(choice.category for choice in self.choices))

    @property
    def section_counts(self) -> dict[str, int]:
        """Tally how many resolved token choices were injected into each manuscript section.

        Mirrors `category_counts` but grouped by destination section instead
        of source category — the basis for the section-configuration figures
        and the reviewer packet's per-section density reporting.
        """
        return dict(Counter(choice.section for choice in self.choices))

    @property
    def provenance(self) -> dict[str, dict[str, object]]:
        """Map each resolved variable name to the lexicon choice it came from.

        Gives every `{{VARIABLE}}` a traceable (category, value, section,
        source) record so a reviewer can answer "why does the manuscript say
        X here" without re-deriving the deterministic selection in `_choose_value`.
        """
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
        """Return every resolved token value chosen for a given lexicon category, in slot order."""
        return tuple(choice.value for choice in self.choices if choice.category == category)

    def first_value(self, category: str, default: str) -> str:
        """Return the first resolved value for a category, or `default` if that category was never chosen from."""
        values = self.values_for_category(category)
        return values[0] if values else default


def generate_token_plan(config: MadlibConfig) -> TokenPlan:
    """Deterministically resolve every configured slot into a concrete token choice.

    For each slot in `config.slots` and each of its `count` ordinals, derives
    a stable variable name (`_variable_name`) and picks a lexicon value via
    the seeded digest in `_choose_value` (see that function's docstring for
    why a hash digest is used instead of a random generator). The resulting
    `TokenPlan` is the single source of truth consumed by manuscript
    hydration, the composition tables, and the analysis figures — it is
    computed once per run and never mutated.
    """
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
    """Deterministically select one lexicon value for a slot/ordinal pair.

    A SHA-256 digest over `(seed, slot name, category, ordinal, lexicon
    values)` is used instead of `random.Random(seed)` so the choice is
    reproducible across Python versions and stdlib PRNG changes, is
    trivially auditable (any reviewer can recompute the same digest by
    hand), and is stable if unrelated slots are added or reordered upstream
    — only that slot's own inputs affect its own digest, so token plans
    never silently shift when the config grows. Returns both the chosen
    value and its lexicon index so callers (e.g. `generate_token_plan`) can
    record a precise `source_key` back to `manuscript/config.yaml`.
    """
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
