"""Per-exemplar configuration and SDK-binding contract controls."""

from __future__ import annotations

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
