"""Compose original Root census, review ledger and optional same-job draft authoring.

This workflow helper never classifies families, installs policy or executes cases.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
import sys
import time
import tomllib
from typing import Any

from infrastructure.project.public_acceptance_case_policy import digest
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_reference_git import native_git
from infrastructure.project.public_root_case_census import produce_root_census
from infrastructure.project.public_root_policy_authoring import (
    DECISIONS_SCHEMA,
    _tracked,
    author_policy,
    family_ledger,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

TEMPLATE_SCHEMA = "template-root-policy-review-template-v1"
_MODULE_FIELDS = {"path", "source_sha256", "families", "decision", "exceptions", "evidence"}


def fresh_decisions(template: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    """Bind explicit reviewed classifications to a matching fresh complete ledger.

    The observations digest includes members and fixture/marker metadata, so a
    family name alone cannot authorize newly parameterized or changed cases.
    """
    if (
        set(template) != {"schema_version", "modules", "obligations"}
        or template["schema_version"] != TEMPLATE_SCHEMA
        or not isinstance(template["modules"], list)
        or not isinstance(template["obligations"], list)
        or ledger.get("role") != "root-case-policy-authoring-candidate-only"
        or not isinstance(ledger.get("modules"), list)
    ):
        raise ValueError("review template requires its exhaustive explicit versioned fields")
    observed = {row["path"]: row for row in ledger["modules"]}
    if len(observed) != len(ledger["modules"]):
        raise ValueError("fresh ledger repeats a module")
    modules = []
    seen = set()
    for row in template["modules"]:
        if (
            not isinstance(row, dict)
            or set(row) != _MODULE_FIELDS | {"family_observations_sha256"}
            or not isinstance(row.get("path"), str)
            or row["path"] not in observed
            or row["path"] in seen
        ):
            raise ValueError("review template omitted, repeated or invented a module")
        actual = observed[row["path"]]
        if (
            row["source_sha256"] != actual["source_sha256"]
            or row["families"] != [family["id"] for family in actual["families"]]
            or row["family_observations_sha256"] != digest(actual["families"])
        ):
            raise ValueError("reviewed module/source/family/member/fixture observations changed")
        seen.add(row["path"])
        modules.append({key: row[key] for key in _MODULE_FIELDS})
    if seen != set(observed):
        raise ValueError("review template must explicitly cover every fresh module")
    return {
        "schema_version": DECISIONS_SCHEMA,
        "source_identity": ledger["source_identity"],
        "census_sha256": ledger["census_sha256"],
        "modules": modules,
        "obligations": template["obligations"],
    }


def reviewed_template(reader: SnapshotReader, relative: str, expected_sha256: str, source_sha: str) -> dict[str, Any]:
    """Read only the exact nominated regular tracked Source JSON and original SHA."""
    path = Path(relative)
    if (
        not relative
        or path.is_absolute()
        or path.as_posix() != relative
        or ".." in path.parts
        or "\\" in relative
        or not path.is_relative_to("infrastructure/config")
        or path.suffix != ".json"
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError("review template must name one confined Source JSON and exact SHA256")
    tracked = _tracked(reader)
    if tracked.get(relative, ("", ""))[0] != "100644":
        raise ValueError("review template must be a regular tracked Source file")
    held = reader.read(relative)
    if held.path.lstat().st_nlink != 1 or held.path.lstat().st_mode & 0o111:
        raise ValueError("review template must be independent nonexecutable Source JSON")
    deadline = time.monotonic() + 60
    if native_git(reader.root, deadline, "rev-parse", "--verify", "HEAD^{commit}").decode().strip() != source_sha:
        raise ValueError("review template Source commit changed")
    committed = {}
    for row in native_git(reader.root, deadline, "ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0"):
        if row:
            header, name = row.split(b"\t", 1)
            committed[name.decode()] = tuple(header.decode().split())
    blob = hashlib.sha1(
        b"blob " + str(len(held.content)).encode() + b"\0" + held.content, usedforsecurity=False
    ).hexdigest()
    if held.sha256 != expected_sha256 or committed.get(relative) != ("100644", "blob", blob) or not reader.unchanged():
        raise ValueError("review template differs from its exact committed Source/SHA")
    return held.json_object()


def source_runtime(root: Path, source_sha: str) -> dict[str, Any]:
    """Require the actual own installed Root version and current imported Source."""
    import infrastructure

    if root != root.resolve(strict=True) or re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise ValueError("Root census requires its physical Source and exact commit")
    actual = native_git(root, time.monotonic() + 60, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    origin = infrastructure.__file__
    expected = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    if (
        actual != source_sha
        or not isinstance(origin, str)
        or Path(origin).resolve() != root / "infrastructure/__init__.py"
        or metadata.version("research-project-template") != infrastructure.__version__
        or infrastructure.__version__ != expected
    ):
        raise ValueError("Root census runtime/SDK origin/version differs from current Source")
    return {
        "source_commit": actual,
        "sdk_version": expected,
        "sdk_origin": infrastructure.__file__,
        "python": sys.version,
        "executable": sys.executable,
    }


def run(
    root: Path,
    *,
    source_sha: str,
    mode: str,
    directory: Path,
    timeout_seconds: int = 660,
    template_path: str = "",
    template_sha256: str = "",
) -> dict[str, Any]:
    """Keep the census and any existing author API call in this same original job."""
    if (
        mode not in {"collect", "review", "author"}
        or type(timeout_seconds) is not int
        or not 1 <= timeout_seconds <= 3600
    ):
        raise ValueError("Root policy census requires its finite mode/clock")
    if mode == "author" and (sys.platform != "linux" or sys.version_info[:2] != (3, 14)):
        raise ValueError("only the canonical Linux3.14 job may author a reviewed draft")
    if (
        mode == "collect"
        and (template_path or template_sha256)
        or mode in {"review", "author"}
        and not (template_path and template_sha256)
    ):
        raise ValueError("author mode requires both reviewed-template identities; collect mode takes neither")
    root = root.absolute()
    runtime = source_runtime(root, source_sha)
    reader = SnapshotReader(root)
    template = (
        reviewed_template(reader, template_path, template_sha256, source_sha) if mode in {"review", "author"} else None
    )
    directory = evidence_directory(root, directory.absolute(), fresh=True)
    report: dict[str, Any] = {
        "schema_version": "template-root-policy-census-diagnostic-v1",
        "mode": mode,
        "phase": "collect",
        "runtime": runtime,
        "runtime_acceptance_granted": False,
        "policy_installed": False,
    }
    code = 1
    try:
        original = produce_root_census(root, directory / "collection", timeout_seconds=timeout_seconds)
        report["original_bundle"] = write_json(root, directory / "original-bundle.json", original)
        if type(original.get("exit_code")) is not int:
            raise ValueError("original canonical collection omitted its exact exit code")
        code = original["exit_code"]
        if code != 0:
            raise ValueError("original canonical collection did not succeed")
        report["phase"] = "ledger"
        ledger = family_ledger(reader, original)
        report["family_ledger"] = write_json(root, directory / "family-ledger.json", ledger)
        report["modules"] = len(ledger["modules"])
        report["families"] = sum(len(row["families"]) for row in ledger["modules"])
        if template is not None:
            report["phase"] = "review"
            decisions = fresh_decisions(template, ledger)
            decisions_path = directory / "reviewed-decisions.json"
            report["reviewed_decisions"] = write_json(root, decisions_path, decisions)
            if mode == "author":
                report["phase"] = "author"
                draft = author_policy(reader, original, decisions_path.relative_to(root).as_posix())
                report["draft_policy"] = write_json(root, directory / "draft-policy.json", draft)
        if not reader.unchanged() or source_runtime(root, source_sha) != runtime:
            raise ValueError("Root census Source/runtime/template changed during review composition")
        code = 0
        report.update(status="passed", phase="complete")
    except KeyboardInterrupt:
        code = 130
        report.update(status="failed", diagnostic="original collection interrupted")
    except TimeoutError as error:
        code = 124
        report.update(status="failed", diagnostic=str(error)[:1200])
    except (OSError, ValueError, TypeError, KeyError) as error:
        code = code if type(code) is int and code != 0 else 1
        report.update(status="failed", diagnostic=str(error)[:1200])
    report["exit_code"] = code
    return {**report, "receipt": write_json(root, directory / "report.json", report)}


def main() -> int:
    """Expose only collection/review DATA; the parent installs any reviewed policy."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--mode", choices=("collect", "review", "author"), default="collect")
    parser.add_argument("--timeout-seconds", type=int, default=660)
    parser.add_argument("--review-template-path", default="")
    parser.add_argument("--review-template-sha256", default="")
    args = parser.parse_args()
    try:
        result = run(
            args.repo_root,
            source_sha=args.source_sha,
            mode=args.mode,
            directory=args.directory,
            timeout_seconds=args.timeout_seconds,
            template_path=args.review_template_path,
            template_sha256=args.review_template_sha256,
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
