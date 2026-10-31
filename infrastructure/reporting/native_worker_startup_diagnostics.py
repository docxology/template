"""Source-owned inline worker diagnostics; anchored frames are DATA, not custody."""

from __future__ import annotations

from pathlib import Path


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
   self.byte_count = 0
   self.seen = set()
   self.writer = None
   self.sampler = None
   self.phases = frozenset((
    'bootstrap-enter','bootstrap-imports-returned','cache-ready','audit-begin',
    'audit-returned','package-exec-begin','package-exec-returned',
    'worker-dispatch','worker-main-enter',
    'source-admission-begin','source-admission-returned','worker-execution-begin',
    'worker-dispatch-returned','protected-body-raised','bootstrap-leaving'))
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
   if self.stop.is_set() or not self.lock.acquire(blocking=False):
    return
   try:
    observed = time.monotonic()
    if (observed >= self.deadline or self.events >= 96
      or (depth == -1 and phase in self.seen)):
     return
    record = ('NATIVE_WORKER_STARTUP_V1 %s %d %.9f %.9f %d %s %d\n' %
     (phase,self.owner_pid,observed,self.deadline-observed,depth,label,line)).encode('ascii')
    self.events += 1
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
    prelude = _PRELUDE.replace("@DEADLINE@", repr(deadline)).replace(
        "@WORKER_FILENAME@", repr(str(sdk_package_root / "reporting/native_format_acceptance_worker.py"))
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
