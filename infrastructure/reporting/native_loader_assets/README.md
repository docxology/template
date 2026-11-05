# Native loader observation assets

`linux_audit.c` implements the bounded glibc loader callback protocol for the
supported Linux x86_64 and aarch64 ABIs. The Source-owned Python observer selects
its compiler flags and retains the actual process and loader events.

`persistent_rx_drift.c` is a real qualification control. It changes a private
executable mapping and crosses a later loader boundary so the observer can
demonstrate rejection. It does not modify the official executable under test.

These sources are inputs to qualification. Their presence, successful compilation
or a control's output alone does not establish complete native acceptance.

## `fail` must stay declared `noreturn`

`linux_audit.c` builds under `-Wall -Wextra -Werror`, so every warning is fatal.
Its `fail()` terminates through `exit_group`, and callers rely on that: `get()`
ends with `fail();` and has no trailing `return`. The declaration therefore
carries `_Noreturn` (C11, which `-std=c11` selects) or
`__attribute__((noreturn))` as the GCC/Clang fallback.

Removing it does not merely warn: it fails the audit-loader build, and the
renderer then reports a missing PDF rather than the compile error that caused it.
Hosted run 41940842593 hit exactly that in `template_madlib` and
`template_pools_rules_tools`.

The attribute is only truthful because the syscall cannot return. Marking a
function `noreturn` that can return is undefined behaviour at every call site, so
change this only together with the syscall it rests on.

