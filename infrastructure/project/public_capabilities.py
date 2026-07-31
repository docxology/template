"""Deterministic static capability manifest for canonical public exemplars.

This gate describes what every public project declares and what repository
structure statically proves. It deliberately does not execute project tests,
analysis, hydration, or rendering; runtime evidence belongs to the public
matrix and rendered-provenance receipts.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml

try:
    import tomllib
except ImportError:  # Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]

from infrastructure.core.script_discovery import discover_analysis_scripts
from infrastructure.project.export_smoke import discover_import_targets
from infrastructure.project.public_capability_contracts import (
    PACKAGE_NAME_OVERRIDES,
    SkipContract,
    discover_skip_contracts,
    package_identity_contract,
    python_minor_series_compatibility,
    validate_python_entrypoint,
    validate_python_files,
    validate_unique_package_names,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files

REQUIRED_DIRECTORIES = ("src", "tests", "manuscript", "scripts", ".agents/skills")
REQUIRED_FILES = ("README.md", "AGENTS.md", "pyproject.toml")
CAPABILITY_MANIFEST_SCHEMA_VERSION = "template-public-capabilities-v1"
CANONICAL_CI_PYTHON_VERSIONS = ("3.10", "3.12")
RENDER_FORMAT_NAMES = ("pdf", "html", "slides", "docx", "epub")

_HYDRATION_TOKEN_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}|\$\{[A-Za-z_][A-Za-z0-9_]*\}")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class CapabilityProbe:
    """One deterministic declaration-versus-observation check."""

    id: str
    status: str
    evidence: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the probe passed."""
        return self.status == "pass"


@dataclass(frozen=True)
class PackageCapability:
    """Static Python package metadata and import surface."""

    name: str
    normalized_name: str
    expected_name: str
    requires_python: str
    import_targets: tuple[str, ...]


@dataclass(frozen=True)
class RenderFormatCapability:
    """Resolved render-format switches and their explicit YAML declarations."""

    declared: tuple[str, ...]
    pdf: bool
    html: bool
    slides: bool
    docx: bool
    epub: bool


@dataclass(frozen=True)
class HydrationCapability:
    """Static manuscript-token and hydration-entrypoint contract."""

    mode: str
    declared: bool
    required: bool
    entrypoint: str | None
    entrypoint_sha256: str | None
    smoke: str
    token_count: int
    source_files: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisCapability:
    """Canonical Stage 2 analysis discovery result."""

    configured: bool
    entrypoints: tuple[str, ...]


@dataclass(frozen=True)
class CIMatrixEntry:
    """One canonical public-project CI lane."""

    project: str
    python_version: str

    def to_dict(self) -> dict[str, str]:
        """Serialize with the key expected by GitHub Actions."""
        return {
            "project": self.project,
            "python-version": self.python_version,
        }


@dataclass(frozen=True)
class PublicCapability:
    """Static structural, packaging, rendering, and lifecycle facts."""

    project: str
    package: PackageCapability
    render_formats: RenderFormatCapability
    hydration: HydrationCapability
    analysis: AnalysisCapability
    ci_python_versions: tuple[str, ...]
    required_directories: tuple[str, ...]
    required_files: tuple[str, ...]
    source_file_count: int
    test_file_count: int
    script_file_count: int
    missing_paths: tuple[str, ...]
    skip_contracts: tuple[SkipContract, ...]
    probes: tuple[CapabilityProbe, ...]
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the exemplar has a complete static contract."""
        return (
            not self.missing_paths
            and not self.issues
            and self.test_file_count > 0
            and bool(self.probes)
            and all(probe.passed for probe in self.probes)
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the inventory for CI and readiness reports."""
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


@dataclass(frozen=True)
class PublicCapabilityReport:
    """Versioned aggregate public-exemplar capability manifest."""

    schema_version: str
    roster_digest: str
    ci_python_versions: tuple[str, ...]
    ci_matrix: tuple[CIMatrixEntry, ...]
    projects: tuple[PublicCapability, ...]
    issues: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether every canonical public exemplar passes."""
        return bool(self.projects) and not self.issues and all(project.passed for project in self.projects)

    def to_dict(self) -> dict[str, object]:
        """Serialize the complete report."""
        return {
            "schema_version": self.schema_version,
            "roster_digest": self.roster_digest,
            "ci_python_versions": self.ci_python_versions,
            "ci_matrix": {"include": [entry.to_dict() for entry in self.ci_matrix]},
            "project_count": len(self.projects),
            "passed": self.passed,
            "projects": [project.to_dict() for project in self.projects],
            "issues": self.issues,
        }


def audit_public_capability(repo_root: Path | str, project: str) -> PublicCapability:
    """Audit one qualified public project using only repository-local facts."""
    root = Path(repo_root).resolve()
    project_root = root / "projects" / project
    missing_paths = tuple(
        path for path in (*REQUIRED_DIRECTORIES, *REQUIRED_FILES) if not (project_root / path).exists()
    )
    source_files = tuple(_python_files(project_root / "src"))
    test_python_files = tuple(_python_files(project_root / "tests"))
    test_files = tuple(_python_files(project_root / "tests", include_private=False))
    script_files = tuple(_python_files(project_root / "scripts", include_private=False))
    skip_contracts = tuple(discover_skip_contracts(project_root / "tests", root))
    structure_issues: list[str] = []
    if project_root.is_symlink():
        structure_issues.append("public exemplar path must not be a symlink")
    if not source_files:
        structure_issues.append("src/ has no Python source files")
    if not test_files:
        structure_issues.append("tests/ has no test modules")
    structure_issues.extend(f"missing required path: {path}" for path in missing_paths)

    source_syntax_issues, source_syntax_evidence = validate_python_files(
        source_files,
        project_root,
        label="source",
    )
    test_syntax_issues, test_syntax_evidence = validate_python_files(
        test_python_files,
        project_root,
        label="test",
    )
    syntax_issues = [*source_syntax_issues, *test_syntax_issues]
    package, package_issues, package_evidence = _package_capability(project_root, project)
    python_issues, python_evidence = python_minor_series_compatibility(
        package.requires_python,
        CANONICAL_CI_PYTHON_VERSIONS,
    )
    config, config_issues = _load_project_config(project_root)
    render_formats, render_issues, render_evidence = _render_format_capability(config)
    analysis, analysis_issues, analysis_evidence = _analysis_capability(root, project, project_root, config)
    hydration, hydration_issues, hydration_evidence = _hydration_capability(project_root, analysis)
    skip_issues: list[str] = []
    if any(not contract.reason.strip() for contract in skip_contracts):
        skip_issues.append("every discovered skip must have a reason or imported capability name")

    probes = (
        _probe(
            "structure",
            structure_issues,
            (
                f"required-directories={len(REQUIRED_DIRECTORIES)}",
                f"required-files={len(REQUIRED_FILES)}",
                f"source-files={len(source_files)}",
                f"test-files={len(test_files)}",
                f"script-files={len(script_files)}",
            ),
        ),
        _probe(
            "python-syntax",
            syntax_issues,
            (*source_syntax_evidence, *test_syntax_evidence),
        ),
        _probe("package", package_issues, package_evidence),
        _probe("python-compatibility", python_issues, python_evidence),
        _probe(
            "project-config",
            config_issues,
            ("manuscript/config.yaml=parsed" if not config_issues else "manuscript/config.yaml=invalid",),
        ),
        _probe("render-formats", render_issues, render_evidence),
        _probe("hydration", hydration_issues, hydration_evidence),
        _probe("analysis", analysis_issues, analysis_evidence),
        _probe("skip-contracts", skip_issues, (f"declared-skips={len(skip_contracts)}",)),
    )
    issues = _unique_issues(
        structure_issues,
        syntax_issues,
        package_issues,
        python_issues,
        config_issues,
        render_issues,
        hydration_issues,
        analysis_issues,
        skip_issues,
    )
    return PublicCapability(
        project=project,
        package=package,
        render_formats=render_formats,
        hydration=hydration,
        analysis=analysis,
        ci_python_versions=CANONICAL_CI_PYTHON_VERSIONS,
        required_directories=REQUIRED_DIRECTORIES,
        required_files=REQUIRED_FILES,
        source_file_count=len(source_files),
        test_file_count=len(test_files),
        script_file_count=len(script_files),
        missing_paths=missing_paths,
        skip_contracts=skip_contracts,
        probes=probes,
        issues=issues,
    )


def audit_public_capabilities(repo_root: Path | str) -> PublicCapabilityReport:
    """Audit the authoritative roster without executing any project runtime."""
    projects = tuple(audit_public_capability(repo_root, project) for project in PUBLIC_PROJECT_NAMES)
    matrix = build_ci_matrix()
    report_issues = _unique_issues(
        validate_manifest_roster(tuple(project.project for project in projects)),
        validate_ci_matrix(matrix),
        validate_unique_package_names(tuple((project.project, project.package.name) for project in projects)),
    )
    return PublicCapabilityReport(
        schema_version=CAPABILITY_MANIFEST_SCHEMA_VERSION,
        roster_digest=manifest_roster_digest(PUBLIC_PROJECT_NAMES),
        ci_python_versions=CANONICAL_CI_PYTHON_VERSIONS,
        ci_matrix=matrix,
        projects=projects,
        issues=report_issues,
    )


def manifest_roster_digest(projects: Sequence[str]) -> str:
    """Return the stable SHA-256 digest of an ordered project roster."""
    payload = json.dumps(list(projects), ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_ci_matrix(
    projects: Sequence[str] = PUBLIC_PROJECT_NAMES,
    python_versions: Sequence[str] = CANONICAL_CI_PYTHON_VERSIONS,
) -> tuple[CIMatrixEntry, ...]:
    """Build the canonical ordered project/Python Cartesian product."""
    return tuple(
        CIMatrixEntry(project=project, python_version=python_version)
        for project in projects
        for python_version in python_versions
    )


def validate_manifest_roster(projects: Sequence[str]) -> tuple[str, ...]:
    """Validate exact membership and order against ``PUBLIC_PROJECT_NAMES``."""
    actual = tuple(projects)
    expected = tuple(PUBLIC_PROJECT_NAMES)
    issues: list[str] = []
    duplicates = sorted(name for name, count in Counter(actual).items() if count > 1)
    if duplicates:
        issues.append(f"manifest roster contains duplicate projects: {', '.join(duplicates)}")
    missing = sorted(set(expected) - set(actual))
    if missing:
        issues.append(f"manifest roster is missing projects: {', '.join(missing)}")
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        issues.append(f"manifest roster has unexpected projects: {', '.join(unexpected)}")
    if not missing and not unexpected and not duplicates and actual != expected:
        issues.append("manifest roster order differs from PUBLIC_PROJECT_NAMES")
    return tuple(issues)


def validate_ci_matrix(
    matrix: Sequence[CIMatrixEntry],
    projects: Sequence[str] = PUBLIC_PROJECT_NAMES,
    python_versions: Sequence[str] = CANONICAL_CI_PYTHON_VERSIONS,
) -> tuple[str, ...]:
    """Validate exact CI lane membership, uniqueness, and canonical order."""
    actual = tuple(matrix)
    expected = build_ci_matrix(projects, python_versions)
    issues: list[str] = []
    duplicate_versions = sorted(version for version, count in Counter(python_versions).items() if count > 1)
    if duplicate_versions:
        issues.append(f"canonical CI Python versions contain duplicates: {', '.join(duplicate_versions)}")
    duplicates = sorted(
        f"{entry.project}@{entry.python_version}" for entry, count in Counter(actual).items() if count > 1
    )
    if duplicates:
        issues.append(f"CI matrix contains duplicate lanes: {', '.join(duplicates)}")
    missing = [entry for entry in expected if entry not in actual]
    if missing:
        issues.append(
            "CI matrix is missing lanes: " + ", ".join(f"{entry.project}@{entry.python_version}" for entry in missing)
        )
    unexpected = [entry for entry in actual if entry not in expected]
    if unexpected:
        issues.append(
            "CI matrix has unexpected lanes: "
            + ", ".join(f"{entry.project}@{entry.python_version}" for entry in unexpected)
        )
    if not duplicates and not missing and not unexpected and actual != expected:
        issues.append("CI matrix order differs from the canonical project/Python product")
    return tuple(issues)


def _package_capability(
    project_root: Path,
    project: str,
) -> tuple[PackageCapability, list[str], tuple[str, ...]]:
    pyproject_path = project_root / "pyproject.toml"
    issues: list[str] = []
    name = ""
    requires_python = ""
    try:
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except OSError as exc:
        issues.append(f"could not read pyproject.toml: {exc}")
        payload = {}
    except tomllib.TOMLDecodeError as exc:
        issues.append(f"pyproject.toml is malformed: {exc}")
        payload = {}
    project_table = payload.get("project") if isinstance(payload, dict) else None
    if not isinstance(project_table, dict):
        issues.append("pyproject.toml must contain a [project] table")
    else:
        raw_name = project_table.get("name")
        raw_requires = project_table.get("requires-python")
        if isinstance(raw_name, str) and raw_name.strip():
            name = raw_name.strip()
        else:
            issues.append("[project].name must be a non-empty string")
        if isinstance(raw_requires, str) and raw_requires.strip():
            requires_python = raw_requires.strip()
        else:
            issues.append("[project].requires-python must be a non-empty string")

    normalized_name, expected_name, identity_issues, identity_evidence = package_identity_contract(
        project,
        name,
    )
    issues.extend(identity_issues)
    import_targets = discover_import_targets(project_root / "src")
    if not import_targets:
        issues.append("src/ has no importable top-level targets")
    capability = PackageCapability(
        name=name,
        normalized_name=normalized_name,
        expected_name=expected_name,
        requires_python=requires_python,
        import_targets=import_targets,
    )
    evidence = (
        f"name={name or '<missing>'}",
        *identity_evidence,
        f"requires-python={requires_python or '<missing>'}",
        f"import-targets={','.join(import_targets) or '<none>'}",
    )
    return capability, issues, evidence


def _load_project_config(project_root: Path) -> tuple[dict[str, Any], list[str]]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return {}, ["manuscript/config.yaml is missing"]
    try:
        loaded: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return {}, [f"manuscript/config.yaml is malformed: {exc}"]
    if loaded is None:
        return {}, []
    if not isinstance(loaded, dict):
        return {}, ["manuscript/config.yaml must contain a mapping"]
    return loaded, []


def _render_format_capability(
    config: dict[str, Any],
) -> tuple[RenderFormatCapability, list[str], tuple[str, ...]]:
    issues: list[str] = []
    declared: tuple[str, ...] = ()
    render_block = config.get("render")
    if render_block is not None and not isinstance(render_block, dict):
        issues.append("render must be a mapping")
        render_block = {}
    if not isinstance(render_block, dict):
        render_block = {}
    formats_block = render_block.get("formats")
    if formats_block is not None and not isinstance(formats_block, dict):
        issues.append("render.formats must be a mapping")
        formats_block = {}
    if not isinstance(formats_block, dict):
        formats_block = {}
    unknown = sorted(str(key) for key in formats_block if key not in RENDER_FORMAT_NAMES)
    if unknown:
        issues.append(f"render.formats has unknown keys: {', '.join(unknown)}")
    declared = tuple(name for name in RENDER_FORMAT_NAMES if name in formats_block)

    try:
        resolved = RenderingConfig.from_project_config(config, env={})
    except ValueError as exc:
        issues.append(str(exc))
        resolved = RenderingConfig.from_project_config(None, env={})
    capability = RenderFormatCapability(
        declared=declared,
        pdf=resolved.enable_pdf,
        html=resolved.enable_html,
        slides=resolved.enable_slides,
        docx=resolved.enable_docx,
        epub=resolved.enable_epub,
    )
    enabled = tuple(name for name in RENDER_FORMAT_NAMES if getattr(capability, name))
    evidence = (
        f"declared={','.join(declared) or '<defaults>'}",
        f"enabled={','.join(enabled) or '<none>'}",
    )
    return capability, issues, evidence


def _analysis_capability(
    repo_root: Path,
    project: str,
    project_root: Path,
    config: dict[str, Any],
) -> tuple[AnalysisCapability, list[str], tuple[str, ...]]:
    issues: list[str] = []
    configured = False
    declared: list[str] = []
    analysis_block = config.get("analysis")
    if analysis_block is not None and not isinstance(analysis_block, dict):
        issues.append("analysis must be a mapping")
        analysis_block = {}
    if isinstance(analysis_block, dict) and "scripts" in analysis_block:
        configured = True
        raw_scripts = analysis_block.get("scripts")
        if not isinstance(raw_scripts, list):
            issues.append("analysis.scripts must be a list")
        else:
            for item in raw_scripts:
                if not isinstance(item, str) or not item.strip():
                    issues.append("analysis.scripts entries must be non-empty strings")
                    continue
                declared.append((Path("scripts") / item).as_posix())
            duplicate_entries = sorted(path for path, count in Counter(declared).items() if count > 1)
            if duplicate_entries:
                issues.append(f"analysis.scripts contains duplicates: {', '.join(duplicate_entries)}")

    with _silenced_loggers("infrastructure.core.script_discovery"):
        discovered = discover_analysis_scripts(repo_root, project, project_dir=project_root)
    entrypoints = tuple(_relative(path, project_root) for path in discovered)
    if configured and tuple(declared) != entrypoints:
        issues.append(
            "analysis.scripts declaration does not match confined runnable entrypoints: "
            f"declared={declared!r}, observed={list(entrypoints)!r}"
        )
    capability = AnalysisCapability(configured=configured, entrypoints=entrypoints)
    evidence = (
        f"configured={'true' if configured else 'false'}",
        f"entrypoints={','.join(entrypoints) or '<none>'}",
    )
    return capability, issues, evidence


def _hydration_capability(
    project_root: Path,
    analysis: AnalysisCapability,
) -> tuple[HydrationCapability, list[str], tuple[str, ...]]:
    issues: list[str] = []
    token_count = 0
    token_sources: list[str] = []
    manuscript_dir = project_root / "manuscript"
    try:
        with _silenced_loggers("infrastructure.rendering.manuscript_discovery"):
            manuscript_files = discover_manuscript_files(manuscript_dir)
    except OSError as exc:
        manuscript_files = []
        issues.append(f"could not discover manuscript sources: {exc}")
    for source in manuscript_files:
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(f"could not inspect manuscript source {_relative(source, project_root)}: {exc}")
            continue
        matches = tuple(_HYDRATION_TOKEN_RE.finditer(_markdown_without_code_examples(text)))
        if matches:
            token_count += len(matches)
            token_sources.append(_relative(source, project_root))

    standard = project_root / "scripts" / "z_generate_manuscript_variables.py"
    candidates = list(analysis.entrypoints)
    if standard.is_file():
        standard_relative = standard.relative_to(project_root).as_posix()
        if standard_relative not in candidates:
            candidates.insert(0, standard_relative)
    hydration_candidates = tuple(path for path in candidates if _is_hydration_entrypoint(path))
    entrypoint = hydration_candidates[0] if hydration_candidates else None
    entrypoint_digest: str | None = None
    smoke = "not-applicable"
    entrypoint_evidence: tuple[str, ...] = ()
    if entrypoint is not None:
        contract = validate_python_entrypoint(project_root, entrypoint)
        entrypoint_digest = contract.digest
        smoke = contract.smoke
        issues.extend(contract.issues)
        entrypoint_evidence = contract.evidence
    required = token_count > 0
    if required and entrypoint is None:
        issues.append("rendered manuscript sources contain hydration tokens but no hydration entrypoint is declared")
    mode = "required" if required else "optional" if entrypoint else "none"
    capability = HydrationCapability(
        mode=mode,
        declared=entrypoint is not None,
        required=required,
        entrypoint=entrypoint,
        entrypoint_sha256=entrypoint_digest,
        smoke=smoke,
        token_count=token_count,
        source_files=tuple(token_sources),
    )
    evidence = (
        f"tokens={token_count}",
        f"entrypoint={entrypoint or '<none>'}",
        f"mode={mode}",
        f"smoke={smoke}",
        *entrypoint_evidence,
    )
    return capability, issues, evidence


def _markdown_without_code_examples(text: str) -> str:
    """Remove fenced and inline code so documented token syntax is not a requirement."""
    visible: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            token = marker.group(1)
            if fence_character is None:
                fence_character = token[0]
                fence_length = len(token)
            elif token[0] == fence_character and len(token) >= fence_length:
                fence_character = None
                fence_length = 0
            continue
        if fence_character is None:
            visible.append(_INLINE_CODE_RE.sub("", line))
    return _HTML_COMMENT_RE.sub("", "\n".join(visible))


def _is_hydration_entrypoint(path: str) -> bool:
    name = Path(path).name.lower()
    stem = Path(path).stem.lower()
    return (
        name == "z_generate_manuscript_variables.py"
        or "inject_variables" in stem
        or stem == "generate_manuscript_metrics"
    )


def _probe(probe_id: str, issues: Sequence[str], evidence: tuple[str, ...]) -> CapabilityProbe:
    return CapabilityProbe(
        id=probe_id,
        status="fail" if issues else "pass",
        evidence=evidence,
    )


@contextmanager
def _silenced_loggers(*names: str) -> Iterator[None]:
    """Suppress informational discovery logs while building machine JSON."""
    loggers = tuple(logging.getLogger(name) for name in names)
    prior = tuple(logger.disabled for logger in loggers)
    try:
        for logger in loggers:
            logger.disabled = True
        yield
    finally:
        for logger, disabled in zip(loggers, prior, strict=True):
            logger.disabled = disabled


def _unique_issues(*groups: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(issue for group in groups for issue in group))


def _python_files(directory: Path, *, include_private: bool = True) -> Iterable[Path]:
    if not directory.is_dir():
        return ()
    return (path for path in sorted(directory.rglob("*.py")) if include_private or not path.name.startswith("_"))


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "AnalysisCapability",
    "CANONICAL_CI_PYTHON_VERSIONS",
    "CAPABILITY_MANIFEST_SCHEMA_VERSION",
    "CIMatrixEntry",
    "CapabilityProbe",
    "HydrationCapability",
    "PACKAGE_NAME_OVERRIDES",
    "PackageCapability",
    "PublicCapability",
    "PublicCapabilityReport",
    "REQUIRED_DIRECTORIES",
    "REQUIRED_FILES",
    "RENDER_FORMAT_NAMES",
    "RenderFormatCapability",
    "SkipContract",
    "audit_public_capability",
    "audit_public_capabilities",
    "build_ci_matrix",
    "manifest_roster_digest",
    "validate_ci_matrix",
    "validate_manifest_roster",
    "validate_unique_package_names",
]
