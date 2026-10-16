"""Bounded file-backed acceptance code; exact Source bytes remain caller-owned.

This module admits no Source, package or successful execution. Callers regenerate
payload bytes independently and bind their artifact and exact small command.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined

MAX_PAYLOAD_BYTES = 16 * 1024 * 1024
MAX_LOADER_BYTES = 32 * 1024
IDENTITY_FIELDS = ("device", "inode", "mode", "size", "mtime_ns", "ctime_ns", "uid", "links")


def _identity(path: Path) -> dict[str, int]:
    value = path.lstat()
    return dict(
        zip(
            IDENTITY_FIELDS,
            (
                value.st_dev,
                value.st_ino,
                value.st_mode,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
                value.st_uid,
                value.st_nlink,
            ),
            strict=True,
        )
    )


def _metadata(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "identity"}:
        raise ValueError("acceptance payload requires closed path/hash/physical metadata")
    path, digest, identity = value["path"], value["sha256"], value["identity"]
    if (
        not isinstance(path, str)
        or not Path(path).is_absolute()
        or ".." in Path(path).parts
        or str(Path(path)) != path
        or "\x00" in path
        or len(os.fsencode(path)) > 4096
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or not isinstance(identity, dict)
        or set(identity) != set(IDENTITY_FIELDS)
        or any(type(item) is not int or item < 0 for item in identity.values())
        or not stat.S_ISREG(identity["mode"])
        or stat.S_IMODE(identity["mode"]) != 0o400
        or identity["links"] != 1
        or not 0 < identity["size"] <= MAX_PAYLOAD_BYTES
    ):
        raise ValueError("acceptance payload path/hash/physical declaration is invalid")
    return {"path": path, "sha256": digest, "identity": {name: identity[name] for name in IDENTITY_FIELDS}}


def validate_acceptance_payload(body: bytes, metadata: object, *, expected_path: Path) -> dict[str, Any]:
    """Compare independently regenerated Source bytes; never reopen Original paths."""
    observed = _metadata(metadata)
    if (
        not isinstance(body, bytes)
        or not 0 < len(body) <= MAX_PAYLOAD_BYTES
        or observed["path"] != str(expected_path)
        or observed["identity"]["size"] != len(body)
        or observed["sha256"] != hashlib.sha256(body).hexdigest()
    ):
        raise ValueError("acceptance payload differs from its exact Source body or fixed outside path")
    return observed


def write_acceptance_payload(
    scratch: Path, path: Path, body: bytes, *, forbidden_roots: tuple[Path, ...]
) -> dict[str, Any]:
    """Create one owned readonly payload outside every nominated Source tree."""
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_PAYLOAD_BYTES:
        raise ValueError("acceptance payload body exceeds its finite bound")
    scratch, path = scratch.absolute(), path.absolute()
    if (
        scratch.resolve(strict=True) != scratch
        or path.parent.resolve(strict=True) != path.parent
        or not path.is_relative_to(scratch)
        or path.exists()
        or path.is_symlink()
        or any(path.is_relative_to(root.resolve(strict=True)) for root in forbidden_roots)
    ):
        raise ValueError("acceptance payload requires a fresh owned outside-Source physical path")
    atomic_write_bytes_confined(scratch, path, body, mode=0o400)
    before = _identity(path)
    if read_bytes_confined(scratch, path, max_bytes=MAX_PAYLOAD_BYTES) != body or _identity(path) != before:
        raise ValueError("acceptance payload changed during owned-file admission")
    if hasattr(os, "getuid") and before["uid"] != os.getuid():
        raise ValueError("acceptance payload is not owned by its actual launcher")
    return validate_acceptance_payload(
        body,
        {
            "path": str(path),
            "sha256": hashlib.sha256(body).hexdigest(),
            "identity": before,
        },
        expected_path=path,
    )


def format_acceptance_payload_loader(metadata: object) -> str:
    """Pure fixed loader; metadata alone cannot approve or select Source code."""
    value = _metadata(metadata)
    loader = f"""def _template_acceptance_payload_main():
 import hashlib,os,pathlib,stat,sys
 p=pathlib.Path({value["path"]!r})
 expected={value["identity"]!r}
 def identity(s):
  values=(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_uid,s.st_nlink)
  return dict(zip({IDENTITY_FIELDS!r},values))
 def physical():
  if p.resolve(strict=True)!=p or any(x.is_symlink() for x in (p,*p.parents)):
   raise ValueError('acceptance payload physical path is aliased')
  s=p.lstat()
  if identity(s)!=expected or not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode)!=0o400 or s.st_nlink!=1:
   raise ValueError('acceptance payload physical identity changed')
  if hasattr(os,'getuid') and s.st_uid!=os.getuid():
   raise ValueError('acceptance payload lost its actual launcher owner')
 physical()
 fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_CLOEXEC',0))
 with os.fdopen(fd,'rb') as stream:
  if identity(os.fstat(stream.fileno()))!=expected:
   raise ValueError('acceptance payload opened a different physical file')
  body=stream.read({MAX_PAYLOAD_BYTES}+1)
  if identity(os.fstat(stream.fileno()))!=expected:
   raise ValueError('acceptance payload changed during its bounded read')
 if len(body)!=expected['size'] or hashlib.sha256(body).hexdigest()!={value["sha256"]!r}:
  raise ValueError('acceptance payload Source hash differs')
 physical()
 primary=None
 try:
  exec(compile(body,'<string>','exec',dont_inherit=True),globals(),globals())
 except BaseException as error:
  primary=error
  raise
 finally:
  try:
   physical()
  except BaseException:
   if primary is None or isinstance(primary,SystemExit) and primary.code in (None,0):
    raise
_template_acceptance_payload_main()
"""
    if len(loader.encode()) > MAX_LOADER_BYTES:
        raise ValueError("acceptance payload loader exceeds the bounded argv contract")
    return loader
