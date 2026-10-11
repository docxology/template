"""Actual parser/error parity and immutable source bytes under real config replacement."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from infrastructure.search.literature.configuration_sources import ConfigTextStream
from infrastructure.search.literature.configuration_validation import validate_full_config
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap


@pytest.mark.parametrize(
    "raw",
    [
        b"project_config: {search: {query: topic, max_results: 3}}\n",
        b"project_config: []\n",
        b"[]\n",
        b"",
        b"project_config: [\n",
        b"project_config:\r\n  search: {query: topic, max_results: 3}\r\n",
    ],
)
def test_path_and_admitted_bytes_have_identical_validation_values_and_errors(tmp_path: Path, raw: bytes):
    path = tmp_path / "config.yaml"
    path.write_bytes(raw)
    assert validate_full_config(path, categories=("search_config",)) == validate_full_config(
        path, categories=("search_config",), source_bytes=raw
    )


def test_admitted_yaml_stream_preserves_utf8_newlines_source_name_and_errors(tmp_path: Path):
    path = tmp_path / "config.yaml"
    raw = "name: café\r\nempty: null\r".encode()
    path.write_bytes(raw)
    with path.open(encoding="utf-8") as disk, ConfigTextStream(path, raw) as memory:
        assert memory.name == disk.name
        assert memory.read() == disk.read()
    bad = b"items: [\n"
    path.write_bytes(bad)
    with path.open(encoding="utf-8") as disk:
        with pytest.raises(yaml.YAMLError) as expected:
            yaml.safe_load(disk)
    with ConfigTextStream(path, bad) as memory:
        with pytest.raises(yaml.YAMLError) as actual:
            yaml.safe_load(memory)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize("invalid", [bytearray(b"a: 1"), "a: 1", None, [1]])
def test_config_source_refuses_mutable_or_nonbyte_inputs(tmp_path, invalid):
    with pytest.raises(TypeError, match="immutable bytes"):
        ConfigTextStream(tmp_path / "config.yaml", invalid)


@pytest.mark.timeout(120)
def test_actual_fresh_controller_preserves_its_explicit_bytecode_binding(tmp_path: Path):
    import infrastructure

    root = Path(infrastructure.__file__).absolute().parent.parent
    prefix = tmp_path.resolve() / "fresh-cache"
    prefix.mkdir()
    code = bytecode_audit_bootstrap((root / "infrastructure", root / "scripts"), prefix)
    code += (
        "sys.path.insert(0,sys.argv[1]);"
        "from infrastructure.search.literature.live_contract import "
        "implementation_custody,platform_manifest,environment_identity,verify_platform;"
        "custody=implementation_custody();assert custody['bytecode_binding']=='fresh-owned-prefix';"
        "verify_platform(platform_manifest(),environment_identity(),custody);"
        "print('fresh-controller-verified')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", code, str(root)],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "fresh-controller-verified"
