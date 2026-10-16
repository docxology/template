"""Fresh adjacent Git cohorts for one standalone provider admission."""

from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.publishing._standalone_git import (
    _ADMISSION_STREAM,
    _admission_records,
    _clean_source_records,
    _git_environment,
)


def _provider_records(
    cwd: Path,
    script: str,
    prefix: str,
    arguments: list[str],
    labels: tuple[str, ...],
    refusal_steps: tuple[int, ...],
) -> tuple[dict[str, str], bool]:
    result = run_bounded_subprocess(
        [sys.executable, "-I", "-S", "-c", _ADMISSION_STREAM + script, prefix, *arguments],
        cwd=cwd,
        env=_git_environment(),
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git provider admission batch failed in {cwd}: {(result.stderr or result.command_error).strip()}"
        )
    refused = result.stdout.endswith(prefix + "REFUSED\n")
    # A shorter form could absorb later frame markers into its last payload.
    # Parse the longest completed prefix before considering earlier refusals.
    candidates = (
        tuple(labels[:step] + ("REFUSED",) for step in reversed(refusal_steps)) if refused else (labels + ("END",),)
    )
    for candidate in candidates:
        try:
            return _admission_records(result.stdout, prefix, candidate), refused
        except ValueError:
            continue
    raise ValueError("native Git provider admission framing is malformed or ambiguous")


def _git_provider_opening(cwd: Path, supplied: str, repository: str) -> str:
    """Admit TOP, clean HEAD, canonical origin and routing before metadata IO."""
    from infrastructure.publishing.standalone_mirror import _validate_destination_inventory

    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", supplied):
        raise ValueError("install provider requires its existing full commit identity")
    probe = "template-admission-" + uuid.uuid4().hex
    prefix = "template-git-provider-opening-v1:" + probe + ":"
    # Native --show-toplevel emits the complete canonical path plus one newline.
    # The SHA observer retains its old 512-byte default; long valid paths do not.
    path_limit = max(512, len(os.fsencode(str(cwd))) + 1)
    script = """
from pathlib import Path
supplied,checkout,repository,probe,path_limit=sys.argv[2:]
top=read('TOP',['rev-parse','--show-toplevel'],'identity',identity_limit=int(path_limit))
if top is None or Path(top).resolve()!=Path(checkout):
    refuse()
head=read('HEAD',['rev-parse','--verify','HEAD^{commit}'],'identity')
resolved=read('LABEL',['rev-parse','--verify',supplied+'^{commit}'],'identity')
dirty=read('STATUS',['status','--porcelain','--untracked-files=all'],'status')
if head is None or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',head) or resolved!=head or dirty or head!=supplied:
    refuse()
declared=read('ORIGIN',['config','--get','remote.origin.url'],'identity')
if declared not in (repository,repository+'.git') or not declared or any(c in declared for c in '\\r\\n\\0'):
    refuse()
expected=(probe+'\\t'+declared+' (fetch)',probe+'\\t'+declared+' (push)')
if not read('INVENTORY',['-c','remote.'+probe+'.url='+declared,'remote','-v'],'probe',expected):
    refuse()
print(prefix+'END',flush=True)
"""
    records, refused = _provider_records(
        cwd,
        script,
        prefix,
        [supplied, str(cwd), repository, probe, str(path_limit)],
        ("TOP", "HEAD", "LABEL", "STATUS", "ORIGIN", "INVENTORY"),
        (1, 4, 5, 6),
    )
    if Path(records["TOP"].strip()).resolve() != cwd:
        raise ValueError("install provider cannot inherit an ancestor repository")
    if not {"HEAD", "LABEL", "STATUS"} <= records.keys():
        raise ValueError("native Git observer refused an otherwise valid provider root")
    head = _clean_source_records(records["HEAD"].strip(), records["LABEL"].strip(), records["STATUS"], supplied)
    if head != supplied:
        raise ValueError("install provider differs from its admitted commit")
    if "ORIGIN" not in records:
        raise ValueError("native Git observer refused an otherwise valid provider commit")
    declared = records["ORIGIN"].strip()
    if declared not in {repository, repository + ".git"}:
        raise ValueError("install provider origin is not its canonical public repository")
    if not declared or any(character in declared for character in "\r\n\0"):
        raise ValueError("publication transport must have one exact admitted destination")
    if "INVENTORY" not in records:
        raise ValueError("native Git observer refused an otherwise valid provider origin")
    _validate_destination_inventory(declared, probe, records["INVENTORY"].splitlines())
    if refused:
        raise ValueError("native Git observer refused otherwise valid provider routing")
    return declared


def _git_provider_closing(cwd: Path, supplied: str) -> str:
    """Recheck clean HEAD after metadata verification, then read that tree."""
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", supplied):
        raise ValueError("install provider requires its existing full commit identity")
    prefix = "template-git-provider-closing-v1:" + uuid.uuid4().hex + ":"
    script = """
supplied=sys.argv[2]
head=read('HEAD',['rev-parse','--verify','HEAD^{commit}'],'identity')
resolved=read('LABEL',['rev-parse','--verify',supplied+'^{commit}'],'identity')
dirty=read('STATUS',['status','--porcelain','--untracked-files=all'],'status')
if head is None or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',head) or resolved!=head or dirty:
    refuse()
read('TREE',['rev-parse',supplied+'^{tree}'])
print(prefix+'END',flush=True)
"""
    records, refused = _provider_records(cwd, script, prefix, [supplied], ("HEAD", "LABEL", "STATUS", "TREE"), (3,))
    _clean_source_records(records["HEAD"].strip(), records["LABEL"].strip(), records["STATUS"], supplied)
    if refused:
        raise ValueError("native Git observer refused an otherwise valid provider commit")
    return records["TREE"].strip()


def _git_provider_closing_metadata(cwd: Path, supplied: str) -> tuple[str, str]:
    """Read committed metadata, then recheck clean HEAD and read its tree."""
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", supplied):
        raise ValueError("install provider requires its existing full commit identity")
    prefix = "template-git-provider-closing-metadata-v1:" + uuid.uuid4().hex + ":"
    script = """
supplied=sys.argv[2]
read('METADATA',['ls-tree','-z',supplied,'--','pyproject.toml'])
head=read('HEAD',['rev-parse','--verify','HEAD^{commit}'],'identity')
resolved=read('LABEL',['rev-parse','--verify',supplied+'^{commit}'],'identity')
dirty=read('STATUS',['status','--porcelain','--untracked-files=all'],'status')
if head is None or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',head) or resolved!=head or dirty:
    refuse()
read('TREE',['rev-parse',supplied+'^{tree}'])
print(prefix+'END',flush=True)
"""
    records, refused = _provider_records(
        cwd, script, prefix, [supplied], ("METADATA", "HEAD", "LABEL", "STATUS", "TREE"), (4,)
    )
    _clean_source_records(records["HEAD"].strip(), records["LABEL"].strip(), records["STATUS"], supplied)
    if refused:
        raise ValueError("native Git observer refused an otherwise valid provider commit")
    return records["METADATA"], records["TREE"].strip()
