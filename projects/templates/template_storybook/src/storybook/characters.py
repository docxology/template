from __future__ import annotations

from collections.abc import Mapping

from .models import Character

VALID_SHAPES = frozenset({"cube", "tetrahedron"})


def _require_text(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"character.{key} must be a non-empty string")
    return value


def generate_character(record: Mapping[str, object]) -> Character:
    shape = _require_text(record, "shape")
    family_shape = _require_text(record, "family_shape")
    if shape not in VALID_SHAPES:
        raise ValueError(f"Unsupported character shape: {shape}")
    if family_shape not in VALID_SHAPES:
        raise ValueError(f"Unsupported family shape: {family_shape}")

    return Character(
        character_id=_require_text(record, "id"),
        name=_require_text(record, "name"),
        shape=shape,
        family_shape=family_shape,
        fill=_require_text(record, "fill"),
        accent=_require_text(record, "accent"),
        role=_require_text(record, "role"),
    )


def generate_cast(records: list[object]) -> tuple[Character, ...]:
    characters: list[Character] = []
    seen: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Each character entry must be a mapping")
        character = generate_character(item)
        if character.character_id in seen:
            raise ValueError(f"Duplicate character id: {character.character_id}")
        seen.add(character.character_id)
        characters.append(character)
    if not characters:
        raise ValueError("Storybook requires at least one character")
    return tuple(characters)


def child_pair(characters: tuple[Character, ...]) -> tuple[Character, Character]:
    tetra = next((character for character in characters if character.character_id == "tessa"), None)
    cube = next((character for character in characters if character.character_id == "ciro"), None)
    if tetra is None or cube is None:
        raise ValueError("Storybook cast must include tessa and ciro")
    return tetra, cube
