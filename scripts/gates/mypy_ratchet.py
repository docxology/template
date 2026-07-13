#!/usr/bin/env python3
"""Run mypy as a strict zero-debt blocking gate."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    paths = (argv if argv is not None else sys.argv[1:]) or ["infrastructure"]

    proc = subprocess.run(
        [sys.executable, "-m", "mypy", *paths],
        check=False,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        print("mypy strict gate failed: typing debt must remain at zero", file=sys.stderr)
        return proc.returncode
    print("mypy strict gate passed (0 errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
