"""Install and audit pinned Agent Skills across Codex, Claude Code, and Hermes.

The tracked ``.agents/skills`` tree is the reviewed source. Installation copies
that tree into a revisioned user data directory, then creates reversible
per-skill links in each runtime's native user skill root. Existing paths are
moved to a timestamped backup before links are created; upstream scripts are
never executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

from .discovery import split_yaml_frontmatter

__all__ = [
    "compute_skill_tree_digest",
    "install_runtime_skills",
    "load_source_lock",
    "main",
    "runtime_status",
    "validate_vendored_source",
]

LOCK_PATH = Path(".agents/context-engineering.lock.json")
SOURCE_PATH = Path(".agents/skills")
RUNTIME_ROOTS: tuple[tuple[str, Path], ...] = (
    ("codex", Path(".agents/skills")),
    ("claude", Path(".claude/skills")),
    ("hermes", Path(".hermes/skills")),
)


def _skill_directories(source_root: Path) -> list[Path]:
    """Return immediate child directories that contain a ``SKILL.md``."""
    if not source_root.is_dir():
        return []
    return sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and not path.is_symlink() and (path / "SKILL.md").is_file()
    )


def _iter_tree_files(source_root: Path, skill_dirs: Iterable[Path]) -> Iterable[Path]:
    for skill_dir in skill_dirs:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"vendored skill tree contains a symlink: {path}")
            if path.is_file():
                yield path


def compute_skill_tree_digest(source_root: Path) -> tuple[str, int]:
    """Hash every file in skill directories using path-NUL-content-NUL framing."""
    root = source_root.resolve()
    digest = hashlib.sha256()
    count = 0
    for path in _iter_tree_files(root, _skill_directories(root)):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
        count += 1
    return digest.hexdigest(), count


def load_source_lock(repo_root: Path) -> dict[str, Any]:
    """Load and minimally validate the tracked upstream source lock."""
    path = repo_root.resolve() / LOCK_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "source_url",
        "revision",
        "plugin_version",
        "license",
        "skill_count",
        "file_count",
        "vendored_tree_sha256",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        missing = sorted(required - set(data if isinstance(data, dict) else {}))
        raise ValueError(f"invalid context-engineering source lock; missing: {missing}")
    if data["schema_version"] != 1:
        raise ValueError(f"unsupported context-engineering lock schema: {data['schema_version']}")
    revision = data["revision"]
    digest = data["vendored_tree_sha256"]
    if not isinstance(revision, str) or len(revision) != 40:
        raise ValueError("lock revision must be a 40-character Git commit")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("lock vendored_tree_sha256 must be a SHA-256 hex digest")
    return data


def validate_vendored_source(repo_root: Path) -> dict[str, Any]:
    """Validate the pinned tree, inventory, frontmatter, and content digest."""
    root = repo_root.resolve()
    source_root = root / SOURCE_PATH
    lock = load_source_lock(root)
    issues: list[str] = []
    skill_dirs = _skill_directories(source_root)
    names: list[str] = []
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        frontmatter, body = split_yaml_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not isinstance(frontmatter, dict):
            issues.append(f"{skill_file}: invalid YAML frontmatter")
            continue
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if name != skill_dir.name:
            issues.append(f"{skill_file}: name {name!r} does not match directory {skill_dir.name!r}")
        if not isinstance(description, str) or not description.strip():
            issues.append(f"{skill_file}: description must be a non-empty string")
        if not body.strip():
            issues.append(f"{skill_file}: body is empty")
        if isinstance(name, str):
            names.append(name)
    if len(names) != len(set(names)):
        issues.append("vendored skill names are not unique")
    digest, file_count = compute_skill_tree_digest(source_root)
    if len(skill_dirs) != lock["skill_count"]:
        issues.append(f"skill count mismatch: lock={lock['skill_count']} tree={len(skill_dirs)}")
    if file_count != lock["file_count"]:
        issues.append(f"file count mismatch: lock={lock['file_count']} tree={file_count}")
    if digest != lock["vendored_tree_sha256"]:
        issues.append("vendored skill tree digest does not match the source lock")
    return {
        "ok": not issues,
        "issues": issues,
        "source_root": str(source_root),
        "revision": lock["revision"],
        "plugin_version": lock["plugin_version"],
        "skill_count": len(skill_dirs),
        "file_count": file_count,
        "tree_sha256": digest,
        "skill_names": sorted(names),
    }


def _shared_paths(home: Path, revision: str, tree_digest: str) -> tuple[Path, Path, Path]:
    base = home / ".local/share/template-agent-skills/context-engineering"
    release = f"{revision}-{tree_digest[:12]}"
    revision_skills = base / "revisions" / release / "skills"
    current = base / "current"
    return base, revision_skills, current


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _link_matches(path: Path, expected_target: Path) -> bool:
    if not path.is_symlink():
        return False
    try:
        return path.resolve(strict=True) == expected_target.resolve(strict=True)
    except OSError:
        return False


def _atomic_symlink(target: Path, link: Path) -> None:
    temp = link.with_name(f".{link.name}.template-sync-{uuid.uuid4().hex}")
    os.symlink(str(target), str(temp), target_is_directory=True)
    try:
        os.replace(temp, link)
    finally:
        if _lexists(temp):
            temp.unlink()


def _stage_revision(source_root: Path, revision_skills: Path, expected_digest: str) -> None:
    if revision_skills.is_dir():
        digest, _ = compute_skill_tree_digest(revision_skills)
        if digest != expected_digest:
            raise RuntimeError(f"existing shared revision has unexpected content: {revision_skills}")
        return
    revision_root = revision_skills.parent
    revision_root.parent.mkdir(parents=True, exist_ok=True)
    staging = revision_root.parent / f".{revision_root.name}.staging-{uuid.uuid4().hex}"
    staging_skills = staging / "skills"
    staging_skills.mkdir(parents=True)
    try:
        for skill_dir in _skill_directories(source_root):
            shutil.copytree(skill_dir, staging_skills / skill_dir.name, symlinks=False)
        digest, _ = compute_skill_tree_digest(staging_skills)
        if digest != expected_digest:
            raise RuntimeError("staged shared copy does not match the tracked source lock")
        os.replace(staging, revision_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _backup_existing(path: Path, backup_root: Path) -> Path:
    backup = backup_root / path.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    if _lexists(backup):
        backup = backup.with_name(f"{backup.name}-{uuid.uuid4().hex[:8]}")
    shutil.move(str(path), str(backup))
    return backup


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _ensure_hermes_trusted_root(config_path: Path, target: Path, backup_root: Path) -> dict[str, Any]:
    """Append the shared root to Hermes external dirs using an atomic YAML write."""
    data: dict[str, Any] = {}
    if config_path.is_file():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if loaded is not None and not isinstance(loaded, dict):
            raise ValueError(f"Hermes config root must be a mapping: {config_path}")
        data = loaded or {}
    skills = data.setdefault("skills", {})
    if not isinstance(skills, dict):
        raise ValueError(f"Hermes skills config must be a mapping: {config_path}")
    raw_dirs = skills.get("external_dirs") or []
    if isinstance(raw_dirs, str):
        raw_dirs = [raw_dirs]
    if not isinstance(raw_dirs, list):
        raise ValueError(f"Hermes skills.external_dirs must be a list: {config_path}")
    target_text = str(target)
    if target_text in raw_dirs:
        return {"action": "unchanged", "config": str(config_path), "trusted_root": target_text}
    if config_path.is_file():
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, backup_root / "hermes-config.yaml")
    raw_dirs.append(target_text)
    skills["external_dirs"] = raw_dirs
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temp = config_path.with_name(f".{config_path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(temp, config_path)
    return {"action": "configured", "config": str(config_path), "trusted_root": target_text}


def _hermes_trust_status(config_path: Path, target: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        skills = data.get("skills") if isinstance(data, dict) else None
        raw_dirs = skills.get("external_dirs") if isinstance(skills, dict) else []
        if isinstance(raw_dirs, str):
            raw_dirs = [raw_dirs]
        trusted = str(target) in raw_dirs if isinstance(raw_dirs, list) else False
        return {"ok": trusted, "config": str(config_path), "trusted_root": str(target)}
    except (OSError, yaml.YAMLError):
        return {"ok": False, "config": str(config_path), "trusted_root": str(target)}


def install_runtime_skills(repo_root: Path, home: Path) -> dict[str, Any]:
    """Install the pinned tree and link all three runtime skill roots.

    Any existing managed-name path is moved to a timestamped backup first.
    Calling the function repeatedly is idempotent when links already match.
    """
    root = repo_root.resolve()
    user_home = home.expanduser().resolve()
    source = validate_vendored_source(root)
    if not source["ok"]:
        raise RuntimeError("vendored source validation failed: " + "; ".join(source["issues"]))
    lock = load_source_lock(root)
    source_root = root / SOURCE_PATH
    base, revision_skills, current = _shared_paths(
        user_home,
        lock["revision"],
        lock["vendored_tree_sha256"],
    )
    _stage_revision(source_root, revision_skills, lock["vendored_tree_sha256"])
    base.mkdir(parents=True, exist_ok=True)
    if not _link_matches(current, revision_skills):
        if _lexists(current):
            if current.is_symlink() or current.is_file():
                current.unlink()
            else:
                shutil.rmtree(current)
        _atomic_symlink(revision_skills, current)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_base = user_home / ".local/state/template-agent-skills/backups" / timestamp
    actions: list[dict[str, str]] = []
    for runtime, relative_root in RUNTIME_ROOTS:
        runtime_root = user_home / relative_root
        runtime_root.mkdir(parents=True, exist_ok=True)
        for name in source["skill_names"]:
            destination = runtime_root / name
            target = current / name
            if _link_matches(destination, target):
                actions.append({"runtime": runtime, "skill": name, "action": "unchanged"})
                continue
            backup = None
            if _lexists(destination):
                backup = _backup_existing(destination, backup_base / runtime)
            _atomic_symlink(target, destination)
            row = {"runtime": runtime, "skill": name, "action": "linked"}
            if backup is not None:
                row["backup"] = str(backup)
            actions.append(row)

    hermes_trust = _ensure_hermes_trusted_root(
        user_home / ".hermes/config.yaml",
        current,
        backup_base / "hermes-config",
    )

    receipt = {
        "schema_version": 1,
        "source_url": lock["source_url"],
        "revision": lock["revision"],
        "plugin_version": lock["plugin_version"],
        "shared_skills": str(revision_skills),
        "current": str(current),
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "actions": actions,
        "hermes_trust": hermes_trust,
    }
    state_root = user_home / ".local/state/template-agent-skills"
    receipt_path = state_root / "receipts" / f"{timestamp}-{uuid.uuid4().hex}.json"
    state_path = state_root / "context-engineering.json"
    receipt["receipt_path"] = str(receipt_path)
    receipt["state_path"] = str(state_path)
    _atomic_write_json(receipt_path, receipt)
    _atomic_write_json(state_path, receipt)
    return receipt


def runtime_status(repo_root: Path, home: Path) -> dict[str, Any]:
    """Return offline source and three-runtime parity status."""
    root = repo_root.resolve()
    user_home = home.expanduser().resolve()
    source = validate_vendored_source(root)
    result: dict[str, Any] = {"source": source, "runtimes": {}, "ok": False}
    if not source["ok"]:
        return result
    lock = load_source_lock(root)
    _, revision_skills, current = _shared_paths(
        user_home,
        lock["revision"],
        lock["vendored_tree_sha256"],
    )
    shared_ok = revision_skills.is_dir() and _link_matches(current, revision_skills)
    result["shared_store"] = {
        "ok": shared_ok,
        "revision_skills": str(revision_skills),
        "current": str(current),
    }
    hermes_trust = _hermes_trust_status(user_home / ".hermes/config.yaml", current)
    result["hermes_trust"] = hermes_trust
    all_ok = shared_ok and hermes_trust["ok"]
    for runtime, relative_root in RUNTIME_ROOTS:
        runtime_root = user_home / relative_root
        issues: list[str] = []
        for name in source["skill_names"]:
            destination = runtime_root / name
            expected = current / name
            if not _link_matches(destination, expected):
                issues.append(f"{name}: missing, stale, or not managed by runtime sync")
        runtime_row = {
            "ok": not issues,
            "root": str(runtime_root),
            "skill_count": len(source["skill_names"]) - len(issues),
            "expected_skill_count": len(source["skill_names"]),
            "issues": issues,
        }
        result["runtimes"][runtime] = runtime_row
        all_ok = all_ok and not issues
    result["ok"] = all_ok
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(child: argparse.ArgumentParser) -> None:
        """Add shared --repo-root, --home, and --json flags to a subparser."""
        child.add_argument("--repo-root", type=Path, default=Path("."))
        child.add_argument("--home", type=Path, default=Path.home())
        child.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    status_parser = sub.add_parser("status", help="Audit pinned source and runtime parity")
    add_common(status_parser)
    install_parser = sub.add_parser("install", help="Install reversible managed runtime links")
    add_common(install_parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the runtime parity status or reversible installer."""
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "install":
            payload = install_runtime_skills(args.repo_root, args.home)
            status = runtime_status(args.repo_root, args.home)
            payload = {"install": payload, "status": status}
        else:
            payload = runtime_status(args.repo_root, args.home)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"runtime skill sync failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        status = payload["status"] if args.command == "install" else payload
        verdict = "ok" if status["ok"] else "drift"
        print(f"context-engineering runtime parity: {verdict}")
        for runtime, row in status.get("runtimes", {}).items():
            print(f"  {runtime}: {row['skill_count']}/{row['expected_skill_count']}")
        if args.command == "install":
            print(f"  receipt: {payload['install']['receipt_path']}")
    status = payload["status"] if args.command == "install" else payload
    return 0 if status["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
