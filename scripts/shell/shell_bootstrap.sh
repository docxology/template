#!/usr/bin/env bash
# Prepared-runtime admission and dispatch only. Installation is explicit.

setup_orchestration_sandbox_env() {
    export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/matplotlib_cache}"
    export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/uv_cache}"
    export MPLBACKEND="${MPLBACKEND:-Agg}"
}

dispatch_prepared_root_python() {
    local repository_root="$1"
    shift
    local selected="${TEMPLATE_ROOT_PYTHON-$repository_root/.venv/bin/python}"
    local budget="${TEMPLATE_DISPATCH_TIMEOUT_SECONDS-14400}" native_limit
    # Validate before launching a child; awk is the existing POSIX shell toolchain,
    # never a substitute Python interpreter or a dependency installer.
    if [[ ! "$budget" =~ ^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$ ]] || ! native_limit="$(LC_ALL=C awk -v value="$budget" 'BEGIN {
        value += 0; if (value <= 0 || tolower(sprintf("%g", value)) ~ /inf|nan/) exit 1;
        cap = value < 10 ? value : 10; rounded = int(cap); if (rounded < cap) rounded++;
        printf "%d\n", rounded;
    }')"; then
        echo "Invalid dispatch configuration: TEMPLATE_DISPATCH_TIMEOUT_SECONDS must be positive and finite" >&2
        return 2
    fi
    if [[ "$selected" != /* || "$selected" == */../* || "$selected" == */.. || ! -x "$selected" || ! -f "$selected" ]]; then
        echo "BLOCKED: selected root Python is absent, broken, or not an absolute executable." >&2
        print_preparation_instructions "${0##*/}"
        return 75
    fi
    local control nonce child_pid native_started receipt interrupted=0 status=0
    control="$(mktemp -d "${TMPDIR:-/tmp}/template-root-python.XXXXXXXX")" || return 75
    nonce="${control##*/}"
    # Open owned pipes before launch. Reads use held descriptors with deadlines,
    # so replacing a READY path with a FIFO cannot redirect or block receipt IO.
    if ! mkfifo "$control/ready" "$control/continue"; then
        rmdir "$control" 2>/dev/null || true
        return 75
    fi
    exec 3<>"$control/ready" 4<>"$control/continue"
    rm -f "$control/ready" "$control/continue"
    rmdir "$control"
    native_started=$SECONDS
    "$selected" -I -S -c '
import math, os, select, signal, stat, sys, time
from pathlib import Path
selected, root, nonce = sys.argv[1:4]
arguments = sys.argv[4:]
entered = time.monotonic()

def expired(_signal, _frame):
    raise TimeoutError("Prepared native startup/admission exceeded its finite deadline")

def regular_bytes(path):
    # Ancestor handles require search access; bounded source reads still require read access.
    directory_flags = getattr(os, "O_SEARCH", getattr(os, "O_PATH", os.O_RDONLY)) | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors = [os.open(path.anchor, directory_flags)]
    bindings = []
    try:
        parent = descriptors[0]
        for name in path.parts[1:-1]:
            child = os.open(name, directory_flags, dir_fd=parent)
            bindings.append((parent, name, child))
            descriptors.append(child)
            parent = child
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        content = os.read(descriptor, 65537)
        after = os.fstat(descriptor)
        current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
        if not stat.S_ISREG(before.st_mode) or not 0 < len(content) <= 65536 or len(content) != before.st_size:
            raise ValueError("Prepared startup requires bounded regular source/configuration bytes")
        if any(getattr(before, field) != getattr(after, field) or getattr(after, field) != getattr(current, field) for field in fields):
            raise ValueError("Prepared startup bytes changed during held read")
        for parent, name, child in reversed(bindings):
            held, named = os.fstat(child), os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(named.st_mode) or (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino):
                raise ValueError("Prepared startup ancestor changed during held read")
        return content
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)

try:
    budget = float(os.environ.get("TEMPLATE_DISPATCH_TIMEOUT_SECONDS", "14400"))
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("Dispatch budget must be positive and finite")
    # Bash async commands initially ignore SIGINT. Restore it before READY and
    # before the parent can relinquish native-startup observation.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(30, budget))
    assert sys.implementation.name == "cpython" and sys.version_info.major == 3 and sys.version_info.minor >= 14
    assert str(Path(sys.executable).absolute()) == selected
    prefix = Path(selected).parent.parent
    assert prefix.is_absolute() and prefix.is_dir() and prefix != Path(sys.base_prefix).absolute()
    observed = Path(sys.prefix).absolute()
    assert observed == prefix
    configuration = regular_bytes(prefix / "pyvenv.cfg").decode("utf-8")
    assert any(line.partition("=")[0].strip() == "home" and line.partition("=")[2].strip() for line in configuration.splitlines())
    assert all("\n" not in item and "\t" not in item for item in (selected, str(prefix)))
    pid = os.getpid()
    receipt = f"{nonce}\t{pid}\t{selected}\t{prefix}\t{sys.version_info.major}.{sys.version_info.minor}\n".encode()
    assert len(receipt) < 4096
    assert os.write(3, receipt) == len(receipt)
    if not select.select([4], [], [], min(10, budget))[0]:
        raise TimeoutError("Prepared parent did not admit the native startup receipt")
    continuation = os.read(4, 4096).decode().rstrip("\n").split("\t")
    assert len(continuation) == 3 and continuation[:2] == [nonce, str(pid)]
    elapsed = int(continuation[2])
    assert elapsed >= 0
    # Bash 3.2 provides whole-second elapsed time. Subtract one further second
    # conservatively, including first native exec rather than resetting budget.
    started = entered - elapsed - 1
    startup_deadline = started + min(30, budget)
    remaining = min(started + budget, startup_deadline) - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Whole-dispatch deadline expired during native admission")
    signal.setitimer(signal.ITIMER_REAL, remaining)
    os.environ["TEMPLATE_PREPARED_DISPATCH_STARTED"] = repr(started)
    os.environ["TEMPLATE_PREPARED_STARTUP_DEADLINE"] = repr(startup_deadline)
    os.close(3)
    os.close(4)
    seed = Path(root) / "scripts/runner/prepared_dispatch.py"
    content = regular_bytes(seed)
    main = sys.modules["__main__"]
    main.__file__ = str(seed)
    main.__cached__ = None
    main.__spec__ = None
    sys.argv = [str(seed), *arguments]
    exec(compile(content, str(seed), "exec", dont_inherit=True), main.__dict__)
except KeyboardInterrupt:
    raise SystemExit(130) from None
except TimeoutError as error:
    print(f"TIMED OUT: {error}", file=sys.stderr)
    raise SystemExit(124) from None
except (AssertionError, OSError, ValueError) as error:
    print(f"BLOCKED: prepared root admission refused: {error}; run uv sync --locked explicitly.", file=sys.stderr)
    raise SystemExit(75) from None
' "$selected" "$repository_root" "$nonce" "$@" <&0 &
    child_pid=$!
    trap 'interrupted=1; kill -INT "$child_pid" 2>/dev/null || true' INT TERM
    receipt=""
    while kill -0 "$child_pid" 2>/dev/null && ((SECONDS - native_started < native_limit)); do
        if ((interrupted)); then
            break
        fi
        if IFS= read -r -n 4096 -t 1 -u 3 receipt; then
            break
        fi
    done
    local observed_nonce observed_pid observed_python observed_prefix observed_version extra
    IFS=$'\t' read -r observed_nonce observed_pid observed_python observed_prefix observed_version extra <<<"$receipt"
    if ((interrupted)); then
        kill -KILL "$child_pid" 2>/dev/null || true
        wait "$child_pid" 2>/dev/null || true
        status=130
    elif ((SECONDS - native_started >= native_limit)) || [[ "$observed_nonce" != "$nonce" || "$observed_pid" != "$child_pid" || "$observed_python" != "$selected" || "$observed_prefix" != "$(dirname "$(dirname "$selected")")" || ! "$observed_version" =~ ^3\.[0-9]+$ || -n "$extra" || ${#receipt} -ge 4096 ]]; then
        if kill -0 "$child_pid" 2>/dev/null; then
            kill -KILL "$child_pid" 2>/dev/null || true
            wait "$child_pid" 2>/dev/null || true
            if ((SECONDS - native_started >= native_limit)); then
                echo "TIMED OUT: native prepared interpreter did not arm its finite startup receipt." >&2
                status=124
            else
                echo "BLOCKED: selected root interpreter emitted an invalid admission receipt." >&2
                status=75
            fi
        else
            wait "$child_pid" || status=$?
            if [[ "$status" != 124 && "$status" != 130 && "$status" != 2 ]]; then
                status=75
                print_preparation_instructions "${0##*/}"
            fi
        fi
    else
        printf '%s\t%s\t%s\n' "$nonce" "$child_pid" "$((SECONDS - native_started))" >&4
        # wait may be interrupted before the actual child has finished guardian
        # cleanup. Retry until that same admitted child has really exited.
        while true; do
            status=0
            wait "$child_pid" || status=$?
            if ! kill -0 "$child_pid" 2>/dev/null; then
                break
            fi
        done
        if ((interrupted)); then
            status=130
        fi
    fi
    trap - INT TERM
    exec 3>&- 4>&-
    return "$status"
}

print_preparation_instructions() {
    local script_name="${1:-run.sh}"
    cat >&2 <<EOF
${script_name} requires an existing prepared Python 3.14+ environment.

Explicit preparation (not performed by ordinary execution):
  bash scripts/shell/setup-system-deps.sh --check
  uv sync --locked
  uv sync --locked --group steganography  # for secure PDF operations

To use another prepared environment, nominate its absolute interpreter:
  TEMPLATE_ROOT_PYTHON=/absolute/environment/bin/python ./${script_name}

Inspect and repair a broken nominated environment explicitly; execution never
installs uv, resolves dependencies, syncs environments, or switches runtimes.
EOF
}
