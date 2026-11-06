"""Per-exemplar configuration and SDK-binding contract controls."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib

import pytest
from pathlib import Path

from infrastructure.project.exemplar_config_contract import (
    format_exemplar_config_report,
    validate_exemplar_configs,
)

from infrastructure.core.testing.pytest_marker_exprs import repository_marker_expression
from infrastructure.core.testing.pytest_profiles import build_profile_marker_expression, resolve_test_profile
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]
_ROOT_PYTEST_OPTIONS = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"][
    "ini_options"
]
_CANONICAL_MARKERS = tuple(clause.removeprefix("not ") for clause in repository_marker_expression().split(" and "))
_CANONICAL_DECLARATIONS = [
    row
    for row in _ROOT_PYTEST_OPTIONS["markers"]
    if row.split(":", 1)[0].split("(", 1)[0].strip() in _CANONICAL_MARKERS
]


def test_every_canonical_exemplar_satisfies_the_configuration_contract() -> None:
    report = validate_exemplar_configs(REPO_ROOT)
    assert report.projects == 25
    assert report.passed, format_exemplar_config_report(report)


def _scaffold(
    root: Path, *, pin: str, platform: str, config_block: str, published: str, output_published: str | None = None
) -> None:
    project = root / "projects" / "templates" / "template_probe"
    (project / "manuscript").mkdir(parents=True)
    (project / "output" / "manuscript").mkdir(parents=True)
    root.joinpath("pyproject.toml").write_text('[project]\nname = "research-project-template"\nversion = "9.9.9"\n')
    (project / "pyproject.toml").write_text(
        "[project]\n"
        'name = "template-probe"\n'
        'version = "0.1.0"\n'
        "dependencies = " + repr([pin]).replace("'", '"') + "\n\n"
        "[tool.uv.sources]\n"
        'research-project-template = { path = "../../..", editable = true }\n\n'
        "[tool.template]\n"
        f'platform_version = "{platform}"\n'
        "\n[tool.pytest.ini_options]\n"
        f"markers = {json.dumps(_CANONICAL_DECLARATIONS)}\n"
    )
    (project / "manuscript" / "config.yaml").write_text(
        f'paper:\n  title: probe\npublication:\n  platform_version: "{published}"\n{config_block}',
        encoding="utf-8",
    )
    (project / "output" / "manuscript" / "config.yaml").write_text(
        f"paper:\n  title: probe\npublication:\n  platform_version: "
        f'"{published if output_published is None else output_published}"\n',
        encoding="utf-8",
    )


def test_missing_pin_and_stale_publication_copy_are_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==1.0.0",
        platform="1.0.0",
        config_block="",
        published="1.0.0",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    rules = {item.rule for item in report.findings}
    assert "sdk-binding" in rules and "platform-version" in rules
    assert not report.passed


def test_stale_published_platform_version_is_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="",
        published="9.9.9",
        output_published="1.0.0",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    details = " ".join(item.detail for item in report.findings)
    assert "output/manuscript/config.yaml" in details
    assert "platform_version" in details


def test_unknown_config_block_is_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="undeclared_block:\n  value: 1\n",
        published="9.9.9",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    assert any("undeclared_block" in item.detail for item in report.findings)


def test_source_platform_version_must_equal_the_root_version(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="",
        published="1.0.0",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    details = " ".join(item.detail for item in report.findings)
    assert "differs from root '9.9.9'" in details


def test_stale_uv_lock_sdk_version_is_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="",
        published="9.9.9",
    )
    project = tmp_path / "projects" / "templates" / "template_probe"
    (project / "uv.lock").write_text(
        'version = 1\n\n[[package]]\nname = "research-project-template"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    details = " ".join(item.detail for item in report.findings)
    assert "uv.lock research-project-template version ['1.0.0']" in details


def test_stale_artifact_manifest_sha256_is_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="",
        published="9.9.9",
    )
    project = tmp_path / "projects" / "templates" / "template_probe"
    reports = project / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "artifact_manifest.json").write_text(
        json.dumps({"entries": [{"path": "output/manuscript/config.yaml", "sha256": "0" * 64}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    details = " ".join(item.detail for item in report.findings)
    assert "stale sha256" in details


def test_matching_artifact_manifest_is_not_reported(tmp_path: Path) -> None:
    _scaffold(
        tmp_path,
        pin="research-project-template==9.9.9",
        platform="9.9.9",
        config_block="",
        published="9.9.9",
    )
    project = tmp_path / "projects" / "templates" / "template_probe"
    generated = project / "output" / "manuscript" / "config.yaml"
    digest = hashlib.sha256(generated.read_bytes()).hexdigest()
    reports = project / "output" / "reports"
    reports.mkdir(parents=True)
    (reports / "artifact_manifest.json").write_text(
        json.dumps({"entries": [{"path": "output/manuscript/config.yaml", "sha256": digest}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    details = " ".join(item.detail for item in report.findings)
    assert "artifact_manifest.json" not in details


@pytest.mark.parametrize("missing", _CANONICAL_MARKERS)
def test_missing_canonical_profile_marker_is_reported(tmp_path: Path, missing: str) -> None:
    _scaffold(tmp_path, pin="research-project-template==9.9.9", platform="9.9.9", config_block="", published="9.9.9")
    project = tmp_path / "projects/templates/template_probe"
    config = project / "pyproject.toml"
    declarations = [row for row in _CANONICAL_DECLARATIONS if row.split(":", 1)[0].strip() != missing]
    config.write_text(config.read_text().replace(json.dumps(_CANONICAL_DECLARATIONS), json.dumps(declarations)))
    report = validate_exemplar_configs(tmp_path, projects=("templates/template_probe",))
    findings = [item for item in report.findings if item.rule == "pytest-markers"]
    assert len(findings) == 1 and findings[0].detail.endswith(missing)


def _strict_selection(tmp_path: Path, declarations: list[str], expression: str, *, foreign: bool = False):
    config = tmp_path / "pyproject.toml"
    config.write_text(
        "[tool.pytest.ini_options]\nstrict_markers = true\n" + "markers = " + json.dumps(declarations) + "\n"
    )
    cases = tmp_path / "test_selection.py"
    cases.write_text(
        "import pytest\n\ndef test_baseline():\n    assert True\n"
        + "".join(f"\n@pytest.mark.{marker}\ndef test_{marker}():\n    assert True\n" for marker in _CANONICAL_MARKERS)
        + ("\n@pytest.mark.foreign_marker_control\ndef test_foreign():\n    assert True\n" if foreign else "")
    )
    environment = os.environ.copy()
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        environment.pop(key, None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(config),
            "--confcutdir",
            str(tmp_path),
            "--strict-markers",
            "-p",
            "no:cacheprovider",
            "-q",
            "-m",
            expression,
            str(cases),
        ],
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("project", PUBLIC_PROJECT_NAMES)
@pytest.mark.parametrize(
    "profile, expected", [("quick", "1 passed, 10 deselected"), ("release", "2 passed, 9 deselected")]
)
def test_actual_project_marker_declarations_preserve_strict_profile_selection(
    tmp_path: Path, project: str, profile: str, expected: str
) -> None:
    metadata = tomllib.loads((REPO_ROOT / "projects" / project / "pyproject.toml").read_text(encoding="utf-8"))
    declarations = metadata["tool"]["pytest"]["ini_options"]["markers"]
    expression = build_profile_marker_expression(resolve_test_profile(profile))
    assert expression is not None
    selected = _strict_selection(tmp_path, declarations, expression)
    assert selected.returncode == 0, selected.stdout + selected.stderr
    assert expected in selected.stdout
    rejected = _strict_selection(tmp_path, declarations, expression, foreign=True)
    assert rejected.returncode == 2, rejected.stdout + rejected.stderr
    assert "foreign_marker_control" in rejected.stdout + rejected.stderr
