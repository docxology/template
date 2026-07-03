from __future__ import annotations

import pytest
import yaml

from storybook import child_pair, generate_character, load_storybook


def test_load_storybook_story_contract(project_root) -> None:
    spec = load_storybook(project_root)
    assert spec.title == "The Shape Between"
    assert spec.subtitle == "A geometric fable of belonging, bracing, and reciprocal form"
    assert spec.page_count == 14
    assert spec.pages[0].slug == "cover"
    assert spec.pages[1].slug == "publication_information"
    assert spec.page_by_number(6).slug == "tetra_inside_cube"
    assert spec.page_by_number(9).slug == "shadow_school"
    assert spec.page_by_number(10).slug == "tensegrity_lantern"
    assert spec.page_by_number(11).slug == "vector_garden"
    assert spec.page_by_number(12).slug == "mega_symbol"
    assert spec.pages[-1].slug == "shared_home"
    assert all(page.text for page in spec.pages)
    assert "A geometric fable of belonging" in spec.pages[0].text
    assert "Daniel Ari Friedman" in spec.pages[0].text
    assert "DOI 10.5281/zenodo.21176000" in spec.pages[0].text
    assert "Daniel Ari Friedman" in spec.pages[1].text
    assert "DOI: 10.5281/zenodo.21176000" in spec.pages[1].text
    assert "Synergetics" in spec.pages[1].text
    assert "tetrahedron inside the cube" in spec.page_by_number(6).text
    assert "struts that pushed and threads that pulled" in spec.page_by_number(10).text


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
