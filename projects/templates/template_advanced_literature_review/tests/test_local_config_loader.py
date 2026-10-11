"""Real local YAML and output-directory boundaries for the standalone producer."""

from pathlib import Path

import pytest
import yaml

from config_loader import (
    _load_yaml,
    load_fulltext_config,
    load_project_config,
    load_search_config,
    resolve_fulltext_directory,
)


def test_real_current_project_configuration_loads_without_sibling_alias():
    path = Path(__file__).resolve().parents[1] / "manuscript/config.yaml"
    raw = _load_yaml(path)
    assert load_project_config(path) == raw["project_config"]
    search = load_search_config(path)
    assert search["query"] == raw["project_config"]["search"]["query"]
    assert search["engines"] == raw["project_config"]["search"]["engines"]
    assert load_fulltext_config(path)["download_dir"] == raw["project_config"]["fulltext"]["download_dir"]
    # The loader is project-owned even when the declared literature engine has
    # already been imported by another test in this process.
    assert _load_yaml.__module__ == "config_loader"
    assert Path(__import__("config_loader").__file__).parent == path.parents[1] / "src"


@pytest.mark.parametrize("raw", ["", "[]", "null", "17"])
def test_missing_or_nonmapping_configuration_has_no_invented_topic(tmp_path, raw):
    path = tmp_path / "config.yaml"
    assert _load_yaml(path) == {}
    path.write_text(raw)
    assert _load_yaml(path) == {}
    assert load_search_config(path)["query"] is None


def test_yaml_parser_errors_are_not_silently_converted_to_defaults(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("project_config: [")
    with pytest.raises(yaml.YAMLError):
        load_search_config(path)


def test_search_and_fulltext_use_real_selected_yaml_values(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "project_config": {
                    "search": {
                        "query": "public domain",
                        "max_results": 5,
                        "resume": False,
                        "engines": {"crossref": True},
                        "arxiv_queries": ["public domain"],
                    },
                    "fulltext": {"enabled": True, "download_dir": "owned/fulltext"},
                }
            }
        )
    )
    search = load_search_config(path)
    assert search["query"] == "public domain" and search["max_results"] == 5
    assert search["arxiv_queries"] == ["public domain"]
    directory, explicit = resolve_fulltext_directory(project_root=tmp_path, fulltext_config=load_fulltext_config(path))
    assert directory == tmp_path.resolve() / "owned/fulltext" and explicit is False
    override, explicit = resolve_fulltext_directory(
        project_root=tmp_path, fulltext_config=load_fulltext_config(path), override="override"
    )
    assert override == tmp_path.resolve() / "override" and explicit is True
