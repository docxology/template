"""Pinned Docker execution for a fixed classifier with one numeric mutation."""

from __future__ import annotations

import csv
import json
import re
import shutil
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from infrastructure.core.subprocess_policy import BoundedSubprocessResult, SubprocessPolicy, run_with_policy

from .proposal_domain import LiveCapabilityBlocked, LiveProposalFailed
from .proposal_watchdog import CONTAINER_BOOTSTRAP, ControllerHeartbeat

SOURCE_PATH = "projects/templates/template_sia/src/template_sia/loop/proposal_sandbox.py"
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


def command(argv: list[str], cwd: Path, timeout: int = 15) -> BoundedSubprocessResult:
    """Run every child under the shared credential-free process-group boundary."""
    return run_with_policy(
        argv,
        cwd=cwd,
        env=None,
        policy=SubprocessPolicy(
            policy_id="sia-proposal-sandbox",
            source_path=SOURCE_PATH,
            timeout_seconds=timeout,
            capture_output=True,
            credential_free=True,
        ),
    )


def require_docker_image(image_id: str, cwd: Path, *, executable: str = "docker", timeout: int = 15) -> str:
    """Require an existing daemon and immutable local image; never pull an image."""
    if not image_id:
        raise LiveCapabilityBlocked("a pinned local Docker image id is required")
    if not _IMAGE_ID.fullmatch(image_id):
        raise ValueError("container image must be an immutable sha256:<64 hex> local image id")
    docker = shutil.which(executable)
    if docker is None:
        raise LiveCapabilityBlocked("Docker CLI is unavailable")
    daemon = command([docker, "version", "--format", "{{.Server.Version}}"], cwd, timeout)
    if daemon.returncode or daemon.timed_out:
        raise LiveCapabilityBlocked("Docker daemon is unavailable")
    image = command([docker, "image", "inspect", "--format", "{{.Id}}", image_id], cwd, timeout)
    if image.returncode or image.stdout.strip() != image_id:
        raise LiveCapabilityBlocked("the pinned Docker image is not available locally")
    return docker


def container_argv(docker: str, image_id: str, sandbox: Path, name: str, timeout: int = 60) -> list[str]:
    """Mount only the fixed target, unlabeled features, and disposable predictions."""
    return [
        docker,
        "run",
        "--pull=never",
        "--rm",
        "--name",
        name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65534:65534",
        "--pids-limit",
        "32",
        "--memory",
        "128m",
        "--cpus",
        "1",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16m",  # nosec B108: isolated bounded container tmpfs, never host /tmp.
        "--entrypoint",
        "python",
        "--mount",
        f"type=bind,source={sandbox / 'program'},destination=/program,readonly",
        "--mount",
        f"type=bind,source={sandbox / 'data'},destination=/data,readonly",
        "--mount",
        f"type=bind,source={sandbox / 'working'},destination=/working",
        image_id,
        "-I",
        "-c",
        CONTAINER_BOOTSTRAP,
        str(timeout),
    ]


def run_target(
    docker: str,
    image_id: str,
    source: str,
    rows: tuple[dict[str, str], ...],
    output_dir: Path,
    timeout: int,
) -> Path:
    """Run fixed-source classifier without labels or credentials and always remove its container."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError("target timeout must be in [1,60] seconds")
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f"template-sia-{uuid.uuid4().hex}"
    with TemporaryDirectory(prefix="template-sia-container-") as temp:
        sandbox = Path(temp)
        (sandbox / "program").mkdir(mode=0o755)
        (sandbox / "data").mkdir()
        (sandbox / "working").mkdir()
        (sandbox / "working").chmod(0o777)
        (sandbox / "program/target.py").write_text(source, encoding="utf-8")
        with (sandbox / "data/train.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "feature_0"])
            writer.writeheader()
            writer.writerows({key: row[key] for key in ("id", "feature_0")} for row in rows)
        heartbeat = ControllerHeartbeat(sandbox / "program")
        argv = container_argv(docker, image_id, sandbox, name, timeout)
        receipt: dict[str, object] = {
            "runner": "docker",
            "image_id": image_id,
            "container_name": name,
            "sandbox_root": str(sandbox),
            "status": "launching",
            "container_deadline_sec": timeout,
            "controller_heartbeat_grace_sec": 2,
            "cleanup_verified": False,
        }
        (output_dir / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        heartbeat.start()
        try:
            result = command(argv, sandbox, timeout)
            receipt.update(
                {
                    "runner": "docker",
                    "image_id": image_id,
                    "network": "none",
                    "read_only_root": True,
                    "host_credentials_forwarded": False,
                    "returncode": result.returncode,
                    "timed_out": result.timed_out or result.returncode == 124,
                    "controller_heartbeat_lost": result.returncode == 125,
                    "status": "passed" if not result.returncode and not result.timed_out else "failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "limits": {"cpus": 1, "memory_bytes": 134217728, "pids": 32, "target_timeout_sec": timeout},
                }
            )
            (output_dir / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            if result.returncode or result.timed_out:
                raise LiveProposalFailed("Docker target failed; execution.json preserves its diagnostics")
            predictions = sandbox / "working/predictions.csv"
            if not predictions.is_file() or predictions.is_symlink() or predictions.stat().st_size > 65536:
                raise LiveProposalFailed("Docker target did not produce bounded regular predictions")
            destination = output_dir / "predictions.csv"
            shutil.copyfile(predictions, destination)
            return destination
        finally:
            heartbeat.stop()
            removed = command([docker, "rm", "--force", name], sandbox)
            # A completed --rm container is already absent; require positively verified absence.
            if removed.returncode:
                exists = command([docker, "container", "inspect", name], sandbox)
                if exists.returncode == 0:
                    raise LiveProposalFailed("Docker cleanup failed; named container remains")
                if "No such object" not in exists.stderr and "No such container" not in exists.stderr:
                    raise LiveProposalFailed("Docker cleanup could not verify container absence")
            receipt["cleanup_verified"] = True
            (output_dir / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
