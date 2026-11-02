"""Draft literal policy only from original census and exhaustive reviewed decisions."""

from __future__ import annotations

from collections import defaultdict
import time
from typing import Any

from infrastructure.project.public_acceptance_case_policy import (
    POLICY_SCHEMA,
    RUNTIMES,
    RootCasePolicy,
    compile_case_plan,
    digest,
)
from infrastructure.project.public_root_case_contract import _json
from infrastructure.project.public_reference_git import _PINNED_SUBMODULE, native_git
from infrastructure.project.public_root_case_readback import _read_collection, read_root_census
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

DECISIONS_SCHEMA = "template-root-policy-reviewed-decisions-v2"


def _tracked(reader: SnapshotReader) -> dict[str, tuple[str, str]]:
    """Observe the actual native Root index with no inherited Git routing or PATH."""
    deadline = time.monotonic() + 60
    top = native_git(reader.root, deadline, "rev-parse", "--show-toplevel").decode().rstrip("\n")
    if top != str(reader.root):
        raise ValueError("Root policy requires its actual native top-level public index")
    result: dict[str, tuple[str, str]] = {}
    seen: set[str] = set()
    for raw in native_git(reader.root, deadline, "ls-files", "--stage", "-z").split(b"\0"):
        if not raw:
            continue
        header, filename = raw.split(b"\t", 1)
        mode, object_id, stage = header.decode().split(" ")
        name = filename.decode("utf-8")
        if name in seen or stage != "0":
            raise ValueError("Root public index has duplicate/unmerged paths")
        seen.add(name)
        if not name.startswith(("tests/", "infrastructure/", "scripts/", "docs/")):
            continue
        if (
            mode not in {"100644", "100755", "160000"}
            or not object_id
            or any(part in {"", ".", ".."} for part in name.split("/"))
        ):
            raise ValueError("Root public policy index has a linked/unsupported origin")
        if mode == "160000" and name != _PINNED_SUBMODULE:
            raise ValueError("Root public policy index has an undeclared inert gitlink")
        result[name] = (mode, object_id)
    return result


def _candidate(reader: SnapshotReader, bundle: object) -> tuple[dict[str, Any], dict[str, tuple[str, str]]]:
    if (
        not isinstance(bundle, dict)
        or set(bundle)
        != {"role", "exit_code", "spec_artifact", "process_artifact", "receipt_artifact", "coordinator_artifact"}
        or bundle["role"] != "canonical-collection-only"
        or type(bundle["exit_code"]) is not int
        or bundle["exit_code"] != 0
    ):
        raise ValueError("policy draft needs its original successful canonical census bundle")
    census = _read_collection(reader, bundle["spec_artifact"], bundle["process_artifact"], bundle["receipt_artifact"])
    tracked = _tracked(reader)
    if any(
        tracked.get(family["id"].split("::", 1)[0], ("", ""))[0] not in {"100644", "100755"}
        for family in census["families"]
    ):
        raise ValueError("public policy draft contains a case outside its actual tracked public test inventory")
    return census, tracked


def family_ledger(reader: SnapshotReader, original_bundle: object) -> dict[str, Any]:
    """Emit a candidate ledger; it cannot establish classified/runtime acceptance."""
    census, tracked = _candidate(reader, original_bundle)
    modules: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in census["families"]:
        modules[family["id"].split("::", 1)[0]].append(family)
    ledger = {
        "role": "root-case-policy-authoring-candidate-only",
        "source_identity": census["source_identity"],
        "census_sha256": digest(census),
        "runtime": census["runtime"],
        "platform": census["platform"],
        "modules": [
            {"path": path, "source_sha256": reader.read(path).sha256, "families": families}
            for path, families in sorted(modules.items())
        ],
    }
    if _tracked(reader) != tracked or not reader.unchanged():
        raise ValueError("Root candidate source or original public index changed during authoring observation")
    return ledger


def author_policy(reader: SnapshotReader, original_bundle: object, decisions_reference: str) -> dict[str, Any]:
    """Refuse missing module/family review; emit every literal case/member row.

    Review decisions are local draft inputs, not execution authority. The result
    requires fresh independent source review and recollection after installation.
    The authoritative producer/reader later loads only source-owned policy files.
    """
    census, tracked = _candidate(reader, original_bundle)
    decisions = _json(reader.read(decisions_reference))
    if (
        set(decisions) != {"schema_version", "source_identity", "census_sha256", "modules", "obligations"}
        or decisions["schema_version"] != DECISIONS_SCHEMA
        or decisions["source_identity"] != census["source_identity"]
        or decisions["census_sha256"] != digest(census)
        or not isinstance(decisions["modules"], list)
        or not isinstance(decisions["obligations"], list)
    ):
        raise ValueError("Root policy authoring needs its exact original census and exhaustive reviewed decisions")
    observed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in census["families"]:
        observed[family["id"].split("::", 1)[0]].append(family)
    seen_modules: set[str] = set()
    families = []
    for module in decisions["modules"]:
        if (
            not isinstance(module, dict)
            or set(module) != {"path", "source_sha256", "families", "decision", "exceptions", "evidence"}
            or not isinstance(module["path"], str)
            or module["path"] not in observed
            or module["path"] in seen_modules
            or module["source_sha256"] != reader.read(module["path"]).sha256
            or not isinstance(module["families"], list)
            or module["families"] != [family["id"] for family in observed[module["path"]]]
            or not isinstance(module["exceptions"], list)
            or not isinstance(module["evidence"], list)
            or not module["evidence"]
        ):
            raise ValueError("Root policy authoring omitted, repeated, invented or source-staled a reviewed module")
        seen_modules.add(module["path"])
        for reference in module["evidence"]:
            if (
                not isinstance(reference, dict)
                or set(reference) != {"path", "source_sha256", "line"}
                or not isinstance(reference["path"], str)
                or tracked.get(reference["path"], ("", ""))[0] not in {"100644", "100755"}
                or type(reference["line"]) is not int
                or reference["line"] < 1
            ):
                raise ValueError("review evidence must name exact public source lines, never private prose/paths")
            snapshot = reader.read(reference["path"])
            if snapshot.sha256 != reference["source_sha256"] or reference["line"] > len(snapshot.content.splitlines()):
                raise ValueError("reviewed classification evidence is source-stale or outside actual public content")
        decision = module["decision"]
        if not isinstance(decision, dict) or set(decision) != {"lane", "obligations"}:
            raise ValueError("every public test module needs an explicit reviewed decision; no core default exists")
        exceptions: dict[str, dict[str, Any]] = {}
        for exception in module["exceptions"]:
            if (
                not isinstance(exception, dict)
                or set(exception) != {"id", "lane", "obligations"}
                or not isinstance(exception["id"], str)
                or exception["id"] not in module["families"]
                or exception["id"] in exceptions
            ):
                raise ValueError("Root policy authoring repeated or invented a family exception")
            exceptions[exception["id"]] = exception
        for family in observed[module["path"]]:
            chosen = exceptions.get(family["id"], decision)
            families.append(
                {key: family[key] for key in ("id", "members", "source_sha256", "metadata_sha256")}
                | {"lane": chosen["lane"], "obligations": chosen["obligations"]}
            )
    if seen_modules != set(observed):
        raise ValueError("Root policy authoring requires a reviewed decision for every actual public test module")
    policy = {
        "schema_version": POLICY_SCHEMA,
        "runtimes": list(RUNTIMES),
        "platforms": ["darwin", "linux"],
        "families": sorted(families, key=lambda family: family["id"]),
        "obligations": decisions["obligations"],
    }
    parsed = RootCasePolicy.parse(policy)
    compile_case_plan(parsed, census, source_identity=census["source_identity"])
    # Authenticate the original outer process too; this is still a draft input
    # baseline, never the source-owned runtime admission authority.
    if read_root_census(reader, original_bundle, parsed) != census:
        raise ValueError("policy draft differs from its original whole census process")
    if not reader.unchanged() or _tracked(reader) != tracked:
        raise ValueError("Root census/decisions/source or original public index changed during full policy authoring")
    return policy
