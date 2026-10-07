# setup-acceptance-model contract

This composite action only orchestrates preparation of one pinned local model and its owned daemon.
Do not call it on a shared workstation. It uses fresh `RUNNER_TEMP` storage
and the disposable hosted runner's user font/tool directories. Third-party
archives and model blobs must retain their exact source-pinned hashes and lengths.

The model action binds an unoccupied loopback port, disables cloud operations
and implicit model acquisition, and records its owned daemon PID and birth.
Every caller of that action must perform identity-checked process-group cleanup
in an `always()` step. No shared service may be stopped or replaced.

Run `actionlint` after edits and retain genuine failed preparation diagnostics.
See [README.md](README.md) for usage.

An owned supervisor remains the process-group anchor throughout observation,
including when the server or its first runner exits. It ignores SIGTERM so
cleanup retains a verified owner until the final whole-group SIGKILL and live
member readback. Cleanup authenticates PID/birth identities and refuses reuse.
