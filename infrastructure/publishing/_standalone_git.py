"""Bounded standalone Git routing, commit/status and source-inventory reads."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES


_GIT_LOCAL_ENVIRONMENT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_GRAFT_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
        "GIT_PREFIX",
        "GIT_INTERNAL_SUPER_PREFIX",
        "GIT_SHALLOW_FILE",
        "GIT_NAMESPACE",
        "GIT_TEMPLATE_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_CURL_VERBOSE",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_EXEC_PATH",
    }
)


_PUBLIC_ROOTS = tuple(
    Path(f"{kind}/{name}")
    for kind, names in (
        ("projects", PUBLIC_PROJECT_NAMES),
        ("fonds", PUBLIC_FOND_NAMES),
        ("rules", PUBLIC_RULE_NAMES),
        ("tools", PUBLIC_TOOL_NAMES),
    )
    for name in names
)


def _git_environment() -> dict[str, str]:
    """Retain the original Git repository-selector and routing environment boundary."""
    # Keep normal global credential-helper configuration, while refusing
    # inherited repository/index selectors and command-level config injection.
    env = {
        name: value
        for name, value in build_bounded_env().items()
        if name not in _GIT_LOCAL_ENVIRONMENT
        and not name.startswith(("GIT_TRACE", "GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
    }
    # A replacement ref must never change the objects bound to a published SHA.
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    # Metadata reads must not optionally refresh the held Git index.
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = _git_environment()
    result = run_bounded_subprocess(
        ["git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        cwd=cwd,
        env=env,
        timeout=60,
    )
    proc = subprocess.CompletedProcess(args, result.returncode, result.stdout, result.stderr or result.command_error)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed in {cwd}: {proc.stderr.strip()}")
    return proc


def _git_head_status(cwd: Path, supplied: str | None = None) -> tuple[str, str | None, str]:
    """Run the original native commit/status reads under one bounded guardian.

    Git stdout/stderr stream directly into the existing bounded supervisor.
    No child output is accumulated in an unbounded intermediate buffer.
    """
    script = """
import os,signal,subprocess,sys
prefix='template-git-head-status-v1:'
commands=[('HEAD',['rev-parse','--verify','HEAD^{commit}'])]
if len(sys.argv)>1:
    commands.append(('LABEL',['rev-parse','--verify',sys.argv[1]+'^{commit}']))
commands.append(('STATUS',['status','--porcelain','--untracked-files=all']))
for label,args in commands:
    print(prefix+label,flush=True)
    try:
        result=subprocess.run(
            ['git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',*args],
            check=False,timeout=60,
        )
    except subprocess.TimeoutExpired:
        print('original native Git read exceeded its 60-second deadline',file=sys.stderr,flush=True)
        raise SystemExit(124)
    if result.returncode:
        print('original native Git return code: '+str(result.returncode),file=sys.stderr,flush=True)
        if result.returncode<0:
            signum=-result.returncode
            if signum!=signal.SIGKILL:
                signal.signal(signum,signal.SIG_DFL)
            os.kill(os.getpid(),signum)
            raise SystemExit(1)
        raise SystemExit(result.returncode)
print(prefix+'END',flush=True)
"""
    command = [sys.executable, "-I", "-S", "-c", script]
    if supplied is not None:
        command.append(supplied)
    result = run_bounded_subprocess(command, cwd=cwd, env=_git_environment(), timeout=60)
    if result.returncode != 0:
        raise RuntimeError(
            f"git HEAD/status read batch failed in {cwd}: {(result.stderr or result.command_error).strip()}"
        )
    prefix = "template-git-head-status-v1:"
    labels = ("HEAD", "LABEL", "STATUS", "END") if supplied is not None else ("HEAD", "STATUS", "END")
    output = result.stdout
    records: dict[str, str] = {}
    for index, label in enumerate(labels[:-1]):
        marker = prefix + label + "\n"
        if not output.startswith(marker):
            raise ValueError("native Git admission read framing is malformed")
        output = output[len(marker) :]
        next_marker = prefix + labels[index + 1] + "\n"
        if output.count(next_marker) != 1:
            raise ValueError("native Git admission read framing is ambiguous")
        records[label], output = output.split(next_marker, 1)
        output = next_marker + output
    if output != prefix + "END\n":
        raise ValueError("native Git admission read has trailing output")
    return (
        records["HEAD"].strip(),
        records.get("LABEL", "").strip() if supplied is not None else None,
        records["STATUS"],
    )


def _git_source_inventory(cwd: Path, revision: str) -> tuple[list[str], str]:
    """Read the same tracked paths and committed provider tree under one60s guardian."""
    commands = [
        ("TRACKED", ["ls-files", "-z", "--", "."]),
        (
            "TREE",
            [
                "ls-tree",
                "-r",
                "-z",
                revision,
                "--",
                *(root.as_posix() for root in _PUBLIC_ROOTS),
                "infrastructure",
                "pyproject.toml",
            ],
        ),
    ]
    script = """
import json,os,signal,subprocess,sys
prefix='template-git-source-inventory-v1:'
for label,args in json.loads(sys.argv[1]):
    print(prefix+label,flush=True)
    try:
        result=subprocess.run(
            ['git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',*args],
            check=False,timeout=60,
        )
    except subprocess.TimeoutExpired:
        print('original native Git read exceeded its 60-second deadline',file=sys.stderr,flush=True)
        raise SystemExit(124)
    if result.returncode:
        print('original native Git return code: '+str(result.returncode),file=sys.stderr,flush=True)
        if result.returncode<0:
            signum=-result.returncode
            if signum!=signal.SIGKILL:
                signal.signal(signum,signal.SIG_DFL)
            os.kill(os.getpid(),signum)
            raise SystemExit(1)
        raise SystemExit(result.returncode)
print(prefix+'END',flush=True)
"""
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-S", "-c", script, json.dumps(commands)],
        cwd=cwd,
        env=_git_environment(),
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git source inventory batch failed in {cwd}: {(result.stderr or result.command_error).strip()}"
        )
    prefix = "template-git-source-inventory-v1:"
    output = result.stdout
    records = {}
    for label, next_label in (("TRACKED", "TREE"), ("TREE", "END")):
        marker = prefix + label + "\n"
        following = prefix + next_label + "\n"
        if not output.startswith(marker) or output.count(following) != 1:
            raise ValueError("native Git source inventory framing is malformed or ambiguous")
        records[label], output = output[len(marker) :].split(following, 1)
        output = following + output
    if output != prefix + "END\n":
        raise ValueError("native Git source inventory has trailing output")
    return [path for path in records["TRACKED"].split("\0") if path], records["TREE"]
