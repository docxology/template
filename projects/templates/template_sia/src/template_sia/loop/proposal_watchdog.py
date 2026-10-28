"""Container-owned target deadline and read-only controller heartbeat.

The trusted PID1 watchdog survives the host Docker client/controller. Losing
heartbeat for two seconds terminates PID1, after which Docker removes the
container and its PID namespace. The target cannot write the heartbeat mount.
"""

from __future__ import annotations

import threading
from pathlib import Path

CONTAINER_BOOTSTRAP = """
import json, os, subprocess, sys, time
assert (3,14)<=sys.version_info[:2]<=(3,15)
print(json.dumps({'python_version':sys.version.split()[0]}), flush=True)
timeout=int(sys.argv[1]); started=time.monotonic()
heartbeat='/program/controller_heartbeat'
last=open(heartbeat).read(); last_update=started
worker="import runpy,sys; sys.argv=['/program/target.py','--dataset_dir','/data','--working_dir','/working']; runpy.run_path('/program/target.py',run_name='__main__')"
target=subprocess.Popen([sys.executable,'-I','-c',worker])
while target.poll() is None:
    now=time.monotonic()
    if now-started >= timeout:
        print('container target deadline expired', flush=True)
        os._exit(124)
    try:
        current=open(heartbeat).read()
    except OSError:
        current=last
    if current != last:
        last=current; last_update=now
    elif now-last_update >= 2:
        print('controller heartbeat lost', flush=True)
        os._exit(125)
    time.sleep(0.1)
raise SystemExit(target.returncode)
"""


class ControllerHeartbeat:
    """Advance a read-only-mounted counter while the controller remains alive."""

    def __init__(self, program: Path) -> None:
        self.path = program / "controller_heartbeat"
        self.path.write_text("0", encoding="ascii")
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._advance, daemon=True)

    def _advance(self) -> None:
        count = 0
        while not self.stopped.wait(0.2):
            count += 1
            temporary = self.path.with_suffix(".next")
            try:
                temporary.write_text(str(count), encoding="ascii")
                temporary.replace(self.path)
            except OSError:
                return  # Container watchdog independently rejects lost custody.

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stopped.set()
        self.thread.join(timeout=1)
