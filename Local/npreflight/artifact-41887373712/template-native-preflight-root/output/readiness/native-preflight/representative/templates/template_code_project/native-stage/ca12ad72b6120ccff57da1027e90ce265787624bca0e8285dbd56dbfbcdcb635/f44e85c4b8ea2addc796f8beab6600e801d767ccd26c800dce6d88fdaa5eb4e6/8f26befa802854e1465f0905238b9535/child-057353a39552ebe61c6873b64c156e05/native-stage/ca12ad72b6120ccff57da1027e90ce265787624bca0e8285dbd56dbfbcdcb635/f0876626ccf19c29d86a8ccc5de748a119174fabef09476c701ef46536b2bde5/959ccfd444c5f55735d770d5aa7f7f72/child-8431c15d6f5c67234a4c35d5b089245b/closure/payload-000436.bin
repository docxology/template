"""Bounded standalone Git routing, commit/status and source-inventory reads."""

from __future__ import annotations

import json
import re
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


# Only adjacent admission reads share this fresh guardian. Native stdout still
# streams into its bounded supervisor; the observer retains two tiny commit
# identities, a dirty-status flag, or two probe-line counters, never an inventory.
_ADMISSION_STREAM = """
import codecs,json,os,re,signal,subprocess,sys,threading
prefix=sys.argv[1]
def read(label,args,observe=None,expected=(),identity_limit=512):
    print(prefix+label,flush=True)
    read_fd,write_fd=os.pipe()
    identity=bytearray()
    invalid_identity=False
    dirty=False
    counts=[0,0]
    invalid_probe=False
    line=''
    line_overflow=False
    failures=[]
    probe=expected[0].split('\\t',1)[0]+'\\t' if expected else ''
    line_limit=max(map(len,expected),default=0)
    def complete_line():
        nonlocal line,line_overflow,invalid_probe
        if line.startswith(probe):
            if line_overflow or line not in expected:
                invalid_probe=True
            else:
                index=expected.index(line)
                counts[index]=min(2,counts[index]+1)
        line=''
        line_overflow=False
    def observe_text(text):
        nonlocal dirty,line,line_overflow
        if observe=='status':
            dirty=dirty or bool(text.strip())
        elif observe=='probe':
            for character in text:
                if character in '\\n\\r\\v\\f\\x1c\\x1d\\x1e\\x85\\u2028\\u2029':
                    complete_line()
                elif len(line)<line_limit:
                    line+=character
                else:
                    line_overflow=True
    def drain():
        nonlocal invalid_identity
        decoder=codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            with os.fdopen(read_fd,'rb',buffering=0) as stream:
                while True:
                    chunk=stream.read(65536)
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    if observe=='identity':
                        remaining=identity_limit-len(identity)
                        identity.extend(chunk[:remaining])
                        invalid_identity=invalid_identity or len(chunk)>remaining
                    elif observe in ('status','probe'):
                        observe_text(decoder.decode(chunk))
                if observe in ('status','probe'):
                    observe_text(decoder.decode(b'',final=True))
                if observe=='probe' and (line or line_overflow):
                    complete_line()
        except BaseException as error:
            failures.append(error)
    reader=threading.Thread(target=drain)
    reader.start()
    try:
        result=subprocess.run(
            ['git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',*args],
            stdout=write_fd,check=False,timeout=60,
        )
    except subprocess.TimeoutExpired:
        print('original native Git read exceeded its 60-second deadline',file=sys.stderr,flush=True)
        raise SystemExit(124)
    finally:
        os.close(write_fd)
        reader.join()
    if failures:
        raise failures[0]
    if result.returncode:
        print('original native Git return code: '+str(result.returncode),file=sys.stderr,flush=True)
        if result.returncode<0:
            signum=-result.returncode
            if signum!=signal.SIGKILL:
                signal.signal(signum,signal.SIG_DFL)
            os.kill(os.getpid(),signum)
            raise SystemExit(1)
        raise SystemExit(result.returncode)
    if observe=='identity':
        return None if invalid_identity else identity.decode('utf-8',errors='replace').strip()
    if observe=='status':
        return dirty
    if observe=='probe':
        return not invalid_probe and counts==[1,1]
def refuse():
    # All native reads completed successfully. The parent repeats the original
    # admission predicate and raises its original ValueError before consumption.
    print(prefix+'REFUSED',flush=True)
    raise SystemExit(0)
"""


def _admission_records(output: str, prefix: str, labels: tuple[str, ...]) -> dict[str, str]:
    records: dict[str, str] = {}
    for index, label in enumerate(labels[:-1]):
        marker = prefix + label + "\n"
        following = prefix + labels[index + 1] + "\n"
        if not output.startswith(marker) or output.count(following) != 1:
            raise ValueError("native Git admission read framing is malformed or ambiguous")
        records[label], output = output[len(marker) :].split(following, 1)
        output = following + output
    if output != prefix + labels[-1] + "\n":
        raise ValueError("native Git admission read has trailing output")
    return records


def _clean_source_records(head: str, resolved: str | None, status: str, supplied: str | None) -> str:
    """Repeat the existing clean-HEAD admission before consuming an inventory."""
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head):
        raise ValueError("standalone source HEAD has an unsupported commit identity")
    if supplied is not None and resolved != head:
        raise ValueError("standalone source revision differs from current HEAD")
    if status.strip():
        raise ValueError("standalone publication requires a clean source working tree")
    return head


def _git_clean_source_inventory(cwd: Path, supplied: str) -> tuple[str, list[str], str]:
    """Admit clean HEAD, then read its tracked/tree inventory in one fresh60s cohort."""
    if not re.fullmatch(r"[0-9a-f]{7,64}", supplied):
        raise ValueError("standalone source revision must be an actual hexadecimal HEAD identity")
    prefix = "template-git-clean-source-inventory-v1:"
    script = (
        _ADMISSION_STREAM
        + """
supplied=sys.argv[2]
head=read('HEAD',['rev-parse','--verify','HEAD^{commit}'],'identity')
resolved=read('LABEL',['rev-parse','--verify',supplied+'^{commit}'],'identity')
dirty=read('STATUS',['status','--porcelain','--untracked-files=all'],'status')
if head is None or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',head) or resolved!=head or dirty:
    refuse()
read('TRACKED',['ls-files','-z','--','.'])
read('TREE',['ls-tree','-r','-z',head,'--',*json.loads(sys.argv[3])])
print(prefix+'END',flush=True)
"""
    )
    roots = [*(root.as_posix() for root in _PUBLIC_ROOTS), "infrastructure", "pyproject.toml"]
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-S", "-c", script, prefix, supplied, json.dumps(roots)],
        cwd=cwd,
        env=_git_environment(),
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git clean source inventory batch failed in {cwd}: {(result.stderr or result.command_error).strip()}"
        )
    refused = result.stdout.endswith(prefix + "REFUSED\n")
    labels = (
        ("HEAD", "LABEL", "STATUS", "REFUSED") if refused else ("HEAD", "LABEL", "STATUS", "TRACKED", "TREE", "END")
    )
    records = _admission_records(result.stdout, prefix, labels)
    head = _clean_source_records(records["HEAD"].strip(), records["LABEL"].strip(), records["STATUS"], supplied)
    if refused:
        raise ValueError("native Git admission observer refused an otherwise valid source record")
    return head, [path for path in records["TRACKED"].split("\0") if path], records["TREE"]


def _git_destination_inventory(cwd: Path, admitted: str, probe: str) -> tuple[str, str | None]:
    """Read direct routing, then origin routing, with no intervening mutable operation."""
    prefix = "template-git-destination-inventory-v1:"
    script = (
        _ADMISSION_STREAM
        + """
admitted,probe=sys.argv[2:]
expected=(probe+'\\t'+admitted+' (fetch)',probe+'\\t'+admitted+' (push)')
if not read('INVENTORY',['-c','remote.'+probe+'.url='+admitted,'remote','-v'],'probe',expected):
    refuse()
read('ORIGIN',['remote','get-url','--push','--all','origin'])
print(prefix+'END',flush=True)
"""
    )
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-S", "-c", script, prefix, admitted, probe],
        cwd=cwd,
        env=_git_environment(),
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git destination inventory batch failed in {cwd}: {(result.stderr or result.command_error).strip()}"
        )
    refused = result.stdout.endswith(prefix + "REFUSED\n")
    labels = ("INVENTORY", "REFUSED") if refused else ("INVENTORY", "ORIGIN", "END")
    records = _admission_records(result.stdout, prefix, labels)
    return records["INVENTORY"], records.get("ORIGIN")
