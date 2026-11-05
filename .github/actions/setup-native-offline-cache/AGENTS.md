# Offline native cache action contract

Use after checkout and Python/uv provisioning, before Source custody and any
installed observation. No acceptance outputs are defined; `project-scopes` only
selects which locks are warmed. Preserve the fresh job-owned
`native-installed-cache` directory, locked dependency exports, actual
normalization, required hashes and existing build policy.

Root is always warmed. Callers that install another lock must name it in
`project-scopes`, because a scope whose own `uv.lock` resolves a package
differently from Root cannot install from a Root-only warm. Take the selection
from `native_installed_launcher --print-preparation-scopes` rather than
re-deriving it in shell; one predicate keeps warming and preparation aligned.
Never expand the default to the whole roster: a sharded cell warms its own lock
plus Root, not 25 locks.

The unchanged cold factory must consume the prepared cache independently;
never replace its original results with preparation success. Keep credentials
out of this action and preserve Root/project declarations and locks. Maintain
the local documentation pair and run actionlint after edits. See the
[parent action contract](../AGENTS.md) and [README.md](README.md).
