"""Source-owned Root v2 policy, operation eligibility and exact plan admission."""

from __future__ import annotations

import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

from infrastructure.project.public_acceptance_case_policy import RootCasePlan, RootCasePolicy, compile_case_plan
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.project.public_root_case_contract import _json
from infrastructure.project.public_root_case_readback import read_root_census
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

DECLARATION_SCHEMA = 2
PREREQUISITE_SCHEMA = "template-root-case-prerequisites-v2"
ELIGIBILITY_SCHEMA = "template-unpaid-operation-eligibility-v1"


@dataclass(frozen=True)
class Prerequisite:
    id: str
    kind: str
    environment_keys: tuple[str, ...]
    executables: tuple[str, ...]
    platforms: tuple[str, ...]


@dataclass(frozen=True)
class RootCaseAdmission:
    policy: RootCasePolicy
    plan: RootCasePlan
    policy_artifact: dict[str, str]
    prerequisites_artifact: dict[str, str]
    prerequisites: tuple[Prerequisite, ...]


def _path(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("infrastructure/config/")
        or not value.endswith(".json")
        or "\\" in value
        or "\0" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ValueError("Root v2 policy references must be exact public source configuration files")
    return value


def _list(value: object, pattern: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or re.fullmatch(pattern, item) is None for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError("Root obligation prerequisites require explicit unique public names")
    return tuple(value)


def _eligibility(policy: RootCasePolicy, reader: SnapshotReader) -> dict[str, tuple[str, ...]]:
    credential_names: dict[str, tuple[str, ...]] = {}
    for obligation in policy.obligations:
        if obligation.eligibility is None:
            continue
        provider, operation, reference, expected = obligation.eligibility
        snapshot = reader.read(reference)
        record = _json(snapshot)
        if (
            snapshot.sha256 != expected
            or set(record)
            != {
                "schema_version",
                "provider",
                "operation",
                "billing",
                "verified_utc",
                "valid_until_utc",
                "primary_sources",
                "environment_keys",
            }
            or record["schema_version"] != ELIGIBILITY_SCHEMA
            or record["provider"] != provider
            or record["operation"] != operation
            or record["billing"] != "unpaid"
            or not isinstance(record["verified_utc"], str)
            or not isinstance(record["valid_until_utc"], str)
        ):
            raise ValueError("unpaid operation eligibility differs from its reviewed public source contract")
        verified = datetime.fromisoformat(record["verified_utc"])
        expires = datetime.fromisoformat(record["valid_until_utc"])
        now = datetime.now(timezone.utc)
        if (
            verified.tzinfo is None
            or expires.tzinfo is None
            or not verified <= now < expires
            or expires - verified > timedelta(days=30)
        ):
            raise MissingRootCasePolicy("Root unpaid operation eligibility needs fresh primary-source verification")
        credential_names[obligation.id] = _list(record["environment_keys"], "[A-Z][A-Z0-9_]*")
        sources = record["primary_sources"]
        if (
            not isinstance(sources, list)
            or not sources
            or any(not isinstance(source, str) for source in sources)
            or len(set(sources)) != len(sources)
        ):
            raise ValueError("unpaid operation eligibility requires explicit reviewed primary sources")
        for source in sources:
            if not isinstance(source, str):
                raise ValueError("primary operation eligibility sources must be public URLs")
            parsed = urlsplit(source)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("primary operation eligibility source must be a credential-free public HTTPS URL")

    return credential_names


def declaration(reader: SnapshotReader) -> dict[str, Any]:
    metadata = tomllib.loads(reader.read("pyproject.toml").content.decode())
    tool = metadata.get("tool")
    template = tool.get("template") if isinstance(tool, dict) else None
    contract = template.get("root_acceptance") if isinstance(template, dict) else None
    if (
        not isinstance(contract, dict)
        or set(contract) != {"schema_version", "policy", "prerequisites"}
        or type(contract["schema_version"]) is not int
        or contract["schema_version"] != DECLARATION_SCHEMA
    ):
        raise MissingRootCasePolicy(
            "ROOT-ACCEPTANCE-CASE-POLICY-2: reviewed complete Root v2 source declaration is missing"
        )
    return {
        "schema_version": DECLARATION_SCHEMA,
        "policy": _path(contract["policy"]),
        "prerequisites": _path(contract["prerequisites"]),
    }


def load_policy(
    reader: SnapshotReader,
) -> tuple[RootCasePolicy, dict[str, str], dict[str, str], tuple[Prerequisite, ...]]:
    """Load the complete baseline from source; callers cannot supply replacement families."""
    contract = declaration(reader)
    policy_snapshot = reader.read(contract["policy"])
    policy = RootCasePolicy.parse(_json(policy_snapshot))
    credential_names = _eligibility(policy, reader)
    prerequisites_snapshot = reader.read(contract["prerequisites"])
    prerequisites = _json(prerequisites_snapshot)
    if (
        set(prerequisites) != {"schema_version", "obligations"}
        or prerequisites["schema_version"] != PREREQUISITE_SCHEMA
        or not isinstance(prerequisites["obligations"], list)
    ):
        raise ValueError("Root obligations need their versioned explicit prerequisite inventory")
    expected = {item.id: item.kind for item in policy.obligations}
    admitted: dict[str, Prerequisite] = {}
    for row in prerequisites["obligations"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"id", "kind", "environment_keys", "executables", "platforms"}
            or not isinstance(row["id"], str)
            or row["id"] in admitted
            or expected.get(row["id"]) != row["kind"]
        ):
            raise ValueError("Root prerequisite inventory omitted, repeated or invented an obligation")
        keys = _list(row["environment_keys"], "[A-Z][A-Z0-9_]*")
        executables = _list(row["executables"], "[A-Za-z][A-Za-z0-9_.+-]*")
        platforms = _list(row["platforms"], "darwin|linux")
        if (
            (row["kind"] in {"local-model", "tool"} and not executables)
            or (row["kind"] in {"private-provider", "external-fixture"} and not keys)
            or row["kind"] == "platform"
            and not platforms
            or row["kind"] != "network-unpaid"
            and any(re.search("TOKEN|SECRET|PASSWORD|API_KEY", key) for key in keys)
        ):
            raise ValueError("required Root capability has no concrete prerequisite or admits unrelated credentials")
        if row["kind"] == "network-unpaid" and keys != credential_names[row["id"]]:
            raise ValueError("unpaid lane credentials differ from reviewed provider/operation prerequisites")
        admitted[row["id"]] = Prerequisite(row["id"], row["kind"], keys, executables, platforms)
    if set(admitted) != set(expected) or not reader.unchanged():
        raise ValueError("complete Root obligations/source changed during policy admission")

    def binding(snapshot: ArtifactSnapshot) -> dict[str, str]:
        return {"path": snapshot.relative, "sha256": snapshot.sha256}

    return (
        policy,
        binding(policy_snapshot),
        binding(prerequisites_snapshot),
        tuple(admitted[key] for key in sorted(admitted)),
    )


def admit_plan(reader: SnapshotReader, bundle: object) -> RootCaseAdmission:
    policy, policy_binding, prerequisites_binding, prerequisites = load_policy(reader)
    census = read_root_census(reader, bundle, policy)
    plan = compile_case_plan(policy, census, source_identity=RuntimeScope(reader.root, "root").source_identity())
    if not reader.unchanged():
        raise ValueError("Root policy or current full census changed after plan admission")
    return RootCaseAdmission(policy, plan, policy_binding, prerequisites_binding, prerequisites)


def lane_blockers(admission: RootCaseAdmission, lane_id: str, mode: str) -> list[dict[str, str]]:
    if mode not in {"core", "live"}:
        raise ValueError("Root execution mode must be core or live")
    from infrastructure.project.public_root_case_units import admitted_units

    selected = next((unit for unit in admitted_units(admission) if unit.id == lane_id), None)
    if selected is None:
        raise ValueError("Root execution requires a nonempty exact declared applicability unit")
    if sys.platform not in selected.platforms:
        return [{"id": lane_id, "reason": "required-applicable-platform-unavailable"}]
    if mode == "core" and selected.lane not in {"core", "offline-benchmark"}:
        return [{"id": lane_id, "reason": "explicit-live-mode-required"}]
    blockers = []
    for prerequisite in admission.prerequisites:
        if prerequisite.id not in selected.obligations:
            continue
        if prerequisite.platforms and sys.platform not in prerequisite.platforms:
            blockers.append({"id": prerequisite.id, "reason": "required-platform-unavailable"})
        if any(not os.environ.get(key, "").strip() for key in prerequisite.environment_keys):
            blockers.append({"id": prerequisite.id, "reason": "required-configuration-or-credential-missing"})
        if any(shutil.which(name) is None for name in prerequisite.executables):
            blockers.append({"id": prerequisite.id, "reason": "required-executable-missing"})
    return blockers
