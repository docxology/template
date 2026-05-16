"""Tests for the per-project schema-extension registry.

Covers ``register_project_schema_extension`` /
``get_project_schema_extensions`` / ``clear_project_schema_extensions``
in ``infrastructure.core.config.schema`` and the ``project_name``
parameter on ``validate_config_keys`` / ``load_config`` in
``infrastructure.core.config.loader``.

Real-data only: no mocks. Uses real YAML files in ``tmp_path`` and
captures log output via the ``caplog`` fixture.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
import yaml

from infrastructure.core.config.loader import load_config, validate_config_keys
from infrastructure.core.config.schema import (
    clear_project_schema_extensions,
    generate_manuscript_config_schema,
    get_project_schema_extensions,
    register_project_schema_extension,
)

LOADER_LOGGER = "infrastructure.core.config.loader"


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Keep registry state from leaking across tests."""
    clear_project_schema_extensions()
    try:
        yield
    finally:
        clear_project_schema_extensions()


def _write_config(path: str, data: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


def test_register_and_get_roundtrip() -> None:
    """Registered extensions are returned by the getter."""
    register_project_schema_extension("alpha", {"custom_block": dict, "knobs": list})

    extensions = get_project_schema_extensions("alpha")

    assert extensions == {"custom_block": dict, "knobs": list}


def test_register_merges_repeated_calls() -> None:
    """Repeated registration for the same project merges keys."""
    register_project_schema_extension("alpha", {"first": dict})
    register_project_schema_extension("alpha", {"second": list})

    extensions = get_project_schema_extensions("alpha")

    assert set(extensions) == {"first", "second"}


def test_get_unknown_project_returns_empty_mapping() -> None:
    """Querying a project that never registered returns an empty mapping."""
    assert get_project_schema_extensions("never_registered") == {}


def test_clear_empties_registry() -> None:
    """``clear_project_schema_extensions`` resets the registry."""
    register_project_schema_extension("alpha", {"k": dict})

    clear_project_schema_extensions()

    assert get_project_schema_extensions("alpha") == {}


def test_validate_config_keys_suppresses_warning_for_registered_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Registered project extensions exempt the key from warnings."""
    register_project_schema_extension("alpha", {"alpha_block": dict})
    config = {"paper": {"title": "T"}, "alpha_block": {"k": "v"}}

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        warnings = validate_config_keys(config, "test.yaml", project_name="alpha")

    assert warnings == []
    assert not any("alpha_block" in rec.getMessage() for rec in caplog.records)


def test_validate_config_keys_warns_after_clear(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """After ``clear_project_schema_extensions``, the warning fires again."""
    register_project_schema_extension("alpha", {"alpha_block": dict})
    config = {"paper": {"title": "T"}, "alpha_block": {"k": "v"}}

    # Sanity check: registered extension suppresses the warning.
    assert validate_config_keys(config, "test.yaml", project_name="alpha") == []

    clear_project_schema_extensions()
    caplog.clear()

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        warnings = validate_config_keys(config, "test.yaml", project_name="alpha")

    assert any("alpha_block" in w for w in warnings)
    assert any("alpha_block" in rec.getMessage() for rec in caplog.records)


def test_validate_config_keys_does_not_share_extensions_across_projects(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An extension registered for project A does not leak to project B."""
    register_project_schema_extension("alpha", {"alpha_block": dict})
    config = {"paper": {"title": "T"}, "alpha_block": {"k": "v"}}

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        warnings = validate_config_keys(config, "test.yaml", project_name="beta")

    assert any("alpha_block" in w for w in warnings)


def test_validate_config_keys_default_project_name_skips_extensions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When no project_name is supplied, per-project extensions don't apply."""
    register_project_schema_extension("alpha", {"alpha_block": dict})
    config = {"paper": {"title": "T"}, "alpha_block": {"k": "v"}}

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        warnings = validate_config_keys(config, "test.yaml")

    assert any("alpha_block" in w for w in warnings)


def test_validate_config_keys_global_extension_applies_to_all_projects(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An extension registered with empty project name suppresses warnings everywhere."""
    register_project_schema_extension("", {"shared_block": dict})
    config = {"paper": {"title": "T"}, "shared_block": {"k": "v"}}

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        warnings_a = validate_config_keys(config, "test.yaml", project_name="alpha")
        warnings_b = validate_config_keys(config, "test.yaml", project_name="beta")

    assert warnings_a == []
    assert warnings_b == []


def test_load_config_infers_project_name_from_path(tmp_path: object, caplog: pytest.LogCaptureFixture) -> None:
    """``load_config`` infers the project name from a projects/<name>/manuscript layout."""
    # Mypy needs help understanding tmp_path is a pathlib.Path.
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    project_dir = tmp_path / "projects" / "alpha" / "manuscript"
    project_dir.mkdir(parents=True)
    config_path = project_dir / "config.yaml"
    _write_config(str(config_path), {"paper": {"title": "T"}, "alpha_block": {"k": "v"}})

    register_project_schema_extension("alpha", {"alpha_block": dict})

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        loaded = load_config(config_path)

    assert loaded is not None
    assert loaded["paper"]["title"] == "T"
    assert not any("alpha_block" in rec.getMessage() for rec in caplog.records)


def test_load_config_explicit_project_name_overrides_inference(
    tmp_path: object, caplog: pytest.LogCaptureFixture
) -> None:
    """An explicit ``project_name=`` argument is honored."""
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    config_path = tmp_path / "config.yaml"
    _write_config(str(config_path), {"paper": {"title": "T"}, "alpha_block": {"k": "v"}})

    register_project_schema_extension("alpha", {"alpha_block": dict})

    with caplog.at_level(logging.WARNING, logger=LOADER_LOGGER):
        loaded = load_config(config_path, project_name="alpha")

    assert loaded is not None
    assert not any("alpha_block" in rec.getMessage() for rec in caplog.records)


def test_register_rejects_non_string_project_name() -> None:
    """``register_project_schema_extension`` raises TypeError for non-str names."""
    with pytest.raises(TypeError):
        register_project_schema_extension(123, {"k": dict})  # type: ignore[arg-type]


def test_validate_config_keys_strict_raises_for_unknown_key() -> None:
    """Strict validation turns unknown top-level keys into a hard failure."""
    with pytest.raises(ValueError, match="papr"):
        validate_config_keys({"papr": {"title": "T"}}, "test.yaml", strict=True)


def test_load_config_strict_raises_for_unknown_key(tmp_path: object) -> None:
    """``load_config(strict=True)`` surfaces schema drift for tooling."""
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    config_path = tmp_path / "config.yaml"
    _write_config(str(config_path), {"unknown_block": {"k": "v"}})

    with pytest.raises(ValueError, match="unknown_block"):
        load_config(config_path, strict=True)


def test_generate_manuscript_config_schema_includes_registered_extension() -> None:
    """JSON Schema export includes registered project keys."""
    register_project_schema_extension("alpha", {"alpha_block": dict})

    schema = generate_manuscript_config_schema("alpha")

    assert schema["additionalProperties"] is False
    assert "paper" in schema["properties"]
    assert "alpha_block" in schema["properties"]
