"""Source-owned inline worker diagnostics; anchored frames are DATA, not custody."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, ExitStack, contextmanager
from contextvars import ContextVar
import os
from pathlib import Path
import sys
import threading
from types import FrameType
from typing import TypeVar


_EXECUTION_PHASES = (
    "run-native-worker",
    "scope-setup",
    "producer-entry",
    "mermaid-readmission",
    "mermaid-runtime-entry",
    "pdfium-execution-entry",
    "worker-body",
    "worker-initial-setup",
    "worker-correspondence",
    "worker-fingerprint",
    "worker-runtime-observation",
    "worker-runtime-binding",
    "mermaid-producer-verify",
    "mermaid-observe-before",
    "mermaid-tool-api",
    "mermaid-post-node",
    "mermaid-post-node-guard",
    "mermaid-post-node-data",
    "mermaid-observe-after",
    "mermaid-post-node-unchanged",
    "retain-tool-verify",
    "retain-tool-data",
    "retain-tool-unchanged",
)
_WorkerObserver = Callable[[str, FrameType], None]
_WORKER_EXECUTION_OBSERVER: ContextVar[tuple[_WorkerObserver, int, int] | None] = ContextVar(
    "native_worker_execution_observer", default=None
)
_WORKER_MERMAID_TOOL: ContextVar[bool] = ContextVar("native_worker_mermaid_tool", default=False)
_EntryValue = TypeVar("_EntryValue")


def _worker_execution_notify(phase: str) -> None:
    try:
        selected = _WORKER_EXECUTION_OBSERVER.get()
        if selected is not None:
            observer, owner_pid, owner_thread = selected
            if os.getpid() == owner_pid and threading.get_ident() == owner_thread:
                observer(phase, sys._getframe(1))
    except BaseException:
        pass


@contextmanager
def _worker_execution_observer(observer: object) -> Iterator[None]:
    """Bind diagnostic DATA only; this token supplies no Source or runtime authority."""
    selected = (observer, os.getpid(), threading.get_ident()) if callable(observer) else None
    token = _WORKER_EXECUTION_OBSERVER.set(selected)
    try:
        yield
    finally:
        _WORKER_EXECUTION_OBSERVER.reset(token)


@contextmanager
def _worker_execution_phase(phase: str) -> Iterator[None]:
    """Observe only fixed inline boundaries without replacing a result or exception."""
    if (
        type(phase) is not str
        or phase not in _EXECUTION_PHASES
        or phase.startswith("retain-tool-")
        and not _WORKER_MERMAID_TOOL.get()
    ):
        yield
        return
    token = _WORKER_MERMAID_TOOL.set(True) if phase == "mermaid-tool-api" else None
    try:
        _worker_execution_notify(phase + "-begin")
        try:
            yield
        except BaseException:
            _worker_execution_notify(phase + "-raised")
            raise
        else:
            _worker_execution_notify(phase + "-returned")
    finally:
        if token is not None:
            _WORKER_MERMAID_TOOL.reset(token)


@contextmanager
def _worker_execution_entry(phase: str, manager: AbstractContextManager[_EntryValue]) -> Iterator[_EntryValue]:
    """Bracket actual __enter__, forwarding body/exit semantics to the original owner."""
    with ExitStack() as stack:
        with _worker_execution_phase(phase):
            value = stack.enter_context(manager)
        yield value


_PRELUDE = r"""
_native_startup = None
try:
 import math,os,queue,sys,threading,time,types
 class _NativeStartupDiagnostics:
  def __init__(self):
   self.deadline = @DEADLINE@
   self.started = time.monotonic()
   self.owner_pid = os.getpid()
   self.owner_thread = threading.get_ident()
   self.worker_filename = @WORKER_FILENAME@
   self.anchor = None
   self.stop = threading.Event()
   self.lock = threading.Lock()
   self.pending = queue.Queue(maxsize=96)
   self.events = 0
   self.stack_events = 0
   self.byte_count = 0
   self.seen = set()
   self.writer = None
   self.sampler = None
   self.execution_phases = frozenset((@EXECUTION_PHASES@))
   self.phases = frozenset((
    'bootstrap-enter','bootstrap-imports-returned','cache-ready','audit-begin',
    'audit-returned','package-exec-begin','package-exec-returned',
    'worker-dispatch','worker-main-enter',
    'source-admission-begin','source-admission-returned','worker-execution-begin',
    'source-providers-begin','source-providers-returned',
    'pdfium-readmission-begin','pdfium-readmission-returned',
    'worker-dispatch-returned','protected-body-raised','bootstrap-leaving',
    @EXECUTION_PHASES@))
  def start(self):
   if type(self.deadline) not in (int,float) or not math.isfinite(self.deadline):
    return
   if time.monotonic() >= self.deadline:
    return
   descriptor = os.dup(2)
   try:
    self.writer = threading.Thread(target=self.write,args=(descriptor,),daemon=True,
     name='native-worker-startup-sink')
    self.writer.start()
   except Exception:
    os.close(descriptor)
    raise
   self.sampler = threading.Thread(target=self.sample,daemon=True,
    name='native-worker-startup-sampler')
   self.sampler.start()
  def observe(self,phase,frame):
   try:
    if (type(phase) is not str or phase not in self.phases or type(frame) is not types.FrameType
      or os.getpid() != self.owner_pid or threading.get_ident() != self.owner_thread
      or self.stop.is_set()):
     return
    if phase not in self.execution_phases:
     self.anchor = frame
    self.emit(phase)
   except Exception:
    pass
  def emit(self,phase,depth=-1,label='none',line=0):
   if (type(phase) is not str or type(label) is not str
     or phase not in self.phases and phase != 'anchored-stack'
     or label not in ('none','unlisted','bootstrap','worker-main')
     or type(depth) is not int or not -1 <= depth < 12
     or type(line) is not int or not 0 <= line <= 1000000):
    return
   if phase != 'anchored-stack' and depth != -1:
    return
   if self.stop.is_set() or not self.lock.acquire(blocking=False):
    return
   try:
    observed = time.monotonic()
    if (observed >= self.deadline or self.events >= 96
      or (phase == 'anchored-stack' and self.stack_events >= 96-len(self.phases))
      or (depth == -1 and phase in self.seen)):
     return
    record = ('NATIVE_WORKER_STARTUP_V1 %s %d %.9f %.9f %d %s %d\n' %
     (phase,self.owner_pid,observed,self.deadline-observed,depth,label,line)).encode('ascii')
    self.events += 1
    if phase == 'anchored-stack':
     self.stack_events += 1
    if len(record) > 512 or self.byte_count + len(record) > 32768:
     return
    self.byte_count += len(record)
    if depth == -1:
     self.seen.add(phase)
    self.pending.put_nowait(record)
   except Exception:
    pass
   finally:
    self.lock.release()
  def write(self,descriptor):
   try:
    while not self.stop.is_set():
     record = self.pending.get(timeout=max(0.0,self.deadline-time.monotonic()))
     if record is None or self.stop.is_set() or time.monotonic() >= self.deadline:
      return
     if os.write(descriptor,record) != len(record):
      return
   except Exception:
    pass
   finally:
    try:
     os.close(descriptor)
    except OSError:
     pass
  def sample(self):
   try:
    targets = sorted(set((self.started+1,self.started+5,self.started+20,
     self.started+60,self.deadline-30,self.deadline-5)))
    for target in targets:
     if target < self.started or target >= self.deadline:
      continue
     if self.stop.wait(max(0.0,target-time.monotonic())):
      return
     current = self.anchor
     try:
      for depth in range(12):
       if current is None or self.stop.is_set() or time.monotonic() >= self.deadline:
        break
       label = 'unlisted'
       line = 0
       if current.f_code.co_filename == self.worker_filename:
        if current.f_code.co_name == 'main':
         label = 'worker-main'
       elif current.f_code.co_filename == '<string>' and current.f_code.co_name == '<module>':
        label = 'bootstrap'
       if label != 'unlisted':
        line = min(max(current.f_lineno,0),1000000)
       self.emit('anchored-stack',depth,label,line)
       current = current.f_back
     finally:
      del current
   except Exception:
    pass
  def close(self):
   self.stop.set()
   self.anchor = None
   try:
    self.pending.put_nowait(None)
   except queue.Full:
    pass
   join_deadline = min(self.deadline,time.monotonic()+0.05)
   for thread in (self.sampler,self.writer):
    if thread is not None and thread.ident is not None:
     thread.join(timeout=max(0.0,join_deadline-time.monotonic()))
 _native_startup = _NativeStartupDiagnostics()
 _native_startup.start()
 _native_startup.observe('bootstrap-enter',sys._getframe())
except Exception:
 if _native_startup is not None:
  try:
   _native_startup.close()
  except Exception:
   pass
 _native_startup = None
def _native_startup_checkpoint(phase):
 try:
  if _native_startup is not None:
   _native_startup.observe(phase,sys._getframe(1))
 except Exception:
  pass
"""


def _diagnostic_envelope(body: str, sdk_package_root: Path, deadline: float) -> str:
    """Wrap fixed caller-owned code; tests exercise transport, never Source admission."""
    execution_phases = ",".join(
        repr(phase + "-" + outcome) for phase in _EXECUTION_PHASES for outcome in ("begin", "returned", "raised")
    )
    prelude = (
        _PRELUDE.replace("@EXECUTION_PHASES@", execution_phases)
        .replace("@DEADLINE@", repr(deadline))
        .replace("@WORKER_FILENAME@", repr(str(sdk_package_root / "reporting/native_format_acceptance_worker.py")))
    )
    return (
        prelude + "\ntry:\n" + "\n".join(" " + line for line in body.splitlines()) + "\nfinally:\n"
        " _native_startup_checkpoint('bootstrap-leaving')\n"
        " if _native_startup is not None:\n"
        "  try:\n"
        "   _native_startup.close()\n"
        "  except Exception:\n"
        "   pass\n"
    )


def wrap_native_worker_startup(body: str, sdk_package_root: Path, deadline: float) -> str:
    """Embed fixed diagnostics in the exact already Source-owned native command.

    Only a retained worker frame and at most eleven callers are sampled. The active
    callee is unobserved; there is no global thread scan or signal handler.
    This pure formatter does not import or admit any Source/SDK in the child.
    """
    worker = "infrastructure.reporting.native_format_acceptance_worker"
    for before, after in (
        (
            "with tempfile.TemporaryDirectory",
            "_native_startup_checkpoint('bootstrap-imports-returned')\nwith tempfile.TemporaryDirectory",
        ),
        (
            " sys.pycache_prefix=str(Path(cache).resolve())\n",
            " sys.pycache_prefix=str(Path(cache).resolve())\n"
            " _native_startup_checkpoint('cache-ready')\n _native_startup_checkpoint('audit-begin')\n",
        ),
        (
            " outcome={'kind':'not_started'}",
            " _native_startup_checkpoint('audit-returned')\n outcome={'kind':'not_started'}",
        ),
        (
            "  spec.loader.exec_module(package)",
            "  _native_startup_checkpoint('package-exec-begin')\n"
            "  spec.loader.exec_module(package)\n  _native_startup_checkpoint('package-exec-returned')",
        ),
        (
            f"  runpy.run_module({worker!r},run_name='__main__')",
            "  _native_startup_checkpoint('worker-dispatch')\n"
            f"  runpy.run_module({worker!r},run_name='__main__',init_globals={{"
            "'_native_startup_observer':_native_startup.observe if _native_startup is not None else None})\n"
            "  _native_startup_checkpoint('worker-dispatch-returned')",
        ),
        (
            " except BaseException as worker_error:\n",
            " except BaseException as worker_error:\n  _native_startup_checkpoint('protected-body-raised')\n",
        ),
    ):
        if body.count(before) != 1:
            raise ValueError("native worker diagnostic insertion lost its exact Source anchor")
        body = body.replace(before, after, 1)
    return _diagnostic_envelope(body, sdk_package_root, deadline)


__all__ = ["wrap_native_worker_startup"]
