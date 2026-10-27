#!/usr/bin/env bash
# Validate the actual selected Python and bundled portable implementation.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${TEMPLATE_PYTHON:-python3}" -I -c '
import os, pathlib, select, sys
root=pathlib.Path(sys.argv[1])
manifest=(root/"tools.yaml").read_text()
checks={"Python >=3.14":sys.version_info >= (3,14),
 "POSIX exit watcher":os.name=="posix" and (hasattr(os,"pidfd_open") or hasattr(select,"kqueue")),
 "manifest type/entrypoints":manifest.startswith("type: code_executor\n") and "entrypoints:" in manifest,
 "run.sh executable":os.access(root/"scripts/run.sh",os.X_OK),
 "bundled supervisor":all((root/"src"/name).is_file() for name in ("code_executor.py","process_cleanup.py"))}
for label,passed in checks.items():print(("[OK] " if passed else "[FAIL] ")+label)
raise SystemExit(0 if all(checks.values()) else 1)
' "${SCRIPT_DIR}/.."
