"""Source-owned platform candidate and release acceptance requirements."""

from __future__ import annotations

import fnmatch
import re
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pypdf.errors import PyPdfError

from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS, RENDER_FORMAT_NAMES
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import validate_runtime_version_provider
from infrastructure.rendering.config import RenderingConfig
from infrastructure.reporting.readiness_receipts import (
    SCHEMA_VERSION,
    GateEvidence,
    ReadinessEvidence,
    aggregate_state,
    deliverable_identity,
    project_source_identity,
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ARTIFACT_SCHEMA = "template-required-acceptance-v1"


@dataclass(frozen=True)
class Requirement:
    """A gate derived from public source declarations, never from a receipt's allowlist."""

    id: str
    kind: str
    scope: str
    version: str
    platform_version: str
    source_identity: str
    deliverables_identity: str = ""
    profile: str = "candidate"
    python_version: str = ""
    formats: tuple[str, ...] = ()
    capability: str = ""
    draft: bool = False
    package: str = ""
    source_files: tuple[str, ...] = ()
    test_files: tuple[str, ...] = ()
    case_unit: str = ""
    case_platform: str = ""
    case_policy_sha256: str = ""
    case_nodes: tuple[str, ...] = ()
    case_obligations: tuple[str, ...] = ()


def _python_scope(root: Path, scope: str, metadata: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    base = root if scope == "root" else root / "projects" / scope
    source = base / "infrastructure" if scope == "root" else base / "src"
    omitted = metadata.get("tool", {}).get("coverage", {}).get("run", {}).get("omit", [])
    if not isinstance(omitted, list) or any(not isinstance(pattern, str) for pattern in omitted):
        raise ValueError("source-owned coverage omissions are invalid")
    files = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in source.rglob("*.py")
            if not any(fnmatch.fnmatch(path.relative_to(base).as_posix(), pattern) for pattern in omitted)
            and "__pycache__" not in path.parts
        )
    )
    tests = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in (base / "tests").rglob("*.py")
            if path.name.startswith("test_") or path.name.endswith("_test.py")
        )
    )
    return files, tests


def required_profile(
    root: Path, reader: SnapshotReader, fingerprint: str
) -> tuple[tuple[Requirement, ...], tuple[GateEvidence, ...]]:
    """Compile root and every canonical project's declared acceptance obligations."""
    requirements: list[Requirement] = []
    faults: list[GateEvidence] = []
    try:
        metadata = tomllib.loads(reader.read("pyproject.toml").content.decode())
        version = metadata["project"]["version"]
        package = metadata["project"]["name"]
        if not isinstance(version, str) or not version.strip() or package != "research-project-template":
            raise ValueError("root metadata has invalid version/package")
        default_runtime = reader.read(".python-version").content.decode().strip()
        if default_runtime != "3.14":
            raise ValueError("root default runtime must explicitly declare Python 3.14")
        validate_runtime_version_provider(reader.read("infrastructure/_version.py").content.decode())
        changelog = reader.read("CHANGELOG.md").content.decode()
        headings = [
            match.group(1).strip()
            for match in re.finditer(r"^##\s*\[([^\]]+)\]", changelog, re.MULTILINE)
            if match.group(1).strip().lower() != "unreleased"
        ]
        if not headings or headings[0] != version:
            raise ValueError("root intended version has no matching changelog heading")
    except FileNotFoundError:
        return (), (GateEvidence("root:metadata", "unknown", diagnostic="root metadata is missing"),)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, SyntaxError):
        return (), (GateEvidence("root:metadata", "fail", diagnostic="root metadata is invalid"),)

    from infrastructure.project.public_acceptance_scope import RuntimeScope

    files, tests = _python_scope(root, "root", metadata)
    root_deliverables = RuntimeScope(root, "root").deliverables_identity()

    def add(id_: str, kind: str, **kwargs: Any) -> None:
        requirements.append(
            Requirement(
                id_,
                kind,
                "root",
                version,
                version,
                fingerprint,
                deliverables_identity=root_deliverables,
                package=package,
                source_files=files,
                test_files=tests,
                **kwargs,
            )
        )

    root_case_contract = metadata.get("tool", {}).get("template", {}).get("root_acceptance")
    root_v2 = isinstance(root_case_contract, dict) and root_case_contract.get("schema_version") in {2, 3}
    if root_v2:
        from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy
        from infrastructure.reporting.release_readiness_root_cases import case_requirements

        try:
            requirements.extend(
                case_requirements(
                    reader,
                    version=version,
                    package=package,
                    fingerprint=fingerprint,
                    deliverables=root_deliverables,
                    source_files=files,
                    test_files=tests,
                )
            )
        except MissingRootCasePolicy:
            add("root:case-policy", "root-policy")
            faults.append(
                GateEvidence(
                    "root:case-declaration",
                    "blocked",
                    diagnostic="required complete Root case policy/operation eligibility is unavailable",
                )
            )
        except (OSError, ValueError, TypeError, KeyError, UnicodeError):
            add("root:case-policy", "root-policy")
            faults.append(
                GateEvidence(
                    "root:case-declaration",
                    "fail",
                    diagnostic="source-owned complete Root case policy/prerequisites are invalid",
                )
            )
    else:
        for runtime in CANONICAL_CI_PYTHON_VERSIONS:
            add(f"root:runtime:{runtime}", "runtime", python_version=runtime)
    for id_, kind in (
        ("roster", "roster"),
        ("docs_lint", "docs"),
        ("methods", "oracle"),
        ("installed", "installed"),
        ("export", "export"),
        ("sandbox:transfer", "transfer"),
        ("macos:process", "platform"),
        ("macos:rendering", "platform"),
    ):
        add(f"root:{id_}", kind)
    add("root:coverage", "coverage", python_version=default_runtime)
    add("root:publication", "publication", profile="released")
    for project in PUBLIC_PROJECT_NAMES:
        prefix = f"projects/{project}"
        try:
            meta = tomllib.loads(reader.read(f"{prefix}/pyproject.toml").content.decode())
            project_version, project_package = meta["project"]["version"], meta["project"]["name"]
            contract = meta["tool"]["template"]
            runtimes, capabilities = contract["tested_python_versions"], contract["required_unpaid_capabilities"]
            if (
                contract["platform_version"] != version
                or not isinstance(project_version, str)
                or not isinstance(project_package, str)
            ):
                raise ValueError("project/platform version binding is invalid")
            if runtimes != list(CANONICAL_CI_PYTHON_VERSIONS):
                raise ValueError("declared runtime roster differs from platform support")
            if not isinstance(capabilities, list) or any(
                not isinstance(item, str) or re.fullmatch(r"[a-z][a-z0-9-]*", item) is None for item in capabilities
            ):
                raise ValueError("unpaid capability declarations must be stable labels")
            if len(set(capabilities)) != len(capabilities):
                raise ValueError("unpaid capability declarations contain duplicates")
            config = yaml.safe_load(reader.read(f"{prefix}/manuscript/config.yaml").content)
            if not isinstance(config, dict):
                raise ValueError("project config must be a mapping")
            publication = config.get("publication", {})
            if (
                not isinstance(publication, dict)
                or publication.get("intended_version") != project_version
                or publication.get("platform_version") != version
            ):
                raise ValueError("publication intended/platform versions differ from source metadata")
            rendering = RenderingConfig.from_project_config(config, env={})
            formats = tuple(name for name in RENDER_FORMAT_NAMES if getattr(rendering, f"enable_{name}"))
            source_files, test_files = _python_scope(root, project, meta)
            common: dict[str, Any] = dict(
                scope=project,
                version=project_version,
                platform_version=version,
                source_identity=project_source_identity(root, project),
                deliverables_identity=deliverable_identity(root, project),
                package=project_package,
                source_files=source_files,
                test_files=test_files,
            )
            for runtime in runtimes:
                requirements.append(
                    Requirement(f"{project}:runtime:{runtime}", "runtime", python_version=runtime, **common)
                )
                requirements.append(
                    Requirement(f"{project}:coverage:{runtime}", "coverage", python_version=runtime, **common)
                )
            for kind in ("pipeline", "formats", "domain", "installed", "export"):
                requirements.append(Requirement(f"{project}:{kind}", kind, formats=formats, **common))
            for capability in capabilities:
                requirements.append(
                    Requirement(f"{project}:live:{capability}", "live", capability=capability, **common)
                )
            requirements.append(
                Requirement(
                    f"{project}:publication",
                    "publication",
                    profile="released",
                    draft=publication.get("status") == "draft" and not publication.get("doi"),
                    **common,
                )
            )
        except (FileNotFoundError, KeyError):
            faults.append(
                GateEvidence(f"{project}:declaration", "unknown", diagnostic="required source declaration is missing")
            )
        except (OSError, ValueError, TypeError, yaml.YAMLError, UnicodeError):
            faults.append(
                GateEvidence(f"{project}:declaration", "fail", diagnostic="required source declaration is invalid")
            )
    return tuple(requirements), tuple(faults)


def _gate(requirement: Requirement, entries: dict[str, Any], reader: SnapshotReader, fingerprint: str) -> GateEvidence:
    from infrastructure.reporting.release_readiness_validators import validate_acceptance

    entry = entries.get(requirement.id)
    if entry is None:
        return GateEvidence(
            requirement.id, "unknown", requirement.profile, diagnostic="required execution evidence is missing"
        )
    try:
        if not isinstance(entry, dict) or entry.get("status") not in {"pass", "fail", "blocked", "unknown"}:
            raise ValueError("receipt entry has invalid status/type")
        command = entry.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(arg, str) or not arg for arg in command):
            raise ValueError("execution command must be a nonempty argv array")
        artifact = reader.read(entry.get("artifact", ""))
        if entry.get("artifact_sha256") != artifact.sha256:
            raise ValueError("receipt does not match exact artifact bytes")
        payload = artifact.json_object()
        expected = {
            "schema_version": ARTIFACT_SCHEMA,
            "gate": requirement.id,
            "status": entry["status"],
            "platform_version": requirement.platform_version,
            "version": requirement.version,
            "scope": requirement.scope,
            "source_fingerprint": fingerprint,
            "source_identity": requirement.source_identity,
        }
        if requirement.scope != "root":
            expected["deliverables_identity"] = requirement.deliverables_identity
        if any(payload.get(key) != value for key, value in expected.items()):
            raise ValueError("artifact version/source/scope/status binding is invalid")
        status = entry["status"]
        if status == "blocked":
            blockers = payload.get("blockers")
            if (
                not isinstance(blockers, list)
                or not blockers
                or any(
                    not isinstance(row, dict)
                    or not isinstance(row.get("tool"), str)
                    or not row["tool"].strip()
                    or not isinstance(row.get("reason"), str)
                    or not row["reason"].strip()
                    for row in blockers
                )
            ):
                raise ValueError("required capability blocker must name its tool and reason")
            diagnostic = "required tool/capability is blocked"
        elif status in {"unknown", "fail"}:
            diagnostic = "required execution is unknown" if status == "unknown" else "required execution failed"
        else:
            validate_acceptance(requirement, payload, reader)
            diagnostic = "declared draft remains explicitly unpublished" if requirement.draft else ""
        return GateEvidence(requirement.id, status, requirement.profile, artifact.relative, diagnostic)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        zipfile.BadZipFile,
        PyPdfError,
        EOFError,
        RuntimeError,
    ):
        return GateEvidence(
            requirement.id,
            "fail",
            requirement.profile,
            diagnostic="invalid, stale, unbound, or malformed acceptance evidence",
        )


def collect_profile(root: Path, receipt_path: Path | None, reader: SnapshotReader) -> ReadinessEvidence:
    """Validate all required gates against one source/artifact observation."""
    try:
        fingerprint = source_fingerprint(root)
        requirements, faults = required_profile(root, reader, fingerprint)
    except (OSError, ValueError):
        return ReadinessEvidence(
            available=receipt_path is not None,
            candidate_state="fail",
            released_state="fail",
            issues=("public source/deliverable custody is unavailable",),
        )
    entries: dict[str, Any] = {}
    source = None
    if receipt_path is not None:
        source = receipt_path.name
        try:
            relative = receipt_path.resolve().relative_to(root).as_posix()
            receipt = reader.read(relative).json_object()
            if receipt.get("schema_version") != SCHEMA_VERSION or receipt.get("platform_version") != next(
                (r.platform_version for r in requirements), None
            ):
                raise ValueError("unsupported receipt schema/version")
            if receipt.get("source_fingerprint") != fingerprint or receipt.get("roster") != list(PUBLIC_PROJECT_NAMES):
                raise ValueError("receipt source/roster is stale or incomplete")
            if not isinstance(receipt.get("gates"), dict):
                raise ValueError("receipt gates must be a mapping")
            entries = receipt["gates"]
            required_ids = {r.id for r in requirements}
            if set(entries) - required_ids:
                raise ValueError("receipt contains unsupported acceptance gates")
        except (OSError, ValueError, TypeError):
            faults += (
                GateEvidence(
                    "receipt", "fail", diagnostic="unsupported, malformed, or source-stale required acceptance receipt"
                ),
            )
    gates = faults + tuple(_gate(requirement, entries, reader, fingerprint) for requirement in requirements)
    try:
        if source_fingerprint(root) != fingerprint or not reader.unchanged():
            gates += (GateEvidence("snapshot", "fail", diagnostic="source or evidence changed during collection"),)
    except (OSError, ValueError):
        gates += (GateEvidence("snapshot", "fail", diagnostic="source or evidence custody changed during collection"),)
    candidate = aggregate_state(tuple(gate.state for gate in gates if gate.profile == "candidate"))
    released = aggregate_state(tuple(gate.state for gate in gates))
    publication = next((gate for gate in gates if gate.id == "root:publication" and gate.state == "pass"), None)
    tag = published = None
    if publication and publication.artifact:
        details = reader.read(publication.artifact).json_object()["details"]
        tag, published = details.get("actual_tag"), details.get("published_version")
    issues = tuple(f"{gate.id}: {gate.state}: {gate.diagnostic}" for gate in gates if gate.state != "pass")
    return ReadinessEvidence(
        receipt_path is not None,
        released == "pass",
        source,
        fingerprint,
        candidate,
        released,
        gates,
        issues,
        tag,
        published,
    )
