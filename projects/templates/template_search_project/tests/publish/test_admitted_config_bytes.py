"""The typed domain loader consumes exact admitted bytes under real file edits."""

from pathlib import Path

import pytest
import yaml

from template_search_project.publish.config import load_project_config


@pytest.mark.parametrize(
    "raw",
    [
        b"paper: {title: Public}\nproject_config: {search: {query: topic, max_results: 3}}\n",
        b"[]\n",
        b"project_config: [\n",
    ],
)
def test_actual_domain_loader_value_and_error_parity(tmp_path: Path, raw: bytes):
    path = tmp_path / "config.yaml"
    path.write_bytes(raw)
    if raw == b"[]\n" or raw.endswith(b"[\n"):
        with pytest.raises((ValueError, yaml.YAMLError)) as expected:
            load_project_config(path)
        with pytest.raises((ValueError, yaml.YAMLError)) as actual:
            load_project_config(path, source_bytes=raw)
        assert type(actual.value) is type(expected.value)
        assert str(actual.value) == str(expected.value)
    else:
        assert load_project_config(path) == load_project_config(path, source_bytes=raw)


@pytest.mark.parametrize("restore", [False, True], ids=["lasting", "aba"])
def test_admitted_search_query_survives_real_config_path_replacement(tmp_path: Path, restore):
    path = tmp_path / "config.yaml"
    raw = b"project_config: {search: {query: admitted, max_results: 3}}\n"
    path.write_bytes(raw)
    expected = load_project_config(path)
    path.write_bytes(b"project_config: {search: {query: injected, max_results: 1}}\n")
    actual = load_project_config(path, source_bytes=raw)
    assert actual == expected and actual.search.query == "admitted"
    if restore:
        path.write_bytes(raw)
