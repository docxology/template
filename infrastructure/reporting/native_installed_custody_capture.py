"""Observe the real cold installed SDK against its separately admitted wheel.

This produces DATA under the parent-held Source installation nomination; it
creates no NativeSourceContext or original completion capability. The parent
owns the true process result and validates retained Code before forwarding it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.implementation_custody import capture_implementation_custody, verify_implementation_custody
from infrastructure.project.installed_acceptance_artifacts import inspect_wheel_bytes
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--core-wheel", required=True, type=Path)
    parser.add_argument("--core-wheel-sha256", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--deadline", required=True, type=float)
    args = parser.parse_args(argv)
    remaining(args.deadline)
    raw = read_bytes_confined(args.core_wheel.parent, args.core_wheel, max_bytes=64 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != args.core_wheel_sha256:
        raise ValueError("cold SDK input differs from the parent's actual Source-admitted wheel")
    reader = SnapshotReader(args.root)
    requirement = Requirement(
        "root:installed", "installed", "root", "4.0.1", "", "", package="research-project-template"
    )
    targets, members = inspect_wheel_bytes(args.root, requirement, raw, reader=reader)
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix else None
    if prefix is None or targets != ("infrastructure",):
        raise ValueError("cold SDK capture requires its real fresh audited installed provider")
    value = capture_implementation_custody(fresh_pycache_prefix=prefix)
    expected = {
        name: digest for name, digest in members.items() if name.startswith("infrastructure/") and name.endswith(".py")
    }
    if (
        value["binding_kind"] != "installed-distribution"
        or value["distribution"]["version"] != "4.0.1"
        or value["files"] != expected
    ):
        raise ValueError("cold installed SDK metadata/RECORD/body differs from actual admitted Source4.0.1")
    verify_implementation_custody(value, fresh_pycache_prefix=prefix)
    if not reader.unchanged():
        raise ValueError("cold SDK capture Source changed")
    destination = reader.public_path(args.destination.relative_to(args.root).as_posix())
    atomic_write_bytes_confined(
        args.root, destination, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(), mode=0o600
    )
    verify_implementation_custody(value, fresh_pycache_prefix=prefix)
    remaining(args.deadline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
