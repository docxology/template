"""Per-exemplar configuration and SDK-binding contract controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from infrastructure.project.exemplar_config_contract import (
    format_exemplar_config_report,
    validate_exemplar_configs,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


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
