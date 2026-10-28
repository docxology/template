"""Version identity for the root release and every canonical standalone exemplar.

The root package and each public exemplar publish independently, so "properly
versioned" means two different things that must not be confused:

* the *intended* version — `pyproject.toml` `[project].version`, the version a
  build produces and a release tag must match;
* the *published* version — the last artifact that actually exists, recorded in
  the project's own `CITATION.cff`, `.zenodo.json`, `codemeta.json` and
  `manuscript/config.yaml` `publication.last_published_version`.

A pending (unreleased) exemplar keeps both, and its citation sidecars keep
describing the last real publication rather than the pending one. This contract
checks that every surface agrees on which number means which thing, that the root
release carries its notes and artwork, and — when a tag is supplied — that the tag
is the declared version.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.project_pyproject import load_project_pyproject
from infrastructure.publishing.root_release_contract import (
    root_changelog_versions,
    validate_root_release_tag,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPOSITORY_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")
_SIMPLE_VERSION = re.compile(r"^(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?$")
RELEASE_STATUSES = frozenset({"unreleased", "published"})


@dataclass(frozen=True)
class ReleaseVersionFinding:
    """One version-identity violation for the root release or an exemplar."""

    subject: str
    rule: str
    detail: str


@dataclass(frozen=True)
class ReleaseVersionReport:
    """Aggregate result for the root release plus the canonical public roster."""

    root_version: str
    tag: str | None
    projects: int
    findings: tuple[ReleaseVersionFinding, ...]

    @property
    def passed(self) -> bool:
        """Return whether every version surface agrees."""
        return not self.findings


def normalize_version(value: object) -> str:
    """Normalize a simple version for comparison without inventing structure.

    `0.1` and `0.1.0` compare equal because a published tag may legitimately be
    recorded either way; anything else is compared literally.
    """
    text = str(value or "").strip().lstrip("v")
    match = _SIMPLE_VERSION.fullmatch(text)
    if match is None:
        return text
    return f"{int(match.group('major'))}.{int(match.group('minor') or 0)}.{int(match.group('patch') or 0)}"


def _root_findings(root: Path, version: str, tag: str | None) -> list[ReleaseVersionFinding]:
    findings: list[ReleaseVersionFinding] = []
    if version not in {str(item) for item in root_changelog_versions(root)}:
        findings.append(
            ReleaseVersionFinding("root", "changelog", f"CHANGELOG.md has no released heading for {version!r}")
        )
    notes = root / "docs" / "releases" / f"v{version}.md"
    if not notes.is_file():
        findings.append(ReleaseVersionFinding("root", "release-notes", f"missing {notes.relative_to(root).as_posix()}"))
    for suffix in ("overview.svg", "overview.png"):
        asset = root / "docs" / "releases" / f"template-v{version}-{suffix}"
        if not asset.is_file():
            findings.append(
                ReleaseVersionFinding(
                    "root",
                    "release-artifact",
                    f"missing {asset.relative_to(root).as_posix()} (release.yml uploads and indexes it)",
                )
            )
    if tag is not None:
        try:
            validate_root_release_tag(root, tag)
        except ValueError as error:
            findings.append(ReleaseVersionFinding("root", "tag", str(error)))
    return findings


def _project_findings(root: Path, name: str, root_version: str, record: object) -> list[ReleaseVersionFinding]:
    findings: list[ReleaseVersionFinding] = []
    project_root = root / "projects" / name
    declared = load_project_pyproject(project_root)
    if declared is None:
        return [ReleaseVersionFinding(name, "pyproject", "pyproject.toml is missing or invalid")]
    try:
        payload = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        package_version = payload["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        return [ReleaseVersionFinding(name, "pyproject", f"unreadable project version: {error}")]

    intended = str(getattr(record, "intended_version", "") or "").strip()
    published = str(getattr(record, "last_published_version", "") or "").strip()
    status = str(getattr(record, "release_status", "") or "").strip().lower()
    version_doi = str(getattr(record, "version_doi", "") or "").strip()
    repository = str(getattr(record, "github_repository", "") or "").strip()
    sidecars = tuple(getattr(record, "sidecar_findings", ()) or ())

    if not intended:
        findings.append(ReleaseVersionFinding(name, "intended-version", "publication.intended_version is missing"))
    elif normalize_version(intended) != normalize_version(package_version):
        findings.append(
            ReleaseVersionFinding(
                name,
                "intended-version",
                f"pyproject version {package_version!r} differs from intended_version {intended!r}",
            )
        )
    if status not in RELEASE_STATUSES:
        findings.append(
            ReleaseVersionFinding(
                name, "release-status", f"release_status {status!r} is not one of {sorted(RELEASE_STATUSES)}"
            )
        )
    if status == "published" and published and normalize_version(published) != normalize_version(intended):
        findings.append(
            ReleaseVersionFinding(
                name,
                "release-status",
                f"a published project must have intended {intended!r} equal to last published {published!r}",
            )
        )
    if status == "unreleased" and published and normalize_version(published) == normalize_version(intended):
        findings.append(
            ReleaseVersionFinding(
                name,
                "release-status",
                f"release_status is unreleased but intended {intended!r} equals last published {published!r}",
            )
        )
    if bool(published) != bool(version_doi):
        findings.append(
            ReleaseVersionFinding(
                name,
                "version-doi",
                "version_doi must be present exactly when last_published_version is declared",
            )
        )
    if not REPOSITORY_PATTERN.fullmatch(repository):
        findings.append(
            ReleaseVersionFinding(name, "repository", f"github_repository {repository!r} is not owner/name")
        )
    platform = payload.get("tool", {}).get("template", {}).get("platform_version")
    if str(platform) != root_version:
        findings.append(
            ReleaseVersionFinding(
                name, "platform-version", f"[tool.template].platform_version {platform!r} differs from {root_version!r}"
            )
        )
    for finding in sidecars:
        findings.append(ReleaseVersionFinding(name, "sidecar", str(finding)))
    return findings


def validate_release_versions(
    repo_root: Path, *, tag: str | None = None, projects: tuple[str, ...] | None = None
) -> ReleaseVersionReport:
    """Check root release identity and every canonical exemplar's version surfaces."""
    from infrastructure.documentation._publication_records_load import load_publication_record

    root = Path(repo_root).resolve()
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    roster = PUBLIC_PROJECT_NAMES if projects is None else projects
    findings = _root_findings(root, version, tag)
    for name in roster:
        findings.extend(_project_findings(root, name, version, load_publication_record(root, name)))
    return ReleaseVersionReport(
        root_version=version,
        tag=tag,
        projects=len(roster),
        findings=tuple(findings),
    )


def format_release_version_report(report: ReleaseVersionReport) -> str:
    """Render the report for a CI log."""
    status = "pass" if report.passed else "fail"
    scope = f"root {report.root_version}"
    if report.tag:
        scope += f" (tag {report.tag})"
    lines = [f"release versions: {scope} + {report.projects} exemplars", f"status: {status}"]
    lines.extend(f"{item.subject}: [{item.rule}] {item.detail}" for item in report.findings)
    return "\n".join(lines)


__all__ = [
    "RELEASE_STATUSES",
    "ReleaseVersionFinding",
    "ReleaseVersionReport",
    "format_release_version_report",
    "normalize_version",
    "validate_release_versions",
]
