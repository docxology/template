"""Source-owned case applicability units; every declared target stays required."""

from __future__ import annotations

from dataclasses import dataclass

from infrastructure.project.public_acceptance_case_policy import LANES, RootCasePolicy
from infrastructure.project.public_root_case_admission import Prerequisite, RootCaseAdmission


@dataclass(frozen=True)
class RootCaseUnit:
    id: str
    lane: str
    families: tuple[str, ...]
    nodeids: tuple[str, ...]
    obligations: tuple[str, ...]
    runtimes: tuple[str, ...]
    platforms: tuple[str, ...]


@dataclass(frozen=True)
class RootCaseCell:
    id: str
    unit: str
    lane: str
    runtime: str
    platform: str
    nodeids: tuple[str, ...]
    obligations: tuple[str, ...]
    policy_sha256: str


def declared_units(policy: RootCasePolicy, prerequisites: tuple[Prerequisite, ...]) -> tuple[RootCaseUnit, ...]:
    """Partition explicit families by reviewed platform-kind applicability only.

    A tool/provider availability declaration cannot narrow required case targets.
    Families without a platform-kind condition apply to every globally required
    platform. Every family retains all globally required supported runtimes.
    """
    declared = {item.id: item.kind for item in policy.obligations}
    conditions = {item.id: item for item in prerequisites}
    if len(conditions) != len(prerequisites) or set(conditions) != set(declared):
        raise ValueError("Root execution units require the full source-owned prerequisite inventory")
    if any(conditions[key].kind != kind for key, kind in declared.items()):
        raise ValueError("Root applicability cannot substitute another obligation kind")
    grouped: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for family in policy.families:
        if family.lane == "optional-external":
            continue  # Exact v3 exception remains in the authenticated full census.
        targets = set(policy.platforms)
        for id_ in family.obligations:
            condition = conditions[id_]
            if condition.kind == "platform":
                if not condition.platforms or set(condition.platforms) - set(policy.platforms):
                    raise ValueError("Root platform applicability must name explicit supported targets")
                targets.intersection_update(condition.platforms)
        if not targets:
            raise ValueError("Root case family has no required applicable platform; it cannot be waived")
        key = family.lane, tuple(platform for platform in policy.platforms if platform in targets)
        grouped.setdefault(key, []).append(family.id)
    families = {family.id: family for family in policy.families}
    units = []
    seen: set[str] = set()
    for (lane, platforms), ids in sorted(grouped.items(), key=lambda item: (LANES.index(item[0][0]), item[0][1])):
        if seen.intersection(ids):
            raise ValueError("Root execution units repeat a source-owned case family")
        seen.update(ids)
        identity = lane if platforms == policy.platforms else lane + ":" + ":".join(platforms)
        units.append(
            RootCaseUnit(
                identity,
                lane,
                tuple(ids),
                tuple(member.nodeid for id_ in ids for member in families[id_].members),
                tuple(sorted({obligation for id_ in ids for obligation in families[id_].obligations})),
                policy.runtimes,
                platforms,
            )
        )
    mandatory = {family.id for family in policy.families if family.lane != "optional-external"}
    if seen != mandatory or len({unit.id for unit in units}) != len(units):
        raise ValueError("Root execution units omitted a declared family or repeated a stable identity")
    return tuple(units)


def admitted_units(admission: RootCaseAdmission) -> tuple[RootCaseUnit, ...]:
    """Bind source-owned applicability to the separately verified complete census."""
    units = declared_units(admission.policy, admission.prerequisites)
    expected = {node for lane in admission.plan.lanes if lane.id != "optional-external" for node in lane.nodeids}
    observed = [node for unit in units for node in unit.nodeids]
    if set(observed) != expected or len(observed) != len(expected):
        raise ValueError("Root applicability differs from its separately authenticated full census")
    return units


def optional_external_records(policy: RootCasePolicy) -> list[dict[str, object]]:
    """Visibility for the exact source exception, never execution or pass proof."""
    obligations = {item.id: item for item in policy.obligations}
    records: list[dict[str, object]] = []
    for family in policy.families:
        if family.lane != "optional-external":
            continue
        eligibility = obligations[family.obligations[0]].eligibility
        if eligibility is None:
            raise ValueError("optional external operation has no exact source-owned review")
        records.append(
            {
                "family": family.id,
                "nodeids": [member.nodeid for member in family.members],
                "status": "unexecuted",
                "reason": "optional-authenticated-production-catalog-not-certified",
                "provider": eligibility[0],
                "operation": eligibility[1],
                "eligibility_artifact": {"path": eligibility[2], "sha256": eligibility[3]},
                "source_sha256": family.source_sha256,
                "metadata_sha256": family.metadata_sha256,
            }
        )
    return records


def required_cells(policy: RootCasePolicy, prerequisites: tuple[Prerequisite, ...]) -> tuple[RootCaseCell, ...]:
    """Declare every unit/runtime/platform obligation; unavailable cells remain required."""
    return tuple(
        RootCaseCell(
            f"root:cases:{unit.id}:{platform}:{runtime}",
            unit.id,
            unit.lane,
            runtime,
            platform,
            unit.nodeids,
            unit.obligations,
            policy.sha256,
        )
        for unit in declared_units(policy, prerequisites)
        for platform in unit.platforms
        for runtime in unit.runtimes
    )
