from __future__ import annotations

import pytest

from storybook.characters import character_by_id, child_pair, generate_cast, generate_character


def _record(character_id: str = "tessa", shape: str = "tetrahedron", family_shape: str = "cube") -> dict[str, object]:
    return {
        "id": character_id,
        "name": "Tessa",
        "shape": shape,
        "family_shape": family_shape,
        "fill": "#e8f1f8",
        "accent": "#1d3557",
        "role": "protagonist",
    }


def test_generate_character_builds_frozen_record() -> None:
    character = generate_character(_record())
    assert character.character_id == "tessa"
    assert character.shape == "tetrahedron"
    assert character.family_shape == "cube"
    assert character.role == "protagonist"


def test_generate_character_rejects_unsupported_shapes() -> None:
    with pytest.raises(ValueError, match="Unsupported character shape"):
        generate_character(_record(shape="sphere"))
    with pytest.raises(ValueError, match="Unsupported family shape"):
        generate_character(_record(family_shape="sphere"))


def test_generate_character_rejects_blank_fields() -> None:
    record = _record()
    record["name"] = "   "
    with pytest.raises(ValueError, match="character.name must be a non-empty string"):
        generate_character(record)


def test_generate_cast_rejects_duplicate_ids_and_non_mappings() -> None:
    with pytest.raises(ValueError, match="Duplicate character id"):
        generate_cast([_record(), _record()])
    with pytest.raises(ValueError, match="must be a mapping"):
        generate_cast(["tessa"])  # type: ignore[list-item]


def test_generate_cast_rejects_empty_roster() -> None:
    with pytest.raises(ValueError, match="at least one character"):
        generate_cast([])


def test_child_pair_requires_tessa_and_ciro(project_root) -> None:
    from storybook import load_storybook

    spec = load_storybook(project_root)
    tetra, cube = child_pair(spec.characters)
    assert tetra.shape == "tetrahedron"
    assert cube.shape == "cube"

    with pytest.raises(ValueError, match="must include tessa and ciro"):
        child_pair((generate_character(_record(character_id="solo")),))


def test_character_by_id_resolves_hits_and_misses(project_root) -> None:
    from storybook import load_storybook

    spec = load_storybook(project_root)
    assert character_by_id(spec.characters, "ciro") is not None
    assert character_by_id(spec.characters, "nobody") is None
