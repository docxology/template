"""Closed Root case classification; plans do not themselves grant acceptance."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

POLICY_SCHEMA = "template-root-case-policy-v2"
OPTIONAL_POLICY_SCHEMA = "template-root-case-policy-v3"
OPTIONAL_MONID_FAMILY = "tests/infra_tests/search/test_monid.py::test_live_discover_includes_price_when_key_present"
CENSUS_SCHEMA = "template-root-case-census-v2"
PLAN_SCHEMA = "template-root-case-plan-v2"
LANES = (
    "core",
    "live-unpaid",
    "live-unverified",
    "private-contract",
    "external-fixture",
    "offline-benchmark",
    "optional-external",
)
RUNTIMES = ("3.12", "3.13", "3.14")
PLATFORMS = ("darwin", "linux")
KINDS = (
    "local-model",
    "network-unpaid",
    "network-unverified",
    "private-provider",
    "external-fixture",
    "tool",
    "platform",
)
_ORDINARY_MARKERS = frozenset(
    {
        "parametrize",
        "usefixtures",
        "timeout",
        "skipif",
        "hypothesis",
        "integration",
        "no_patch_llm_client",
        "slow",
        "bench",
        "benchmark",
        "performance",
        "long_running",
        "requires_gate_artifacts",
    }
)
_MARKER_KINDS = {
    "requires_ollama": "local-model",
    "network": "network-unpaid",
    "requires_network": "network-unpaid",
    "requires_credentials": "network-unpaid",
    "requires_zenodo": "network-unpaid",
    "requires_github": "network-unpaid",
    "requires_arxiv": "network-unpaid",
    "requires_docker": "tool",
    "requires_latex": "tool",
    "private_project": "private-provider",
    "external_fixture": "external-fixture",
}


def digest(value: object) -> str:
    """Hash a stable finite JSON structure without Python object reprs."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _object(value: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} requires exactly its versioned fields")
    return value


def _strings(value: object, label: str, *, empty: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or (not empty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{label} must be a unique explicit string list")
    return tuple(value)


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} must be a SHA-256")
    return value


def _family_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("case family identity must be text")
    pieces = value.split("::")
    file, names = pieces[0], pieces[1:]
    if (
        not file.startswith("tests/")
        or not file.endswith(".py")
        or any(part in ("", ".", "..") for part in file.split("/"))
        or not names
        or any(not name.isidentifier() for name in names)
    ):
        raise ValueError("case family must name an exact public Root test function")
    return value


@dataclass(frozen=True)
class CaseMember:
    nodeid: str
    parameter_id: str | None

    @classmethod
    def parse(cls, value: object, family: str) -> CaseMember:
        row = _object(value, {"nodeid", "parameter_id"}, "case member")
        parameter = row["parameter_id"]
        if parameter is not None and not isinstance(parameter, str):
            raise ValueError("parameter identity must be explicit text or null")
        expected = family if parameter is None else family + "[" + parameter + "]"
        if row["nodeid"] != expected:
            raise ValueError("case member differs from its family/parameter identity")
        return cls(expected, parameter)


@dataclass(frozen=True)
class CaseFamily:
    id: str
    lane: str
    members: tuple[CaseMember, ...]
    obligations: tuple[str, ...]
    source_sha256: str
    metadata_sha256: str

    @classmethod
    def parse(cls, value: object) -> CaseFamily:
        row = _object(
            value, {"id", "lane", "members", "obligations", "source_sha256", "metadata_sha256"}, "case family"
        )
        family = _family_id(row["id"])
        if row["lane"] not in LANES or not isinstance(row["members"], list) or not row["members"]:
            raise ValueError("case family requires a declared execution lane and members")
        members = tuple(CaseMember.parse(member, family) for member in row["members"])
        if len({member.nodeid for member in members}) != len(members):
            raise ValueError("case family has duplicate parameter members")
        return cls(
            family,
            row["lane"],
            members,
            _strings(row["obligations"], "family obligations", empty=True),
            _sha(row["source_sha256"], "family source"),
            _sha(row["metadata_sha256"], "family metadata"),
        )


@dataclass(frozen=True)
class Obligation:
    id: str
    kind: str
    eligibility: tuple[str, str, str, str] | None

    @classmethod
    def parse(cls, value: object) -> Obligation:
        row = _object(value, {"id", "kind", "eligibility"}, "required obligation")
        if (
            not isinstance(row["id"], str)
            or re.fullmatch(r"[a-z][a-z0-9:_.-]*", row["id"]) is None
            or row["kind"] not in KINDS
        ):
            raise ValueError("required obligation needs a stable public identity and supported kind")
        eligibility = row["eligibility"]
        if row["kind"] in {"network-unpaid", "network-unverified"}:
            proof = _object(
                eligibility,
                {"provider", "operation", "billing", "public_reference", "reference_sha256"},
                "unpaid operation eligibility",
            )
            billing = "unpaid" if row["kind"] == "network-unpaid" else "unverified"
            if proof["billing"] != billing or any(
                not isinstance(proof[key], str) or not proof[key].strip() for key in ("provider", "operation")
            ):
                raise ValueError("network markers cannot grant unpaid provider/operation eligibility")
            reference = proof["public_reference"]
            if (
                not isinstance(reference, str)
                or not reference.startswith(("docs/", "infrastructure/"))
                or "\\" in reference
                or any(part in ("", ".", "..") for part in reference.split("/"))
            ):
                raise ValueError("unpaid eligibility must bind a reviewed public source contract")
            eligibility = (
                proof["provider"],
                proof["operation"],
                reference,
                _sha(proof["reference_sha256"], "eligibility reference"),
            )
        elif eligibility is not None:
            raise ValueError("non-network obligations cannot grant provider billing eligibility")
        return cls(row["id"], row["kind"], eligibility)


@dataclass(frozen=True)
class RootCasePolicy:
    families: tuple[CaseFamily, ...]
    obligations: tuple[Obligation, ...]
    runtimes: tuple[str, ...]
    platforms: tuple[str, ...]
    sha256: str

    @classmethod
    def parse(cls, value: object) -> RootCasePolicy:
        row = _object(value, {"schema_version", "runtimes", "platforms", "families", "obligations"}, "Root case policy")
        if row["schema_version"] not in {POLICY_SCHEMA, OPTIONAL_POLICY_SCHEMA}:
            raise ValueError("unsupported Root case policy schema")
        runtimes = _strings(row["runtimes"], "required runtimes")
        platforms = _strings(row["platforms"], "required platforms")
        if runtimes != RUNTIMES or platforms != PLATFORMS:
            raise ValueError("Root policy cannot waive required supported runtimes/platforms")
        if not isinstance(row["families"], list) or not row["families"] or not isinstance(row["obligations"], list):
            raise ValueError("Root policy requires its explicit nonempty case inventory")
        families = tuple(CaseFamily.parse(entry) for entry in row["families"])
        obligations = tuple(Obligation.parse(entry) for entry in row["obligations"])
        if len({family.id for family in families}) != len(families) or len({item.id for item in obligations}) != len(
            obligations
        ):
            raise ValueError("Root policy has duplicate families or obligations")
        declared = {item.id for item in obligations}
        optional = [family for family in families if family.lane == "optional-external"]
        for family in optional:
            obligation = next((item for item in obligations if item.id == "monid-discover"), None)
            if (
                row["schema_version"] != OPTIONAL_POLICY_SCHEMA
                or family.id != OPTIONAL_MONID_FAMILY
                or family.obligations != ("monid-discover",)
                or family.members != (CaseMember(OPTIONAL_MONID_FAMILY, None),)
                or obligation is None
                or obligation.kind != "network-unverified"
                or obligation.eligibility is None
                or obligation.eligibility[:2] != ("monid", "POST /v1/discover")
                or [item.id for item in families if "monid-discover" in item.obligations] != [OPTIONAL_MONID_FAMILY]
            ):
                raise ValueError("optional external policy permits only the exact reviewed Monid catalog case")
        if optional and len(optional) == len(families):
            raise ValueError("optional external inventory cannot replace mandatory Root cases")
        used = {item for family in families for item in family.obligations}
        if used != declared:
            raise ValueError("every required obligation must bind a case; unknown obligations are refused")
        return cls(families, obligations, runtimes, platforms, digest(row))


@dataclass(frozen=True)
class PlannedLane:
    id: str
    nodeids: tuple[str, ...]
    obligations: tuple[str, ...]


@dataclass(frozen=True)
class RootCasePlan:
    policy_sha256: str
    census_sha256: str
    source_identity: str
    runtime: str
    platform: str
    lanes: tuple[PlannedLane, ...]

    @property
    def nodeids(self) -> tuple[str, ...]:
        return tuple(node for lane in self.lanes for node in lane.nodeids)


def compile_case_plan(policy: RootCasePolicy, census: object, *, source_identity: str) -> RootCasePlan:
    """Classify a separately authenticated full census; never execute or grant a gate.

    The execution/receipt reader must independently authenticate original process,
    specification, runtime, bytecode, providers and artifacts before calling this
    pure classifier. A JSON-shaped census alone cannot establish actual collection.
    """
    row = _object(
        census, {"schema_version", "source_identity", "runtime", "platform", "families", "nodeids"}, "case census"
    )
    if row["schema_version"] != CENSUS_SCHEMA or row["source_identity"] != _sha(source_identity, "current source"):
        raise ValueError("Root case census is unsupported or source-stale")
    if row["runtime"] not in policy.runtimes or row["platform"] not in policy.platforms:
        raise ValueError("Root case census uses an undeclared target environment")
    if not isinstance(row["families"], list) or len(row["families"]) != len(policy.families):
        raise ValueError("Root census case-family inventory differs from policy")
    observed: dict[str, dict[str, Any]] = {}
    for entry in row["families"]:
        observed_row = _object(
            entry, {"id", "members", "source_sha256", "metadata_sha256", "markers", "public_closure"}, "observed family"
        )
        identity = _family_id(observed_row["id"])
        if identity in observed:
            raise ValueError("Root census repeats a case family")
        observed[identity] = observed_row
    if set(observed) != {family.id for family in policy.families}:
        raise ValueError("Root census contains missing or unexpected case families")
    kinds = {item.id: item.kind for item in policy.obligations}
    for family in policy.families:
        actual = observed[family.id]
        if (
            not isinstance(actual["members"], list)
            or tuple(CaseMember.parse(member, family.id) for member in actual["members"]) != family.members
            or actual["source_sha256"] != family.source_sha256
            or actual["metadata_sha256"] != family.metadata_sha256
        ):
            raise ValueError("case parameter/source/marker/fixture metadata changed after policy review")
        if type(actual["public_closure"]) is not bool or not actual["public_closure"]:
            raise ValueError("public Root census imported inadmissible or unresolved case/fixture source")
        markers = _strings(actual["markers"], "observed markers", empty=True)
        if set(markers) - (_ORDINARY_MARKERS | _MARKER_KINDS.keys()):
            raise ValueError("unknown Root marker needs explicit reviewed classification")
        required = {_MARKER_KINDS[marker] for marker in markers if marker in _MARKER_KINDS}
        if "network-unpaid" in required and "network-unverified" in {kinds[item] for item in family.obligations}:
            required = required - {"network-unpaid"} | {"network-unverified"}
        if not required.issubset({kinds[item] for item in family.obligations}):
            raise ValueError("Root policy cannot waive observed live/private/external/tool obligations")
        assigned = {kinds[item] for item in family.obligations}
        if ("network-unverified" in assigned) != (family.lane in {"live-unverified", "optional-external"}):
            raise ValueError("unverified network eligibility requires its permanently blocked lane")
        if family.lane in {"core", "offline-benchmark"} and (required | assigned) - {"tool", "platform"}:
            raise ValueError("an opt-in capability cannot be reclassified as ordinary core execution")
        if family.lane == "private-contract" and "private-provider" not in required:
            raise ValueError("private lane requires its actual public contract marker")
    expected = [member.nodeid for family in policy.families for member in family.members]
    nodeids = _strings(row["nodeids"], "complete census nodes")
    if set(nodeids) != set(expected) or len(expected) != len(set(expected)):
        raise ValueError("Root census omitted, duplicated or invented case nodes")
    lanes = tuple(
        PlannedLane(
            lane,
            tuple(member.nodeid for family in policy.families if family.lane == lane for member in family.members),
            tuple(sorted({item for family in policy.families if family.lane == lane for item in family.obligations})),
        )
        for lane in LANES
        if any(family.lane == lane for family in policy.families)
    )
    return RootCasePlan(policy.sha256, digest(row), source_identity, row["runtime"], row["platform"], lanes)
