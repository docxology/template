"""Real path/immutable-byte parity at the owned phase runner boundary."""

from pathlib import Path

import pytest
import yaml

from config_loader import _load_yaml, load_project_config
from multi_phase.search import MultiPhaseSearchRunner


@pytest.mark.parametrize("raw", [b"", b"[]", b"project_config: {}\n", b"project_config: [\n"])
def test_actual_local_parser_value_and_error_parity(tmp_path: Path, raw: bytes):
    path = tmp_path / "config.yaml"
    path.write_bytes(raw)
    if raw.endswith(b"[\n"):
        with pytest.raises(yaml.YAMLError) as expected:
            _load_yaml(path)
        with pytest.raises(yaml.YAMLError) as actual:
            _load_yaml(path, source_bytes=raw)
        assert str(actual.value) == str(expected.value)
    else:
        assert _load_yaml(path) == _load_yaml(path, source_bytes=raw)
        assert load_project_config(path) == load_project_config(path, source_bytes=raw)


@pytest.mark.parametrize("restore", [False, True], ids=["lasting", "aba"])
def test_real_phase_runner_consumes_admitted_config_under_path_replacement(tmp_path: Path, restore):
    path = Path(__file__).resolve().parents[1] / "manuscript/config.yaml"
    admitted = path.read_bytes()
    owned = tmp_path / "config.yaml"
    owned.write_bytes(admitted)
    expected = MultiPhaseSearchRunner(owned, project_root=tmp_path, output_dir=tmp_path / "expected")
    expected_validation = expected.validate_phase_configuration()
    owned.write_text("project_config: {search_phases: {injected: {queries: [changed]}}}\n")
    actual = MultiPhaseSearchRunner(
        owned, project_root=tmp_path, output_dir=tmp_path / "actual", config_source_bytes=admitted
    )
    assert actual.config == expected.config
    assert actual.search_phases == expected.search_phases
    assert actual.llm_filters == expected.llm_filters
    assert actual.validate_phase_configuration() == expected_validation
    if restore:
        owned.write_bytes(admitted)
    assert actual.config != {"project_config": {"search_phases": {"injected": {"queries": ["changed"]}}}}
