"""One complete functional infrastructure roster, complementary shards and receipts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from infrastructure.core.testing.ci_contracts import CONTRACT_SECONDS, combined_groups, contract_files

from infrastructure.core.testing.pytest_orchestration import resolve_infrastructure_test_paths
from infrastructure.core.testing.ci_test_ownership import SOURCE_TEST_OWNERS
from infrastructure.core.testing.pytest_observations import (
    DIRECTORY_ENV,
    NONCE_ENV,
    ROOT_ENV,
    member_digest,
    read_execution_receipts,
)

CI_EXTRA_PATHS = (
    "tests/infra_tests/core/test_ci_smoke.py",
    "tests/infra_tests/core/test_secure_write.py",
    "tests/infra_tests/config/test_acceptance_model.py",
    "tests/infra_tests/project/test_distribution_contract.py",
    "tests/infra_tests/project/test_acceptance_fixture_preparation.py",
    "tests/infra_tests/project/test_public_source_body_admission.py",
    "tests/infra_tests/reporting/test_native_tex_root_admission.py",
    "tests/infra_tests/reporting/test_native_installed_preparation_source.py",
    "tests/infra_tests/rendering/test_literature_hydration.py",
    "tests/infra_tests/rendering/test_shared_web_fonts.py",
    "tests/infra_tests/rendering/test_latex_texttt.py",
)


def infrastructure_files(root: Path, changed: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Preserve legacy smoke, include changed tests and conventional Source owners."""
    paths = [Path(p) for p in resolve_infrastructure_test_paths(root, "pipeline-smoke")]
    paths.extend(root / p for p in CI_EXTRA_PATHS)
    for name in changed:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("changed infrastructure input escapes repository")
        if name in {"tests/conftest.py", "conftest.py"}:
            paths.append(root / "tests/infra_tests")
        elif name.startswith(("tests/infra_tests/", "tests/integration/")) and relative.suffix == ".py":
            selected = root / relative
            if relative.name == "conftest.py" or not selected.exists():
                selected = selected.parent
                while not selected.exists() and selected != root / "tests":
                    selected = selected.parent
            paths.append(selected)
        elif name in SOURCE_TEST_OWNERS or (name.startswith("infrastructure/") and relative.suffix == ".py"):
            owners = (
                tuple(root / owner for owner in SOURCE_TEST_OWNERS[name])
                if name in SOURCE_TEST_OWNERS
                else tuple((root / "tests/infra_tests").rglob("test_" + relative.stem.lstrip("_") + "*.py"))
            )
            if owners:
                paths.extend(owners)
            else:
                # Missing conventional ownership cannot silently omit changed behavior.
                package = relative.parts[1] if len(relative.parts) > 2 else ""
                paths.append(root / "tests/infra_tests" / package)
    files: set[str] = set()
    for path in paths:
        if not path.exists() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("functional infrastructure roster contains a missing/linked/escaping path")
        candidates = path.rglob("test_*.py") if path.is_dir() else (path,)
        for candidate in candidates:
            if candidate.is_symlink() or candidate.resolve() != candidate.absolute():
                raise ValueError("functional infrastructure test must be a real confined file")
            files.add(candidate.relative_to(root).as_posix())
    if not files:
        raise ValueError("functional infrastructure selection is empty")
    return tuple(sorted(files))


def infrastructure_shards(root: Path, changed: tuple[str, ...] = (), count: int = 3) -> list[list[str]]:
    """Stable largest-file-first balancing; sizes are estimates, not measured speedups."""
    if type(count) is not int or not 1 <= count <= 8:
        raise ValueError("functional shard count must be between one and eight")
    files = infrastructure_files(root, changed)
    contracts = contract_files(files, infrastructure_files(root))
    files = tuple(name for name in files if name not in contracts)
    shards: list[list[str]] = [[] for _ in range(min(count, len(files)))]
    loads = [0] * len(shards)
    for name in sorted(files, key=lambda p: (-(root / p).stat().st_size, p)):
        selected = min(range(len(loads)), key=lambda i: (loads[i], i))
        shards[selected].append(name)
        loads[selected] += (root / name).stat().st_size
    return [sorted(shard) for shard in shards]


def validate_shards(shards: list[list[str]], expected: tuple[str, ...]) -> None:
    flattened = [path for shard in shards for path in shard]
    if (
        not shards
        or any(not shard for shard in shards)
        or len(flattened) != len(set(flattened))
        or set(flattened) != set(expected)
    ):
        raise ValueError("functional shards are empty, overlapping or differ from the exact roster")


def validate_plan(root: Path, plan: dict) -> None:
    expected = infrastructure_files(root, tuple(plan["changed_paths"]))
    if plan.get("contract_modules", []) != list(contract_files(expected, infrastructure_files(root))):
        raise ValueError("deep contract selection differs from its source-owned exact roster")
    validate_shards(combined_groups(plan), expected)


def run_shard(root: Path, plan: dict, shard: int, directory: Path) -> int:
    shards = combined_groups(plan)
    validate_plan(root, plan)
    if type(shard) is not int or not 0 <= shard < len(shards):
        raise ValueError("invalid functional shard")
    directory.mkdir(parents=True, exist_ok=False)
    nonce = uuid4().hex
    environment = {**os.environ, DIRECTORY_ENV: str(directory / "execution"), NONCE_ENV: nonce, ROOT_ENV: str(root)}
    command = [
        sys.executable,
        "-m",
        "pytest",
        *shards[shard],
        "--no-cov",
        "-q",
        "--benchmark-disable",
        "-p",
        "infrastructure.core.testing.pytest_receipt",
        "--junitxml=" + str(directory / "junit.xml"),
    ]
    is_contract = shard >= len(plan["infra_shards"])
    # Full contracts use the established infrastructure harness default.
    # A CLI option preserves test markers without changing nested child environments.
    command.append("--timeout=120" if is_contract else "--timeout=60")
    timeout = CONTRACT_SECONDS if is_contract else 540
    # A hard pytest exit cannot write terminal receipts. Retain its request
    # before launch; this diagnostic cannot stand in for execution outcomes.
    with (directory / "request.json").open("x") as stream:
        json.dump(
            {
                "schema_version": "template-functional-pytest-request/v1",
                "role": "diagnostic-request-only",
                "shard": shard,
                "nonce": nonce,
                "files": shards[shard],
                "command": command,
                "timeout_seconds": timeout,
            },
            stream,
            sort_keys=True,
            indent=2,
        )
    result = subprocess.run(command, cwd=root, env=environment, check=False, timeout=timeout)
    if result.returncode:
        return result.returncode
    selected, outcomes = read_execution_receipts(directory / "execution", nonce)
    if {node.split("::", 1)[0] for node in selected} != set(shards[shard]):
        raise ValueError("functional shard omitted a selected test file")
    payload = {
        "shard": shard,
        "nonce": nonce,
        "files": shards[shard],
        "selected": selected,
        "outcomes": outcomes,
        "member_sha256": member_digest(selected),
        "outcome_sha256": member_digest(outcomes),
    }
    (directory / "summary.json").write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    return 0


def verify_shard_receipts(plan: dict, directory: Path) -> dict:
    paths = sorted(directory.glob("**/summary.json"))
    summaries = [json.loads(path.read_bytes()) for path in paths]
    expected = combined_groups(plan)
    if len(summaries) != len(expected) or {row["shard"] for row in summaries} != set(range(len(expected))):
        raise ValueError("missing or duplicate functional shard receipt")
    nodes: list[str] = []
    for path, row in zip(paths, summaries, strict=True):
        selected, outcomes = read_execution_receipts(path.parent / "execution", row["nonce"])
        if tuple(row["selected"]) != selected or tuple(row["outcomes"]) != outcomes:
            raise ValueError("functional summary differs from original pytest observations")
        if row["files"] != expected[row["shard"]] or member_digest(tuple(row["selected"])) != row["member_sha256"]:
            raise ValueError("functional receipt differs from its selected shard")
        if {n.split("::", 1)[0] for n in row["selected"]} != set(row["files"]):
            raise ValueError("functional receipt is missing selected files")
        if member_digest(tuple(row["outcomes"])) != row["outcome_sha256"] or len(row["outcomes"]) != len(
            row["selected"]
        ):
            raise ValueError("functional receipt outcomes differ")
        nodes.extend(row["selected"])
    if len(nodes) != len(set(nodes)):
        raise ValueError("functional shards executed overlapping members")
    return {"shards": len(summaries), "members": len(nodes), "member_sha256": member_digest(tuple(sorted(nodes)))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--shard", type=int)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    validate_plan(Path.cwd(), plan)
    if args.shard is None:
        print(json.dumps(verify_shard_receipts(plan, args.directory), sort_keys=True))
        return 0
    return run_shard(Path.cwd(), plan, args.shard, args.directory)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["infrastructure_files", "infrastructure_shards", "validate_shards", "verify_shard_receipts", "run_shard"]
