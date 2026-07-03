from __future__ import annotations

import pytest
import yaml

from storybook import child_pair, generate_character, load_storybook


def test_load_storybook_story_contract(project_root) -> None:
    spec = load_storybook(project_root)
    assert spec.title == "The Shape Between"
    assert spec.page_count == 9
    assert spec.pages[0].slug == "cover"
    assert spec.pages[-1].slug == "shared_home"
    assert all(page.text for page in spec.pages)


def test_child_pair_uses_opposite_family_shapes(project_root) -> None:
    spec = load_storybook(project_root)
    tetra_child, cube_child = child_pair(spec.characters)
    assert tetra_child.shape == "tetrahedron"
    assert tetra_child.family_shape == "cube"
    assert cube_child.shape == "cube"
    assert cube_child.family_shape == "tetrahedron"


def test_unknown_page_slug_fails(project_root) -> None:
    spec = load_storybook(project_root)
    with pytest.raises(KeyError):
        spec.page_by_slug("missing")


def test_invalid_character_shape_fails() -> None:
    record = {
        "id": "round_one",
        "name": "Round One",
        "shape": "sphere",
        "family_shape": "cube",
        "fill": "#ffffff",
        "accent": "#000000",
        "role": "invalid shape",
    }
    with pytest.raises(ValueError):
        generate_character(record)


def test_invalid_palette_fails(isolated_project) -> None:
    story_path = isolated_project / "content" / "story.yaml"
    payload = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    payload["pages"][0]["palette"] = ["#ffffff"]
    story_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_storybook(isolated_project)
