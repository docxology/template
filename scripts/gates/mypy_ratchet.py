#!/usr/bin/env python3
"""Run mypy with per-package debt ceilings and closed file allowlists."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ERROR_RE = re.compile(r"^(?P<path>infrastructure/(?P<package>[^/]+)/[^:]+):\d+: error:")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["infrastructure"])
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(__file__).with_name("mypy_debt_baseline.json"),
    )
    args = parser.parse_args(argv)
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    packages = baseline.get("packages", {})

    proc = subprocess.run(
        [sys.executable, "-m", "mypy", *args.paths],
        check=False,
        capture_output=True,
        text=True,
    )
    combined = proc.stdout + proc.stderr
    counts: dict[str, int] = {}
    files: dict[str, set[str]] = {}
    unratcheted: list[str] = []
    for line in combined.splitlines():
        match = ERROR_RE.match(line)
        if not match:
            continue
        package = match.group("package")
        path = match.group("path")
        if package not in packages:
            unratcheted.append(line)
            continue
        counts[package] = counts.get(package, 0) + 1
        files.setdefault(package, set()).add(path)

    findings: list[str] = []
    if unratcheted:
        findings.append(f"{len(unratcheted)} mypy error(s) outside ratcheted packages")
    for package, policy in packages.items():
        current = counts.get(package, 0)
        ceiling = int(policy["max_errors"])
        allowed_files = set(policy["allowed_files"])
        new_files = sorted(files.get(package, set()) - allowed_files)
        if current > ceiling:
            findings.append(f"infrastructure.{package}: {current} errors exceeds ceiling {ceiling}")
        if new_files:
            findings.append(f"infrastructure.{package}: errors appeared in new files: {', '.join(new_files)}")

    if proc.returncode not in (0, 1):
        findings.append(f"mypy execution failed with exit code {proc.returncode}")
    if findings:
        print("mypy ratchet failed:")
        for finding in findings:
            print(f"  {finding}")
        if unratcheted:
            print("\n".join(unratcheted[:20]))
        return 1

    debt = ", ".join(f"{name}={counts.get(name, 0)}/{policy['max_errors']}" for name, policy in packages.items())
    print(f"mypy ratchet passed ({debt})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
