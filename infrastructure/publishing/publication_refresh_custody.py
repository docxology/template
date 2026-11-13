"""Exact tracked ownership and review-artifact custody for publication refresh."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.artifacts import (
    STABLE_OUTPUT_INVENTORY_MODE,
    artifact_manifest_from_payload,
    validate_artifact_manifest,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing._publication_refresh_protocol import (
    gate_commands,
    generation_commands,
    successful_command_receipt,
)
from infrastructure.publishing.release_provider_graph import current_provider_graph
from infrastructure.publishing.root_release_contract import root_package_version

SCHEMA = "template-coordinated-publication-refresh/v4"
REFRESH_MODES = ("refresh", "rebind-only")


def git(root: Path, *arguments: str) -> bytes:
    """Read or mutate only the nominated disposable checkout."""
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        stdin=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=60,
    )


def write_json(path: Path, value: object) -> None:
    """Publish a new operator record without replacing prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _regular(root: Path, relative: str) -> bytes:
    path = root / relative
    body = read_bytes_confined(root, path, max_bytes=256 * 1024 * 1024)
    metadata = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
        raise ValueError(f"refresh evidence must retain mode 100644: {relative}")
    return body


def _compiled(root: Path, scope: str, tracked: dict[str, dict[str, str]]) -> list[str]:
    """Read explicit sheaf compiler ownership; numbering alone grants nothing."""
    prefix = f"projects/{scope}/"
    declaration = prefix + "manuscript/sheaf/manifest.yaml"
    if declaration not in tracked:
        return []
    for source in ("src/manuscript/sheaf/compose.py", "src/manuscript/compilation_io.py"):
        producer = prefix + source
        if producer not in tracked:
            raise ValueError("compiled manuscript declaration lacks its tracked Source producer")
        _regular(root, producer)
    manifest = yaml.safe_load(_regular(root, declaration))
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 2
        or not isinstance(manifest.get("sections"), list)
    ):
        raise ValueError("compiled manuscript requires the explicit schema-2 sheaf declaration")
    targets = []
    for row in manifest["sections"]:
        if not isinstance(row, dict):
            raise ValueError("compiled section declaration is malformed")
        compose = row.get("compose", row.get("kind", "section") == "section")
        if type(compose) is not bool:
            raise ValueError("compiled section compose flag must be boolean")
        if not compose:
            continue
        name = row.get("output_name")
        tracks = row.get("tracks")
        if not isinstance(name, str) or re.fullmatch(r"[0-9]{2}_[A-Za-z0-9_]+\.md", name) is None:
            raise ValueError("compiled section needs one explicit flat numbered output_name")
        if not isinstance(tracks, dict) or not tracks:
            raise ValueError("compiled section must name its authored fragment inputs")
        for fragment in tracks.values():
            if (
                not isinstance(fragment, str)
                or not fragment.startswith("manuscript/sections/")
                or ".." in Path(fragment).parts
            ):
                raise ValueError("compiled fragment is outside the authored sections")
            if prefix + fragment not in tracked:
                raise ValueError("compiled fragment must be tracked Source")
            _regular(root, prefix + fragment)
        target = prefix + "manuscript/" + name
        if target not in tracked or target in targets:
            raise ValueError("compiled target must be unique and already tracked")
        targets.append(target)
    return targets


# One reviewed semantic dependency: these producers consume live COUNTS/version
# facts into Pitch DATA/decks. This is Source policy, never an operator list.
DEPENDENT_ANALYSIS_SCOPE = "templates/template_pitch_deck"
_DEPENDENT_INPUTS = (
    "docs/_generated/COUNTS.md",
    "pyproject.toml",
    "infrastructure/__init__.py",
    "projects/templates/template_pitch_deck/manuscript/config.yaml",
)
_DEPENDENT_PRODUCERS = (
    "scripts/pipeline/stage_02_analysis.py",
    "projects/templates/template_pitch_deck/scripts/16_generate_charts.py",
    "projects/templates/template_pitch_deck/scripts/20_render_decks.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/coverage_chart_data.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/deck_tokens.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/infra_facts.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/paths.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/render_orchestration.py",
    "projects/templates/template_pitch_deck/src/template_pitch_deck/standalone_slides.py",
)


def _dependent_analysis(root: Path, tracked: dict[str, dict[str, str]], mode: str) -> dict[str, dict[str, Any]]:
    """Bind the finite reviewed consumer without changing generated ownership."""
    if mode == "rebind-only":
        return {}
    if DEPENDENT_ANALYSIS_SCOPE not in PUBLIC_PROJECT_NAMES:
        raise ValueError("dependent analysis must belong to the canonical public roster")

    def bindings(paths: tuple[str, ...]) -> list[dict[str, Any]]:
        result = []
        for relative in paths:
            record = tracked.get(relative)
            if record is None or record["kind"] != "blob" or record["mode"] not in {"100644", "100755"}:
                raise ValueError("dependent analysis requires its tracked Source input/producer: " + relative)
            body = read_bytes_confined(root, root / relative, max_bytes=256 * 1024 * 1024)
            if not stat.S_ISREG((root / relative).stat(follow_symlinks=False).st_mode):
                raise ValueError("dependent analysis Source must remain a regular file")
            result.append({"path": relative, **record, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
        return result

    config = yaml.safe_load(_regular(root, "projects/" + DEPENDENT_ANALYSIS_SCOPE + "/manuscript/config.yaml"))
    deck = config.get("project_config", {}).get("deck", {}) if isinstance(config, dict) else {}
    subject = deck.get("pitch_subject", "template_template") if isinstance(deck, dict) else None
    if not isinstance(subject, str) or "templates/" + subject not in PUBLIC_PROJECT_NAMES:
        raise ValueError("dependent Pitch subject must be one declared canonical public project")
    inputs = (*_DEPENDENT_INPUTS, "projects/templates/" + subject + "/manuscript/config.yaml")
    input_bindings = bindings(tuple(dict.fromkeys(inputs)))
    producer_bindings = bindings(_DEPENDENT_PRODUCERS)
    from infrastructure.core.script_discovery import discover_analysis_scripts

    scripts = tuple(
        path.relative_to(root).as_posix() for path in discover_analysis_scripts(root, DEPENDENT_ANALYSIS_SCOPE)
    )
    charts, decks = _DEPENDENT_PRODUCERS[1:3]
    if charts not in scripts or decks not in scripts or scripts.index(charts) >= scripts.index(decks):
        raise ValueError("dependent Pitch Stage 02 must select its charts before its deck producer")
    return {
        DEPENDENT_ANALYSIS_SCOPE: {
            "inputs": input_bindings,
            "producers": producer_bindings,
            "analysis_scripts": bindings(scripts),
            "stage": "scripts/pipeline/stage_02_analysis.py",
        }
    }


def _inventory_plan(root: Path, source_sha: str, version: str, mode: str = "refresh") -> dict[str, Any]:
    root = root.absolute()
    if mode not in REFRESH_MODES:
        raise ValueError("unknown publication refresh mode")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("publication refresh requires the exact dispatched Source SHA")
    if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("publication refresh needs its actual Git root")
    if root_package_version(root) != version:
        raise ValueError("requested release version differs from current Source metadata")
    tracked = {}
    for raw in git(root, "ls-tree", "-rz", "--full-tree", source_sha).split(b"\0"):
        if raw:
            header, encoded_path = raw.split(b"\t", 1)
            blob_mode, kind, oid = header.decode().split()
            tracked[encoded_path.decode()] = {"mode": blob_mode, "kind": kind, "blob": oid}
    allowed = {}
    refresh = list(PUBLIC_PROJECT_NAMES) if mode == "refresh" else []
    publication_copies = []
    dependent_analysis = _dependent_analysis(root, tracked, mode)
    compiled_manuscripts: list[str] = []
    artifact_manifests = {}
    for scope in PUBLIC_PROJECT_NAMES:
        prefix = f"projects/{scope}/"
        config = prefix + "output/manuscript/config.yaml"
        if mode == "refresh" and config in tracked:
            publication_copies.append(scope)
        manifest = prefix + "output/reports/artifact_manifest.json"
        if mode == "refresh" and manifest in tracked:
            artifact_manifests[scope] = {"path": manifest, "blob": tracked[manifest]["blob"]}
        compiled = set(_compiled(root, scope, tracked)) if mode == "refresh" else set()
        compiled_manuscripts.extend(compiled)
        for path, record in tracked.items():
            owned = path.startswith(prefix + "output/") or path in compiled
            if mode == "rebind-only":
                owned = re.fullmatch(re.escape(prefix) + r"output/reports/[A-Za-z0-9_.-]+\.json", path) is not None
            if owned:
                if record["mode"] != "100644" or record["kind"] != "blob":
                    raise ValueError(f"canonical generated evidence must be a tracked regular file: {path}")
                allowed[path] = record
    if not allowed:
        raise ValueError("canonical tracked publication output inventory is missing")
    graph = current_provider_graph(root)
    return {
        "schema_version": SCHEMA,
        "role": "publication-refresh-preparation-only",
        "mode": mode,
        "compiled_manuscripts": sorted(compiled_manuscripts),
        "dependent_analysis": dependent_analysis,
        "publication_copies": publication_copies,
        "artifact_manifests": artifact_manifests,
        "base_commit": source_sha,
        "base_tree": git(root, "rev-parse", source_sha + "^{tree}").decode().strip(),
        "platform_version": version,
        "public_roster": list(PUBLIC_PROJECT_NAMES),
        "providers": graph,
        "refresh": refresh,
        "rebind": [scope for scope in PUBLIC_PROJECT_NAMES if scope not in refresh],
        "allowed": allowed,
    }


def build_plan(root: Path, source_sha: str, version: str, *, mode: str = "refresh") -> dict[str, Any]:
    """Bind a clean exact Source and finite canonical generated-path inventory."""
    if git(root, "rev-parse", "HEAD").decode().strip() != source_sha or git(
        root, "status", "--porcelain", "--untracked-files=all"
    ):
        raise ValueError("publication refresh requires a clean exact dispatched Source")
    plan = _inventory_plan(root, source_sha, version, mode)
    for path in plan["allowed"]:
        _regular(root, path)
    return plan


def load_plan(directory: Path, *, mode: str | None = None) -> dict[str, Any]:
    plan = json.loads((directory / "plan.json").read_bytes())
    if (
        not isinstance(plan, dict)
        or plan.get("schema_version") != SCHEMA
        or plan.get("public_roster") != list(PUBLIC_PROJECT_NAMES)
        or plan.get("mode") not in REFRESH_MODES
    ):
        raise ValueError("unknown refresh plan or canonical roster")
    if mode is not None and plan["mode"] != mode:
        raise ValueError("refresh plan mode differs from the dispatched mode")
    return plan


def _artifact_inventory(
    root: Path,
    plan: dict[str, Any],
    path: str,
    cache: dict[str, tuple[set[str], set[str]]],
) -> tuple[set[str], set[str]] | None:
    """Bind a finite output transition to frozen and current canonical manifests."""
    for scope, binding in plan["artifact_manifests"].items():
        prefix = f"projects/{scope}/"
        if not path.startswith(prefix + "output/"):
            continue
        if scope not in cache:
            before = artifact_manifest_from_payload(json.loads(git(root, "cat-file", "blob", binding["blob"])))
            after = artifact_manifest_from_payload(json.loads(_regular(root, binding["path"])))
            for manifest, project in ((before, None), (after, root / "projects" / scope)):
                result = validate_artifact_manifest(
                    manifest,
                    project_dir=project,
                    expected_inventory_mode=STABLE_OUTPUT_INVENTORY_MODE,
                )
                if not result.valid or any(not entry.path.startswith("output/") for entry in manifest.entries):
                    raise ValueError("canonical artifact inventory is invalid: " + "; ".join(result.issues[:8]))
            cache[scope] = (
                {prefix + entry.path for entry in before.entries} & plan["allowed"].keys(),
                {prefix + entry.path for entry in after.entries},
            )
        return cache[scope]
    return None


def _check_changed_paths(
    root: Path,
    plan: dict[str, Any],
    paths: list[str],
    cache: dict[str, tuple[set[str], set[str]]],
) -> None:
    for path in paths:
        record = plan["allowed"].get(path)
        if record is None:
            inventory = _artifact_inventory(root, plan, path, cache)
            if inventory is None or path not in inventory[1]:
                raise ValueError(f"path is outside declared generated ownership: {path}")
        try:
            (root / path).lstat()
        except FileNotFoundError:
            inventory = _artifact_inventory(root, plan, path, cache)
            if record is None or inventory is None or path not in inventory[0] or path in inventory[1]:
                raise ValueError(f"generated removal is outside canonical artifact inventory: {path}") from None
        else:
            _regular(root, path)
            if record is not None and git(root, "ls-files", "-s", "--", path).split(b" ", 1)[0] != b"100644":
                raise ValueError("refresh path changed index mode")


def check_footprint(root: Path, plan: dict[str, Any]) -> list[str]:
    """Admit only regular generated updates and manifested output transitions."""
    if plan != _inventory_plan(root, plan["base_commit"], plan["platform_version"], plan["mode"]):
        raise ValueError("refresh plan differs from current Source ownership")
    if git(root, "rev-parse", "HEAD").decode().strip() != plan["base_commit"] or git(
        root, "diff", "--cached", "--name-only"
    ):
        raise ValueError("refresh Source or index moved before candidate capture")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    cache: dict[str, tuple[set[str], set[str]]] = {}
    additions = []
    labels = []
    for encoded in untracked.split(b"\0"):
        if not encoded:
            continue
        path = encoded.decode()
        inventory = _artifact_inventory(root, plan, path, cache)
        if inventory is not None and path in inventory[1]:
            additions.append(path)
        else:
            labels.append(encoded)
    if labels:
        details = {
            "count": len(labels),
            "paths": [label[:256].decode("utf-8", errors="backslashreplace") for label in labels[:16]],
            "path_bytes_clipped": any(len(label) > 256 for label in labels[:16]),
            "paths_omitted": max(0, len(labels) - 16),
            "nul_listing_sha256": hashlib.sha256(untracked).hexdigest(),
        }
        raise ValueError(
            "unexpected untracked path prevents complete refresh capture: "
            + json.dumps(details, ensure_ascii=True, sort_keys=True)
        )
    changed = sorted(
        {p.decode() for p in git(root, "diff", "--name-only", "-z", plan["base_commit"]).split(b"\0") if p}
        | set(additions)
    )
    _check_changed_paths(root, plan, changed, cache)
    return changed


def commit_candidate(root: Path, directory: Path) -> dict[str, str]:
    """Commit only the admitted footprint in the disposable hosted checkout."""
    plan = load_plan(directory)
    paths = check_footprint(root, plan)
    if paths:
        pathspec = directory / "candidate-paths.nul"
        pathspec.write_bytes(b"\0".join(p.encode() for p in paths) + b"\0")
        git(root, "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul")
    git(
        root,
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit",
        "--allow-empty",
        "-m",
        "chore(evidence): refresh canonical publication outputs",
    )
    result = {
        "commit": git(root, "rev-parse", "HEAD").decode().strip(),
        "tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
    }
    write_json(directory / "candidate.json", result)
    return result


def finish_review(root: Path, directory: Path) -> Path:
    """Retain the exact patch only after all three original committed-tree gates."""
    plan = load_plan(directory)
    candidate = json.loads((directory / "candidate.json").read_bytes())
    if plan != _inventory_plan(root, plan["base_commit"], plan["platform_version"], plan["mode"]):
        raise ValueError("refresh plan differs from committed Source ownership")
    if (
        git(root, "rev-parse", "HEAD").decode().strip() != candidate["commit"]
        or git(root, "rev-parse", "HEAD^{tree}").decode().strip() != candidate["tree"]
        or git(root, "rev-parse", "HEAD^").decode().strip() != plan["base_commit"]
        or git(root, "status", "--porcelain", "--untracked-files=all")
    ):
        raise ValueError("committed candidate changed during verification")
    for label, arguments in gate_commands(root, directory).items():
        if not successful_command_receipt(directory, label, arguments, candidate["commit"]):
            raise ValueError("all original gates must succeed on the committed candidate")
    for label, arguments in generation_commands(root, plan, plan["public_roster"]):
        if not successful_command_receipt(directory, label, arguments, plan["base_commit"]):
            raise ValueError("every canonical generation requires its actual successful original commands")
    changes = []
    paths = [
        p.decode()
        for p in git(root, "diff", "--no-renames", "--name-only", "-z", plan["base_commit"], "HEAD").split(b"\0")
        if p
    ]
    _check_changed_paths(root, plan, paths, {})
    for path in paths:
        before = plan["allowed"].get(path)
        after = git(root, "ls-tree", "HEAD", "--", path)
        body = _regular(root, path) if after else None
        oid = None
        if after:
            mode, kind, oid = after.split(b"\t")[0].decode().split()
            if mode != "100644" or kind != "blob":
                raise ValueError("candidate evidence mode changed")
        changes.append(
            {
                "path": path,
                "change": "A" if before is None else "M" if after else "D",
                "before_blob": before["blob"] if before is not None else None,
                "after_blob": oid,
                "mode": "100644",
                "sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
                "bytes": len(body) if body is not None else None,
            }
        )
    review = directory / "review"
    review.mkdir()
    (review / "refresh.patch").write_bytes(
        git(root, "diff", "--no-renames", "--binary", "--full-index", plan["base_commit"], "HEAD")
    )
    write_json(review / "manifest.json", {"plan": plan, "candidate": candidate, "changes": changes})
    if any(path.is_symlink() for path in (directory / "diagnostics").rglob("*")):
        raise ValueError("refresh diagnostics must not contain symlinks")
    shutil.copytree(directory / "diagnostics", review / "receipts", symlinks=False)
    write_json(review / "COMPLETE.json", {"role": plan["role"], "all_committed_tree_gates_passed": True})
    sums = []
    for artifact in sorted(review.rglob("*")):
        if artifact.is_file():
            sums.append(
                hashlib.sha256(artifact.read_bytes()).hexdigest() + "  " + artifact.relative_to(review).as_posix()
            )
    (review / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return review


__all__ = [
    "REFRESH_MODES",
    "build_plan",
    "check_footprint",
    "commit_candidate",
    "finish_review",
    "gate_commands",
    "git",
    "load_plan",
    "write_json",
]
