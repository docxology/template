# Native loader observation assets

`linux_audit.c` implements the bounded glibc loader callback protocol for the
supported Linux x86_64 and aarch64 ABIs. The Source-owned Python observer selects
its compiler flags and retains the actual process and loader events.

`persistent_rx_drift.c` is a real qualification control. It changes a private
executable mapping and crosses a later loader boundary so the observer can
demonstrate rejection. It does not modify the official executable under test.

These sources are inputs to qualification. Their presence, successful compilation
or a control's output alone does not establish complete native acceptance.
