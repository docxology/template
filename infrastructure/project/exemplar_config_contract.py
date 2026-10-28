"""Per-exemplar configuration and SDK-binding contract.

Every canonical exemplar must be runnable and forkable from its own directory:
its `manuscript/config.yaml` must load without unknown keys, it must pin the
platform SDK it builds against, declare its own extra config blocks, and keep
its generated publication copy consistent with the source. `public_capabilities`
already covers package identity and the tested-runtime range; this module covers
the configuration surface it does not read.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

from infrastructure.core.config.loader import validate_config_keys
from infrastructure.core.project_pyproject import load_project_pyproject
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

SDK_PACKAGE = "research-project-template"


def root_package_version(repo_root: Path) -> str:
    """Return the root package version declared by ``pyproject.toml``."""
    payload = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    version = payload.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("root pyproject.toml must declare project.version")
    return version.strip()


@dataclass(frozen=True)
class ExemplarConfigFinding:
    """One contract violation for a canonical exemplar."""

    project: str
    rule: str
    detail: str


@dataclass(frozen=True)
class ExemplarConfigReport:
    """Aggregate result for the canonical public roster."""

    projects: int
    findings: tuple[ExemplarConfigFinding, ...]

    @property
    def passed(self) -> bool:
        """Return whether every exemplar satisfies the configuration contract."""
        return not self.findings


def _declared_requirements(payload: dict) -> set[str]:
    """Collect every requirement string a project declares, in any group.

    The SDK pin legitimately lives in ``[project].dependencies``, an optional
    ``[project.optional-dependencies]`` extra, or a PEP 735
    ``[dependency-groups]`` entry depending on the exemplar's runtime shape.
    """
    project = payload.get("project") or {}
    requirements = set(project.get("dependencies") or [])
    for group in (project.get("optional-dependencies") or {}).values():
        requirements.update(group or [])
    for group in (payload.get("dependency-groups") or {}).values():
        requirements.update(item for item in (group or []) if isinstance(item, str))
    return requirements


def _sdk_binding(root: Path, project_root: Path, version: str) -> tuple[list[str], str | None]:
    """Return contract violations for the SDK pin and its declared source."""
    findings: list[str] = []
    pyproject = project_root / "pyproject.toml"
    try:
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [f"unreadable pyproject.toml: {error}"], None
    pin = f"{SDK_PACKAGE}=={version}"
    if pin not in _declared_requirements(payload):
        findings.append(f"a declared requirement group must pin {pin!r}")
    sources = payload.get("tool", {}).get("uv", {}).get("sources") or {}
    if SDK_PACKAGE not in sources:
        findings.append(f"[tool.uv.sources] must declare {SDK_PACKAGE!r}")
    template = payload.get("tool", {}).get("template") or {}
    declared = template.get("platform_version")
    return findings, declared if isinstance(declared, str) else None


def _manuscript_findings(project_name: str, project_root: Path) -> list[str]:
    """Validate the source config and its generated publication copy."""
    findings: list[str] = []
    source = project_root / "manuscript" / "config.yaml"
    if not source.is_file():
        return ["manuscript/config.yaml is missing"]
    try:
        config = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return [f"manuscript/config.yaml is not valid YAML: {error}"]
    if not isinstance(config, dict):
        return ["manuscript/config.yaml must be a mapping"]
    for warning in validate_config_keys(config, source, project_name=project_name):
        findings.append(warning)
    generated = project_root / "output" / "manuscript" / "config.yaml"
    if generated.is_file():
        try:
            published = yaml.safe_load(generated.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            return [*findings, f"output/manuscript/config.yaml is not valid YAML: {error}"]
        if isinstance(published, dict):
            source_version = (config.get("publication") or {}).get("platform_version")
            published_version = (published.get("publication") or {}).get("platform_version")
            if source_version != published_version:
                findings.append(
                    "output/manuscript/config.yaml publication.platform_version "
                    f"{published_version!r} differs from source {source_version!r}; "
                    "regenerate the publication copy"
                )
    return findings


def validate_exemplar_configs(repo_root: Path, *, projects: tuple[str, ...] | None = None) -> ExemplarConfigReport:
    """Check every canonical exemplar's configuration and SDK binding.

    ``projects`` defaults to the canonical public roster; tests inject a smaller
    roster so the negative controls do not need a full checkout.
    """
    root = Path(repo_root).resolve()
    roster = PUBLIC_PROJECT_NAMES if projects is None else projects
    version = root_package_version(root)
    findings: list[ExemplarConfigFinding] = []
    for name in roster:
        project_root = root / "projects" / name
        project_name = Path(name).name
        declared = load_project_pyproject(project_root)
        if declared is None:
            findings.append(ExemplarConfigFinding(name, "pyproject", "pyproject.toml is missing or invalid"))
            continue
        if declared.declared_config_keys_error:
            findings.append(ExemplarConfigFinding(name, "config_keys", declared.declared_config_keys_error))
        binding_findings, declared_version = _sdk_binding(root, project_root, version)
        for detail in binding_findings:
            findings.append(ExemplarConfigFinding(name, "sdk-binding", detail))
        if declared_version is not None and declared_version != version:
            findings.append(
                ExemplarConfigFinding(
                    name,
                    "platform-version",
                    f"[tool.template].platform_version {declared_version!r} differs from {version!r}",
                )
            )
        for detail in _manuscript_findings(project_name, project_root):
            findings.append(ExemplarConfigFinding(name, "manuscript-config", detail))
    return ExemplarConfigReport(projects=len(roster), findings=tuple(findings))


def format_exemplar_config_report(report: ExemplarConfigReport) -> str:
    """Render the report for a CI log."""
    status = "pass" if report.passed else "fail"
    lines = [f"exemplar configuration: {report.projects} projects", f"status: {status}"]
    lines.extend(f"{item.project}: [{item.rule}] {item.detail}" for item in report.findings)
    return "\n".join(lines)


__all__ = [
    "ExemplarConfigFinding",
    "ExemplarConfigReport",
    "format_exemplar_config_report",
    "validate_exemplar_configs",
]
